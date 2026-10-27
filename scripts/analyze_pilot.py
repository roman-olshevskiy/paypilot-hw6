"""Offline completeness and native-verdict analysis of the six-live-step pilot."""
import hashlib,json
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def main():
    index=read(ROOT/"evidence/pilot-run-index.json")
    assert [x["scenario"] for x in index]==["HW6-01","HW6-09","HW6-10"]
    all_rows=[];groups=[]
    for entry in index:
        folder=ROOT/entry["folder"];manifest=read(folder/"manifest.json")
        assert manifest["exit_code"]==0 and manifest["error"] is None and not manifest["restore_errors"]
        assert manifest["restore_status"]=="passed" and manifest["responses"]==manifest["complete"]
        for name,digest in manifest["report_sha256"].items():
            assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==digest
        raw=read(folder/"raw-results.json");rows=read(folder/"captures.json");all_rows+=rows
        assert len(raw)==2
        for condition in raw:
            assert len(condition["runs"])==1
            live=[x for x in rows if x["condition"]==condition["condition"] and x["live"]]
            assert len(live)==1
            row=live[0];native=condition["runs"][0]
            assert row["response"]["request_id"]==row["trace"]["request_id"]
            assert native["answer"]==row["response"]["answer"]
            tools=[x for x in row["trace"].get("children",[]) if x["name"].startswith("tool.")]
            llm=[x for x in row["trace"].get("children",[]) if x["name"]=="llm.call"]
            target="TX-0402" if entry["scenario"]=="HW6-09" else "TX-0202"
            state=[x for x in row["state_after"]["disputes"]["rows"] if x.get("transaction_id")==target]
            groups.append({"scenario":entry["scenario"],"condition":condition["condition"],"native_passed":native["passed"],
              "request_id":row["response"]["request_id"],"session_id":row["response"]["session_id"],
              "root_usage":row["response"]["usage"],"model_calls":native["model_calls"],"cache_read":native["cache_read"],
              "tool_calls":[{"name":x["name"],"arguments":x["attributes"].get("tool.arguments"),"result":x["attributes"].get("tool.result")} for x in tools],
              "matching_disputes":state,"verdicts":native["verdicts"],
              "llm_usage":[{k:v for k,v in x["attributes"].items() if "usage" in k or "cost" in k or "model" in k} for x in llm]})
    assert len(all_rows)==18
    assert len({x["response"]["request_id"] for x in all_rows})==18
    assert len({x["response"]["session_id"] for x in all_rows})==6
    assert sum(x["live"] for x in all_rows)==6
    for row in all_rows:
        assert row["status"]=="complete"
        if not row["live"]:
            assert row["response"]["usage"]["input_tokens"]==0 and row["response"]["usage"]["cost_usd"]==0
    known=[Decimal(str(x["root_usage"]["cost_usd"])) for x in groups if x["root_usage"].get("cost_usd") is not None]
    cost=sum(known,Decimal(0)) if len(known)==6 else None
    cache={x["condition"]:x for x in groups if x["scenario"]=="HW6-10"}
    ratio=None
    if cache["baseline"]["root_usage"].get("cost_usd") and cache["defect"]["root_usage"].get("cost_usd") is not None:
        ratio=cache["defect"]["root_usage"]["cost_usd"]/cache["baseline"]["root_usage"]["cost_usd"]
    result={"date":"2026-10-27","groups":groups,"chat_requests":18,"live_steps":6,"mock_steps":12,"independent_sessions":6,
      "root_cost_usd":float(cost) if cost is not None else None,"cost_known_live_steps":len(known),
      "cache_step_cost_ratio":ratio,"linear_full_root_estimate_usd":float(cost/6*52) if cost is not None else None,
      "forecast_D29_forbidden_writes":"2/5, not testable from one pilot repeat",
      "forecast_D28_cost_ratio":2.5,"scope":"Pilot only; no5/5 frequency claim. Root estimate is not an invoice."}
    (ROOT/"evidence/pilot-analysis.json").write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+"\n").encode())
    print(json.dumps({k:v for k,v in result.items() if k!="groups"},indent=2))
    for x in groups:print(x["scenario"],x["condition"],"PASS" if x["native_passed"] else "FAIL",x["cache_read"],x["root_usage"].get("cost_usd"))
if __name__=="__main__":main()
