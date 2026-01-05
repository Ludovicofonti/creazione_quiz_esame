import streamlit as st
import random

from material_loader import (
    load_material,
    group_by_summary
)
from quiz_generator import generate_questions, filter_duplicate_questions

if "seen_questions" not in st.session_state:
    st.session_state["seen_questions"] = set()

# =========================
# CONFIG
# =========================
JSON_PATH = "Estratto_psicologia_sociale.json"
MAX_DOMANDE = 20
MAX_ATTEMPT = 5  # max tentativi per rigenerare domande duplicate

st.set_page_config(
    page_title="Generatore Quiz",
    layout="centered"
)

st.title("📚 Generatore di quiz per lo studio")

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
def build_content_for_topic(materials, n, extra=3):
    """
    Seleziona n+extra estratti casuali per dare più varietà.
    Se non bastano, ripete alcuni estratti.
    """
    total_needed = n + extra
    if not materials:
        return ""

    if len(materials) >= total_needed:
        sampled = random.sample(materials, total_needed)
    else:
        sampled = []
        while len(sampled) < total_needed:
            sampled.append(random.choice(materials))

    return "\n\n".join(m["content"] for m in sampled)

# =========================
# GENERAZIONE QUIZ
# =========================
if st.button("🚀 Genera domande"):
    with st.spinner("Sto creando le domande..."):

        if selected_topic == ALL_TOPICS_LABEL:
            # tutti gli argomenti
            contents_list = []
            for summary, mats in grouped.items():
                contents_list.append(build_content_for_topic(mats, num_questions))
            final_content = "\n\n".join(contents_list)
            final_summary = "Quiz su tutti gli argomenti del corso"
        else:
            final_content = build_content_for_topic(grouped[selected_topic], num_questions)
            final_summary = selected_topic

        final_questions = []
        attempts = 0

        while len(final_questions) < num_questions and attempts < MAX_ATTEMPT:
            remaining = num_questions - len(final_questions)
            # generiamo le domande mancanti
            questions = generate_questions(
                content=final_content,
                summary=final_summary,
                n=remaining
            )
            # filtriamo i duplicati
            questions = filter_duplicate_questions(
                questions,
                st.session_state["seen_questions"]
            )
            final_questions.extend(questions)
            attempts += 1

        st.session_state["questions"] = final_questions

    st.success("✅ Quiz generato!")

# =========================
# VISUALIZZAZIONE QUIZ
# =========================
if "questions" in st.session_state:
    questions = st.session_state["questions"]

    for i, q in enumerate(questions, 1):
        st.markdown(f"### ❓ Domanda {i}")
        st.write(q["question"])

        options = q["options"]
        correct = q["correct_answer"]

        selected = st.radio(
            "Seleziona una risposta:",
            options=list(options.keys()),
            format_func=lambda x: f"{x}. {options[x]}",
            index=None,
            key=f"question_{i}"
        )

        if selected is not None:
            if selected == correct:
                st.success("✅ Risposta corretta!")
            else:
                st.error(
                    f"❌ Risposta sbagliata. "
                    f"La risposta corretta è **{correct}. {options[correct]}**"
                )

        st.divider()
