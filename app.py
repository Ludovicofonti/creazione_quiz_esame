import streamlit as st
import random

from material_loader import load_material, group_by_summary
from quiz_generator import generate_questions, filter_duplicate_questions

# =========================
# SESSION STATE
# =========================
if "seen_questions" not in st.session_state:
    st.session_state["seen_questions"] = set()

# =========================
# CONFIG
# =========================
JSON_PATH = "Estratto_psicologia_sociale.json"
MAX_DOMANDE = 20
MAX_ATTEMPT = 5

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
# UI — SELEZIONE ARGOMENTI
# =========================
ALL_TOPICS_LABEL = "Tutti gli argomenti (casuale)"

topic_options = [ALL_TOPICS_LABEL] + sorted(grouped.keys())

selected_topics = st.multiselect(
    "Scegli uno o più argomenti:",
    topic_options,
    default=[],
    placeholder="Seleziona uno o più argomenti"
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
def build_content_from_topics(topic_list, n, extra=3):
    """
    Unisce estratti da più argomenti.
    Campiona più estratti per aumentare varietà.
    """
    all_materials = []

    for topic in topic_list:
        all_materials.extend(grouped.get(topic, []))

    if not all_materials:
        return ""

    total_needed = n + extra

    sampled = []
    while len(sampled) < total_needed:
        sampled.append(random.choice(all_materials))

    return "\n\n".join(m["content"] for m in sampled)

# =========================
# GENERAZIONE QUIZ
# =========================
if st.button("🚀 Genera domande"):
    if not selected_topics:
        st.warning("⚠️ Seleziona almeno un argomento.")
    else:
        with st.spinner("Sto creando le domande..."):

            if ALL_TOPICS_LABEL in selected_topics:
                chosen_topics = list(grouped.keys())
                final_summary = "Quiz su tutti gli argomenti del corso"
            else:
                chosen_topics = selected_topics
                final_summary = "Quiz su: " + ", ".join(chosen_topics)

            final_questions = []
            attempts = 0

            while len(final_questions) < num_questions and attempts < MAX_ATTEMPT:
                remaining = num_questions - len(final_questions)

                final_content = build_content_from_topics(
                    chosen_topics,
                    remaining
                )

                questions = generate_questions(
                    content=final_content,
                    summary=final_summary,
                    n=remaining
                )

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
    for i, q in enumerate(st.session_state["questions"], 1):
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

            # 🔍 Mostra spiegazione / estratto
            if "explanation" in q and q["explanation"].strip():
                with st.expander("📖 Mostra estratto dal testo"):
                    st.write(q["explanation"])

        st.divider()
