# Case Study: Project Covenant

> Secure RAG with Policy-First RBAC — adventuringghost.com

---

## Problem

Enterprise RAG pipelines typically enforce access in application code: a tangle of `if role == "admin"` checks scattered across handlers, easy to miss and hard to audit. When the LLM generates a response, there is often no single point where policy is validated — the access logic lives implicitly in the retrieval filter.

## Approach

Covenant inverts this: **policy is the first thing evaluated, before any retrieval or generation.** Open Policy Agent (OPA) receives a structured decision request on every query. If the policy returns `allow = false`, the request terminates with a 403. Claude Sonnet never runs.

## Architecture Decisions

### OPA as the Policy Gateway

Rego is declarative, versionable, and testable independently of the application. Moving policy out of Python means:
- Policy changes don't require application deploys
- Policy is auditable by security teams who don't read Python
- Decision logs are emitted automatically and can be shipped to a SIEM

### pgvector over a Dedicated Vector DB

A separate vector database (Pinecone, Qdrant, Weaviate) adds operational complexity and another trust boundary. pgvector keeps vector search inside PostgreSQL, so row-level security and role-based filtering happen at the database layer using familiar SQL semantics.

### Role Embedded in JWT

The `covenant_role` claim travels with the token. OPA receives it alongside the document classification label and the requested action. This makes the decision entirely stateless — OPA doesn't query the database to resolve permissions.

### Auditor Isolation

Auditors are never in a code path that touches the `documents` table. Their requests route to a separate `/audit` endpoint backed exclusively by `audit_logs`. This is enforced at both the OPA layer (action `read_logs` only) and the router layer.

## Results

- Policy enforcement is fully testable with `opa test`
- Zero application code changes required to update access rules
- Decision logs provide a complete audit trail for compliance

## Lessons Learned

TODO — fill in after first production run.
