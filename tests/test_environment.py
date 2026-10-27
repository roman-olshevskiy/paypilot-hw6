import os,json,unittest,urllib.request,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STAND=ROOT.parent/'paypilot-stand-shared'
def api(base,path,method='GET',data=None,headers=None):
    req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,
                               method=method,headers={'Content-Type':'application/json',**(headers or {})})
    with urllib.request.urlopen(req,timeout=30) as response:
        raw=response.read()
        return json.loads(raw) if raw else None
def stand(path,**kw):return api('http://localhost:8000',path,**kw)
def mock(path,**kw):return api('http://localhost:1080',path,**kw)

@unittest.skipUnless(os.environ.get('HW6_RUN_ENVIRONMENT')=='1','Explicit environment tests disabled')
class Environment(unittest.TestCase):
    def test_01_health(self):
        h=stand('/health')
        self.assertEqual(h['status'],'ok')
        self.assertEqual(h['provider'],'openrouter')
    def test_02_registry(self):
        self.assertTrue({'D11','D12','D13','D28','D29'}.issubset(stand('/api/_test/defects')['all_defects']))
        result=stand('/api/_test/tools')
        self.assertEqual(len(result['tools'] if isinstance(result,dict) else result),9)
    def test_03_runtime(self):
        script="import os,json;print(json.dumps({**{k:os.environ.get(k,'') for k in ['LLM_PROVIDER','LLM_MODEL','PROFILE','DEFECTS','HTTPS_PROXY','SSL_CERT_FILE']},'key_present':bool(os.environ.get('OPENROUTER_API_KEY'))}))"
        data=json.loads(subprocess.check_output(['docker','compose','exec','-T','stand','python','-c',script],cwd=STAND,text=True))
        self.assertEqual(data['LLM_PROVIDER'],'openrouter')
        self.assertEqual(data['LLM_MODEL'],'anthropic/claude-haiku-5.5')
        self.assertEqual(data['PROFILE'],'clean');self.assertEqual(data['DEFECTS'],'')
        self.assertEqual(data['HTTPS_PROXY'],'http://host.docker.internal:1080')
        self.assertEqual(data['SSL_CERT_FILE'],'/certs/mockserver-ca.pem')
        self.assertTrue(data['key_present'])
        (ROOT/'evidence/preflight-runtime.json').write_bytes((json.dumps(data,indent=2)+'\n').encode())
    def test_04_ca(self):
        code="import hashlib;print(hashlib.sha256(open('/certs/mockserver-ca.pem','rb').read()).hexdigest())"
        actual=subprocess.check_output(['docker','compose','exec','-T','stand','python','-c',code],cwd=STAND,text=True).strip()
        self.assertEqual(actual,hashlib.sha256((ROOT/'mock/mockserver-ca.pem').read_bytes()).hexdigest())
    def test_05_expectations(self):
        active=mock('/mockserver/retrieve?type=ACTIVE_EXPECTATIONS',method='PUT',data={})
        expected=json.loads((ROOT/'mock/expectations.json').read_text())
        self.assertEqual({x['id'] for x in active},{x['id'] for x in expected})
    def test_06_mock_route_without_upstream_fallback(self):
        guard='hw6-environment-block-unmatched'
        states={name:stand('/api/_test/state/'+name) for name in ['disputes','statements_sent','escalations']}
        query={'path':'.*/chat/completions'}
        before=mock('/mockserver/retrieve?type=RECORDED_EXPECTATIONS',method='PUT',data=query)
        mock('/mockserver/expectation',method='PUT',data={
            'id':guard,'priority':-100,
            'httpRequest':{'method':'POST','path':'.*'},
            'httpResponse':{'statusCode':503,'body':'Unmatched model request blocked during zero-cost setup test'}})
        try:
            scenario=json.loads((ROOT/'scenarios/hw6-01.json').read_text())
            first=scenario['turns'][0]
            response=stand('/chat',method='POST',data={'message':first['user'],'customer_id':scenario['customer_id']},
                           headers={'X-Stand-Settings':json.dumps({'profile':'clean','defects':''})})
            self.assertEqual(response['answer'],first['model'][-1]['text'])
            self.assertEqual(response['usage']['input_tokens'],0)
            self.assertEqual(response['usage']['output_tokens'],0)
            self.assertEqual(response['usage']['cost_usd'],0)
            trace=stand('/api/_test/traces/'+response['request_id'])
            for name,old in states.items():self.assertEqual(stand('/api/_test/state/'+name),old)
            after=mock('/mockserver/retrieve?type=RECORDED_EXPECTATIONS',method='PUT',data=query)
            self.assertEqual(len(after),len(before),'Unexpected request was forwarded upstream')
            proof={'response':response,'trace':trace,'upstream_forwarded_delta':len(after)-len(before),
                   'fallback_blocked':True,'action_tables_unchanged':True,'scope':'Known first S1 turn only; live routing not exercised'}
            (ROOT/'evidence/preflight-mock-route.json').write_bytes((json.dumps(proof,ensure_ascii=False,indent=2)+'\n').encode())
        finally:
            mock('/mockserver/clear',method='PUT',data={'id':guard})
            remaining=mock('/mockserver/retrieve?type=ACTIVE_EXPECTATIONS',method='PUT',data={})
            expected=json.loads((ROOT/'mock/expectations.json').read_text())
            self.assertEqual({x['id'] for x in remaining},{x['id'] for x in expected})


    def test_07_tool_contract_snapshots(self):
        before=stand('/api/_test/defects')
        baseline=stand('/api/_test/tools',headers={'X-Stand-Settings':json.dumps({'profile':'clean','defects':''})})
        changed=stand('/api/_test/tools',headers={'X-Stand-Settings':json.dumps({'profile':'clean','defects':'D13'})})
        def tools(result):
            rows=result['tools'] if isinstance(result,dict) else result
            return {x['name']:x for x in rows}
        b,d=tools(baseline),tools(changed)
        self.assertEqual(len(b),9)
        for name in ['check_limits','get_transactions']:
            self.assertNotEqual(b[name]['description'],d[name]['description'])
        self.assertEqual(stand('/api/_test/defects'),before)
        (ROOT/'evidence/tool-contracts.json').write_bytes((json.dumps({'baseline':baseline,'D13':changed},ensure_ascii=False,indent=2)+'\n').encode())

    def test_08_request_scope_and_runtime_sources(self):
        before={name:stand('/api/_test/'+name) for name in ['clock','summarize_after','defects']}
        headers={'X-Stand-Settings':json.dumps({'profile':'clean','defects':'D28','clock':'2026-09-15T10:00:00Z','summarize_after':8})}
        self.assertEqual(stand('/api/_test/clock',headers=headers)['request_override'],'2026-09-15T10:00:00Z')
        self.assertEqual(stand('/api/_test/summarize_after',headers=headers)['summarize_after_steps'],8)
        self.assertEqual({name:stand('/api/_test/'+name) for name in before},before)
        paths=['app/seed.py','app/runctx.py','app/agent/tools.py','app/agent/loop.py','app/agent/prompt.py','app/agent/providers/openrouter_provider.py']
        code="import hashlib,json;paths="+repr(paths)+";print(json.dumps({p:hashlib.sha256(open('/stand/'+p,'rb').read()).hexdigest() for p in paths}))"
        actual=json.loads(subprocess.check_output(['docker','compose','exec','-T','stand','python','-c',code],cwd=STAND,text=True))
        for path,digest in actual.items():self.assertEqual(hashlib.sha256((STAND/path).read_bytes()).hexdigest(),digest)
        (ROOT/'evidence/preflight-runtime-sources.json').write_bytes((json.dumps(actual,indent=2)+'\n').encode())


    def test_09_openrouter_model_catalogue(self):
        data=api('https://openrouter.ai','/api/v1/models')
        selected=[m for m in data['data'] if m.get('id')=='anthropic/claude-haiku-5.5']
        self.assertEqual(len(selected),1,'Configured L07 model is absent from the public catalogue')
        m=selected[0]
        safe={k:m.get(k) for k in ['id','name','context_length','pricing','supported_parameters']}
        (ROOT/'evidence/preflight-model-catalogue.json').write_bytes((json.dumps(safe,ensure_ascii=False,indent=2)+'\n').encode())
