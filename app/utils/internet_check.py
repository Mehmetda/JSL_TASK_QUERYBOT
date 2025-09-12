"""
Internet connectivity check utility
"""
import socket
import requests
import time

def check_internet_connection(timeout: int = 5) -> bool:
    """
    Check if internet connection is available
    
    Args:
        timeout: Timeout in seconds
        
    Returns:
        True if internet is available, False otherwise
    """
    try:
        # Try to connect to a reliable host
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except OSError:
        pass
    
    try:
        # Try to make a simple HTTP request
        response = requests.get("https://www.google.com", timeout=timeout)
        return response.status_code == 200
    except:
        pass
    
    return False

def check_openai_availability(timeout: int = 10) -> bool:
    """
    Check if OpenAI API is available
    
    Args:
        timeout: Timeout in seconds
        
    Returns:
        True if OpenAI API is available, False otherwise
    """
    try:
        import os
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False
            
        client = OpenAI(api_key=api_key)
        # Try a simple API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1,
            timeout=timeout
        )
        return True
    except Exception:
        return False
