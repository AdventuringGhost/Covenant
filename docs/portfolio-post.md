<!-- Portfolio write-up for adventuringghost.com: project summary, enforcement walkthrough, and key takeaways -->

# The AI Doesn't Get to Decide Who Sees What

Most RAG demos skip the hard part: what happens when different users should see different data? Not "show them different results" — actually enforce that some users cannot see certain documents at all, regardless of what they ask.

I built Covenant to answer that question properly. It's a retrieval-augmented generation pipeline where Open Policy Agent decides access before Claude ever runs. If OPA says no, the response is a 403 — not a hallucinated apology, not a filtered result, a hard rejection at the policy layer before any retrieval or generation occurs.

## The setup

Three roles: **Admin** sees everything. **User** sees documents filtered to public and internal classifications — confidential is denied with 403 before the vector search runs. **Auditor** sees only audit logs, never document content — a query request returns 403 regardless of classification.

The tech: FastAPI handles the API layer, JWT tokens carry the `covenant_role` claim, PostgreSQL with pgvector stores documents and their embeddings, OPA evaluates every request against Rego policies, Claude Sonnet generates answers only after OPA has approved the retrieval.

## Why OPA instead of application code

The usual approach is to filter in Python: extract the role from the token, check it in the handler, retrieve everything, strip what the user shouldn't see. This is fragile. A missed conditional, a refactor that changes execution order, a new endpoint that forgets the check — any of these silently breaks access control.

OPA is a hard gate at the start of the request. The Rego policy is a default-deny with three explicit allow rules: admin gets everything, user gets query on public and internal, auditor gets read_logs and nothing else. Anything not in that list is denied. The retrieval code contains no access logic because it doesn't need to — by the time it runs, OPA has already approved the request. Changing the policy doesn't require touching Python, rerunning the Python test suite, or deploying the application.

## What went wrong and how I fixed it

OPA's install failed because a previous partial install left a directory where the binary was supposed to go. The error message blamed permissions rather than the real cause, which added a debugging round. Once I identified the conflicting path and cleared it, the install was clean.

The Rego policy started with v0 syntax — rule heads without the `if` keyword — which OPA 0.61+ rejects. The error (`rego_parse_error: unexpected open brace`) wasn't an obvious pointer to a syntax-version issue. Switching all rule heads to the v1 form with `allow if { ... }` fixed it, and the policy is cleaner for it.

PostgreSQL 15+ restricts public schema creation by default. The application's database user couldn't run `CREATE EXTENSION IF NOT EXISTS vector` on startup. Granting `CREATE ON SCHEMA public` to the app user resolved it — now in the setup notes.

Docker Desktop on WSL2 stopped responding mid-session and didn't recover after a restart. Rather than reinstall it, I ran the stack directly: OPA as a binary with `--server`, PostgreSQL from the system package, FastAPI via uvicorn. This was faster and proved the pipeline without needing Docker working. The Compose setup is in the repo for clean environments.

JWTs generated for manual testing expired mid-session. Requests that had been working started returning 401s. The fix was regenerating tokens with a longer development expiry. The automated test suite avoids this entirely by generating tokens inline in each test function.

## What this demonstrates

Covenant's architecture separates policy from retrieval. OPA is infrastructure — it has its own API, its own test framework, its own audit log. Every access decision gets a structured log entry regardless of whether it was allowed or denied. That's the audit trail a compliance requirement asks for, and it comes from the policy engine, not from application logging that might be incomplete.

The three roles were proven against a live stack. Admin got an answer. User got a 403 on a confidential query before the database was touched. Auditor got a 403 on a query request. Total cost: zero dollars — the whole system runs locally.

## Links

GitHub: [github.com/adventuringghost/covenant](https://github.com/adventuringghost/covenant)
