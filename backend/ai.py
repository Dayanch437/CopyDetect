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
    """Remove markdown formatting from text"""
    text = re.sub(r'\*\*', '', text)  # Remove **
    text = re.sub(r'__', '', text)    # Remove __
    text = re.sub(r'```[a-z]*\n?', '', text)  # Remove code blocks
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)  # Remove headers
    return text


def build_authorship_prompt(original_text: str, suspect_text: str) -> str:
    """Build the AI prompt for authorship checking"""
    system_instruction = (
        "You are an authorship checker for the Turkmen language. "
        "You will receive two Turkmen texts: one is the original, the other may be fake or plagiarized. "
        "Compare the two texts and decide if the second text is written by the same author as the first, or if it is plagiarized. "
        "Explain your reasoning briefly. "
        "Show statistics about the texts, such as word choice, sentence structure, and writing style, specially meaning vocabulary usage. "
        "Give mathematical scores for similarity and likelihood of same authorship. "
        "All responses must be written only in the Turkmen language (not Turkish)."
    )
    
    return (
        f"{system_instruction}\n\n"
        f"Original: {original_text}\n"
        f"Suspect: {suspect_text}\n"
        "Is the suspect text plagiarized or written by the same author? Provide your answer in Turkmen."
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
            for attempt in range(settings.MAX_RETRIES):
                client = None
                try:
                    # Create a new client for each attempt
                    client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    chat = client.chats.create(model=model)
                    response = chat.send_message(message)
                    result = clean_markdown(response.text)
                    
                    # Clean up client
                    if hasattr(client, 'close'):
                        try:
                            client.close()
                        except Exception as e:
                            logger.warning(f"Error closing client: {e}")
                    
                    proxy_manager.restore_proxies()
                    logger.info(f"Successfully got response from {model}")
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