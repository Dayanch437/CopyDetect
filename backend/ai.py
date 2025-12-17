"""
AI-powered plagiarism detection using Google Gemini
"""
import asyncio
import logging
import os
import re
import time
from typing import Optional

from google import genai
from config import settings

# Configure logging
logger = logging.getLogger(__name__)


class ProxyManager:
    """Manages proxy environment variables to avoid httpx conflicts"""
    
    PROXY_VARS = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
        'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy'
    ]
    
    def __init__(self):
        self.old_proxies = {}
    
    def disable_proxies(self):
        """Temporarily disable all proxy settings"""
        for proxy_var in self.PROXY_VARS:
            if proxy_var in os.environ:
                self.old_proxies[proxy_var] = os.environ[proxy_var]
                del os.environ[proxy_var]
        
        # Explicitly set NO_PROXY to bypass proxy
        os.environ['NO_PROXY'] = '*'
        os.environ['no_proxy'] = '*'
        logger.debug("Proxies disabled")
    
    def restore_proxies(self):
        """Restore original proxy settings"""
        # Remove NO_PROXY
        os.environ.pop('NO_PROXY', None)
        os.environ.pop('no_proxy', None)
        
        # Restore old proxies
        for key, value in self.old_proxies.items():
            os.environ[key] = value
        
        self.old_proxies.clear()
        logger.debug("Proxies restored")


def clean_markdown(text: str) -> str:
    """Remove excessive markdown formatting but preserve structure"""
    # Remove code blocks only
    text = re.sub(r'```[a-z]*\n?', '', text)
    text = re.sub(r'```', '', text)
    # Remove triple asterisks
    text = re.sub(r'\*\*\*', '', text)
    return text.strip()


def build_authorship_prompt(original_text: str, suspect_text: str) -> str:
    """Build the AI prompt for authorship checking"""
    system_instruction = (
        "Siz türkmen dili üçin ýokary derejeli awtorlyk barlag ulgamysyňyz. "
        "Iki sany türkmen dilindäki teksti seljerersiňiz we olar bir awtor tarapyndan ýazylandymy ýa-da ikinji tekst göçürme (plagiat) bolup durmy kesgitlersiňiz."
        "\n\nDÜÝPLI SELJERME TALAPLARY:"
        "\n1. ÝAZ STILI SELJERIŞI: Sözlem gurluşyny, paragraf düzümini, geçiş sözleriniň ulanylyşyny derňäň"
        "\n2. LEKSIKA SELJERIŞI: Söz saýlamasy, terminologiýa, frazeologiýa, sinonimler ulanylyşyny seljeriň"
        "\n3. GRAMMATIKA SELJERIŞI: Dil häsiýetnamalary, grammatik gurluşlar, ýalňyşlyklaryň ahyrjaňlygy"
        "\n4. TEKST STATISTIKASY: Sözlem uzaklygyny, söz gaýtalanmasyny, täze sözleriň mukdaryny hasaplaň"
        "\n5. MEŇZEŞLIK BAHALARY: 0-100% aralygynda anyk meňzeşlik bahasy beriň"
        "\n6. AWTORLYK ÄHTIMALLYK: 0-100% aralygynda bir awtor ähtimallygy görkeziň"
        "\n\nNETIJE FORMATY (hökmany bölümleri):"
        "\n═══════════════════════════════════════"
        "\n📊 TEKST STATISTIKASY"
        "\n   • Asyl tekstiň sözleriniň sany: [san]"
        "\n   • Barlanýan tekstiň sözleriniň sany: [san]"
        "\n   • Ortaça sözlem uzaklygy: [san]"
        "\n"
        "\n🔍 LEKSIKA SELJERIŞI"
        "\n   • Umumy sözleriň meňzeşlik derejesi: [%]"
        "\n   • Ulanylýan terminleriň meňzeşligi: [%]"
        "\n   • Täsin/üýtgeşik sözleriň sany: [san]"
        "\n"
        "\n✍️ STIL SELJERIŞI"
        "\n   • Sözlem gurluşynyň meňzeşligi: [%]"
        "\n   • Dil häsiýetnama meňzeşligi: [%]"
        "\n   • Awtorlyk gol nyşanlary: [jikme-jik düşündiriş]"
        "\n"
        "\n📈 UMUMY BAHALAMA"
        "\n   • TEKST MEŇZEŞLIGI: [0-100]%"
        "\n   • AWTORLYK ÄHTIMALLYGY: [0-100]%"
        "\n   • PLAGIAT HOWPY: [Pes/Orta/Ýokary]"
        "\n"
        "\n🎯 NETIJE"
        "\n   [Jikme-jik düşündiriş beriň - bu tekstler bir awtor tarapyndan ýazylandymy?"
        "\n    Subutnamalary we sebäpleri aýdyň düşündiriň. 3-5 sany anyk mysallar getiriň.]"
        "\n═══════════════════════════════════════"
        "\n\n‼️ MÖHÜM: Bütin jogaby diňe TÜRKMEN DILINDE ýazyň! (Türk dili däl, Türkmen dili!)"
    )
    
    return (
        f"{system_instruction}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📄 ASYL TEKST (Original Text):\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{original_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 BARLANÝAN TEKST (Suspect Text):\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{suspect_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Indi bu iki teksti ýokarda görkezilen format boýunça düýpli seljeriň!"
    )


