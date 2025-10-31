from openai import OpenAI

# Connect to Ollama (local)
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

MODEL = "qwen2.5:0.5b"
TEMPERATURE = 0.4  # lower for reasoning accuracy

def get_text_response(prompt: str) -> str:
    """Query your local Ollama model and return text output."""
    system_message = {
        "role": "system",
        "content": "You are an expert Python code analyst. Be concise and technical."
    }
    user_message = {"role": "user", "content": prompt}

    response = client.chat.completions.create(
        model=MODEL,
        messages=[system_message, user_message],
        temperature=TEMPERATURE,
    )
    return response.choices[0].message.content.strip()
