# Covenant

> Secure RAG pipeline with OPA-enforced RBAC. Policy gates every query before Claude Sonnet generates a single token.

Built by **Skipper** — portfolio project for [adventuringghost.com](https://adventuringghost.com).

---

## Architecture

```
┌─────────┐   JWT    ┌──────────┐   OPA check   ┌─────┐
│  Client ├─────────►│  FastAPI ├──────────────►│ OPA │
└─────────┘          └────┬─────┘               └──┬──┘
                          │ allow=true             │
                     ┌────▼──────┐                 │ deny → 403
                     │ pgvector  │                 │
                     └────┬──────┘                 │
                          │ chunks                  │
                     ┌────▼──────┐
                     │  Claude   │
                     │  Sonnet   │
                     └──────────-┘
```

## Roles

| Role | Can Do |
|------|--------|
| `admin` | Query all documents, view all metadata |
| `user` | Query documents at or below their clearance |
| `auditor` | Read audit logs — no document access |

## Quick Start

```bash
cp .env.example .env        # fill in secrets
docker compose -f docker/docker-compose.yml up -d
pytest tests/ -v
```

API docs available at `http://localhost:8000/docs` once running.

## Stack

Python · FastAPI · PostgreSQL · pgvector · OPA · Claude Sonnet · JWT · Docker · Terraform · Azure

## License

MIT
