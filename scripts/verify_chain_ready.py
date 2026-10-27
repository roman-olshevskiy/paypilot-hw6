"""Run canonical native CLI on a clean clone using recorded full-series HTTP fixtures.
No network or new model calls. This does not claim a new live clean-clone run."""
import contextlib,hashlib,importlib.util,io,json,os,shutil,subprocess,sys,tempfile,uuid
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def git(*args,cwd=ROOT):return subprocess.check_output(["git",*args],cwd=cwd,text=True).strip()
def main():
    output=ROOT/"evidence/chain-ready"/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+"-"+uuid.uuid4().hex[:8])
    output.mkdir(parents=True)
    lookup={}
    for batch in read(ROOT/"evidence/full-run-index.json"):
        for row in read(ROOT/batch["folder"]/"captures.json"):
            if row["live"]:lookup[(row["scenario"],row["condition"],row["repeat"])]=row
    expected={(g["scenario"],g["condition"],g["repeat"]):g["native_passed"] for g in read(ROOT/"evidence/full-run-analysis.json")["groups"]}
    parent=Path(tempfile.gettempdir()).resolve()
    workspace=Path(tempfile.mkdtemp(prefix="hw6-clean-replay-",dir=parent)).resolve()
    clone=workspace/"clone";sys.dont_write_bytecode=True
    try:
        subprocess.run(["git","clone","--local","--no-hardlinks",str(ROOT),str(clone)],check=True,capture_output=True)
        assert not git("status","--porcelain",cwd=clone)
        for path in ["run_step.py","build_mock.py"]+[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/"scenarios").glob("*.json"))]:
            assert (ROOT/path).read_bytes()==(clone/path).read_bytes()
        spec=importlib.util.spec_from_file_location("native_clean_hw6",clone/"run_step.py")
        native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
        active={};counts={};replayed=[]
        def no_network(base,method,path,body=None,headers=None,timeout=300):
            if method=="GET" and path.startswith("/api/_test/state/"):
                return active["row"]["state_after"][path.split("/")[-1]]
            if path.startswith("/mockserver/retrieve"):
                return [{}]*active["row"]["proxy_counts"]["received"]
            raise AssertionError("Unexpected HTTP during offline replay: "+method+" "+path)
        def once(scenario,settings):
            condition=next(k for k,v in scenario["conditions"].items() if v==settings)
            key=(scenario["id"],condition);counts[key]=counts.get(key,0)+1
            triple=(*key,counts[key]);row=lookup[triple];active["row"]=row
            replayed.append(triple)
            scripted=sum(len(t.get("model",[])) for t in scenario["turns"] if not t.get("live"))
            return row["step"],row["response"],row["trace"],scripted
        native._call=no_network;native.run_once=once
        native.doctor=lambda scenarios:{"provider":"recorded-offline-replay"}
        tests=[]
        for label,args in [("daily",["--gate","daily"]),("baseline",["--condition","baseline"]),("release",["--gate","release"])]:
            counts.clear();replayed.clear()
            console=io.StringIO();report=output/(label+"-replay.json")
            saved=sys.argv[:];sys.argv=["run_step.py",*args,"--json",str(report)]
            try:
                with contextlib.redirect_stdout(console):native.main()
            finally:sys.argv=saved
            (output/(label+"-console.txt")).write_bytes(console.getvalue().encode())
            raw=read(report);n=passed=0
            for item in raw:
                for row in item["runs"]:
                    assert row["passed"]==expected[(item["scenario"],item["condition"],row["run"])]
                    n+=1;passed+=row["passed"]
                    if item["condition"]=="baseline":assert row["passed"]
            tests.append({"canonical_equivalent":"docker compose run --rm eval "+" ".join(args),"execution":"Python native.main() from clean clone with recorded fixtures; Docker command not executed","scope":"Native CLI recorded replay, not new live calls","repeats":n,"passed":passed,"report":report.name})
        assert not git("status","--porcelain",cwd=clone)
        result={"date":"2026-10-27","cloned_commit":git("rev-parse","HEAD",cwd=clone),
          "native_clone_clean_before_and_after":True,"native_code_and_scenarios_identical":True,
          "commands":tests,"all_original_full_native_verdicts_reproduced":True,
          "real_stand_requests":0,"real_model_calls":0,"fresh_live_clean_clone_run":False,
          "live_basis":"Existing full daily/release captures, baseline34/34; pilot excluded from frequency"}
        (output/"verification.json").write_bytes((json.dumps(result,indent=2)+"\n").encode())
        print(json.dumps(result,indent=2))
        print("Output:",output)
    finally:
        assert workspace.parent==parent and workspace.name.startswith("hw6-clean-replay-")
        shutil.rmtree(workspace)
if __name__=="__main__":main()
