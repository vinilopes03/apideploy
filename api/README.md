# Overview

This directory contains the implementation of a REST API server that follows **Hawksbill’s NGVD Analyzer contract**.

The service:
- exposes `/health` and `/analyze` endpoints
- accepts analysis requests asynchronously
- executes internal analysis tools in the background
- posts SARIF v2.1.0 results back to the provided callback URL



## API Contract Summary

The service implements the following endpoints:

- `GET /health`  
  Returns `200` when the service and Redis broker are reachable, otherwise `503`.

- `POST /analyze`  
  Accepts an NGVD analysis request, immediately returns `202 Accepted`, and asynchronously:
  1. downloads referenced artifacts
  2. runs the analyzer
  3. posts SARIF results to the provided `callback_url` with required headers



## File Structure

```
./
    main.py             # FastAPI endpoints: /health, /analyze
    models.py           # Pydantic request models
    worker.py           # Celery app configuration
    tasks.py            # Core Celery task logic (download artifacts, run tools, post SARIF)
    artifacts.py        # Artifact download helpers
    sarif.py            # SARIF v2.1.0 generation helpers
    config.py           # Environment and analyzer configuration
    requirements.txt    # Python dependencies
    Dockerfile          # Docker build instructions
    docker-compose.yml  # Docker Compose services (API, worker, Redis)
    analyzer.env        # Environment variables for local development
````



## Pre-requisites

### With Docker
- Docker
- Docker Compose v2+

### Without Docker
- Python 3.10+
- Redis
- `pip` or `virtualenv`



## Configuration

The service is configured via environment variables. See `api.env` for an example.
These variables are required by both the API server and the Celery worker.


## Running the Service

### Option 1: With Docker (recommended)

This will start:

* the FastAPI server
* the Celery worker
* a Redis broker

```bash
docker compose up --build
```

The API will be available at:

```
http://localhost:8080
```

Swagger UI:

```
http://localhost:8080/docs
```

### Option 2: Without Docker (local development)

#### 1. Install dependencies

```bash
pip install -r requirements.txt
```

#### 2. Start Redis

```bash
redis-server
```

#### 3. Start the API server

```bash
uvicorn app.main:app --reload --port 8080 --env-file api.env 
```

#### 4. Start the Celery worker (in a second terminal)

```bash
set -a
source api.env
set +a

celery -A worker:celery_app worker --loglevel=INFO
```

or 
```bash
env $(cat api.env | xargs)  celery -A worker:celery_app worker --loglevel=INFO 
```

---

## Notes

* The API is **stateless**; all correlation is handled via `asset_id` and callback delivery.
* Analysis execution is asynchronous and relies on Celery and Redis.
* An analysis is considered complete once SARIF results are successfully POSTed and a `202` response is received from the callback endpoint.

---

## Common Issues / Errors FAQ

* **`503` from `/health`**
  Indicates Redis is unreachable or misconfigured.

* **No SARIF callback received**
  If the platform does not receive SARIF results at the provided `callback_url`, check the following:

  * **Celery worker logs**  
    Ensure the worker is running and that the analysis task is being executed.  
    Look for errors during:
    - task startup
    - artifact download
    - analyzer execution
    - HTTP POST to the callback URL

  * **Redis connectivity**  
    Verify that Redis is reachable and that the Celery worker is successfully consuming tasks from the queue.  
    A misconfigured or unavailable Redis broker will prevent tasks from running.

  * **Artifact download URL expiration**  
    Artifact `download_url` values are time-limited.  
    If the Celery worker starts after URLs expire, artifact downloads will fail and analysis will not complete.


---

## Out of Scope

The following are intentionally not included:

* database storage
* authentication or authorization
* Kubernetes or production orchestration configuration

These concerns are handled by the NGVD platform or higher-level deployment infrastructure.

---

## Optional Future Improvements

Potential enhancements if needed:

* example `/analyze` request payload
* local callback receiver for testing SARIF delivery
* Makefile targets for common workflows
* structured metrics endpoint

