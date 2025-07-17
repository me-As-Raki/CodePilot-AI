from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import subprocess
import shutil
import os
import json

# ... [imports unchanged] ...
from backend.generator import generate_answer

app = FastAPI(
    title="RAG Code Assistant API",
    description="Ask questions about your C/C++ codebase using RAG (Retrieval-Augmented Generation).",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 7

@app.post("/ask")
async def ask_code_assistant(request: QueryRequest):
    try:
        print(f"📥 /ask - Received query: {request.query}")
        result = generate_answer(request.query, top_k=request.top_k)
        print("✅ /ask - Answer successfully generated.")
        return result
    except Exception as e:
        print(f"❌ /ask - Error: {e}")
        return {"error": f"❌ Failed to generate answer: {str(e)}"}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    print("📤 /upload - Upload endpoint hit.")
    os.makedirs("data/codebase", exist_ok=True)
    os.makedirs("data/chunks_uploaded", exist_ok=True)
    allowed_exts = {".c", ".cpp", ".h", ".hpp"}
    saved_files = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_exts:
            print(f"🚫 /upload - Rejected: {file.filename}")
            return {"error": f"🚫 Invalid file extension: {file.filename}"}

        file_path = os.path.join("data/codebase", file.filename)
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            saved_files.append(file.filename)
            print(f"✅ /upload - Saved: {file.filename}")
        except Exception as e:
            print(f"❌ /upload - Failed to save {file.filename}: {e}")
            return {"error": f"❌ Failed to save file {file.filename}: {e}"}

    try:
        print("🧠 /upload - Running parser_treesitter.py...")
        subprocess.run(["python", "backend/parser_treesitter.py"], check=True)

        print("🔍 /upload - Running heuristic-enhancer.py...")
        subprocess.run(["python", "backend/heuristic_enhancer.py"], check=True)

        print("🔍 /upload - Running parser.py...")
        subprocess.run(["python", "backend/parser.py"], check=True)

        print("📦 /upload - Running parser_cli.py...")
        subprocess.run(["python", "backend/parser_cli.py"], check=True)

        with open("data/chunks.json", "r", encoding="utf-8") as f:
            all_chunks = json.load(f)

        uploaded_set = set(saved_files)
        uploaded_chunks = [c for c in all_chunks if os.path.basename(c.get("file", "")) in uploaded_set]

        for filename in uploaded_set:
            name = os.path.splitext(filename)[0]
            chunks_for_file = [c for c in uploaded_chunks if os.path.basename(c["file"]) == filename]
            path = os.path.join("data/chunks_uploaded", f"{filename}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(chunks_for_file, f, indent=2)
            print(f"💾 /upload - Saved: chunks_uploaded/{filename}.json with {len(chunks_for_file)} chunks.")

        file_log_path = "data/last_uploaded_files.json"
        with open(file_log_path, "w", encoding="utf-8") as f:
            json.dump(saved_files, f)
        print(f"📚 /upload - Logged uploaded filenames: {saved_files}")

        print(f"🧬 /upload - Embedding new chunks from: {saved_files}")
        subprocess.run(
            ["python", "backend/embedder.py"],
            check=True,
            env={**os.environ, "FILES_TO_EMBED": ",".join(saved_files)}
        )

        print("✅ /upload - All steps completed.")
        return {"status": "success", "files_saved": saved_files}

    except subprocess.CalledProcessError as e:
        print(f"❌ /upload - Subprocess failed: {e}")
        return {"error": f"❌ Subprocess failed: {e}"}
    except Exception as e:
        print(f"❌ /upload - Unexpected error: {e}")
        return {"error": f"❌ Unexpected error during processing: {e}"}

@app.get("/")
async def health_check():
    print("✅ / - Health check passed.")
    return {"message": "✅ RAG Code Assistant API is up and running."}

if __name__ == "__main__":
    print("🚀 Starting RAG Code Assistant API...")
    print("📡 Swagger UI: http://127.0.0.1:9000/docs")
    print("💬 Endpoints: /ask and /upload")
    import uvicorn
    uvicorn.run("backend.api:app", host="127.0.0.1", port=9000, reload=True)
