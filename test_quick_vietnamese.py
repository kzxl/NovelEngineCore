"""Quick test for Vietnamese generation with local Ollama using generate_text."""

import sys
import asyncio

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from novel_engine.adapters.ollama_adapter import OllamaAdapter


async def main():
    adapter = OllamaAdapter(model_name="qwen2.5-coder:3b")
    prompt = (
        "Đóng vai tác giả tiểu thuyết Tiên Hiệp. Hãy viết một đoạn văn ngắn khoảng 120 chữ bằng TIẾNG VIỆT:\n"
        "Nhân vật Lâm Phong giơ tay ném túi 500 linh thạch xuống bàn, đối mặt với nụ cười nham hiểm của Đại Trưởng Lão Triệu khi bị đòi tăng giá."
    )
    print("--- CALLING LOCAL OLLAMA (qwen2.5-coder:3b) ---", flush=True)
    text = await adapter.generate_text(prompt=prompt, max_tokens=250)
    print("\n--- OUTPUT FROM LOCAL OLLAMA ---", flush=True)
    print(text, flush=True)
    print("--- DONE ---", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
