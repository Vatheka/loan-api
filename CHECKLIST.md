# Production Image Checklist

Evidence collected locally on 2026-11-13 using Docker Desktop 29.8.2 on
Apple silicon. Image sizes are Docker's displayed (uncompressed) sizes and
can vary slightly by platform.

## 1. Multi-stage, slim, non-root, health-checked production image

`Dockerfile.prod` uses two `FROM python:3.12-slim` stages, copies only the
virtual environment, trained model, and runtime source into the final stage,
sets `USER appuser`, and defines a `HEALTHCHECK`.

Commands:

```console
$ docker compose up -d --build
$ docker compose ps
NAME                 IMAGE           SERVICE   STATUS
loan-api-adminer-1   adminer:4.8.1   adminer   Up
loan-api-api-1       loan-api-api    api       Up (healthy)
loan-api-db-1        postgres:17     db        Up (healthy)

$ docker compose exec -T api whoami
appuser
```

Result: **PASS**.

## 2. Clean Docker build context

Command:

```console
$ cat .dockerignore
.git
.venv
__pycache__/
*.pyc
.pytest_cache/
.devcontainer/
.env
model.joblib
models/
CHECKLIST.md
```

Git data, virtual environments, caches, development configuration, secrets,
locally trained models, and verification output are excluded.

Result: **PASS**.

## 3. Configurable model path

`main.py` reads `MODEL_PATH` with `model.joblib` as its safe default. A version
1.1.0 model was mounted read-only without rebuilding the image.

```console
$ python3 train.py --version 1.1.0 --out models/model.joblib
Saved model 1.1.0 to models/model.joblib (test AUC 0.923)

$ docker run -d --rm --name loan-api-model-test -p 8001:8000 \
    -v "$PWD/models:/models:ro" \
    -e MODEL_PATH=/models/model.joblib loan-api:prod
$ curl -fsS http://127.0.0.1:8001/health
{"status":"ok","model_version":"1.1.0"}
```

Result: **PASS**.

## 4. Compose runs API, PostgreSQL, and Adminer

`compose.yaml` builds the API with `context: .` and
`dockerfile: Dockerfile.prod`. PostgreSQL has a health check and a named
volume; Adminer and the API wait for the database to become healthy.

```console
$ docker compose ps
NAME                 IMAGE           SERVICE   STATUS
loan-api-adminer-1   adminer:4.8.1   adminer   Up
loan-api-api-1       loan-api-api    api       Up (healthy)
loan-api-db-1        postgres:17     db        Up (healthy)

$ curl -fsS http://127.0.0.1:8000/health
{"status":"ok","model_version":"1.0.0"}

$ docker compose exec -T db psql -U loans -d loans \
    -c 'SELECT COUNT(*) AS applications FROM loan_applications;'
 applications
--------------
            6
(1 row)
```

Result: **PASS**.

## 5. Production image is at least 40% smaller

```console
$ docker images loan-api --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}'
REPOSITORY   TAG    SIZE
loan-api     full   2.2GB
loan-api     prod   818MB
loan-api     slim   800MB
```

The production image is approximately 62.8% smaller than the full-Python
variant: `(2.2 GB - 0.818 GB) / 2.2 GB = 62.8%`.

Result: **PASS**.

## 6. HIGH and CRITICAL vulnerability scan

Command:

```console
$ docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy:0.69.3 image --severity HIGH,CRITICAL \
    --scanners vuln loan-api:prod
```

The first scan reported 49 HIGH and 0 CRITICAL findings. Two zlib findings
(`CVE-2026-76844` and `CVE-2026-85091`) had a fixed Debian package. The image
was rebuilt after `apt-get upgrade`, installing
`zlib1g 1:1.3.dfsg+really1.3.1-1+deb13u1`. The second scan reported:

```text
HIGH: 47
CRITICAL: 0
Findings with a fixed version available: 0
```

The 47 package occurrences correspond to these 11 unique CVEs:

