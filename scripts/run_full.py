"""Run daily and release once, with native scenario runs, never auto-retry chat."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from hw6_capture import verify_forecast
def main():
    verify_forecast(ROOT)
    results=[]
    for gate in ["daily","release"]:
        parent=ROOT/"evidence/runs"
        before=set(parent.iterdir())
        process=subprocess.Popen([sys.executable,"-u",str(ROOT/"scripts/hw6_capture.py"),"--gate",gate],
                                 cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8")
        chunks=[]
        for line in process.stdout:
            chunks.append(line);print(line,end="",flush=True)
        code=process.wait()
        folders=set(parent.iterdir())-before
        if len(folders)!=1:raise RuntimeError("Expected exactly one new gate folder")
        folder=folders.pop()
        (folder/"console.txt").write_bytes("".join(chunks).encode())
        manifest=json.loads((folder/"manifest.json").read_text())
        results.append({"gate":gate,"folder":folder.relative_to(ROOT).as_posix(),"manifest":manifest})
        (ROOT/"evidence/full-run-index.json").write_bytes((json.dumps(results,indent=2)+"\n").encode())
        if code or manifest["error"] or manifest["restore_errors"]:
            raise RuntimeError("Stopped on capture/restore failure; no automatic repeat")
        raw=json.loads((folder/"raw-results.json").read_text())
        expected=0
        for entry in raw:
            case=json.loads((ROOT/"scenarios"/(entry["scenario"].lower()+".json")).read_text())
            expected+=len(case["turns"])*case["runs"]
        if manifest["responses"]!=expected or manifest["complete"]!=expected:
            raise RuntimeError("Incomplete gate capture")
        if any(not run["passed"] for entry in raw if entry["condition"]=="baseline" for run in entry["runs"]):
            raise RuntimeError("Baseline failure: preserved evidence; stop before further gates")
    print("Both full gates complete; no additional suite launched.",flush=True)
if __name__=="__main__":main()
