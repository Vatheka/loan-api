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
