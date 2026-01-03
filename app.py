import streamlit as st
import random

from material_loader import (
    load_material,
    group_by_summary
)
from quiz_generator import generate_questions

# =========================
# CONFIG
# =========================
JSON_PATH = "Estratto_psicologia_sociale.json"
MAX_DOMANDE = 20

st.set_page_config(page_title="Generatore Quiz", layout="centered")
st.title("Generatore di quiz per lo studio")

# =========================
# LOAD MATERIALS
# =========================
materials = load_material(JSON_PATH)
grouped = group_by_summary(materials)

# =========================
# UI — SELEZIONE ARGOMENTO
# =========================
ALL_TOPICS_LABEL = "Tutti gli argomenti (casuale)"

topics = [ALL_TOPICS_LABEL] + sorted(grouped.keys())

selected_topic = st.selectbox(
    "Scegli l'argomento:",
    topics
)

num_questions = st.slider(
    "Quante domande vuoi generare?",
    min_value=3,
    max_value=MAX_DOMANDE,
    value=5
)

# =========================
# LOGICA ESTRATTI
# =========================
def build_content_for_topic(materials, n):
    """
    Seleziona n estratti casuali.
    Se non bastano, ripete alcuni estratti.
    """
    if not materials:
        return ""

    if len(materials) >= n:
        sampled = random.sample(materials, n)
    else:
        sampled = []
        while len(sampled) < n:
            sampled.append(random.choice(materials))

    return "\n\n".join(m["content"] for m in sampled)


# =========================
# GENERAZIONE
# =========================
if st.button("Genera domande"):
    with st.spinner("Sto creando le domande..."):
        if selected_topic == ALL_TOPICS_LABEL:
            # usa TUTTI gli argomenti
            contents = []
            for summary, mats in grouped.items():
                contents.append(
                    build_content_for_topic(mats, num_questions)
                )

            final_content = "\n\n".join(contents)
            final_summary = "Quiz su tutti gli argomenti del corso"

        else:
            final_content = build_content_for_topic(
                grouped[selected_topic],
                num_questions
            )
            final_summary = selected_topic

        questions = generate_questions(
            content=final_content,
            summary=final_summary,
            n=num_questions
        )

    st.success("Quiz generato!")

    for i, q in enumerate(questions, 1):
        st.markdown(f"### ❓ Domanda {i}")
        st.write(q["question"])
        for key, val in q["options"].items():
            st.write(f"**{key}.** {val}")
        st.info(f"✅ Risposta corretta: {q['correct_answer']}")
