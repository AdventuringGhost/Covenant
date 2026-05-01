<!-- Technical case study: architecture decisions, OPA policy design, RBAC enforcement, and pipeline results -->

# Covenant: Secure RAG with Policy-First RBAC — Case Study

*By Skipper · [adventuringghost.com](https://adventuringghost.com)*

---

## The Problem

Enterprise RAG pipelines typically scatter access control through application code: `if role == "admin"` checks in handlers, retrieval filters that depend on correct call order, and LLM prompts that instruct the model not to reveal certain data. Any of these can be missed in a refactor, bypassed by a new endpoint, or silently broken by a schema change. When the LLM generates a response, there is often no single, auditable point where access was formally decided.

The goal with Covenant was to invert this: make policy the first thing evaluated on every request, externalized from application code, independently testable, and provably enforced before any retrieval or generation occurs.

---

## Architecture

```
Client
  → FastAPI
  → JWT decode (app/auth.py)            — extract covenant_role claim
  → OPA enforce() (app/opa_client.py)   ← ACCESS DECIDED HERE
  → pgvector similarity search          — filtered to role-allowed classifications
  → Claude Sonnet generation
  → Response
```

OPA receives `{ "role": "user", "action": "query", "classification": "internal" }`. If `allow == false`, the request ends with a 403 before anything else runs.

### OPA as the Policy Gateway

The Rego policy for Covenant is a default-deny with three explicit allow rules:

```rego
package covenant.authz

default allow := false

allow if {
    input.role == "admin"
}

allow if {
    input.role == "user"
    input.action == "query"
    input.classification in {"public", "internal"}
}

allow if {
    input.role == "auditor"
    input.action == "read_logs"
}
```

Every role, every action, and every document classification has to be explicitly granted. Anything not listed is denied. Moving this out of Python means:

- Policy changes don't require application deploys or test coverage changes
- The policy is auditable by security teams who don't read Python
- OPA's decision log provides a structured audit trail of every allow and deny

### pgvector over a Dedicated Vector DB

A separate vector database (Pinecone, Qdrant, Weaviate) adds an additional trust boundary and operational complexity. pgvector keeps vector search inside PostgreSQL, so classification-based filtering happens in a single SQL query using familiar semantics:

```sql
SELECT content FROM documents
WHERE classification IN ('public', 'internal')
ORDER BY embedding <=> CAST(:q AS vector)
LIMIT 5
```

The allowed classifications are computed per-role in application code (`_ROLE_ALLOWED` in `query.py`) after OPA has already approved the request. OPA decides whether the role may act at all; the SQL filter enforces which documents they reach. Documents use 384-dimensional embeddings from `all-MiniLM-L6-v2` with an ivfflat cosine index.

### Role Embedded in JWT

The `covenant_role` claim travels with the token. OPA receives it alongside the document classification and the requested action. The policy decision is entirely stateless — OPA does not query the database to resolve permissions, and the application does not maintain a session store.

`app/auth.py` decodes the JWT with `python-jose`, validates that the role is in `{"admin", "user", "auditor"}`, and returns the payload. An invalid role produces a 403 before the request reaches any business logic.

### Auditor Isolation

Auditors are never in a code path that touches the `documents` table. Their requests reach OPA with `action="query"`, which the policy denies — `allow` requires `action="read_logs"` for auditors. If they reach a `/query` endpoint anyway, OPA terminates the request with 403. The `/query` handler also explicitly branches: an auditor role that somehow passes OPA routes to `audit_logs` and returns immediately, never running the vector search or Claude call.

Isolation is enforced at two independent layers. Removing one still leaves the other.

### Prompt Caching

The system prompt sent to Claude is identical across requests for the same role. `claude_client.py` marks the system text with `cache_control: {"type": "ephemeral"}`, which caches it at the Anthropic API layer. Repeat queries within the cache TTL pay roughly 10% of normal input token cost for the cached portion.

---

## Challenges

### OPA Directory Conflict During Install

The first `opa` binary install attempt failed because the target path already contained a directory from a previous partial install — the install script refused to overwrite a directory with a file. Clearing the conflicting path and rerunning the install resolved it. Not a hard problem, but the error message pointed at a permissions issue rather than the real cause, which added a debugging round.

### Rego v1 Syntax: the `if` Keyword

OPA 0.61+ enforces Rego v1 syntax, which requires the `if` keyword in rule heads. Early versions of the policy used the v0 form:

```rego
# v0 — rejected by OPA 0.61+
allow {
    input.role == "admin"
}
```

OPA's error message (`rego_parse_error: unexpected open brace`) wasn't immediately obvious as a syntax-version issue. Switching to the v1 form with `allow if { ... }` throughout fixed it. The policy file in the repo uses v1 syntax throughout.

### PostgreSQL Schema Permissions

On first startup, the `CREATE EXTENSION IF NOT EXISTS vector` DDL statement failed because the application's database user didn't have `CREATE` privilege on the `public` schema. PostgreSQL 15+ restricts public schema creation by default. The fix was granting `CREATE ON SCHEMA public TO <app_user>` in the database init step, which is now documented in the setup notes.

### Docker Desktop WSL2 Corruption

Docker Desktop on WSL2 stopped responding mid-session — containers appeared to start but the daemon wasn't reachable, and `docker ps` hung indefinitely. Restarting Docker Desktop didn't recover it. Rather than debug a corrupted Docker Desktop install, the stack was run directly: OPA as a binary with `opa run --server`, PostgreSQL via the system package, and the FastAPI app via `uvicorn`. This was faster than a full Docker Desktop reinstall and proved the pipeline end-to-end without containers. The Docker Compose setup is present in the repo for clean-environment deployment.

### Token Expiry During Testing

JWTs generated for manual testing had a short expiry. Mid-session, requests that had been working started returning 401 errors. The fix was regenerating tokens with a longer expiry for development, and adding a note to the test setup to regenerate tokens at the start of a session. The automated pytest suite avoids this entirely by generating tokens inline in the test setup function.

---

## Design Decisions

**Why OPA rather than middleware in FastAPI?**  OPA is language-independent and independently deployable. A FastAPI dependency that enforces access is application code — it lives and dies with the Python process, it's tested with the Python test suite, and changing it requires a Python deploy. OPA is a sidecar with its own API, its own test framework (`opa test`), and its own audit log. Treating policy as infrastructure rather than application code is the architectural bet Covenant makes.

**Why default-deny in Rego?**  `default allow := false` means a new role, a new action, or a new document classification gets no access until a policy author explicitly grants it. Default-allow requires every new case to remember to add a deny. In a security-sensitive system, the cost of a missed allow (a user gets a 403) is much lower than the cost of a missed deny (a user sees data they shouldn't).

**Why not row-level security in PostgreSQL?**  Row-level security would enforce classification filtering at the database layer, which is a valid approach. Covenant uses application-level filtering after an OPA gate instead. The tradeoff: OPA gets to reason about the full request context (role, action, classification together) before any query runs, which row-level security can't replicate. The OPA gate is the primary enforcement point; the SQL filter is defense-in-depth.

**Why the auditor path hits OPA at all?**  An auditor calling `/query` with `action="query"` gets a 403 from OPA. An auditor calling `/query` with `action="read_logs"` — which the endpoint hardcodes — gets through OPA but then routes to the audit log path. OPA validates that auditors may only perform `read_logs`. This means the policy is exercised on every request regardless of endpoint, and there's a decision log entry for every auditor action.

---

## Results

| Metric | Value |
|---|---|
| Roles enforced | 3 (admin, user, auditor) |
| OPA policy decision | Proven: admin allowed, user denied confidential, auditor denied query |
| Enforcement point | Before retrieval and before LLM call |
| Vector dimensions | 384 (all-MiniLM-L6-v2) |
| Similarity metric | Cosine (ivfflat index) |
| Claude model | `claude-sonnet-4-6` |
| Prompt caching | Enabled (system prompt, ephemeral) |
| Total cost | $0 — runs entirely locally |
| Infrastructure | No cloud resources required |

All three roles were exercised against a running stack: admin received an answer, user was denied access to a confidential-classified query with 403, auditor was denied the query action with 403. The policy is the single enforcement point and its decisions are logged on every request.

---

*Source code: [github.com/adventuringghost/covenant](https://github.com/adventuringghost/covenant)*
