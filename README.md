# Loan Prediction API

A production-ready FastAPI service that scores loan default risk with a
scikit-learn model. The repository includes development and production
Dockerfiles, a three-service Docker Compose stack, seeded PostgreSQL data,
tests, and verification evidence.

## Run the tests

```bash
pip install -r requirements-dev.txt
python -m pytest -v
```

## Run with Docker Compose

```bash
docker compose up -d --build
docker compose ps
```

- API documentation: <http://localhost:8000/docs>
- Health endpoint: <http://localhost:8000/health>
- Adminer: <http://localhost:8080>

See [CHECKLIST.md](CHECKLIST.md) for requirement-by-requirement evidence and
the vulnerability review.

## GitHub Actions and Render

Pull requests run the test job. Pushes to `main` test the code, build and publish
an image tagged with the commit SHA and `latest`, trigger Render with the
commit-tagged image, and verify that `/health` reports the same SHA.

Configure these values in GitHub **Settings → Secrets and variables → Actions**:

- Secret `RENDER_DEPLOY_HOOK`: the deploy hook URL from the Render service.
- Variable `APP_URL`: the public service URL without a trailing slash.

Set `API_KEY` as an environment variable in Render to protect `/api/` routes.
Keep the API key and deploy hook out of the repository, image, and logs.

## Module 2 API contract comparison

Module 6 intentionally preserves the Module 4/5 API rather than retrofitting
the earlier Module 2 contract:

| Module 2 contract | Module 4/5 API retained here |
|---|---|
| `GET/POST /api/v1/applications` | Both exist; listing has no pagination. Creation requires income, previous-loan, and late-payment features. |
| `GET/PATCH /api/v1/applications/{application_id}` | `GET` exists; `PATCH` is not implemented. |
| `POST /api/v1/applications/{application_id}/predictions` | Scoring is instead `POST /api/v1/predictions`. |
| `GET /api/v1/borrowers/{borrower_id}/applications` | Not implemented. |
| Paginated application list and Module 2 response shapes | The list returns an array; application responses include model features and a prediction. |
| Bearer authentication | When configured, `X-API-Key` middleware protects `/api/`; it is not represented as an OpenAPI security scheme. |

`/health` is an additional route. These differences are intentional to preserve
the Module 4/5 API, but the live OpenAPI does not exactly match Module 2.
