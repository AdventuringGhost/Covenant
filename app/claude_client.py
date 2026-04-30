import anthropic
import structlog

from app.config import settings

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = structlog.get_logger()

_SYSTEM_BASE = (
    "You are a secure document assistant. Answer the user's question using only the provided "
    "context. If the context does not contain enough information, say so. Never reveal document "
    "classification labels, access tiers, or internal security metadata."
)

_ROLE_NOTE: dict[str, str] = {
    "admin": "The requester is an administrator with access to all document classifications.",
    "user": "The requester has standard access (public and internal documents only).",
    "auditor": "The requester is an auditor. Provide audit information only — never document content.",
}


async def generate(query: str, chunks: list[str], role: str) -> str:
    context = "\n\n---\n\n".join(chunks) if chunks else "No relevant documents found."
    system_text = f"{_SYSTEM_BASE}\n\n{_ROLE_NOTE.get(role, '')}"

    message = await _client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": system_text,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
    )
    logger.info(
        "llm_response_generated",
        role=role,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
    )
    return message.content[0].text
