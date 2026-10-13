"""One-off: generate polished logo variations from the user's draft with Gemini Nano Banana."""
import asyncio
import base64
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

load_dotenv(Path(__file__).parent / ".env")
OUT = Path(__file__).parent / "static" / "logos"

BASE = (
    "Redesign this logo as a polished, professional brand logo for a UK family protection app called 'safe > sorry'. "
    "Keep the same composition: a sweeping circular ring/swoosh, a house roof line, a family of two adults holding hands with a small child, "
    "a sun at the top right, a flowing wave beneath the family, the wordmark 'safe > sorry' in lowercase bold rounded sans-serif with the '>' as a stylised chevron, "
    "the tagline 'Make sense of your protection needs', a short divider line, and the line 'it's better to be safe than sorry'. "
    "Recolour it exactly to the brand palette: deep navy #223342 (main colour, wordmark, family, ring) and warm gold #BF9B30 (sun, chevron, accents, divider), "
    "with subtle navy-to-slate and gold-to-light-gold gradients for depth and a refined, premium financial-services feel. "
    "Pure white background, crisp clean vector style, centred, perfectly spelled text, no extra words, no mockup, no shadows outside the logo. "
)
VARIANTS = {
    "v1": "Stay very close to the original layout and shapes, just refined and recoloured.",
    "v2": "Make the ring a gold-to-navy gradient swoosh, and the wave a soft gold gradient ribbon. Elegant and premium.",
    "v3": "Slightly more modern and minimal: smoother simplified family silhouettes, thinner elegant ring, generous spacing.",
}


async def gen(name: str, extra: str, ref_b64: str):
    chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"logo-{name}", system_message="You are an expert brand designer.")
    chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
    _, images = await chat.send_message_multimodal_response(UserMessage(text=BASE + extra, file_contents=[ImageContent(ref_b64)]))
    if not images:
        print(name, "no image")
        return
    (OUT / f"logo_{name}.png").write_bytes(base64.b64decode(images[0]["data"]))
    print(name, "saved")


async def main():
    ref = base64.b64encode((OUT / "draft.png").read_bytes()).decode()
    names = sys.argv[1:] or list(VARIANTS)
    await asyncio.gather(*(gen(n, VARIANTS[n], ref) for n in names))


asyncio.run(main())
