"""Final offline integrity checks and an explicit read-only billing refresh."""
import hashlib,json,os,re,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Review(unittest.TestCase):
    def test_policies_and_template(self):
        for name in ["tool-call-testing-policy.md","tool-call-testing-policy-template.md"]:
            text=(ROOT/name).read_text(encoding="utf-8")
            self.assertEqual([int(x) for x in re.findall(r"^## (\d+)\.",text,re.M)],list(range(1,13)))
        blank=(ROOT/"tool-call-testing-policy-template.md").read_text(encoding="utf-8")
        self.assertNotRegex(blank,r"(?i)PayPilot|CUS-|ACC-|TX-|HW6-|D29|D28|create_dispute|send_statement|check_limits|claude")
    def test_frozen_inputs_and_raw_hashes(self):
        frozen=json.loads((ROOT/"evidence/dataset-freeze.json").read_text())
        for name,digest in frozen["scenarios"].items():
            self.assertEqual(hashlib.sha256((ROOT/"scenarios"/name).read_bytes()).hexdigest(),digest)
        for index in ["pilot-run-index.json","full-run-index.json"]:
            for batch in json.loads((ROOT/"evidence"/index).read_text()):
                folder=ROOT/batch["folder"]
                manifest=json.loads((folder/"manifest.json").read_text())
                for name,digest in manifest["report_sha256"].items():
                    self.assertEqual(hashlib.sha256((folder/name).read_bytes()).hexdigest(),digest)
    def test_all_local_document_links(self):
        from urllib.parse import unquote
        for p in [*ROOT.glob("*.md"),*(ROOT/"docs").glob("*.md")]:
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)",p.read_text(encoding="utf-8")):
                if target.startswith(("http:","https:","#")):continue
                self.assertTrue((p.parent/unquote(target.split("#")[0])).exists(),str(p)+":"+target)
@unittest.skipUnless(os.environ.get("HW6_FINAL_BILLING")=="1","Explicit read-only billing refresh disabled")
class FinalBilling(unittest.TestCase):
    def test_current_key_usage(self):
        values={}
        for line in (ROOT.parent/"paypilot-stand-shared/.env").read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k,v=line.split("=",1);values[k.strip()]=v.strip().strip(chr(34)).strip(chr(39))
        req=urllib.request.Request("https://openrouter.ai/api/v1/key",headers={"Authorization":"Bearer "+values["OPENROUTER_API_KEY"]})
        with urllib.request.urlopen(req,timeout=30) as response:data=json.load(response)["data"]
        self.assertGreaterEqual(data["usage"],0)
        safe={k:data.get(k) for k in ["usage","byok_usage","limit","limit_remaining"]}
        safe["date"]="2026-10-27"
        output=ROOT/"evidence/final-key-usage.json"
        self.assertFalse(output.exists())
        output.write_bytes((json.dumps(safe,indent=2)+"\n").encode())
        print(json.dumps(safe))
