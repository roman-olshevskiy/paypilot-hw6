"""Build the HW6 submission scenarios from preserved teaching fixtures. No HTTP."""
import copy,json,hashlib,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STAND=ROOT.parent/"paypilot-stand-shared"
def read(name):return json.loads((ROOT/"sources/upstream/scenarios"/name).read_text(encoding="utf-8"))
def save(p,v):p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
def main():
    s1=read("s1-d12-wrong-account.json");s2=read("s2-anaphora.json")
    s3=read("s3-d29-opaque-result.json");s4=read("s4-repeat.json");s5=read("s5-d28-cache.json")
    state=copy.deepcopy(s1);state["assertions"]=[s1["assertions"][0],s1["assertions"][2]]
    state["assertions"][0]["precondition"]=True
    contract=copy.deepcopy(s3);contract["assertions"]=[s3["assertions"][0]]
    repeat=copy.deepcopy(s4)
    usd={"customer_id":"CUS-0008","conditions":{"baseline":{"profile":"clean","defects":""},"defect":{"profile":"clean","defects":"D11"}},
      "turns":[{"user":"Show my account and the BookDepot US card payment from 9 September.",
        "model":[{"tool_calls":[{"id":"call_usd_acc","name":"get_account","arguments":{}}]},
          {"tool_calls":[{"id":"call_usd_tx","name":"get_transactions","arguments":{"account_id":"ACC-1009"}}]},
          {"text":"The BookDepot US payment is TX-0801, dated 9 September 2026, for 120.00 USD on ACC-1009, an EUR account."}]},
       {"user":"I did not authorize that BookDepot payment. Open an unauthorized-debit dispute for its original amount.","live":True}],
      "assertions":[{"kind":"tool_called","tool":"create_dispute","args":{"transaction_id":"TX-0801","reason_code":"unauthorized_debit"},"precondition":True},
        {"kind":"state_row","table":"disputes","where":{"transaction_id":"TX-0801"},"expected_count":1,
         "expect_fields":{"account_id":"ACC-1009","amount":120.0,"currency":"USD","reason_code":"unauthorized_debit"}}]}
    order=copy.deepcopy(s1);order["conditions"]={"baseline":{"profile":"clean","defects":""}}
    order["assertions"]=[copy.deepcopy(s1["assertions"][0]),copy.deepcopy(s1["assertions"][1])]
    order["assertions"][0]["precondition"]=True
    choice={"customer_id":"CUS-0010","conditions":{"baseline":{"profile":"clean","defects":""},"defect":{"profile":"clean","defects":"D13"}},
      "turns":[{"user":"Can I transfer 4,500 EUR today under my current remaining transfer limits? Check the current allowance.","live":True}],
      "assertions":[{"kind":"tool_sequence","must_include":["check_limits"],"must_exclude":["get_transactions"]}]}
    forbidden={"customer_id":"CUS-0004","conditions":{"baseline":{"profile":"clean","defects":""}},
      "turns":[{"user":"Open a duplicate-charge dispute for TX-0402, the TechMart Online payment of 14 July 2026.","live":True}],
      "assertions":[{"kind":"tool_not_called","tool":"create_dispute"},
        {"kind":"state_row","table":"disputes","where":{"transaction_id":"TX-0402"},"expected_count":0}]}
    behavior=copy.deepcopy(s3);behavior["assertions"]=[s3["assertions"][1]]
    specs=[
      (state,"D12: correct call must persist the transaction account and currency","state","daily","adapted S1","No order assertion in daily",
       ["List my accounts before checking the disputed subscription.","The 89.99 USD CloudServe payment on ACC-1003 dated 8 September was not mine.","Open the unauthorized-debit dispute for that subscription payment now."]),
      (contract,"D29: eligibility result obeys its field/type contract","contract","daily","split S3","Schema verdict is independent of the agent reaction",
       ["Show both TechMart Online charges recorded on ACC-1005.","Check TX-0402 and open a duplicate-charge dispute only if it is eligible."]),
      (repeat,"Repeat request leaves exactly one dispute","state","daily","adapted S4","Checks repeat intent; not guaranteed duplicate backend invocation",
       ["Open the duplicate-charge dispute for TX-0401 on my account.","Repeat that dispute request; make sure the same dispute remains open."]),
      (usd,"D11: USD transaction on EUR account remains USD in disputes","state","daily","own","Expected fields from seed and create_dispute; explicit currency argument can mask D11",None),
      (order,"Eligibility is checked before the dispute is written","order","release","split S1","Write reachability is a precondition, not a vacuous order PASS",
       ["Identify my accounts for the subscription dispute.","I did not make the CloudServe payment TX-0202 on ACC-1003, 89.99 USD on 8 September.","Please open that dispute as an unauthorized debit now."]),
      (copy.deepcopy(s2),"Resolve the other payment from the prepared history","parameters","release","adapted S2","Target TX-0202 exists only in prior history",
       ["List the recent USD card payments for account ACC-1003.","I recognize the FlightHub booking and want to keep it.","The other payment was not mine. Please dispute that other one as unauthorized."]),
      (choice,"D13: use limits, not transaction history","tool","release","own","Oracle is description contract plus customer request",None),
      (forbidden,"No write for the expired duplicate-charge request","tool","release","own","Engine window is 60 days, deadline 12 September; as_of 15 September",None),
      (behavior,"D29: reject an expired dispute despite an opaque result","tool","release","split S3","Behavior verdict separate from schema failure",
       ["Find the pair of TechMart Online charges on my EUR account ACC-1005.","Submit a duplicate-charge dispute for the older charge TX-0402 if permitted."]),
      (copy.deepcopy(s5),"D28: cache reuse from the second live-step model call","cost","release","adapted S5","Frequency interpretation in forecast; not a deterministic cache guarantee",
       ["Identify the accounts linked to my signed-in customer.","List the last two outgoing payments on the GBP account.","Those outgoing payments match my records.","Check my current daily and monthly transfer limits and remaining allowances."])
    ]
    provenance=[]
    levels={"tool_called":1,"tool_not_called":4,"tool_order":3,"state_row":1,"tool_result_schema":1,"tool_call_count":1,"cache_read_min":2}
    for n,(case,title,dimension,gate,origin,note,users) in enumerate(specs,1):
        cid=f"HW6-{n:02}"
        case.update(id=cid,title=title,dimension=dimension,gate=gate,runs=1 if gate=="daily" else 5,
                    origin=origin,design_note=note)
        for setting in case["conditions"].values():setting.update(profile="clean",clock="2026-09-15T10:00:00Z",summarize_after=8)
        if users:
            assert len(users)==len(case["turns"])
            for turn,user in zip(case["turns"],users):turn["user"]=user
        replacements={}
        for turn in case["turns"]:
            for reply in turn.get("model",[]):
                for tc in reply.get("tool_calls",[]):
                    new=f"call_hw6_{n:02}_{len(replacements)+1}"
                    replacements[tc["id"]]=new;tc["id"]=new
        ls=set()
        for a in case["assertions"]:
            a["level"]=([3,4] if a["kind"]=="tool_sequence" else [levels[a["kind"]]])
            ls.update(a["level"])
        case["level"]=sorted(ls)
        save(ROOT/"scenarios"/f"hw6-{n:02}.json",case)
        provenance.append({"id":cid,"origin":origin,"note":note})
    tree=ast.parse((STAND/"app/seed.py").read_text(encoding="utf-8"))
    tables={}
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for name in node.targets:
                if isinstance(name,ast.Name):
                    try:tables[name.id]=ast.literal_eval(node.value)
                    except (ValueError,TypeError):pass
    rows={x[0]:x for v in tables.values() if isinstance(v,(list,tuple)) for x in v if isinstance(x,(list,tuple)) and x and isinstance(x[0],str)}
    refs={k:rows[k] for k in ["CUS-0002","CUS-0004","CUS-0008","CUS-0010","ACC-1003","ACC-1005","ACC-1009","ACC-1011","TX-0202","TX-0204","TX-0401","TX-0402","TX-0801"]}
    sources=["app/seed.py","app/engines/policy.py","app/engines/disputes.py","app/agent/tools.py","app/agent/prompt.py"]
    save(ROOT/"evidence/scenario-provenance.json",{"date":"2026-10-27","scenarios":provenance,"seed_references":refs,
       "source_sha256":{p:hashlib.sha256((STAND/p).read_bytes()).hexdigest() for p in sources},
       "own_ids":["HW6-04","HW6-07","HW6-08"],"expected_as_of":"2026-09-15","live_evidence":False})
    print("Generated10 scenarios:4daily,6release; no HTTP")
if __name__=="__main__":main()
