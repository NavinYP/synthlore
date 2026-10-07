"""Atmospheric image generation (gpt-image-2).

These images make the corpus feel like a real franchise (portraits, maps,
heraldry, battle paintings) but deliberately carry NO ground-truth numbers or
dates - diffusion models cannot render exact text reliably, so every
fact-bearing visual is produced programmatically in fact_visuals.py instead.
"""
import asyncio
import base64
import os
from typing import Dict, Any, Optional

from src.settings import settings

AESTHETIC = ("1990s grimdark fantasy tabletop rulebook illustration, hand-inked, "
             "muted parchment palette, dramatic chiaroscuro, weathered texture")

STYLE_PROMPTS = {
    "portrait": "A {aes} character portrait of {name}, a grim figure of a shattered feudal realm, in thematic attire. No text or lettering in the image.",
    "landscape": "An epic {aes} landscape painting of the stronghold known as {name}: imposing silhouette, storm light, tiny figures for scale. No text or lettering.",
    "heraldry": "A {aes} heraldic banner and sigil of the faction called {name}: bold central emblem, torn cloth, aged gilding. No legible text.",
    "relic": "A {aes} museum-style illustration of the legendary artifact called {name}, presented on dark cloth with ornamental framing. No legible text.",
    "battle_painting": "A {aes} historical battle painting depicting the conflict remembered as {name}: massed banners, smoke, ruin. No legible text.",
    "creature": "A {aes} bestiary illustration of the monster called {name}, anatomically detailed and menacing. No legible text.",
}


async def generate_atmo_images(llm, atmo_images: Dict[str, Dict[str, Any]],
                               out_dir: str, concurrency: int = 3,
                               logger=None, verification: Dict[str, Any] = None):
    """Generates all atmospheric assets; returns (status, verification) maps.

    Images whose spec carries a controlled 'attribute' get the detail injected
    into the prompt and are then vision-verified. Only verified attributes may
    become benchmark questions; unverified images simply stay decorative.
    """
    os.makedirs(out_dir, exist_ok=True)
    sem = asyncio.Semaphore(concurrency)
    status: Dict[str, str] = {}
    verification = dict(verification or {})

    async def verify(spec: Dict[str, Any], out_path: str):
        attr = spec.get("attribute")
        if not attr or spec["image_id"] in verification:
            return
        with open(out_path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        try:
            ok = await llm.vision_check(
                b64, f"Does this image clearly show {attr['detail']}?")
        except Exception as e:
            ok = False
            if logger:
                logger.error(f"vision check {spec['image_id']} failed: {e}")
        verification[spec["image_id"]] = {
            "verified": ok, "slot": attr["slot"], "answer": attr["answer"],
            "detail": attr["detail"], "question": attr["question"],
            "entity": spec["entity"], "entity_name": spec["entity_name"],
            "host_doc": spec["host_doc"], "filename": spec["filename"],
        }

    async def one(spec: Dict[str, Any]):
        out_path = os.path.join(out_dir, spec["filename"])
        if os.path.exists(out_path):
            status[spec["image_id"]] = "cached"
            await verify(spec, out_path)
            return
        prompt = STYLE_PROMPTS[spec["style"]].format(aes=AESTHETIC, name=spec["entity_name"])
        attr = spec.get("attribute")
        if attr:
            prompt += f" The image MUST clearly and unmistakably include {attr['detail']}."
        async with sem:
            for attempt in range(3):
                try:
                    resp = await llm.image_client.images.generate(
                        model=settings.image_generation_deployment,
                        prompt=prompt, n=1, size="1024x1024",
                    )
                    with open(out_path, "wb") as fh:
                        fh.write(base64.b64decode(resp.data[0].b64_json))
                    status[spec["image_id"]] = "ok"
                    await verify(spec, out_path)
                    return
                except Exception as e:
                    if attempt == 2:
                        status[spec["image_id"]] = f"failed: {e}"
                        if logger:
                            logger.error(f"image {spec['image_id']} failed: {e}")
                    else:
                        await asyncio.sleep(4 ** (attempt + 1))

    await asyncio.gather(*(one(s) for s in atmo_images.values()))
    return status, verification
