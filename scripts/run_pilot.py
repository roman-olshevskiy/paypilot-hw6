"""Run only the approved six-live-step HW6 pilot, preserving each native report."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from hw6_capture import verify_forecast
def main():
    verify_forecast(ROOT)  # Before any subprocess/reset/model request.
    selected=["HW6-01","HW6-09","HW6-10"]
    result=[]
    for cid in selected:
        folder_root=ROOT/"evidence/runs"
        before=set(folder_root.iterdir()) if folder_root.exists() else set()
        child=subprocess.run([sys.executable,str(ROOT/"scripts/hw6_capture.py"),"--scenario",cid,"--runs","1"],
                             cwd=ROOT,capture_output=True,text=True,encoding="utf-8")
        after=set(folder_root.iterdir()) if folder_root.exists() else set()
        new=after-before
        if len(new)!=1:raise RuntimeError("Pilot did not create exactly one run folder: "+cid)
        folder=new.pop()
        (folder/"console.txt").write_bytes((child.stdout+child.stderr).encode())
        print(child.stdout,flush=True)
        if child.stderr:print(child.stderr,flush=True)
        manifest=json.loads((folder/"manifest.json").read_text())
        result.append({"scenario":cid,"folder":folder.relative_to(ROOT).as_posix(),
                       "exit_code":child.returncode,"manifest":manifest})
        (ROOT/"evidence/pilot-run-index.json").write_bytes((json.dumps(result,indent=2)+"\n").encode())
        if child.returncode or manifest["error"] or manifest["restore_errors"]:
            raise RuntimeError("Pilot stopped on incomplete capture or restore; do not auto-retry")
        case=json.loads((ROOT/"scenarios"/(cid.lower()+".json")).read_text())
        expected=len(case["turns"])*len(case["conditions"])
        if manifest["responses"]!=expected or manifest["complete"]!=expected:
            raise RuntimeError("Pilot capture count mismatch")
    print("Pilot completed; full suite not started.")
if __name__=="__main__":main()
