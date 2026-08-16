# ─────────────────────────────────────────────────────────
# services/llamacpp.py — Low-level llama.cpp (OpenAI-compatible) client
# ─────────────────────────────────────────────────────────
# Wraps llama.cpp's OpenAI-compatible HTTP API so the AI
# endpoints in api/v1/ai.py stay thin.
#
# HOW THIS WORKS (the method):
#   llama.cpp's `llama-server` exposes an OpenAI-compatible
#   REST API. That means we talk to it exactly like we would
#   talk to OpenAI: POST a chat payload to
#       {server}/v1/chat/completions
#   with a body like
#       {"model": "...", "messages": [{"role": "user", "content": "..."}]}
#   and it replies with a JSON object whose completion text is at
#       choices[0].message.content
#
# REFERENCES (sources):
#   llama.cpp HTTP server README (the authoritative guide):
#     https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
#     -> section "OpenAI API compatible chat completions"
#   OpenAI Chat Completions API reference (the schema we send):
#     https://platform.openai.com/docs/api-reference/chat
#   httpx AsyncClient docs (how we make the request):
#     https://www.python-httpx.org/async/
# ─────────────────────────────────────────────────────────

import httpx

from backend.app.config import settings


# Sends a chat request to llama.cpp and returns the assistant's reply text
# by POSTing OpenAI-style messages to {base}/chat/completions and reading choices[0].message.content.
async def chat_completion(
    messages: list[dict],
    *,
    max_tokens: int = 2048,
    temperature: float = 0.3,
    timeout: float = 180.0,
) -> str:
    payload = {
        "model": settings.llamacpp_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{settings.llamacpp_base_url}/chat/completions",
            json=payload,
        )
    resp.raise_for_status()

    data = resp.json()
    return data["choices"][0]["message"]["content"]
