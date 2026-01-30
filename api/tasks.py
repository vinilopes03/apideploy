import os
import tempfile
from typing import List, Dict, Any

import httpx
from worker import celery_app
from artifacts import download_artifacts
from models import SETTINGS


def _mock_build_sarif(analyzer_name: str, analyzer_version: str, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    rules = {}
    results = []

    for f in findings:
        cwe = f.get("cwe", "CWE-000")
        rules.setdefault(cwe, {
            "id": cwe,
            "shortDescription": {"text": cwe},
            "fullDescription": {"text": cwe},
        })

        results.append({
            "ruleId": cwe,
            "message": {"text": f.get("message", "")},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": f.get("uri", "")},
                    "region": {
                        "startLine": f.get("startLine", 1),
                        "startColumn": f.get("startColumn", 1),
                    },
                }
            }],
            "properties": f.get("properties", {}),
        })

    return {
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": analyzer_name,
                    "version": analyzer_version,
                    "rules": list(rules.values()),
                }
            },
            "results": results,
        }]
    }


@celery_app.task(bind=True)
def run_analysis(self, req: dict):
    asset_id = req["asset_id"]
    callback_url = req["callback_url"]
    callback_token = req["callback_token"]
    manifest = req.get("artifact_manifest", {})

    with tempfile.TemporaryDirectory(prefix=f"ngvd_{asset_id}_") as workdir:
        local_paths = download_artifacts(manifest, workdir)
        # TODO: invoke our tools from CLI
        findings = [{
            "cwe": "CWE-787",
            "message": "Example finding",
            "uri": "example.c",
            "startLine": 10,
            "startColumn": 5,
        }]

        sarif = _mock_build_sarif(SETTINGS.analyzer_name, SETTINGS.analyzer_version, findings)

        headers = {
            "Content-Type": "application/json",
            "X-Callback-Token": callback_token,
            "X-Analyzer-Name": SETTINGS.analyzer_name,
        }

        with httpx.Client(timeout=60.0) as client:
            r = client.post(callback_url, headers=headers, json=sarif)
            r.raise_for_status()
