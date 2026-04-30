# Project Covenant

Secure RAG pipeline with RBAC enforcement. Portfolio project for [adventuringghost.com](https://adventuringghost.com) by Skipper.

## What This Does

Covenant is a retrieval-augmented generation system where Open Policy Agent enforces access **before** Claude Sonnet sees a query or generates a response. No OPA approval → no LLM call, no vector search, no data exposure.

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python 3.12) |
| Vector store | pgvector on PostgreSQL 16 |
| Policy engine | Open Policy Agent (OPA) |
| LLM | Claude Sonnet (Anthropic SDK) |
| Auth | JWT tokens (HS256) |
| Infrastructure | Azure VM + Terraform |
| Containers | Docker + Compose |

## RBAC Roles

| Role | Access |
|------|--------|
| `admin` | All documents, all metadata, audit logs |
| `user` | Filtered results — only documents matching their clearance level |
| `auditor` | Audit logs only — never sees document content |

## Request Flow

```
Client
  → FastAPI
  → JWT decode (app/auth.py)          — extract role + claims
  → OPA policy check (app/opa_client.py)  ← ACCESS DECIDED HERE
  → pgvector similarity search (app/query.py)
  → Claude Sonnet generation (app/claude_client.py)
  → Response
```

OPA receives: `{ "role": "user", "action": "query", "classification": "confidential" }`.
If `allow == false`, the request is rejected with 403 before any retrieval occurs.

## CRITICAL COST RULES

**Never run `terraform apply` without Skipper's explicit written approval in this session.**

- `terraform plan` is always safe — run freely to preview changes
- `terraform apply` requires an explicit go-ahead: "yes apply" or "go ahead and apply"
- Azure VMs and managed PostgreSQL instances incur real costs
- All resources must carry tags: `project = "covenant"` and `env = "dev"`
- Before any apply, confirm the target workspace and subscription

## Development Commands

```bash
# Start local stack (API + PostgreSQL + OPA)
docker compose -f docker/docker-compose.yml up -d

# Run tests
pytest tests/ -v

# Evaluate an OPA policy decision locally
opa eval -d opa/policies/ -i input.json "data.covenant.authz.allow"

# Safe: preview infrastructure changes
cd infra && terraform plan

# REQUIRES EXPLICIT APPROVAL — do not run autonomously:
# cd infra && terraform apply
```

## Environment Setup

```bash
cp .env.example .env
# Fill in all values before starting
```

Key variables:
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `DATABASE_URL` — PostgreSQL + pgvector connection string
- `OPA_URL` — OPA REST API (default: `http://localhost:8181`)
- `JWT_SECRET` — symmetric signing key (min 32 chars)
- `AZURE_SUBSCRIPTION_ID` — for Terraform

## Key Design Decisions

1. **OPA first** — policy is enforced at the gateway layer, not scattered in application code. Policy is auditable Rego, not imperative conditionals.
2. **pgvector over a separate vector DB** — keeps the infrastructure footprint minimal; PostgreSQL handles both relational metadata and ANN search.
3. **Role embedded in JWT** — the `covenant_role` claim is the single source of truth for role; OPA receives it alongside document classification and action.
4. **Auditor isolation** — auditors hit `/audit` endpoints backed by `audit_logs` table only; they are never in a code path that touches `documents`.
5. **Prompt caching** — system prompt and policy context are cached via the Anthropic SDK to reduce latency and cost on repeated queries.

## File Map

```
app/            FastAPI application
infra/          Terraform (Azure)
opa/policies/   Rego policies
docker/         Dockerfile + Compose
docs/           Case study and portfolio post
tests/          pytest suite
```
