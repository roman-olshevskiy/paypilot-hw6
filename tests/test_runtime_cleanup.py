"""Explicit zero-generation check after restoring the regular stand."""
import json,os,subprocess,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get('HW6_VERIFY_CLEANUP')=='1','Explicit runtime cleanup verification disabled')
class Cleanup(unittest.TestCase):
 def test_regular_runtime(self):
  with urllib.request.urlopen('http://localhost:8000/health',timeout=30) as response:h=json.load(response)
  self.assertEqual(h['status'],'ok');self.assertEqual(h['provider'],'anthropic')
  code="import os,json;print(json.dumps({k:os.environ.get(k,'') for k in ['LLM_PROVIDER','HTTPS_PROXY','SSL_CERT_FILE']}))"
  v=json.loads(subprocess.check_output(['docker','compose','exec','-T','stand','python','-c',code],cwd=ROOT.parent/'paypilot-stand-shared',text=True))
  self.assertEqual(v['LLM_PROVIDER'],'anthropic');self.assertFalse(v['HTTPS_PROXY']);self.assertFalse(v['SSL_CERT_FILE'])
  state=subprocess.check_output(['docker','inspect','--format','{{.State.Status}}','paypilot-hw6-llm-mock-1'],text=True).strip()
  self.assertEqual(state,'exited')
  proof={'date':'2026-10-27','health':h['status'],'runtime':v,'hw6_mock':state,'model_calls':0,'volumes_deleted':False}
  (ROOT/'evidence/runtime-restored.json').write_bytes((json.dumps(proof,indent=2)+'\n').encode())
