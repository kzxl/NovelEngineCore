"""Quick test with 1.5B model for blazing speed."""

import sys
import asyncio

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from novel_engine.adapters.ollama_adapter import OllamaAdapter


async def main():
    adapter = OllamaAdapter(model_name="qwen2.5-coder:1.5b")
    prompt = (
        "Đóng vai tác giả tiểu thuyết Tiên Hiệp. Hãy viết một đoạn văn ngắn khoảng 100 chữ bằng TIẾNG VIỆT:\n"
        "Lâm Phong ném túi 500 linh thạch xuống bàn gỗ, nhìn thẳng vào mắt Đại Trưởng Lão Triệu."
    )
    print("--- [OLLAMA 1.5B] GENERATING REAL PROSE ---", flush=True)
    text = await adapter.generate_text(prompt=prompt, max_tokens=150)
    print("\n--- OUTPUT ---", flush=True)
    print(text, flush=True)
    print("\n--- SUCCESS ---", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
