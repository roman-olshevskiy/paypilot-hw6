"""Read-only key usage before/after full suite. No model generation."""
import json,os,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(os.environ.get("HW6_FULL_BILLING") in ("before","after","after-refresh","after-settled"),"Explicit full billing check disabled")
class FullBilling(unittest.TestCase):
    def test_key_counter(self):
        values={}
        for line in (ROOT.parent/"paypilot-stand-shared/.env").read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k,v=line.split("=",1);values[k.strip()]=v.strip().strip(chr(34)).strip(chr(39))
        request=urllib.request.Request("https://openrouter.ai/api/v1/key",headers={"Authorization":"Bearer "+values["OPENROUTER_API_KEY"]})
        with urllib.request.urlopen(request,timeout=30) as response:data=json.load(response)["data"]
        self.assertGreaterEqual(data["usage"],0)
        output=ROOT/("evidence/full-"+os.environ["HW6_FULL_BILLING"]+"-key-usage.json")
        self.assertFalse(output.exists(),"Refuse to overwrite a billing snapshot")
        safe={k:data.get(k) for k in ["usage","byok_usage","limit","limit_remaining"]}
        output.write_bytes((json.dumps(safe,indent=2)+"\n").encode())
        print(json.dumps(safe))
