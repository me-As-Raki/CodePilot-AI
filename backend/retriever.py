# [Your imports unchanged]
import os
import json
import re
import chromadb
from sentence_transformers import SentenceTransformer, models
from chromadb.utils.embedding_functions import EmbeddingFunction

CHUNKS_FILE = "data/chunks.json"
CHUNKS_UPLOADED_DIR = "data/chunks_uploaded"
DB_DIR = "backend/vector_store"
LOCAL_MODEL_PATH = "backend/local_models/microsoft/codebert-base"
COLLECTION_NAME = "code_chunks"

def load_chunks(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Chunk file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

class LocalCodeBERTEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_path):
        print(f"🔄 Loading local CodeBERT model from {model_path}...")
        word_model = models.Transformer(model_path)
        pooling_model = models.Pooling(word_model.get_word_embedding_dimension())
        self.model = SentenceTransformer(modules=[word_model, pooling_model])

    def __call__(self, texts):
        return self.model.encode(texts).tolist()

def is_vector_store_ready():
    return os.path.isdir(DB_DIR) and len(os.listdir(DB_DIR)) > 0

def preprocess_query(query: str) -> str:
    original = query.strip()
    macro_candidates = [w for w in original.split() if w.isupper() and w.isidentifier()]
    if macro_candidates:
        macro = macro_candidates[0]
        new_query = f"#define {macro} VALUE"
        print(f"🛠 Preprocessed query: '{original}' → '{new_query}'")
        return new_query

    if "function" in original.lower() or "(" in original:
        parts = original.replace("?", "").split()
        for word in parts:
            if "(" in word or word.endswith("()"):
                fname = word.strip("()")
                new_query = f"void {fname}(...) {{"
                print(f"🛠 Preprocessed query: '{original}' → '{new_query}'")
                return new_query

    print(f"🛠 Preprocessed query: '{original}' → '{original}'")
    return original

def get_debug_chunks(chunks, query):
    visual_regex = re.compile(r'(printf|puts|print_\w*)\s*\(.*("|\'|-{3,}|={3,}|\\n).*?\)', re.IGNORECASE)
    debug_keywords = ["debug", "print", "log", "output", "display", "trace", "separator", "format"]
    is_debug_query = any(term in query.lower() for term in debug_keywords)

    matched_chunks = []
    for c in chunks:
        code = c.get("code", "")
        if (
            re.search(r'\bprintf\s*\(', code)
            or re.search(r'\bputs\s*\(', code)
            or re.search(r'\bprint_\w*\s*\(', code)
            or "log_" in code
            or visual_regex.search(code)
        ):
            matched_chunks.append(c)

    if matched_chunks:
        print(f"🐞 Injecting {len(matched_chunks)} debug/visual-related chunk(s).")

    return matched_chunks[:3] if not is_debug_query else matched_chunks

def get_struct_related_chunks(chunks, query):
    keywords = re.findall(r'\w+', query.lower())
    struct_words = ["struct", "typedef", "union", "enum"]
    logic_words = ["person", "role", "rank", "gpa", "student", "teacher"]

    inject_struct_chunks = []
    for c in chunks:
        code = c.get("code", "").lower()
        if any(sw in code for sw in struct_words) and any(lw in query.lower() for lw in logic_words):
            inject_struct_chunks.append(c)

    if inject_struct_chunks:
        print(f"🧩 Injecting {len(inject_struct_chunks)} struct/typedef/union-related chunks.")

    return inject_struct_chunks[:3]

def get_chunks_from_uploaded_files(query: str, k: int = 5) -> list[dict]:
    uploaded_files = [
        os.path.join("chunks_uploaded", f)
        for f in os.listdir("chunks_uploaded")
        if f.endswith(".json")
    ]
    if not uploaded_files:
        print("⚠️ No uploaded file chunks found.")
        return []

    all_chunks = []
    for fpath in uploaded_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                all_chunks.extend(chunks)
        except Exception as e:
            print(f"❌ Failed to read {fpath}: {e}")

    filename_keywords = re.findall(r'[\w\-]+\.c(?:pp)?|[\w\-]+\.h(?:pp)?', query, re.IGNORECASE)
    matched_chunks = [
        c for c in all_chunks
        if any(fname.lower() in os.path.basename(c.get("file", "")).lower() for fname in filename_keywords)
    ]

    debug_chunks = get_debug_chunks(matched_chunks if matched_chunks else all_chunks, query)
    struct_chunks = get_struct_related_chunks(matched_chunks if matched_chunks else all_chunks, query)

    final = debug_chunks + struct_chunks + matched_chunks if matched_chunks else debug_chunks + struct_chunks + all_chunks
    return final[:k]