def check_authorship(original_text: str, suspect_text: str) -> str:
    """
    Check authorship between two texts using Google Gemini AI
    
    Args:
        original_text: The original text
        suspect_text: The suspect text to compare
        
    Returns:
        Analysis result in Turkmen language
    """
    proxy_manager = ProxyManager()
    proxy_manager.disable_proxies()
    
    message = build_authorship_prompt(original_text, suspect_text)
    
    try:
        # Try each model with retry logic
        for model in settings.AI_MODELS:
            logger.info(f"Attempting to use model: {model}")
            
            for attempt in range(settings.MAX_RETRIES):
                client = None
                try:
                    # Create a new client for each attempt
                    client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    
                    # Create chat with optimized configuration for detailed analysis
                    chat = client.chats.create(
                        model=model,
                        config={
                            "temperature": 0.4,  # Lower for more consistent, factual analysis
                            "top_p": 0.9,        # Focused nucleus sampling for quality
                            "top_k": 50,         # Broader token selection for detailed responses
                            "max_output_tokens": 4096,  # Allow longer, more detailed analysis
                            "candidate_count": 1,  # Single best response
                        }
                    )
                    
                    # Send message with clear instructions
                    response = chat.send_message(message)
                    
                    # Clean markdown but preserve structure
                    result = response.text
                    
                    # Only remove excessive markdown, keep formatting
                    result = re.sub(r'\*\*\*', '', result)  # Remove triple asterisks
                    result = re.sub(r'```[a-z]*\n?', '', result)  # Remove code blocks only
                    
                    # Verify we got a substantial response
                    if len(result.strip()) < 100:
                        logger.warning(f"Response too short from {model}, retrying...")
                        if attempt < settings.MAX_RETRIES - 1:
                            time.sleep(2)
                            continue
                    
                    # Clean up client
                    if hasattr(client, 'close'):
                        try:
                            client.close()
                        except Exception as e:
                            logger.warning(f"Error closing client: {e}")
                    
                    proxy_manager.restore_proxies()
                    logger.info(f"Successfully got detailed response from {model} ({len(result)} chars)")
                    return result
                    
                except Exception as e:
                    error_str = str(e)
                    logger.warning(f"Attempt {attempt + 1}/{settings.MAX_RETRIES} failed for {model}: {error_str[:100]}")
                    
                    # Clean up client on error
                    if client and hasattr(client, 'close'):
                        try:
                            client.close()
                        except:
                            pass
                    
                    # Handle specific error types
                    if "503" in error_str or "overloaded" in error_str.lower() or "UNAVAILABLE" in error_str:
                        if attempt < settings.MAX_RETRIES - 1:
                            wait_time = settings.RETRY_DELAYS[attempt]
                            logger.info(f"Server overloaded, waiting {wait_time}s before retry")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.warning(f"Max retries reached for {model}, trying next model")
                            break
                    
                    elif "404" in error_str or "NOT_FOUND" in error_str or "not found" in error_str.lower():
                        logger.warning(f"Model {model} not found, trying next model")
                        break
                    
                    elif "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                        proxy_manager.restore_proxies()
                        return settings.MESSAGES["system_busy"]
                    
                    else:
                        if attempt < settings.MAX_RETRIES - 1:
                            time.sleep(2)
                            continue
                        else:
                            break
        
        # If all attempts failed
        proxy_manager.restore_proxies()
        logger.error("All AI models and retry attempts exhausted")
        return settings.MESSAGES["system_unavailable"]
        
    except Exception as e:
        logger.error(f"Unexpected error in check_authorship: {e}")
        proxy_manager.restore_proxies()
        return settings.MESSAGES["system_unavailable"]


# Async wrapper function
async def check_authorship_async(original_text, suspect_text):
    """
    Async wrapper for check_authorship function.
    Runs the sync function in a thread executor to avoid blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, check_authorship, original_text, suspect_text)