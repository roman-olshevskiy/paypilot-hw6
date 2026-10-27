"""One supplemental baseline/D11 pair; no retries, no edits to original freeze."""
import json,os,sys,tempfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from hw6_capture import Capture,verify_forecast
import run_step as native
D=ROOT/'supplemental/d11-no-currency'
def main():
 verify_forecast(ROOT)
 proof=json.loads((D/'before-run.json').read_text())
 for n,h in proof['sha256'].items():
  assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h
 marker=D/'run-index.json'
 if marker.exists():raise RuntimeError('Supplement already attempted; no automatic retry')
 marker.write_text(json.dumps({'status':'started'}))
 expectations=json.loads((D/'expectations.json').read_text())
 ids=[x['id'] for x in expectations]
 saved_root=native.ROOT
 capture=Capture(ROOT)
 try:
  for x in expectations:native._call(native.MOCK,'PUT','/mockserver/expectation',x)
  with tempfile.TemporaryDirectory(prefix='hw6-d11-suite-') as tmp:
   folder=Path(tmp);(folder/'scenarios').mkdir()
   (folder/'scenarios/scenario.json').write_bytes((D/'scenario.json').read_bytes())
   native.ROOT=folder
   code=capture.execute(['--scenario','HW6-D11-R1','--runs','1'])
  marker.write_text(json.dumps({'status':'complete' if code==0 else 'failed','folder':capture.folder.relative_to(ROOT).as_posix(),'supplemental_freeze':'supplemental/d11-no-currency/before-run.json'},indent=2))
  print('Capture:',capture.folder)
  if code:raise SystemExit(code)
 finally:
  native.ROOT=saved_root
  for identity in ids:native._call(native.MOCK,'PUT','/mockserver/clear?type=EXPECTATIONS',{'id':identity})
if __name__=='__main__':main()
