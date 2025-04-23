import os
import requests

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")  # Set this in Railway if using OpenAI fallback

def openai_completion(prompt, model="gpt-3.5-turbo"):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=20)
        resp.raise_for_status()
        result = resp.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"[OpenAI Fallback Error] {e}"
