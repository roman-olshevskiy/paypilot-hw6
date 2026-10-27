"""Native assertion and capture tests with a fake HTTP boundary. No real stand."""
import copy,hashlib,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
import run_step,build_mock,hw6_capture as capture
class Suite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=[json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT/"scenarios").glob("*.json"))]
    def test_metadata_and_cost(self):
        self.assertEqual(len(self.cases),10);self.assertEqual(sum(c["origin"]=="own" for c in self.cases),3)
        live=chat=0;users=set();ids=set()
        for c in self.cases:
            self.assertIn(c["dimension"],{"state","contract","parameters","order","tool","cost"})
            self.assertTrue(c["level"])
            self.assertEqual(c["runs"],1 if c["gate"]=="daily" else 5)
            self.assertEqual([i for i,t in enumerate(c["turns"]) if t.get("live")],[len(c["turns"])-1])
            self.assertEqual(c["conditions"]["baseline"]["defects"],"")
            for turn in c["turns"]:
                self.assertNotIn(turn["user"],users);users.add(turn["user"])
                self.assertNotIn("'",turn["user"]);self.assertNotIn("\\\\",turn["user"])
                for reply in turn.get("model",[]):
                    for call in reply.get("tool_calls",[]):
                        self.assertNotIn(call["id"],ids);ids.add(call["id"])
            for a in c["assertions"]:
                self.assertNotIn("answer",a);self.assertIn("level",a)
                if a["kind"]=="state_row":self.assertIn("expected_count",a)
                if c["gate"]=="daily":self.assertIn(a["kind"],{"state_row","tool_result_schema","tool_called"})
                if c["gate"]=="daily" and a["kind"]=="tool_called":self.assertTrue(a["precondition"])
            live+=len(c["conditions"])*c["runs"]
            chat+=len(c["turns"])*len(c["conditions"])*c["runs"]
        self.assertEqual(live,52);self.assertEqual(chat,121)
        self.assertEqual(sum(c["gate"]=="daily" for c in self.cases),4)
    def test_expectations_are_reproducible_and_do_not_match_live_turns(self):
        generated=[x for c in self.cases for x in build_mock.expectations_for(c)]
        self.assertEqual(generated,json.loads((ROOT/"mock/expectations.json").read_text()))
        self.assertEqual(len(generated),26)
        for c in self.cases:
            for x in generated:self.assertNotIn(c["turns"][-1]["user"],x["httpRequest"]["body"]["jsonPath"])
    def tree(self,*calls):
        return {"children":[{"name":"tool."+name,"attributes":{"tool.name":name,"tool.arguments":args,"tool.result":result}} for name,args,result in calls]}
    def test_wrong_parameters_and_order(self):
        t=self.tree(("create_dispute",{"transaction_id":"wrong"},{}))
        self.assertFalse(run_step.check({"kind":"tool_called","tool":"create_dispute","args":{"transaction_id":"TX-0202"}},t)[0])
        self.assertFalse(run_step.check({"kind":"tool_order","before":["check_dispute_eligibility","create_dispute"]},t)[0])
        self.assertTrue(run_step.check({"kind":"tool_order","before":["check_dispute_eligibility","create_dispute"]},self.tree())[0])
        order=next(c for c in self.cases if c["dimension"]=="order")
        self.assertTrue(any(a.get("precondition") and a["kind"]=="tool_called" for a in order["assertions"]))
    def test_empty_state_and_wrong_currency_fail(self):
        a={"kind":"state_row","table":"disputes","where":{"transaction_id":"TX-0801"},"expected_count":1,"expect_fields":{"currency":"USD"}}
        for rows in [[],[{"transaction_id":"TX-0801","currency":"EUR"}]]:
            with patch.object(run_step,"_call",return_value={"rows":rows}):self.assertFalse(run_step.check(a,self.tree())[0])
    def test_schema_missing_result_and_opaque_result(self):
        a={"kind":"tool_result_schema","tool":"check_dispute_eligibility","required":{"eligible":"boolean","checks":"object"}}
        self.assertFalse(run_step.check(a,self.tree())[0])
        self.assertFalse(run_step.check(a,self.tree(("check_dispute_eligibility",{},{"ok":True,"r":"N"})))[0])
        self.assertTrue(run_step.check(a,self.tree(("check_dispute_eligibility",{},{"eligible":False,"checks":{}})))[0])
    def test_cache_second_call_and_no_missing_as_success(self):
        a={"kind":"cache_read_min","from_call":1,"min":1000}
        def tree(reads):return {"children":[{"name":"llm.call","attributes":{"gen_ai.usage.cache_read_input_tokens":v}} for v in reads]}
        self.assertFalse(run_step.check(a,tree([0]))[0])
        self.assertTrue(run_step.check(a,tree([0,1200]))[0])
        self.assertFalse(run_step.check(a,tree([1200,0]))[0])
    def test_source_oracle_and_expired_window(self):
        import ast
        seed=ast.parse((ROOT.parent/"paypilot-stand-shared/app/seed.py").read_text(encoding="utf-8"))
        refs=json.loads((ROOT/"evidence/scenario-provenance.json").read_text())["seed_references"]
        self.assertEqual(refs["TX-0801"][4],"USD");self.assertEqual(refs["ACC-1009"][2],"EUR")
        from datetime import date,timedelta
        self.assertLess(date.fromisoformat(refs["TX-0402"][2])+timedelta(days=60),date(2026,9,15))

