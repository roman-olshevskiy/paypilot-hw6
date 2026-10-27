import json,os,sys,hashlib,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));import build_mock
D=ROOT/'supplemental/d11-no-currency'
class Design(unittest.TestCase):
 def test_frozen_supplement(self):
  proof=json.loads((D/'before-run.json').read_text())
  for n,h in proof['sha256'].items():self.assertEqual(hashlib.sha256((D/n).read_bytes()).hexdigest(),h)
  s=json.loads((D/'scenario.json').read_text())
  self.assertEqual(build_mock.expectations_for(s),json.loads((D/'expectations.json').read_text()))
  self.assertEqual(sum(bool(t.get('live')) for t in s['turns']),1)
  self.assertNotRegex(s['turns'][-1]['user'],r'USD|EUR')
  self.assertEqual(s['assertions'][1]['expect_fields']['currency'],'USD')
 def test_saved_default_currency_path(self):
  index=json.loads((D/'run-index.json').read_text());folder=ROOT/index['folder']
  manifest=json.loads((folder/'manifest.json').read_text())
  self.assertEqual(manifest['restore_status'],'passed');self.assertEqual(manifest['complete'],4)
  for n,h in manifest['report_sha256'].items():self.assertEqual(hashlib.sha256((folder/n).read_bytes()).hexdigest(),h)
  raw=json.loads((folder/'raw-results.json').read_text())
  self.assertTrue(raw[0]['runs'][0]['passed']);self.assertFalse(raw[1]['runs'][0]['passed'])
  self.assertTrue(raw[1]['runs'][0]['verdicts'][0]['ok']);self.assertFalse(raw[1]['runs'][0]['verdicts'][1]['ok'])
  for row in json.loads((folder/'captures.json').read_text()):
   if not row['live']:continue
   calls=[x for x in row['trace']['children'] if x['name']=='tool.create_dispute'];self.assertEqual(len(calls),1)
   args=calls[0]['attributes']['tool.arguments'];args=json.loads(args) if isinstance(args,str) else args
   self.assertEqual(set(args),{'transaction_id','reason_code'})
@unittest.skipUnless(os.environ.get('HW6_D11_ENV')=='1','Explicit supplemental environment/billing disabled')
class Runtime(unittest.TestCase):
 def test_ready_and_usage(self):
  phase=os.environ['HW6_D11_PHASE'];output=D/('billing-'+phase+'.json');self.assertFalse(output.exists())
  if phase=='before':
   with urllib.request.urlopen('http://localhost:8000/health',timeout=30) as response:h=json.load(response)
   self.assertEqual(h['provider'],'openrouter');self.assertEqual(h['status'],'ok')
   req=urllib.request.Request('http://localhost:1080/mockserver/retrieve?type=ACTIVE_EXPECTATIONS',data=b'{}',method='PUT')
   with urllib.request.urlopen(req,timeout=30) as response:self.assertEqual(len(json.load(response)),26)
  values={}
  for line in (ROOT.parent/'paypilot-stand-shared/.env').read_text(encoding='utf-8-sig').splitlines():
   if '=' in line and not line.lstrip().startswith('#'):
    k,v=line.split('=',1);values[k.strip()]=v.strip().strip(chr(34)).strip(chr(39))
  req=urllib.request.Request('https://openrouter.ai/api/v1/key',headers={'Authorization':'Bearer '+values['OPENROUTER_API_KEY']})
  with urllib.request.urlopen(req,timeout=30) as response:data=json.load(response)['data']
  safe={k:data.get(k) for k in ['usage','byok_usage']};output.write_text(json.dumps(safe,indent=2));print(safe)

@unittest.skipUnless(os.environ.get('HW6_D11_CLEANUP')=='1','Explicit supplemental cleanup disabled')
class Cleanup(unittest.TestCase):
 def test_restored(self):
  import subprocess
  with urllib.request.urlopen('http://localhost:8000/health',timeout=30) as response:h=json.load(response)
  self.assertEqual(h['status'],'ok');self.assertEqual(h['provider'],'anthropic')
  code="import os,json;print(json.dumps({k:os.environ.get(k,'') for k in ['HTTPS_PROXY','SSL_CERT_FILE']}))"
  v=json.loads(subprocess.check_output(['docker','compose','exec','-T','stand','python','-c',code],cwd=ROOT.parent/'paypilot-stand-shared',text=True))
  self.assertFalse(v['HTTPS_PROXY']);self.assertFalse(v['SSL_CERT_FILE'])
  state=subprocess.check_output(['docker','inspect','--format','{{.State.Status}}','paypilot-hw6-llm-mock-1'],text=True).strip()
  self.assertEqual(state,'exited')
  (D/'runtime-restored.json').write_text(json.dumps({'provider':h['provider'],'runtime':v,'mock':state,'model_calls':0},indent=2))
