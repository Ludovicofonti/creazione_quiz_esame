import json
import random
from collections import defaultdict
from typing import List, Dict


def load_material(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def group_by_summary(materials: List[Dict]) -> Dict[str, List[Dict]]:
    grouped = defaultdict(list)
    for m in materials:
        grouped[m["summary"]].append(m)
    return grouped


def sample_contents(materials: List[Dict], k: int = 2) -> str:
    """
    Estrae k testi casuali e concatena i contenuti.
    """
    sampled = random.sample(materials, min(k, len(materials)))
    return "\n\n".join(m["content"] for m in sampled)

def sample_across_topics(grouped_materials, n_topics: int, k_texts: int) -> str:
    """
    Seleziona n_topics argomenti casuali e k_texts per ciascuno.
    """
    summaries = list(grouped_materials.keys())
    chosen_summaries = random.sample(
        summaries,
        min(n_topics, len(summaries))
    )

    contents = []

    for summary in chosen_summaries:
        texts = grouped_materials[summary]
        sampled_texts = random.sample(
            texts,
            min(k_texts, len(texts))
        )
        contents.extend(m["content"] for m in sampled_texts)

    return "\n\n".join(contents)
