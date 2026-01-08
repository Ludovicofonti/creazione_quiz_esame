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
            topics_to_use = grouped.keys()
            final_summary = "Quiz su tutti gli argomenti del corso"
        else:
            topics_to_use = selected_topics
            final_summary = "Quiz su: " + ", ".join(selected_topics)

        for topic in topics_to_use:
            contents.append(
                build_content_for_topic(
                    grouped[topic],
                    max(1, num_questions // len(topics_to_use))
                )
            )

        final_content = "\n\n".join(contents)

        generated = []
        attempts = 0

        while len(generated) < num_questions and attempts < 5:
            attempts += 1

            new_questions = generate_questions(
                content=final_content,
                summary=final_summary,
                n=num_questions - len(generated)
            )

            new_questions = filter_duplicate_questions(
                new_questions,
                st.session_state["seen_questions"]
            )

            generated.extend(new_questions)

        st.session_state["questions"] = generated

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

            if "explanation" in q:
                st.info(
                    f"📖 **Spiegazione (dal testo):**\n\n{q['explanation']}"
                )

        st.divider()