| CVE | Affected runtime packages | Disposition |
|---|---|---|
| CVE-2025-69720 | ncurses libraries/tools | No fixed Debian package is available. |
| CVE-2026-119373 | libsqlite3-0 | No fixed Debian package is available. |
| CVE-2026-119374 | libsqlite3-0 | No fixed Debian package is available. |
| CVE-2026-119379 | libsqlite3-0 | No fixed Debian package is available. |
| CVE-2026-16742 | libsystemd0, libudev1 | No fixed Debian package is available. |
| CVE-2026-54369 | libacl1 | No fixed Debian package is available. |
| CVE-2026-76642 | util-linux packages | No fixed Debian package is available. |
| CVE-2026-78408 | util-linux packages | No fixed Debian package is available. |
| CVE-2026-78409 | util-linux packages | No fixed Debian package is available. |
| CVE-2026-78410 | util-linux packages | No fixed Debian package is available. |
| CVE-2026-9538 | perl-base | No fixed Debian package is available. |

Risk note: these are inherited operating-system packages with no patched
version currently offered by the base distribution. The service runs as the
unprivileged `appuser`, does not expose a shell or accept uploaded files, and
uses only its HTTP API. Rebuild with `--pull` and rescan when Debian publishes
fixes. No Python-package HIGH or CRITICAL findings were reported.

Result: **PASS WITH DOCUMENTED UNFIXED FINDINGS**.

## 7. Published version and latest tags

The verified production image was published under both required tags:

```console
$ docker tag loan-api:prod vatheka/loan-api:1.0.0
$ docker tag loan-api:prod vatheka/loan-api:latest
$ docker push vatheka/loan-api:1.0.0
1.0.0: digest: sha256:adca976b5a673191b254ebd82d5699a54a95956211466655b99d5c2a5550f4d6
$ docker push vatheka/loan-api:latest
latest: digest: sha256:adca976b5a673191b254ebd82d5699a54a95956211466655b99d5c2a5550f4d6
```

Docker Hub: <https://hub.docker.com/r/vatheka/loan-api/tags>

Result: **PASS**.

## 8. Clean pull and run from Docker Hub

The local production tags were removed before running the published image.

```console
$ docker rmi vatheka/loan-api:1.0.0 vatheka/loan-api:latest loan-api:prod
Untagged: vatheka/loan-api:1.0.0
Untagged: vatheka/loan-api:latest
Untagged: loan-api:prod
Deleted: sha256:adca976b5a673191b254ebd82d5699a54a95956211466655b99d5c2a5550f4d6

$ docker run -d --name loan-api-registry-test -p 8000:8000 \
    vatheka/loan-api:1.0.0
Unable to find image 'vatheka/loan-api:1.0.0' locally
Status: Downloaded newer image for vatheka/loan-api:1.0.0

$ docker ps --filter name=loan-api-registry-test
IMAGE                    STATUS                    PORTS
vatheka/loan-api:1.0.0   Up 30 seconds (healthy)   0.0.0.0:8000->8000/tcp

$ curl -fsS -w '\nHTTP %{http_code}\n' -X POST \
    http://127.0.0.1:8000/api/v1/predictions \
    -H 'Content-Type: application/json' \
    -d '{"amount_usd":1500,"term_months":12,"monthly_income_usd":350.0,"previous_loans":1,"late_payments":0}'
{"default_probability":0.095,"risk_band":"low","model_version":"1.0.0"}
HTTP 200
```

Result: **PASS**. The published image ran without the repository's local
files.

## Additional application test

```console
$ python3 -m pytest -v
============================== 5 passed in 1.14s ===============================

$ curl -fsS -X POST http://127.0.0.1:8000/api/v1/predictions \
    -H 'Content-Type: application/json' \
    -d '{"amount_usd":1500,"term_months":12,"monthly_income_usd":350.0,"previous_loans":1,"late_payments":0}'
{"default_probability":0.095,"risk_band":"low","model_version":"1.0.0"}
```

Result: **PASS**.
