"""Capture native L07 runs. Explicit paid guard; no automatic chat retries."""
import argparse,hashlib,json,os,subprocess,sys,time,uuid
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import run_step as native

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scenarios_digest(root):
    rows=[(p.name,sha(p)) for p in sorted((root/"scenarios").glob("*.json"))]
    return hashlib.sha256(json.dumps(rows,separators=(",",":")).encode()).hexdigest()
def verify_forecast(root):
    if os.environ.get("HW6_ENABLE_PAID_RUNS")!="1":raise RuntimeError("Paid runs disabled")
    frozen=json.loads((root/"evidence/dataset-freeze.json").read_text())
    if scenarios_digest(root)!=frozen["suite_sha256"]:raise RuntimeError("Scenario freeze mismatch")
    if sha(root/"mock/expectations.json")!=frozen["expectations_sha256"]:raise RuntimeError("Mock freeze mismatch")
    proof=json.loads((root/"evidence/forecast-commit.json").read_text())
    commit=proof["commit"]
    if len(commit)!=40 or any(c not in "0123456789abcdef" for c in commit):raise RuntimeError("Invalid forecast commit")
    for name in ["docs/forecast-before-runs.md","mock/expectations.json"]+[p.relative_to(root).as_posix() for p in sorted((root/"scenarios").glob("*.json"))]:
        saved=subprocess.check_output(["git","show",commit+":"+name],cwd=root)
        if saved!=(root/name).read_bytes():raise RuntimeError("Forecast commit content mismatch: "+name)
    stamp=int(subprocess.check_output(["git","show","-s","--format=%ct",commit],cwd=root,text=True))
    if stamp>=time.time():raise RuntimeError("Forecast commit is not before this run")
    return proof
