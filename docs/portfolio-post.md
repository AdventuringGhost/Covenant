# Portfolio Post: When the AI Doesn't Get to Decide Who Sees What

> Draft for adventuringghost.com — by Skipper

---

Most RAG demos skip the hard part: **what happens when different users should see different data?**

I built Covenant to answer that question properly. It's a retrieval-augmented generation pipeline where access control is handled by Open Policy Agent before Claude ever runs. If OPA says no, the response is a 403 — not a hallucinated apology, not a redacted document, just a flat denial at the policy layer.

## The Setup

Three roles: **Admin** sees everything. **User** sees documents filtered to their clearance. **Auditor** sees only audit logs — never document content.

The tech: FastAPI handles the API layer. PostgreSQL with the pgvector extension stores documents and their embeddings. OPA evaluates every request against Rego policies that are version-controlled and independently testable. Claude Sonnet generates answers only after OPA has approved the retrieval.

## Why This Architecture

The usual approach is to filter results in application code — retrieve everything, then strip what the user shouldn't see. This is fragile. A missed conditional, a refactor that changes execution order, a new endpoint that forgets the check — any of these silently breaks access control.

Policy-first is different. OPA is a hard gate. The retrieval code doesn't contain access logic because it doesn't need to. The application trusts that if a request reaches the vector search, it has already been approved.

## What I'd Do Differently

TODO — after building this out further.

---

*Source: [github.com/adventuringghost/covenant](https://github.com/adventuringghost/covenant)*
