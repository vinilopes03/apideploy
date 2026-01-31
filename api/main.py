from fastapi import FastAPI
from fastapi import status
from fastapi.responses import JSONResponse
from tasks import run_analysis
from models import SETTINGS, AnalyzeRequest
import redis

app = FastAPI(title=f"{SETTINGS.analyzer_name} analyzer", version=SETTINGS.analyzer_version)


def _is_redis_ok(timeout=0.5):
    """
    Verify whether redis connection is ok.
    :param timeout: how long to wait for redis connection.
    :return: True if redis connection is ok.
    """
    try:
        r = redis.Redis.from_url(SETTINGS.redis_url,
                                 socket_connect_timeout=timeout,
                                 socket_timeout=timeout)
        return r.ping()
    except Exception:
        return False


@app.get("/health")
def health():
    """
    Health check endpoint for container orchestration.
    :return: 200 Service is ready; 503 Service is unavailable.
    """
    # TODO: what else to check in here? maybe LLMs? GPUs availability? etc

    if not _is_redis_ok():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "analyzer": SETTINGS.analyzer_name, "version": SETTINGS.analyzer_version,
                     "reason": "redis_unreachable", },
        )

    return {"status": "healthy", "analyzer": SETTINGS.analyzer_name, "version": SETTINGS.analyzer_version}


@app.post("/analyze", status_code=202)
def analyze(req: AnalyzeRequest):
    required_artifacts = ["firmware", "source", "binary"]
    # FIXME: check if we have the proper artifacts
    # if "firmware" not in req.artifact_manifest:
    #     raise HTTPException(status_code=400, detail="Missing required artifact type: firmware")

    # run_analysis.delay(req.model_dump())

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

        sarif = _mock_build_sarif(
            SETTINGS.analyzer_name,
            SETTINGS.analyzer_version,
            findings
        )

        headers = {
            "Content-Type": "application/json",
            "X-Callback-Token": callback_token,
            "X-Analyzer-Name": SETTINGS.analyzer_name,
        }

        with httpx.Client(timeout=60.0) as client:
            r = client.post(callback_url, headers=headers, json=sarif)
            r.raise_for_status()

    return {"status": "accepted", "asset_id": req.asset_id}