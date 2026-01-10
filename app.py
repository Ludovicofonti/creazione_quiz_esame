import streamlit as st
import random

from material_loader import (
    load_material,
    group_by_summary
)
from quiz_generator import (
    generate_questions,
    filter_duplicate_questions
)

# =========================
# SESSION STATE
# =========================
if "seen_questions" not in st.session_state:
    st.session_state["seen_questions"] = set()

# =========================
# CONFIG
# =========================
MAX_DOMANDE = 20

SUBJECTS = {
    "Psicologia sociale": "psicologia_sociale.json",
    "Imprenditorialità": "Imprenditorialità.json",
}

st.set_page_config(
    page_title="Generatore Quiz",
    layout="centered"
)

st.title("📚 Generatore di quiz per lo studio")

# =========================
# SELEZIONE MATERIA
# =========================
st.subheader("📘 Seleziona la materia")

selected_subject = st.selectbox(
    "Materia:",
    list(SUBJECTS.keys())
)

JSON_PATH = SUBJECTS[selected_subject]

# =========================
# LOAD MATERIALS
# =========================
materials = load_material(JSON_PATH)
grouped = group_by_summary(materials)

# =========================
# UI — SELEZIONE CAPITOLI
# =========================
topics = sorted(grouped.keys())

selected_topics = st.multiselect(
    "Seleziona capitoli",
    options=topics
)

use_all_topics = st.checkbox("Usa tutti gli argomenti", value=False)

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
# GENERAZIONE QUIZ
# =========================
if st.button("🚀 Genera domande"):
    with st.spinner("Sto creando le domande..."):
        contents = []

        if use_all_topics or not selected_topics:
            topics_to_use = list(grouped.keys())
            final_summary = "Quiz su tutti gli argomenti del corso"
        else:
            topics_to_use = selected_topics
            final_summary = "Quiz su: " + ", ".join(selected_topics)

        num_topics = len(topics_to_use)

        # =========================
        # DISTRIBUZIONE DOMANDE
        # =========================
        if num_questions < num_topics:
            # almeno 1 domanda per capitolo
            questions_per_topic = [1] * num_topics
        else:
            base = num_questions // num_topics
            remainder = num_questions % num_topics

            questions_per_topic = [
                base + 1 if i < remainder else base
                for i in range(num_topics)
            ]

        # =========================
        # COSTRUZIONE CONTENUTO
        # =========================
        for topic, q_per_topic in zip(topics_to_use, questions_per_topic):
            contents.append(
                build_content_for_topic(
                    grouped[topic],
                    q_per_topic
                )
            )

        final_content = "\n\n".join(contents)

        generated = []
        attempts = 0
        target_questions = sum(questions_per_topic)

        while len(generated) < target_questions and attempts < 5:
            attempts += 1

            new_questions = generate_questions(
                content=final_content,
                summary=final_summary,
                n=target_questions - len(generated)
            )

            new_questions = filter_duplicate_questions(
                new_questions,
                st.session_state["seen_questions"]
            )

            generated.extend(new_questions)

        st.session_state["questions"] = generated

    st.success(f"✅ Quiz generato! ({len(st.session_state['questions'])} domande)")

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

            if "explanation" in q:
                st.info(
                    f"📖 **Spiegazione (dal testo):**\n\n{q['explanation']}"
                )

        st.divider()
