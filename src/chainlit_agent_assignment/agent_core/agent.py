import os
import json
import asyncio
from typing import AsyncGenerator
import openai
from .history import HistoryLogger

openai.api_key = os.getenv("OPENAI_API_KEY")
HISTORY_FILE = os.getenv("HISTORY_FILE", "runs/chat_history.jsonl")
history = HistoryLogger(HISTORY_FILE)

api_key="AIzaSyA6JAzl5NduSXYwk7lzdGt7vEV0QeBoGRw"



# --- Demo Tool
def web_search_tool(query: str) -> dict:
    return {
        "title": f"Demo search result for {query}",
        "snippet": f"This is a mocked snippet for '{query}'.",
        "url": "https://example.com"
    }

# --- Stream response from OpenAI API
async def stream_completion(messages):
    loop = asyncio.get_event_loop()

    def blocking():
        return openai.ChatCompletion.create(
            model="gemini-2.5-flash",
            messages=messages,
            stream=True
        )

    for chunk in await loop.run_in_executor(None, blocking):
        delta = ""
        try:
            for choice in chunk.get("choices", []):
                delta += choice.get("delta", {}).get("content", "")
        except Exception:
            pass
        if delta:
            yield delta

# --- Agent logic
async def run_agent(user_text: str) -> AsyncGenerator[str, None]:
    history.append({"role": "user", "text": user_text})

    tool_output = None
    if user_text.strip().lower().startswith("search:"):
        q = user_text.split(":", 1)[1].strip()
        tool_output = web_search_tool(q)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_text},
    ]

    if tool_output:
        messages.append({"role": "system", "content": f"Tool Output:\n{json.dumps(tool_output)}"})

    assembled = ""
    async for chunk in stream_completion(messages):
        assembled += chunk
        yield chunk

    history.append({"role": "assistant", "text": assembled, "tool_output": tool_output})
