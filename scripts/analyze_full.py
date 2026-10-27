"""Analyze the selected full daily/release runs offline; keep pilot separate."""
import hashlib,json,subprocess
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def main():
    selected=read(ROOT/"evidence/full-run-index.json")
    assert [x["gate"] for x in selected]==["daily","release"]
    freeze=read(ROOT/"evidence/dataset-freeze.json")
    forecast=read(ROOT/"evidence/forecast-commit.json")
    committed=int(subprocess.check_output(["git","show","-s","--format=%ct",forecast["commit"]],cwd=ROOT,text=True))
    cases={c["id"]:c for c in [read(p) for p in sorted((ROOT/"scenarios").glob("*.json"))]}
    groups=[];all_rows=[];conditions=[]
    for batch in selected:
        folder=ROOT/batch["folder"]
        manifest=read(folder/"manifest.json")
        assert manifest["exit_code"]==0 and manifest["error"] is None and not manifest["restore_errors"]
        assert manifest["restore_status"]=="passed" and manifest["suite_sha256"]==freeze["suite_sha256"]
        for name,digest in manifest["report_sha256"].items():
            assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==digest
        raw=read(folder/"raw-results.json");rows=read(folder/"captures.json");all_rows+=rows
        assert len(rows)==manifest["complete"]==manifest["responses"]==manifest["chat_attempts"]
        for row in rows:
            assert row["status"]=="complete"
            assert row["trace"]["request_id"]==row["response"]["request_id"]
            assert row["trace"]["started_at"]>committed
            assert row["trace"]["attributes"]["run.profile"]=="clean"
            if not row["live"]:
                assert row["response"]["usage"]["input_tokens"]==0
                assert row["response"]["usage"]["output_tokens"]==0
                assert row["response"]["usage"]["cost_usd"]==0
        for item in raw:
            case=cases[item["scenario"]]
            assert case["gate"]==batch["gate"] and len(item["runs"])==case["runs"]
            conditions.append({"scenario":item["scenario"],"condition":item["condition"],"gate":batch["gate"],
                              "passed":sum(x["passed"] for x in item["runs"]),"runs":len(item["runs"])})
            for native in item["runs"]:
                part=[x for x in rows if (x["scenario"],x["condition"],x["repeat"])==(item["scenario"],item["condition"],native["run"])]
                assert len(part)==len(case["turns"])
                assert [x["step"] for x in part]==list(range(1,len(part)+1))
                assert len({x["response"]["session_id"] for x in part})==1
                live=[x for x in part if x["live"]];assert len(live)==1
                row=live[0]
                assert row["response"]["answer"]==native["answer"]
                assert row["response"]["usage"]["cost_usd"]==native["cost_usd"]
                tools=[x for x in row["trace"]["children"] if x["name"].startswith("tool.")]
                model=[x for x in row["trace"]["children"] if x["name"]=="llm.call"]
                prereq=[i for i,(a,v) in enumerate(zip(case["assertions"],native["verdicts"])) if a.get("precondition") and not v["ok"]]
                dispute=row["state_after"]["disputes"]["rows"]
                groups.append({"scenario":item["scenario"],"condition":item["condition"],"repeat":native["run"],
                  "native_passed":native["passed"],"failed_preconditions":prereq,
                  "request_id":row["response"]["request_id"],"session_id":row["response"]["session_id"],
                  "usage":row["response"]["usage"],"cache_read":native["cache_read"],"model_calls":native["model_calls"],
                  "verdicts":native["verdicts"],"disputes":dispute,
                  "tools":[{"name":x["name"],"arguments":x["attributes"].get("tool.arguments"),"result":x["attributes"].get("tool.result")} for x in tools],
                  "llm_usage":[{k:v for k,v in x["attributes"].items() if "usage" in k or "cost" in k or "model" in k} for x in model]})
    assert len(all_rows)==121
    assert len({x["response"]["request_id"] for x in all_rows})==121
    assert len({x["response"]["session_id"] for x in all_rows})==52
    assert len(groups)==sum(x["live"] for x in all_rows)==52
    assert len(conditions)==16
    known=[Decimal(str(x["usage"]["cost_usd"])) for x in groups if x["usage"].get("cost_usd") is not None]
    assert len(known)==52
    full_cost=sum(known,Decimal(0))
    cache={k:[x for x in groups if x["scenario"]=="HW6-10" and x["condition"]==k] for k in ["baseline","defect"]}
    means={k:sum(Decimal(str(x["usage"]["cost_usd"])) for x in v)/len(v) for k,v in cache.items()}
    behavior=[x for x in groups if x["scenario"]=="HW6-09" and x["condition"]=="defect"]
    forbidden=[x for x in behavior if any(row.get("transaction_id")=="TX-0402" for row in x["disputes"])]
    pilot=read(ROOT/"evidence/pilot-analysis.json")
    result={"date":"2026-10-27","suite_sha256":freeze["suite_sha256"],"selected_batches":selected,
      "conditions":conditions,"groups":groups,"full_chat_requests":121,"live_steps":52,"mock_steps":69,
      "full_root_cost_usd":float(full_cost),"all_root_cost_including_pilot_usd":float(full_cost+Decimal(str(pilot["root_cost_usd"]))),
      "full_model_calls":sum(x["model_calls"] for x in groups),
      "full_provider_span_cost_usd":float(sum((Decimal(str(v["provider.cost_usd"])) for g in groups for v in g["llm_usage"] if v.get("provider.cost_usd") is not None),Decimal(0))),
      "D13_detected_repeats":sum(not x["native_passed"] for x in groups if x["scenario"]=="HW6-07" and x["condition"]=="defect"),
      "D11_explicit_currency_masking":any(t["name"]=="tool.create_dispute" and (t["arguments"] or {}).get("currency")=="USD" for g in groups if g["scenario"]=="HW6-04" and g["condition"]=="defect" for t in g["tools"]),
      "baseline_passed":sum(x["native_passed"] for x in groups if x["condition"]=="baseline"),
      "baseline_total":sum(x["condition"]=="baseline" for x in groups),
      "failed_precondition_repeats":sum(bool(x["failed_preconditions"]) for x in groups),
      "D29_forbidden_writes":len(forbidden),"D29_behavior_repeats":len(behavior),
      "D28_mean_root_cost":{k:float(v) for k,v in means.items()},
      "D28_mean_cost_ratio":float(means["defect"]/means["baseline"]) if means["baseline"] else None,
      "D28_detected_repeats":sum(not x["native_passed"] for x in cache["defect"]),
      "pilot_excluded_from_full_frequency":True,"scope":"Native verdicts plus actual live-step state; root cost is not an invoice"}
    (ROOT/"evidence/full-run-analysis.json").write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+"\n").encode())
    print(json.dumps({k:v for k,v in result.items() if k not in ["selected_batches","conditions","groups"]},indent=2))
    for x in conditions:print(x["scenario"],x["condition"],str(x["passed"])+"/"+str(x["runs"]))
if __name__=="__main__":main()
