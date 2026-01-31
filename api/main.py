from fastapi import FastAPI
from fastapi import status
from fastapi.responses import JSONResponse
from models import SETTINGS, AnalyzeRequest
import redis

app = FastAPI(title=f"{SETTINGS.analyzer_name} analyzer", version=SETTINGS.analyzer_version)


def _is_redis_ok(timeout=0.5):
    try:
        r = redis.Redis.from_url(SETTINGS.redis_url,
                                 socket_connect_timeout=timeout,
                                 socket_timeout=timeout)
        return r.ping()
    except Exception:
        return False


@app.get("/health")
def health():
    if not _is_redis_ok():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "analyzer": SETTINGS.analyzer_name, "version": SETTINGS.analyzer_version,
                     "reason": "redis_unreachable"},
        )
    return {"status": "healthy", "analyzer": SETTINGS.analyzer_name, "version": SETTINGS.analyzer_version}


@app.post("/analyze", status_code=202)
def analyze(req: AnalyzeRequest):
    # Mock SARIF response
    findings = [{
        "cwe": "CWE-787",
        "message": "Example finding",
        "uri": "example.c",
        "startLine": 10,
        "startColumn": 5,
    }]

    sarif = {
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": SETTINGS.analyzer_name,
                    "version": SETTINGS.analyzer_version,
                    "rules": [{"id": "CWE-787", "shortDescription": {"text": "CWE-787"}, "fullDescription": {"text": "CWE-787"}}],
                }
            },
            "results": [{
                "ruleId": "CWE-787",
                "message": {"text": "Example finding"},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": "example.c"},
                        "region": {"startLine": 10, "startColumn": 5},
                    }
                }],
                "properties": {},
            }],
        }]
    }

    return {"status": "accepted", "asset_id": req.asset_id, "sarif": sarif}