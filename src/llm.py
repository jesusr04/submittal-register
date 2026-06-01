"""Shared Anthropic client + a structured-output helper.

Every LLM stage in this project wants JSON that conforms to a schema, not prose.
The reliable way to get that from Claude is a forced tool call: we declare a
single tool whose `input_schema` IS the schema we want, then force the model to
call it. Claude returns the arguments as a dict that already matches the schema.

The client is built lazily so the module (and the offline tests) import fine
without a key set.
"""
import os

from anthropic import Anthropic

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY — set it in .env")
        _client = Anthropic(api_key=api_key)
    return _client


def structured(
    *,
    model: str,
    system: str,
    user: str,
    schema: dict,
    tool_name: str,
    max_tokens: int = 4000,
) -> dict:
    """Return Claude's answer as a dict matching `schema`, via a forced tool call.

    temperature=0 because a demo must produce the same register every run.
    """
    msg = _get_client().messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0,
        system=system,
        tools=[
            {
                "name": tool_name,
                "description": "Record the structured result.",
                "input_schema": schema,
            }
        ],
        tool_choice={"type": "tool", "name": tool_name},
        messages=[{"role": "user", "content": user}],
    )
    for block in msg.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError(f"Model did not call tool {tool_name!r}")
