import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from app.utils.logger import log  

_model = None
_active_index = None
_active_table_names = []
_active_schema_data = {}


def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        log.info("Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        log.info("Model loaded.")
    return _model


def load_schema(schema_path: str) -> dict:
    log.info(f"Loading schema from: {schema_path}")
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")
    with open(schema_path, "r") as f:
        return json.load(f)


def create_index(schema_data: dict):
    log.info("Building FAISS index with cosine similarity...")

    table_names = list(schema_data.keys())
    table_texts = []
    for table in table_names:
        table_info = schema_data[table]
        description = table_info.get("description", "")
        columns = table_info.get("columns", {})

        column_text = " | ".join(
            f"{col}: {desc}" for col, desc in columns.items()
        )
        full_text = f"{description} Columns: {column_text}"
        table_texts.append(full_text)

    model = get_embedder()
    embeddings = model.encode(table_texts, normalize_embeddings=True)  # normalize for cosine sim
    vectors = np.array(embeddings).astype("float32")

    dimension = vectors.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(vectors)

    log.info(f"FAISS index built with {len(table_names)} tables.")
    return index, table_names


def initialize_retrieval_system(schema_path: str):
    global _active_index, _active_table_names, _active_schema_data

    _active_schema_data = load_schema(schema_path)
    _active_index, _active_table_names = create_index(_active_schema_data)
    log.info("Retrieval system ready.")


def get_global_schema() -> dict:
    return _active_schema_data


def find_tables(question: str, index, table_names: list, schema_data: dict, top_k: int = 5) -> dict:
    log.info(f"Searching for tables matching: '{question}'")

    model = get_embedder()

    question_embedding = model.encode([question], normalize_embeddings=True)
    question_vector = np.array(question_embedding).astype("float32")

    actual_k = min(top_k, len(table_names))
    scores_raw, indices = index.search(question_vector, actual_k)

    retrieved_tables = []
    scores = []

    for idx, score in zip(indices[0], scores_raw[0]):
        if idx == -1:
            continue  
        table_name = table_names[idx]
        retrieved_tables.append(table_name)
        similarity = round(float(max(0.0, score)), 4)
        scores.append(similarity)

    confidence = round(float(np.mean(scores)), 4) if scores else 0.0

    log.info(f"Retrieved: {retrieved_tables}")
    log.info(f"Scores: {scores} | Confidence: {confidence}")

    return {
        "retrieved_tables": retrieved_tables,
        "scores": scores,
        "confidence": confidence,
    }


def retrieve_top_tables(question: str, top_k: int = 5) -> dict:
    if _active_index is None:
        raise ValueError("Retrieval system not initialized. Call initialize_retrieval_system() first.")
    return find_tables(question, _active_index, _active_table_names, _active_schema_data, top_k)