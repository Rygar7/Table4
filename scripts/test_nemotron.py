"""Verify that the local NVIDIA credentials can reach Nemotron."""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("NVIDIA_API_KEY")
base_url = os.getenv("NVIDIA_BASE_URL")
model = os.getenv("NVIDIA_MODEL")

if not api_key or not base_url or not model:
    raise RuntimeError("Missing NVIDIA configuration in .env")

client = OpenAI(base_url=base_url, api_key=api_key)
response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": "You are a connection-test service. Follow the requested output exactly.",
        },
        {"role": "user", "content": "Reply with exactly: CONNECTION_OK"},
    ],
    temperature=0.0,
    max_tokens=64,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)

message = response.choices[0].message.content or ""
if "CONNECTION_OK" not in message:
    raise RuntimeError("Nemotron responded, but the connection check output was unexpected")

print("Nemotron connection successful.")
