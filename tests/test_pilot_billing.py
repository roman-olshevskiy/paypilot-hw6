"""Read-only OpenRouter key usage check; never calls a completion."""
import json,os,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get("HW6_CHECK_BILLING")=="1","Read-only billing check disabled")
class Billing(unittest.TestCase):
    def test_report_key_usage(self):
        env={}
        for line in (ROOT.parent/"paypilot-stand-shared/.env").read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k,v=line.split("=",1);env[k.strip()]=v.strip().strip(chr(34)).strip(chr(39))
        req=urllib.request.Request("https://openrouter.ai/api/v1/key",headers={"Authorization":"Bearer "+env["OPENROUTER_API_KEY"]})
        with urllib.request.urlopen(req,timeout=30) as response:d=json.load(response)["data"]
        self.assertGreaterEqual(d["usage"],0)
        safe={k:d.get(k) for k in ["limit","limit_remaining","usage","usage_daily","usage_monthly","byok_usage","is_free_tier"]}
        safe.update(date="2026-10-27",scope="Key-reported usage/limit, not account available balance or itemized invoice")
        (ROOT/"evidence/pilot-key-usage.json").write_bytes((json.dumps(safe,indent=2)+"\n").encode())
        print(json.dumps(safe,indent=2))
