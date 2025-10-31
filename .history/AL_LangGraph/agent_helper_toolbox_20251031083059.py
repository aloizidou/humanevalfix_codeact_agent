from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

MODEL = "qwen2.5vl:7b"
TEMPERATURE = 0.4  

def get_text_response(prompt: str) -> str:
    """Get text response from LLM which will help with our logical reasoning"""
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
