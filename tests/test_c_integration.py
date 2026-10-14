"""Optional real C receiving regression. Never targets the business database."""
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(os.environ.get("RUN_C_ACCEPTANCE") != "1",
                    reason="Set RUN_C_ACCEPTANCE=1 after demo/receive_c.py")
def test_real_c_knowledge_receiving(tmp_path):
    root = Path(__file__).resolve().parents[1]
    report = tmp_path / "report.json"
    subprocess.run([sys.executable, "-X", "utf8", "demo/accept_c_knowledge.py"], cwd=root,
        env={**os.environ, "E_ACCEPTANCE_REPORT": str(report)}, check=True)
    import json
    result = json.loads(report.read_text(encoding="utf-8"))
    assert result["status"] == "passed"
    assert len(result["documents"]) == 16
    assert result["checks"]["restart_load"] == "passed"
