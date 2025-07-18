
import requests

def generate(prompt: str, model: str = "gemma3n:e2b") -> str:
    """
    Generate a response from a local Ollama model given a prompt.
    """
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except requests.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return ""

if __name__ == "__main__":
    prompt = input("Enter your prompt: ")
    result = generate(prompt)
    print(result)
