import os
import re
import json
import hashlib

CHUNKS_FILE = 'data/chunks.json'
CODEBASE_DIR = 'data/codebase'

# ==== Load existing chunks ====
with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
    chunks = json.load(f)

# ==== Avoid duplication using hashes ====
existing_hashes = set(hashlib.md5(chunk["code"].encode()).hexdigest() for chunk in chunks)

# ==== Regex Heuristic Patterns ====
patterns = [
    # Macros (single & multi-line)
    (re.compile(r'^#define\s+[^\n\\]*(?:\\\n[^\n]*)*', re.MULTILINE), "macro"),

    # Static const arrays
    (re.compile(r'static\s+const\s+[\w\s\*]+\[\]\s*=\s*\{[\s\S]*?\};', re.MULTILINE), "static_const_array"),

    # Anonymous initializer blocks (typical driver entries)
    (re.compile(r'\{\s*"[^"]*"\s*,\s*"[^"]*"\s*,[\s\S]*?NULL\s*\}', re.MULTILINE), "anonymous_initializer"),

    # Docstring-style comment followed by function
    (re.compile(r'/\*\*[\s\S]*?\*/\s*(?:[a-z_][\w\s\*]+)?\s*\w+\s*\([^;]*?\)\s*\{', re.MULTILINE), "docstring_function"),

    # Typedef struct {...} name;
    (re.compile(r'typedef\s+struct\s*\{[\s\S]*?\}\s*\w+\s*;', re.MULTILINE), "typedef_struct"),

    # Typedef enum {...} name;
    (re.compile(r'typedef\s+enum\s*\{[\s\S]*?\}\s*\w+\s*;', re.MULTILINE), "typedef_enum"),

    # Global assignments (very basic)
    (re.compile(r'^[a-zA-Z_][\w\s\*\[\]]*\s*=\s*[^;\n]+;', re.MULTILINE), "global_assignment"),

    # Global static tables
    (re.compile(r'(const|static)\s+[\w\s\*]+\[\]\s*=\s*\{[\s\S]*?\};', re.MULTILINE), "global_array_table"),
]


def extract_chunks_from_file(filepath, relpath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        source = f.read()

    new_chunks = []
    for pattern, chunk_type in patterns:
        for match in pattern.finditer(source):
            code = match.group(0).strip()
            code_hash = hashlib.md5(code.encode()).hexdigest()
            if code_hash not in existing_hashes:
                start_line = source[:match.start()].count('\n') + 1
                end_line = source[:match.end()].count('\n') + 1
                new_chunks.append({
                    "type": chunk_type,
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": code,
                    "file": relpath,
                    "source": "heuristic"
                })
                existing_hashes.add(code_hash)
    return new_chunks

# ==== Walk codebase and enhance ====
total_new = 0
for root, _, files in os.walk(CODEBASE_DIR):
    for file in files:
        if file.endswith(('.c', '.cpp', '.h', '.hpp')):
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath).replace("\\", "/")
            found_chunks = extract_chunks_from_file(filepath, relpath)
            if found_chunks:
                print(f"🔍 {relpath} — ➕ {len(found_chunks)} heuristic chunks")
                chunks.extend(found_chunks)
                total_new += len(found_chunks)

# ==== Save updated chunks ====
with open(CHUNKS_FILE, 'w', encoding='utf-8') as f:
    json.dump(chunks, f, indent=2)

print(f"\n✅ Heuristic pass complete! ➕ Added {total_new} new chunks.")
print(f"💾 Updated chunks.json written.")
