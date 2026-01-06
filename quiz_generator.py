import os
import json
import re
import time
import random
import string
import hashlib
from dotenv import load_dotenv
from ollama import Client

# ==========================
# ENV & CONFIG
# ==========================
load_dotenv()

OLLAMA_MODEL = "gemma3:27b-cloud"
MAX_CHARS = 6000

API_KEY = os.environ.get("OLLAMA_API_KEY")
if not API_KEY:
    raise RuntimeError("OLLAMA_API_KEY non configurata")

client = Client(
    host="https://ollama.com",
    headers={
        "Authorization": "Bearer " + API_KEY
    }
)

# ==========================
# PROMPT
# ==========================
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
- per ogni domanda, includi un ESTRATTO DEL TESTO fornito
  che giustifichi chiaramente la risposta corretta

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
    "correct_answer": "A",
    "explanation": "Estratto testuale rilevante dal testo di riferimento"
  }}
]
"""

# ==========================
# UTILS
# ==========================
def extract_json(text: str) -> str:
    """
    Estrae il primo array JSON dall'output del modello.
    """
    match = re.search(r"\[\s*{.*?}\s*\]", text, re.DOTALL)
    if not match:
        raise ValueError("Nessun array JSON trovato nell'output")
    return match.group(0)


def shuffle_question_options(question: dict) -> dict:
    """
    Mescola le opzioni e aggiorna correttamente correct_answer.
    """
    options = question["options"]
    correct_letter = question["correct_answer"]

    correct_text = options[correct_letter]

    option_texts = list(options.values())
    random.shuffle(option_texts)

    letters = list(string.ascii_uppercase[:len(option_texts)])
    new_options = dict(zip(letters, option_texts))

    new_correct_letter = next(
        letter for letter, text in new_options.items()
        if text == correct_text
    )

    question["options"] = new_options
    question["correct_answer"] = new_correct_letter

    return question

# ==========================
# CORE FUNCTION
# ==========================
def generate_questions(
    content: str,
    summary: str,
    n: int = 5,
    retries: int = 1
) -> list[dict]:

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
        questions = json.loads(json_text)

        for q in questions:
            shuffle_question_options(q)

        return questions

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

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # rimuove punteggiatura
    text = re.sub(r"\s+", " ", text)    # normalizza spazi
    return text.strip()

def question_fingerprint(question: dict) -> str:
    normalized = normalize_text(question["question"])
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()

def filter_duplicate_questions(
    questions: list[dict],
    seen_fingerprints: set
) -> list[dict]:

    unique_questions = []

    for q in questions:
        fp = question_fingerprint(q)

        if fp not in seen_fingerprints:
            seen_fingerprints.add(fp)
            unique_questions.append(q)

    return unique_questions