class Backend:
    def __init__(self):
        self.chat=0;self.fail_trace=False;self.fail_chat=False;self.puts=[];self.fail_restore=False
        self.data={"health":{"provider":"openrouter"},"defects":{"profile":"clean","extra_defects":[],"all_defects":["D12"]},
           "clock":{"runtime_override":None},"summarize":{"summarize_after_steps":8},"retrieval":{"index_env":"","rag_top_k":4}}
        self.state={"rows":[{"transaction_id":"TX-1","currency":"USD"}]}
    def __call__(self,base,method,path,body=None,headers=None,timeout=300):
        if method=="PUT" and path.startswith("/api/"):
            self.puts.append(path)
            if path.endswith("/profile"):
                if self.fail_restore:raise RuntimeError("profile restore failed")
                self.data["defects"]["profile"]=body["profile"]
            elif path.endswith("/defects"):self.data["defects"]["extra_defects"]=body["defects"].split(",") if body["defects"] else []
            elif path.endswith("/clock"):self.data["clock"]["runtime_override"]=body["now"]
            elif path.endswith("/summarize_after"):self.data["summarize"]["summarize_after_steps"]=body["steps"]
            elif path.endswith("/retrieval"):self.data["retrieval"].update(index_env=body["index"],rag_top_k=body["top_k"])
            return {}
        if path=="/health":return copy.deepcopy(self.data["health"])
        for key,endpoint in [("defects","defects"),("clock","clock"),("summarize","summarize_after"),("retrieval","retrieval")]:
            if path=="/api/_test/"+endpoint:return copy.deepcopy(self.data[key])
        if path=="/api/_test/reset":self.chat=0;return {}
        if path.startswith("/mockserver/retrieve"):return []
        if path.startswith("/mockserver/clear"):return {}
        if path=="/chat":
            self.chat+=1
            if self.fail_chat:raise run_step.RunError("timeout")
            return {"answer":"mocked" if self.chat==1 else "done","session_id":"session1","request_id":"id"+str(self.chat),
                    "usage":{"input_tokens":0 if self.chat==1 else 10,"output_tokens":0 if self.chat==1 else 2,"cost_usd":0 if self.chat==1 else .001}}
        if "/traces/" in path:
            if self.fail_trace:raise run_step.RunError("trace unavailable")
            return {"request_id":path.split("/")[-1],"children":[]}
        if "/state/" in path:return copy.deepcopy(self.state)
        raise AssertionError((method,path))
