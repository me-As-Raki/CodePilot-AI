import os
import sys
import json
import re
import traceback
from dotenv import load_dotenv
import google.generativeai as genai
import cohere
from backend.retriever import get_top_chunks, get_chunks_from_uploaded_files

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
cohere_api_key = os.getenv("COHERE_API_KEY")

CHUNKS_UPLOADED_DIR = "data/chunks_uploaded"

def extract_valid_keyword(query):
    tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", query)
    ignore = {"how", "what", "does", "is", "in", "on", "at", "it", "to", "for", "a", "the", "do", "by", "of", "and", "can", "i"}
    keywords = [t for t in tokens if t.lower() not in ignore and len(t) > 2]
    return keywords[0] if keywords else None

def keyword_in_chunks(keyword, chunks):
    keyword = keyword.lower()
    for chunk in chunks:
        if keyword in chunk['code'].lower():
            return True
    return False

def detect_question_category(query: str) -> str:
    q = query.lower()
    if any(word in q for word in ["test", "debug", "print", "log", "display"]):
        return "🧪 Testing / Debugging"
    elif any(word in q for word in ["flow", "process", "when", "what happens", "logic"]):
        return "🧠 Logic + Flow"
    elif any(word in q for word in ["init", "static", "const", "config", "array", "table"]):
        return "🛠 Static Data / Initialization"
    elif any(word in q for word in ["struct", "enum", "typedef", "union"]):
        return "📦 Configuration / State"
    elif any(word in q for word in ["add", "remove", "register", "lookup", "device"]):
        return "🧑‍🔧 Device Operations"
    return "🧱 General Structure"

def load_chunks_from_filename(filename):
    name = os.path.splitext(os.path.basename(filename))[0]
    json_path = os.path.join(CHUNKS_UPLOADED_DIR, f"{name}.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def build_prompt(user_query, code_chunks, keyword_hint=None, keyword_missing=False, category=None, fallback_reasoning=False):
    system_prompt = (
        "You are a knowledgeable assistant specialized in C/C++ codebases.\n"
        "You are given a user question and several real code snippets extracted from C/C++ files.\n"
        "Your job is to:\n"
        "- Understand the user's question.\n"
        "- Use ONLY the code context to answer it (don't guess).\n"
        "- Provide a clear, technically correct explanation.\n"
        "- If the answer is not in the code, say so politely.\n"
    )

    if fallback_reasoning:
        system_prompt += (
            "- If no direct keyword match is found, analyze the full file structure and code blocks.\n"
            "- Try to infer intent by examining structs, enums, typedefs, unions, and variable roles.\n"
        )

    context_blocks = ""
    for chunk in code_chunks:
        context_blocks += f"📄 File: {chunk.get('file', 'Unknown')} | Lines: {chunk.get('start_line', '?')}-{chunk.get('end_line', '?')}\n"
        context_blocks += "```c\n" + chunk['code'].strip() + "\n```\n\n"

    final_prompt = (
        system_prompt +
        f"\n🗂 Category: {category or 'Uncategorized'}\n\n" +
        "===== CODE CONTEXT START =====\n\n" +
        context_blocks +
        "===== CODE CONTEXT END =====\n\n" +
        f"💬 User's Question: {user_query}\n\n"
        "🧠 Your Answer:"
    )

    if keyword_missing and keyword_hint and not code_chunks:
        final_prompt += (
            f"\n\n⚠️ Note: The keyword or macro `{keyword_hint}` was not found in the retrieved code chunks. "
            f"Please double-check your query or spelling."
        )

    return final_prompt

def generate_with_cohere(prompt):
    try:
        print("🔁 Switching to Cohere...")
        co = cohere.Client(cohere_api_key)
        response = co.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=1024,
            temperature=0.3
        )
        print("✅ Cohere successfully responded.")
        return response.generations[0].text.strip()
    except Exception as e:
        print(f"🔥 Cohere generation failed: {type(e).__name__}: {e}")
        raise

