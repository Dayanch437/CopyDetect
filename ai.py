def check_authorship(original_text, suspect_text):
    from google import genai
    import time
    import os
    
    # Temporarily disable ALL proxy settings to avoid httpx conflicts
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                  'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
    old_proxies = {}
    
    for proxy_var in proxy_vars:
        if proxy_var in os.environ:
            old_proxies[proxy_var] = os.environ[proxy_var]
            del os.environ[proxy_var]
    
    # Explicitly set NO_PROXY to bypass proxy
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    
    def restore_proxies():
        """Helper function to restore proxy settings"""
        # Remove NO_PROXY
        os.environ.pop('NO_PROXY', None)
        os.environ.pop('no_proxy', None)
        # Restore old proxies
        for key, value in old_proxies.items():
            os.environ[key] = value
    
    system_instruction = (
        "You are an authorship checker for Turkmen language. "
        "You will receive two Turkmen texts: one is the original, the other may be fake or plagiarized. "
        "Compare the two texts and say if the second text is written by the same author as the first, or if it is plagiarized. "
        "Explain your reasoning briefly. "
        "Show  statistics about the texts, such as word choice, sentence structure, and style. ",
        "Give mathematical scores for similarity and likelihood of same authorship. "
        "Please provide all responses in Turkmen language."
    )
    
    message = (
        f"{system_instruction}\n\n"
        f"Original: {original_text}\n"
        f"Suspect: {suspect_text}\n"
        "Is the suspect text plagiarized or written by the same author? Provide your answer in Turkmen."
    )

    # Retry logic for overloaded server with exponential backoff
    max_retries = 3
    retry_delays = [3, 7, 15]  # Progressive delays
    
    models_to_try = ["gemini-2.0-flash-exp", "gemini-1.5-flash-latest", "gemini-pro"]
    
    for model in models_to_try:
        for attempt in range(max_retries):
            client = None
            try:
                # Create a new client for each attempt
                client = genai.Client(api_key="AIzaSyACJRBaLcEj9eUliyb8dt292S8Nz66ve30")
                chat = client.chats.create(model=model)
                response = chat.send_message(message)
                result = response.text
                
                # Clean markdown formatting from response
                # Remove ** (bold), __ (bold), * (italic), _ (italic), ``` (code blocks), # (headers)
                import re
                result = re.sub(r'\*\*', '', result)  # Remove **
                result = re.sub(r'__', '', result)    # Remove __
                result = re.sub(r'```[a-z]*\n?', '', result)  # Remove code blocks
                result = re.sub(r'^#+\s+', '', result, flags=re.MULTILINE)  # Remove headers
                
                # Clean up
                try:
                    if hasattr(client, 'close'):
                        client.close()
                except:
                    pass
                
                # Restore proxy settings before returning
                restore_proxies()
                return result
                
            except Exception as e:
                error_str = str(e)
                
                # Clean up on error
                try:
                    if client and hasattr(client, 'close'):
                        client.close()
                except:
                    pass
                
                # Check if it's a 503 or overload error
                if "503" in error_str or "overloaded" in error_str.lower() or "UNAVAILABLE" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = retry_delays[attempt]
                        print(f"Retrying... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Try next model if available
                        print(f"Trying alternative method...")
                        break
                # Check for 404 model not found - silently try next model
                elif "404" in error_str or "NOT_FOUND" in error_str or "not found" in error_str.lower():
                    print(f"Switching to alternative method...")
                    break  # Try next model
                # Check for quota/rate limit errors
                elif "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                    restore_proxies()
                    return "Ulgam häzirki wagtda işjeň ulanylyp dur. Birazdan täzeden synanyşyň.\n\n(The system is currently busy. Please try again in a few moments.)"
                # Other errors - show generic message without technical details
                else:
                    # Don't reveal technical errors to user
                    print(f"Error encountered: {error_str[:100]}...")  # Log for debugging
                    # Try next model instead of returning error
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        break
    
    # Restore proxy settings before final return
    restore_proxies()
    return "Ulgam häzirki wagtda elýeterli däl. Biraz wagtdan soň täzeden synanyşyň. (System is currently unavailable. Please try again in a few moments.)"