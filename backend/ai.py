import asyncio
import logging
import os
import re
import time

from google import genai
from google.genai import types
from config import settings

logger = logging.getLogger(__name__)

_PROXY_VARS = [
    'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
    'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy',
]

_SKIP_KEYWORDS = {"tts", "image", "robotics", "deep-research", "lyria",
                  "banana", "computer-use", "customtools", "clip"}

_client: genai.Client | None = None
available_models: list[str] = []


def init_models(api_key: str) -> None:
    global _client, available_models
    _client = genai.Client(api_key=api_key)
    try:
        available_models = [
            m.name.replace("models/", "")
            for m in _client.models.list()
            if "generateContent" in (m.supported_actions or [])
            and not any(kw in m.name for kw in _SKIP_KEYWORDS)
        ]
        logger.info(f"Available models ({len(available_models)}): {available_models}")
    except Exception as e:
        logger.error(f"Model discovery failed: {e}, using fallback")
        available_models = [settings.AI_MODEL]


def _clear_proxies() -> dict:
    saved = {}
    for var in _PROXY_VARS:
        if var in os.environ:
            saved[var] = os.environ.pop(var)
    return saved


def _restore_proxies(saved: dict) -> None:
    for var in _PROXY_VARS:
        os.environ.pop(var, None)
    os.environ.update(saved)


def build_authorship_prompt(original_text: str, suspect_text: str) -> str:
    system_instruction = (
        "Siz türkmen dilindäki tekstleriň awtorlygyny kesgitleýän ýöriteleşdirilen seljerme ulgamsyňyz. "
        "Size berlen iki teksti jikme-jik öwreniň we olaryň bir adam tarapyndan ýazylandygyny ýa-da biriniň beýlekisinden göçürilendigini (plagiat) anyklaň."
        "\n\nSELJERMEDE ÜNS BERMELI UGURLAR:"
        "\n1. ÝAZUW USLUBY: Sözlem gurluşyny, abzas düzümini we baglanyşdyryjy sözleriň ulanylyşyny öwreniň"
        "\n2. SÖZDAGLYK: Söz saýlawy, hünär terminleri, durnukly söz düzümleri we goşalyşyklaryň ulanylyşy"
        "\n3. GRAMMATIK GURLUŞ: Diliň özüne mahsus aýratynlyklary, grammatik gurluşlaryň we ýalňyşlyklaryň gabat gelşi"
        "\n4. TEKST SANLARY: Sözlem uzynlygyny, gaýtalanýan sözleri we täze sözleriň sanyny hasaplaň"
        "\n5. MEŇZEŞLIK DEREJESI: 0-dan 100%-e çenli takyk meňzeşlik görkezijisini kesgitläň"
        "\n6. AWTORLYK MÜMKINÇILIGI: 0-dan 100%-e çenli bir awtoryň ýazan bolmagy ähtimallygyny görkeziň"
        "\n\nJOGABYŇYZYŇ DÜZÜMI (şu bölümleri hökman goşuň):"
        "\n═══════════════════════════════════════"
        "\n📊 TEKST SANLARY"
        "\n   • Asyl tekstdäki sözleriň sany: [san]"
        "\n   • Barlanýan tekstdäki sözleriň sany: [san]"
        "\n   • Ortaça sözlem uzynlygy: [san söz]"
        "\n"
        "\n🔍 SÖZDAGLYK SELJERMESI"
        "\n   • Umumy sözlügiň meňzeşlik derejesi: [%]"
        "\n   • Hünär terminleriniň gabat gelşi: [%]"
        "\n   • Diňe bir tekstde duş gelýän sözleriň sany: [san]"
        "\n"
        "\n✍️ ÝAZUW USLUBY SELJERMESI"
        "\n   • Sözlem gurluşlarynyň meňzeşligi: [%]"
        "\n   • Diliň umumy häsiýetnamasynyň meňzeşligi: [%]"
        "\n   • Awtora mahsus alamatlar: [giňişleýin düşündiriş]"
        "\n"
        "\n📈 JEMI BAHA"
        "\n   • TEKSTLERIŇ MEŇZEŞLIGI: [0-100]%"
        "\n   • AWTORLYK MÜMKINÇILIGI: [0-100]%"
        "\n   • PLAGIAT HOWPUNYŇ DEREJESI: [Pes / Orta / Ýokary]"
        "\n"
        "\n🎯 NETIJE"
        "\n   [Bu iki teksti bir adam ýazdymy ýa-da biri beýlekisinden göçürilip alyndymy?"
        "\n    Netijäňizi deliller we mysallar bilen düşündiriň. Azyndan 3-5 anyk mysal getiriň.]"
        "\n═══════════════════════════════════════"
        "\n\n‼️ WAJYP: Ähli jogabyňyzy diňe TÜRKMEN DILINDE ýazyň! (Türkçe däl, Türkmençe!)"
    )

    return (
        f"{system_instruction}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📄 ASYL TEKST:\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{original_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 BARLANÝAN TEKST:\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{suspect_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Indi ýokarda görkezilen düzüme laýyklykda bu iki teksti jikme-jik seljeriň!"
    )


def check_authorship(original_text: str, suspect_text: str) -> str:
    prompt = build_authorship_prompt(original_text, suspect_text)
    saved_proxies = _clear_proxies()

    models = available_models or [settings.AI_MODEL]

    for model in models:
        for attempt in range(settings.MAX_RETRIES):
            try:
                response = _client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                        top_p=0.9,
                        max_output_tokens=8192,
                    ),
                )

                result = response.text or ""
                result = re.sub(r'```[a-z]*\n?', '', result)
                result = re.sub(r'```', '', result)
                result = re.sub(r'\*\*\*', '', result)
                result = result.strip()

                if len(result) < 100:
                    logger.warning(f"Response too short [{model}] (attempt {attempt + 1}), retrying...")
                    if attempt < settings.MAX_RETRIES - 1:
                        time.sleep(2)
                    continue

                logger.info(f"Got response from {model} ({len(result)} chars)")
                _restore_proxies(saved_proxies)
                return result

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower() or "resource_exhausted" in error_str.lower():
                    logger.warning(f"{model} rate-limited, trying next model...")
                    break  # skip to next model

                logger.warning(f"Attempt {attempt + 1}/{settings.MAX_RETRIES} [{model}] failed: {error_str[:150]}")
                if attempt < settings.MAX_RETRIES - 1:
                    wait = settings.RETRY_DELAYS[attempt]
                    logger.info(f"Waiting {wait}s before retry...")
                    time.sleep(wait)
                else:
                    logger.error(f"All retry attempts exhausted for {model}")

    _restore_proxies(saved_proxies)
    return settings.MESSAGES["system_unavailable"]


async def check_authorship_async(original_text: str, suspect_text: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, check_authorship, original_text, suspect_text)
