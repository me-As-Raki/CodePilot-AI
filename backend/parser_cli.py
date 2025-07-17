import os
import json
import subprocess
from datetime import datetime
import re

CODEBASE_DIR = "data/codebase"
CHUNKS_PATH = "data/chunks.json"
QUERY_FILE = "backend/full_chunks.scm"  # Tree-sitter query file

def get_c_cpp_files(root):
    extensions = (".c", ".cpp", ".h", ".hpp")
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.lower().endswith(extensions):
                yield os.path.join(dirpath, filename)

def read_source_lines(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()

def extract_chunks_with_tree_sitter(file_path):
    try:
        result = subprocess.run(
            ["tree-sitter", "query", QUERY_FILE, file_path],
            capture_output=True, text=True, check=True
        )
        output = result.stdout.strip().splitlines()
        lines = read_source_lines(file_path)

        chunks = []
        for line in output:
            line = line.strip()
            if "text:" in line and "start:" in line and "end:" in line:
                kind = None
                for k in ["function", "struct", "typedef", "macro", "global", "enum", "class", "prototype", "preproc"]:
                    if f"{k}.name" in line:
                        kind = k
                        break
                if not kind:
                    continue

                name = line.split("text:")[-1].strip().strip("`")
                start_match = re.search(r"start:\s*\((\d+),", line)
                end_match = re.search(r"end:\s*\((\d+),", line)

                if not (start_match and end_match):
                    continue

                start_line = int(start_match.group(1))
                end_line = int(end_match.group(1))
                code_lines = lines[start_line:end_line + 1]

                chunks.append({
                    "file": file_path.replace("\\", "/"),
                    "name": name,
                    "type": kind,
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": "".join(code_lines).strip()
                })

        return chunks

    except subprocess.CalledProcessError as e:
        print(f"❌ Error parsing {file_path}:\n{e.stderr.strip()}")
        return []

def main():
    start_time = datetime.now()
    all_chunks = []
    files = list(get_c_cpp_files(CODEBASE_DIR))

    print(f"\n🚀 Extracting ALL code constructs from {len(files)} files...\n")

    for idx, file in enumerate(files, 1):
        rel_path = os.path.relpath(file, CODEBASE_DIR)
        print(f"[{idx}/{len(files)}] 📄 {rel_path}")
        chunks = extract_chunks_with_tree_sitter(file)
        print(f"    └─ 🧩 {len(chunks)} chunks found")
        all_chunks.extend(chunks)

    if all_chunks:
        with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, indent=2)
        print(f"\n📥 Saved {len(all_chunks)} chunks to {CHUNKS_PATH}")
    else:
        print("\n⚠️ No chunks extracted. Check .scm query and codebase.")

    end_time = datetime.now()
    print("\n✅ Done!")
    print(f"📦 Files parsed    : {len(files)}")
    print(f"🧩 Total chunks    : {len(all_chunks)}")
    print(f"⏱️  Time taken     : {end_time - start_time}")

if __name__ == "__main__":
    main()