class CaptureFailure(RuntimeError):pass
class Capture:
    def __init__(self,root,module=native):
        self.root=Path(root);self.native=module
        self.folder=self.root/"evidence/runs"/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+"-"+uuid.uuid4().hex[:8])
        self.folder.mkdir(parents=True,exist_ok=False)
        self.rows=[];self.attempts=[];self.context={};self.repeat=0;self.step=0
        self.original_call=module._call;self.original_run=module.run
        self.before=None;self.error=None;self.restore_errors=[];self.results=[]
    def save(self,name,value):
        path=self.folder/name;temp=path.with_suffix(path.suffix+".tmp")
        data=(json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode()
        for n in range(8):
            try:temp.write_bytes(data);temp.replace(path);return
            except PermissionError:
                if n==7:raise
                time.sleep(min(.05*2**n,.5))
    def snapshot(self):
        return {key:self.original_call(self.native.STAND,"GET",path) for key,path in
          [("health","/health"),("defects","/api/_test/defects"),("clock","/api/_test/clock"),
           ("summarize","/api/_test/summarize_after"),("retrieval","/api/_test/retrieval")]}
    def proxy_counts(self):
        query={"path":".*/chat/completions"}
        return {name:len(self.original_call(self.native.MOCK,"PUT","/mockserver/retrieve?type="+kind,query))
          for name,kind in [("received","REQUESTS"),("forwarded","RECORDED_EXPECTATIONS")]}
    def call(self,base,method,path,body=None,headers=None,timeout=300):
        if base==self.native.STAND and method=="POST" and path=="/api/_test/reset":
            self.repeat+=1;self.step=0
        if not(base==self.native.STAND and method=="POST" and path=="/chat"):
            return self.original_call(base,method,path,body,headers,timeout)
        self.step+=1
        attempt={**self.context,"repeat":self.repeat,"step":self.step,"request":body,"status":"started"}
        self.attempts.append(attempt);self.save("attempts.json",self.attempts)
        try:
            response=self.original_call(base,method,path,body,headers,timeout)
        except Exception as e:
            attempt.update(status="unknown_or_failed_response",error=type(e).__name__)
            self.save("attempts.json",self.attempts)
            raise CaptureFailure("Chat failed; no automatic retry") from e
        row={**self.context,"repeat":self.repeat,"step":self.step,"request":body,"response":response,"status":"response_saved"}
        self.rows.append(row)
        attempt.update(status="response_received",request_id=response.get("request_id"))
        self.save("captures.json",self.rows);self.save("attempts.json",self.attempts)
        try:
            row["trace"]=self.original_call(self.native.STAND,"GET","/api/_test/traces/"+response["request_id"])
            row["status"]="trace_saved";self.save("captures.json",self.rows)
            row["state_after"]={name:self.original_call(self.native.STAND,"GET","/api/_test/state/"+name)
              for name in ["disputes","statements_sent","escalations"]}
            row["proxy_counts"]=self.proxy_counts()
            row["live"]=self.scenario["turns"][self.step-1].get("live",False)
            if not row["live"] and any(response.get("usage",{}).get(k,0) for k in ["input_tokens","output_tokens","cost_usd"]):
                raise CaptureFailure("A scripted mock step incurred usage; stop")
            if response["request_id"]!=row["trace"]["request_id"]:raise CaptureFailure("Trace identity mismatch")
            row["status"]="complete";self.save("captures.json",self.rows)
        except Exception as e:
            raise CaptureFailure("Incomplete capture; no automatic retry") from e
        return response
    def run(self,scenario,condition,settings,runs):
        self.scenario=scenario;self.context={"scenario":scenario["id"],"condition":condition,"settings":settings}
        self.repeat=0
        rows=self.original_run(scenario,condition,settings,runs)
        diagnostics=[{"repeat":row["run"],"failed_preconditions":[i for i,(a,v) in enumerate(zip(scenario["assertions"],row["verdicts"])) if a.get("precondition") and not v["ok"]]} for row in rows]
        self.results.append({"scenario":scenario["id"],"condition":condition,"settings":settings,"runs":rows,"diagnostics":diagnostics})
        self.save("completed-conditions.json",self.results)
        return rows
    def restore(self):
        if self.before is None:return
        now=self.snapshot();old=self.before
        tasks=[]
        if now["defects"]["profile"]!=old["defects"]["profile"]:tasks.append(("/api/_test/profile",{"profile":old["defects"]["profile"]}))
        if now["defects"]["extra_defects"]!=old["defects"]["extra_defects"]:tasks.append(("/api/_test/defects",{"defects":",".join(old["defects"]["extra_defects"])}))
        if now["clock"]["runtime_override"]!=old["clock"]["runtime_override"]:tasks.append(("/api/_test/clock",{"now":old["clock"]["runtime_override"]}))
        if now["summarize"]["summarize_after_steps"]!=old["summarize"]["summarize_after_steps"]:tasks.append(("/api/_test/summarize_after",{"steps":old["summarize"]["summarize_after_steps"]}))
        if any(now["retrieval"][k]!=old["retrieval"][k] for k in ["index_env","rag_top_k"]):
            tasks.append(("/api/_test/retrieval",{"index":old["retrieval"]["index_env"],"top_k":old["retrieval"]["rag_top_k"]}))
        for path,body in tasks:
            try:self.original_call(self.native.STAND,"PUT",path,body)
            except Exception as e:self.restore_errors.append({"path":path,"error":type(e).__name__})
        after=self.snapshot();self.save("restored.json",after)
        for key,fields in {"defects":["profile","extra_defects"],"clock":["runtime_override"],"summarize":["summarize_after_steps"],"retrieval":["index_env","rag_top_k"]}.items():
            if any(after[key][f]!=old[key][f] for f in fields):self.restore_errors.append({"key":key,"error":"snapshot mismatch"})
    def execute(self,args):
        saved_argv=sys.argv[:];code=0
        try:
            self.before=self.snapshot();self.save("before.json",self.before)
            self.native._call=self.call;self.native.run=self.run
            sys.argv=["run_step.py",*args,"--json",str(self.folder/"raw-results.json")]
            self.native.main()
        except SystemExit as e:
            code=e.code if isinstance(e.code,int) else 2
            if code:self.error=str(e)
        except Exception as e:
            code=2;self.error=type(e).__name__+": "+str(e)
        finally:
            sys.argv=saved_argv;self.native._call=self.original_call;self.native.run=self.original_run
            try:self.restore()
            except Exception as e:self.restore_errors.append({"error":type(e).__name__})
            if self.restore_errors:code=2
            reports={p.name:sha(p) for p in [self.folder/"raw-results.json"] if p.exists()}
            self.save("manifest.json",{"args":args,"exit_code":code,"error":self.error,"restore_errors":self.restore_errors,
              "restore_status":"passed" if self.before is not None and not self.restore_errors else "failed",
              "suite_sha256":scenarios_digest(self.root),"chat_attempts":len(self.attempts),"responses":len(self.rows),
              "complete":sum(x["status"]=="complete" for x in self.rows),"report_sha256":reports,
              "quality_passed":all(x["passed"] for c in self.results for x in c["runs"]) if self.results else None,
              "global_settings_scope":"Compared and restored if changed; per-request settings do not change server config",
              "database_scope":"Seed reset is real; arbitrary pre-run DB/session state is not restored",
              "proxy_scope":"Logs cleared by native runner, active expectations not changed by adapter"})
        return code
def main():
    # This guard must run before Capture or any HTTP/reset.
    verify_forecast(ROOT)
    args=sys.argv[1:]
    if "--json" in args:raise RuntimeError("Output is assigned per run; do not pass --json")
    capture=Capture(ROOT)
    code=capture.execute(args)
    print("Capture:",capture.folder)
    raise SystemExit(code)
if __name__=="__main__":main()