class Harness(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/"scenarios").mkdir()
        self.case={"id":"fixture","title":"offline","customer_id":"CUS-X","conditions":{"baseline":{"profile":"clean","defects":""}},
          "turns":[{"user":"first","model":[{"text":"mocked"}]},{"user":"second","live":True}],
          "assertions":[{"kind":"state_row","table":"disputes","where":{"transaction_id":"TX-1"},"expected_count":1,"expect_fields":{"currency":"USD"}}]}
        (self.root/"scenarios/fixture.json").write_text(json.dumps(self.case))
        self.backend=Backend()
    def tearDown(self):self.tmp.cleanup()
    def execute(self):
        with patch.object(run_step,"ROOT",self.root),patch.object(run_step,"_call",self.backend):
            c=capture.Capture(self.root,run_step);code=c.execute(["--scenario","fixture"])
        return c,code,json.loads((c.folder/"manifest.json").read_text())
    def test_native_success_and_each_turn_captured(self):
        c,code,m=self.execute();self.assertEqual(code,0);self.assertEqual(m["complete"],2);self.assertTrue(m["quality_passed"])
        self.assertTrue((c.folder/"raw-results.json").exists());self.assertEqual(m["restore_status"],"passed")
        self.assertEqual([x["live"] for x in c.rows],[False,True])
    def test_quality_fail_is_not_transport_error(self):
        self.backend.state["rows"][0]["currency"]="EUR"
        c,code,m=self.execute();self.assertEqual(code,0);self.assertFalse(m["quality_passed"]);self.assertEqual(m["complete"],2)
    def test_response_survives_trace_failure_no_retry(self):
        self.backend.fail_trace=True
        c,code,m=self.execute();self.assertEqual(code,2);self.assertEqual(m["chat_attempts"],1);self.assertEqual(m["responses"],1)
        self.assertEqual(c.rows[0]["status"],"response_saved");self.assertEqual(m["restore_status"],"passed")
    def test_unknown_response_stops_without_retry(self):
        self.backend.fail_chat=True
        c,code,m=self.execute();self.assertEqual(code,2);self.assertEqual(m["chat_attempts"],1);self.assertEqual(m["responses"],0)
    def test_restore_failure_does_not_skip_other_settings(self):
        with patch.object(run_step,"_call",self.backend):
            c=capture.Capture(self.root,run_step);c.before=c.snapshot()
            self.backend.data["defects"].update(profile="lesson",extra_defects=["D12"])
            self.backend.data["clock"]["runtime_override"]="changed"
            self.backend.data["summarize"]["summarize_after_steps"]=2
            self.backend.fail_restore=True;c.restore()
        self.assertIn("/api/_test/defects",self.backend.puts);self.assertIn("/api/_test/clock",self.backend.puts)
        self.assertIn("/api/_test/summarize_after",self.backend.puts);self.assertTrue(c.restore_errors)
    def test_file_lock_retries_only_io(self):
        original=Path.replace;counter=[0]
        def locked(path,destination):
            counter[0]+=1
            if counter[0]<3:raise PermissionError("temporary lock")
            return original(path,destination)
        with patch.object(Path,"replace",locked),patch.object(capture.time,"sleep"):
            c,code,m=self.execute()
        self.assertEqual(code,0);self.assertEqual(m["chat_attempts"],2)
    def test_paid_guard_before_http(self):
        with patch.dict(os.environ,{"HW6_ENABLE_PAID_RUNS":""}),patch.object(run_step,"_call") as http:
            with self.assertRaisesRegex(RuntimeError,"disabled"):capture.verify_forecast(self.root)
            http.assert_not_called()


    def test_capture_file_failure_preserves_response_in_memory_and_restores(self):
        original=Path.replace
        def locked(path,destination):
            if Path(destination).name=="captures.json":raise PermissionError("persistent capture lock")
            return original(path,destination)
        with patch.object(Path,"replace",locked),patch.object(capture.time,"sleep"):
            c,code,m=self.execute()
        self.assertEqual(code,2);self.assertEqual(m["chat_attempts"],1);self.assertEqual(m["responses"],1)
        self.assertEqual(m["restore_status"],"passed")
    def test_missing_forecast_proof_blocks_before_http(self):
        (self.root/"mock").mkdir();(self.root/"mock/expectations.json").write_text("[]")
        (self.root/"evidence").mkdir()
        frozen={"suite_sha256":capture.scenarios_digest(self.root),"expectations_sha256":capture.sha(self.root/"mock/expectations.json")}
        (self.root/"evidence/dataset-freeze.json").write_text(json.dumps(frozen))
        with patch.dict(os.environ,{"HW6_ENABLE_PAID_RUNS":"1"}),patch.object(run_step,"_call") as http:
            with self.assertRaises(FileNotFoundError):capture.verify_forecast(self.root)
            http.assert_not_called()

if __name__=="__main__":unittest.main()