def generate_answer(user_query, top_k=10):
    chunks = []
    keyword_hint = None
    keyword_missing = False
    prompt = ""

    try:
        print(f"\n🔍 Query: {user_query}")

        # Step 1: Retrieve chunks
        if os.environ.get("FILES_TO_EMBED"):
            print("📂 Using uploaded file chunks from: chunks_uploaded/")
            chunks = get_chunks_from_uploaded_files(user_query, k=top_k)
        else:
            print("🔎 Using global chunks from chunks.json or vector DB")
            chunks = get_top_chunks(user_query, k=top_k)

        print(f"📊 Retrieved {len(chunks)} chunks.")

        # Step 2: Detect category
        category = detect_question_category(user_query)
        print(f"🧩 Detected question category: {category}")

        # Step 3: Inject debug chunks if needed
        if "debug" in user_query.lower() or "print" in user_query.lower() or "test" in user_query.lower():
            print("🔍 Forcing debug-related chunks (printf, print_)...")
            debug_chunks = [
                c for c in chunks
                if "printf(" in c['code'] or re.search(r'\bprint_\w+\s*\(', c['code'])
            ]
            if debug_chunks:
                print(f"✅ Found {len(debug_chunks)} debug-related chunks.")
                debug_hashes = set(hash(c['code']) for c in debug_chunks)
                chunks += [c for c in debug_chunks if hash(c['code']) not in debug_hashes]
            else:
                print("⚠️ No printf or print_* found in top chunks.")

        # Step 4: Keyword extraction
        keyword_hint = extract_valid_keyword(user_query)
        keyword_missing = keyword_hint and not keyword_in_chunks(keyword_hint, chunks)
        if keyword_missing:
            print(f"⚠️ Keyword '{keyword_hint}' not found in retrieved chunks.")

        # Step 5: Fallback if only file is mentioned
        filename_match = re.findall(r"[\w\-]+\.(?:c|cpp|h|hpp)", user_query, re.IGNORECASE)
        fallback_chunks = []
        if not chunks and filename_match:
            print(f"🔄 No chunks matched. Trying full-file fallback for {filename_match[0]}...")
            fallback_chunks = load_chunks_from_filename(filename_match[0])
            if fallback_chunks:
                print(f"🧠 Loaded {len(fallback_chunks)} fallback chunks from full file.")
                chunks = fallback_chunks

        fallback_reasoning = keyword_missing or (not chunks and bool(filename_match))

        # Step 6: Build prompt
        prompt = build_prompt(user_query, chunks, keyword_hint, keyword_missing, category, fallback_reasoning)

        # Step 7: Generate with Gemini
        print("⚡ Requesting Gemini API (gemini-1.5-flash)...")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        print("✅ Gemini successfully responded.")
        final_answer = response.text.strip()

        if keyword_missing and keyword_hint and not chunks:
            final_answer += (
                f"\n\n⚠️ Note: The keyword or macro `{keyword_hint}` was not found in the retrieved code chunks. "
                f"Please double-check your query or spelling."
            )

        return {
            "answer": final_answer,
            "chunks_used": chunks,
            "query": user_query,
            "provider": "Gemini"
        }

    except Exception as gemini_error:
        print(f"❌ Gemini failed: {type(gemini_error).__name__}: {gemini_error}")
        traceback.print_exc()

        try:
            answer = generate_with_cohere(prompt)
            if keyword_missing and keyword_hint and not chunks:
                answer += (
                    f"\n\n⚠️ Note: The keyword or macro `{keyword_hint}` was not found in the retrieved code chunks. "
                    f"Please double-check your query or spelling."
                )

            return {
                "answer": answer,
                "chunks_used": chunks,
                "query": user_query,
                "provider": "Cohere"
            }

        except Exception as cohere_error:
            print(f"🔥 Cohere also failed: {type(cohere_error).__name__}: {cohere_error}")
            traceback.print_exc()
            return {
                "error": str(cohere_error),
                "answer": "❌ Both Gemini and Cohere failed to generate a response.",
                "chunks_used": chunks,
                "query": user_query,
                "provider": "None"
            }

# === CLI Test ===
if __name__ == "__main__":
    query = "How does the code allow differentiating between GPA and rank for a Person in the complex_code.c?"
    result = generate_answer(query)

    print("\n🔍 User Query:", result.get('query'))
    print("🧠 Provider Used:", result.get('provider'))
    print("\n📥 Final Answer:\n", result.get('answer'))

    print("\n📦 Code Chunks Used:")
    for chunk in result.get('chunks_used', []):
        print(f"- {chunk['file']} (lines {chunk['start_line']}–{chunk['end_line']})")
        if "printf(" in chunk['code'] or "print_" in chunk['code']:
            print("  📌 Includes debug/print statement.")
