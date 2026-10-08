import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')


def get_client():
    key = os.getenv('GROQ_API_KEY', '').strip()
    if not key:
        return None
    return Groq(api_key=key)


def ask_groq(messages, temperature=0.2, max_tokens=1800):
    client = get_client()
    if client is None:
        raise RuntimeError('GROQ_API_KEY is not configured. Add it to your .env file.')
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
