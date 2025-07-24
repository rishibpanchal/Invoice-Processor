
import requests

def generate_ollama_response(prompt: str, model: str = "gemma3n:e2b") -> str:
    """
    Generate a response from a local Ollama model given a prompt.
    
    Args:
        prompt: The input prompt for the model
        model: The model name to use for generation
        
    Returns:
        The generated response text
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
    result = generate_ollama_response(prompt)
    print(result)