def get_top_chunks(query: str, k: int = 3):
    if not query.strip():
        raise ValueError("❌ Query cannot be empty.")

    preprocessed_query = preprocess_query(query)
    filename_keywords = re.findall(r'[\w\-]+\.c(?:pp)?|[\w\-]+\.h(?:pp)?', query, re.IGNORECASE)

    for fname in filename_keywords:
        fname_base = os.path.basename(fname)
        exact_path = os.path.join(CHUNKS_UPLOADED_DIR, f"{fname_base}.json")
        alt_path = os.path.join(CHUNKS_UPLOADED_DIR, f"{os.path.splitext(fname_base)[0]}.json")

        path = exact_path if os.path.exists(exact_path) else alt_path
        if os.path.exists(path):
            print(f"📦 Using uploaded chunks: {path}")
            try:
                file_chunks = load_chunks(path)
                debug_chunks = get_debug_chunks(file_chunks, query)
                struct_chunks = get_struct_related_chunks(file_chunks, query)
                return (debug_chunks + struct_chunks + file_chunks)[:k]
            except Exception as e:
                print(f"❌ Failed to load {path}: {e}")

    if os.environ.get("FILES_TO_EMBED"):
        uploaded_files = [f.strip() for f in os.environ["FILES_TO_EMBED"].split(",")]
        print(f"📂 FILES_TO_EMBED detected: {uploaded_files}")
        all_uploaded_chunks = []
        for fname in uploaded_files:
            path = os.path.join(CHUNKS_UPLOADED_DIR, f"{fname}.json")
            if os.path.exists(path):
                chunks = load_chunks(path)
                all_uploaded_chunks.extend(chunks)
        if all_uploaded_chunks:
            print(f"🔍 {len(all_uploaded_chunks)} chunks loaded from uploaded files.")
            if is_vector_store_ready():
                try:
                    embed_fn = LocalCodeBERTEmbeddingFunction(LOCAL_MODEL_PATH)
                    client = chromadb.PersistentClient(path=DB_DIR)
                    collection = client.get_collection(name=COLLECTION_NAME)
                    results = collection.query(query_texts=[preprocessed_query], n_results=k)
                    vector_chunks = []
                    for i in range(len(results["ids"][0])):
                        meta = results["metadatas"][0][i]
                        doc = results["documents"][0][i]
                        vector_chunks.append({
                            "file": meta.get("file", "Unknown"),
                            "start_line": meta.get("start_line", -1),
                            "end_line": meta.get("end_line", -1),
                            "code": doc
                        })
                        print(f"📦 Vector match: {meta['file']} ({meta['start_line']}–{meta['end_line']})")
                    debug_chunks = get_debug_chunks(vector_chunks, query)
                    struct_chunks = get_struct_related_chunks(vector_chunks, query)
                    return (debug_chunks + struct_chunks + vector_chunks)[:k]
                except Exception as ve:
                    print(f"❌ Vector fallback failed: {ve}")
            else:
                print("⚠️ Vector DB not ready.")

    print("🪫 Falling back to global chunks.json")
    try:
        raw_chunks = load_chunks(CHUNKS_FILE)
        keywords = [w.strip("():.,") for w in query.split() if len(w) > 2 and w.isidentifier()]
        print(f"🔎 Matching keywords: {keywords}")
        required_score = 2 if len(keywords) > 4 else 1

        keyword_hits = []
        for chunk in raw_chunks:
            score = sum(1 for kw in keywords if kw.lower() in chunk.get("code", "").lower())
            if score >= required_score:
                keyword_hits.append((score, chunk))

        keyword_hits.sort(key=lambda x: -x[0])
        best = [c for _, c in keyword_hits][:k] if keyword_hits else raw_chunks[:k]
        debug_chunks = get_debug_chunks(best + raw_chunks, query)
        struct_chunks = get_struct_related_chunks(best + raw_chunks, query)
        return (debug_chunks + struct_chunks + best)[:k]
    except Exception as e:
        print(f"❌ Fallback retrieval error: {e}")
        return []

# CLI Debug
if __name__ == "__main__":
    q = "How does the code allow differentiating between GPA and rank for a Person in the complex_code.c?"
    results = get_top_chunks(q, k=5)

    print("\n🧠 Final Retrieved Chunks:")
    for i, chunk in enumerate(results, 1):
        print(f"\n#{i} — {chunk.get('file', 'Unknown')} ({chunk.get('start_line', '?')}–{chunk.get('end_line', '?')}):\n{chunk.get('code', '')[:300]}...")
