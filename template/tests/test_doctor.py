import json
import subprocess
import sys
from pathlib import Path


def test_doctor_json_contract():
    script = Path(__file__).resolve().parents[1] / "scripts" / "doctor.py"
    result = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    report = json.loads(result.stdout)
    assert result.returncode == (0 if report["ok"] else 1)
    assert {"uv", "node", "pnpm", "task", "python", "sqlite", "api_types"} <= {
        check["code"] for check in report["checks"]
    }
    assert all({"code", "status", "detail", "remediation"} <= check.keys() for check in report["checks"])
