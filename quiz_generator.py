import os
import json
from dotenv import load_dotenv
from ollama import Client
import re
import time

load_dotenv()

OLLAMA_MODEL = "gemma3:27b-cloud"
MAX_CHARS = 6000

client = Client(
    host="https://ollama.com",
    headers={
        "Authorization": "Bearer " + os.environ.get("OLLAMA_API_KEY", "")
    }
)

if not os.environ.get("OLLAMA_API_KEY"):
    raise RuntimeError("Variabile d'ambiente OLLAMA_API_KEY non impostata")


def build_prompt(content: str, summary: str, n: int) -> str:
    content = content[:MAX_CHARS]

    return f"""
Sei un assistente esperto in didattica universitaria.

ARGOMENTO:
{summary}

TESTO DI RIFERIMENTO (estratti coerenti sullo stesso argomento):
{content}

COMPITO:
Genera {n} domande a scelta multipla.

REGOLE OBBLIGATORIE:
- 4 opzioni (A, B, C, D)
- una sola risposta corretta
- distrattori plausibili
- non inventare informazioni
- livello universitario

FORMATO DI OUTPUT:
Restituisci SOLO JSON valido, senza testo extra.

[
  {{
    "question": "...",
    "options": {{
      "A": "...",
      "B": "...",
      "C": "...",
      "D": "..."
    }},
    "correct_answer": "A"
  }}
]
"""


def extract_json(text: str):
    """
    Estrae il primo array JSON valido dall'output del modello.
    """
    match = re.search(r"\[\s*{.*}\s*\]", text, re.DOTALL)
    if not match:
        raise ValueError("Nessun array JSON trovato nell'output")
    return match.group(0)


def generate_questions(content: str, summary: str, n: int = 5, retries: int = 1):
    prompt = build_prompt(content, summary, n)

    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    if not response.message or not response.message.content:
        raise ValueError("Risposta vuota dal modello")

    raw_output = response.message.content.strip()

    try:
        json_text = extract_json(raw_output)
        return json.loads(json_text)

    except Exception as e:
        if retries > 0:
            time.sleep(1)
            return generate_questions(
                content=content,
                summary=summary,
                n=n,
                retries=retries - 1
            )

        print("⚠️ Output non parsabile definitivo:")
        print(raw_output)
        raise ValueError("Output non è JSON valido") from e
