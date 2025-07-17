# backend/embedder.py

import os
import json
import hashlib
import time
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, models
import chromadb

# === Config ===
CHUNKS_DIR = "data/chunks_uploaded"  # New per-file chunks directory
DEFAULT_CHUNKS_FILE = "data/chunks.json"
DB_DIR = "backend/vector_store"
LOCAL_MODEL_PATH = "backend/local_models/microsoft/codebert-base"
COLLECTION_NAME = "code_chunks"
BATCH_SIZE = 32

# === Generate Unique ID ===
def get_chunk_id(chunk):
    raw = (chunk.get("comments", "") + "\n" + chunk.get("code", "")).strip()
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

# === Load chunks from per-file or full chunks.json ===
def load_chunks():
    files_env = os.environ.get("FILES_TO_EMBED")

    if files_env:
        print(f"🧠 Selective embedding mode — files: {files_env}")
        filenames = [f.strip() for f in files_env.split(",")]
        chunks = []
        for fname in filenames:
            chunk_path = os.path.join(CHUNKS_DIR, f"{fname}.json")
            if os.path.exists(chunk_path):
                with open(chunk_path, "r", encoding="utf-8") as f:
                    file_chunks = json.load(f)
                    chunks.extend(file_chunks)
                    print(f"📄 Loaded {len(file_chunks)} chunks from {fname}.json")
            else:
                print(f"⚠️ File not found: {chunk_path}")
        return chunks
    else:
        print(f"📂 Loading chunks from: {DEFAULT_CHUNKS_FILE}")
        if not os.path.exists(DEFAULT_CHUNKS_FILE):
            raise FileNotFoundError(f"❌ Missing chunks file: {DEFAULT_CHUNKS_FILE}")
        with open(DEFAULT_CHUNKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

# === Init Chroma ===
def get_collection():
    client = chromadb.PersistentClient(path=DB_DIR)
    return client.get_or_create_collection(name=COLLECTION_NAME)

# === Embed chunks ===
def embed_chunks(chunks, model, collection):
    all_ids = [get_chunk_id(c) for c in chunks]

    print("📦 Checking for existing embeddings...")
    existing = set()
    try:
        for i in range(0, len(all_ids), 100):
            sub_ids = all_ids[i:i+100]
            res = collection.get(ids=sub_ids, include=[])
            existing.update(res.get("ids", []))
    except Exception as e:
        print(f"⚠️ Could not check existing embeddings: {e}")

    new_chunks = []
    new_ids = []
    for chunk, cid in zip(chunks, all_ids):
        if cid not in existing:
            new_chunks.append(chunk)
            new_ids.append(cid)

    print(f"\n📊 Chunk Summary:")
    print(f"📁 Total Loaded        : {len(chunks)}")
    print(f"📌 Already Embedded    : {len(existing)}")
    print(f"🆕 New Chunks to Embed : {len(new_chunks)}")

    if not new_chunks:
        print("✅ No new chunks to embed. Exiting.")
        return

    for i in tqdm(range(0, len(new_chunks), BATCH_SIZE), desc="🔧 Embedding"):
        batch = new_chunks[i:i+BATCH_SIZE]
        ids = new_ids[i:i+BATCH_SIZE]
        texts = [(c.get("comments", "") + "\n" + c.get("code", "")).strip() for c in batch]
        metas = [
            {
                "file": c.get("file", ""),
                "type": c.get("type", ""),
                "start_line": c.get("start_line", -1),
                "end_line": c.get("end_line", -1),
            }
            for c in batch
        ]

        try:
            vectors = model.encode(texts, show_progress_bar=False, convert_to_numpy=True).tolist()
            collection.add(documents=texts, embeddings=vectors, metadatas=metas, ids=ids)
        except Exception as e:
            print(f"❌ Failed batch: {e}")

# === Main Entrypoint ===
if __name__ == "__main__":
    start = time.time()

    chunks = load_chunks()

    print(f"🔄 Loading CodeBERT from: {LOCAL_MODEL_PATH}")
    word = models.Transformer(LOCAL_MODEL_PATH)
    pool = models.Pooling(word.get_word_embedding_dimension())
    model = SentenceTransformer(modules=[word, pool])

    collection = get_collection()
    embed_chunks(chunks, model, collection)

    print(f"\n✅ Embedding complete!")
    print(f"🕒 Time Taken: {round(time.time() - start, 2)}s")
    print(f"💾 Vector Store: {DB_DIR}")
