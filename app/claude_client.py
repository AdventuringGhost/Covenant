# Claude Sonnet client: send OPA-approved context chunks to Claude and return the generated answer

import anthropic

from app.config import settings

_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question using only the provided context. "
    "If the context does not contain enough information, say so."
)


async def generate(query: str, chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(chunks)
    message = await _client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=[
            # Cache the system prompt — stable across requests
            {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
        ],
        messages=[
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
    )
    return message.content[0].text
