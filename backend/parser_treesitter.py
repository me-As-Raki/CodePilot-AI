# backend/parser_treesitter.py

import os
import json
from tree_sitter import Language, Parser
from datetime import datetime
import sys

# ===== Paths =====
BUILD_DIR = 'backend/build'
BUILD_PATH = os.path.join(BUILD_DIR, 'my-languages.so')
CHUNKS_FILE = 'data/chunks.json'
CHUNKS_UPLOADED_DIR = 'data/chunks_uploaded'
CODEBASE_DIR = 'data/codebase'

# ===== Get Specific Files to Parse if Passed via ENV (e.g., during upload) =====
FILES_TO_PARSE = os.environ.get("FILES_TO_EMBED")
if FILES_TO_PARSE:
    FILES_TO_PARSE = set(FILES_TO_PARSE.split(","))
    print(f"🗂️ Selective parse mode: {FILES_TO_PARSE}")

# ===== Build Tree-sitter language library if missing =====
if not os.path.exists(BUILD_PATH):
    print("🔨 Building Tree-sitter language library...")
    os.makedirs(BUILD_DIR, exist_ok=True)
    Language.build_library(
        BUILD_PATH,
        ['backend/tree-sitter-c', 'backend/tree-sitter-cpp']
    )
else:
    print("✅ Tree-sitter library already built.")

# ===== Load Tree-sitter languages =====
C_LANG = Language(BUILD_PATH, 'c')
CPP_LANG = Language(BUILD_PATH, 'cpp')

def get_language_for_file(filename):
    return CPP_LANG if filename.endswith(('.cpp', '.hpp')) else C_LANG

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def get_node_text(source_code, node):
    return source_code[node.start_byte:node.end_byte]

def walk_and_extract(source_code, root):
    chunks = []

    def walk(node):
        ntype = node.type
        text = get_node_text(source_code, node)
        sl, el = node.start_point[0] + 1, node.end_point[0] + 1

        if ntype == "function_definition":
            chunks.append({"type": "function", "start_line": sl, "end_line": el, "code": text})
        elif ntype == "declaration":
            if "=" in text and ";" in text:
                chunks.append({"type": "global_variable", "start_line": sl, "end_line": el, "code": text})
        elif ntype == "preproc_def":
            chunks.append({"type": "macro", "start_line": sl, "end_line": el, "code": text})
        elif ntype == "preproc_function_def":
            chunks.append({"type": "macro_function", "start_line": sl, "end_line": el, "code": text})
        elif ntype == "preproc_include":
            chunks.append({"type": "include", "start_line": sl, "end_line": el, "code": text})
        elif ntype in ("preproc_if", "preproc_ifdef", "preproc_ifndef"):
            chunks.append({"type": "preprocessor", "start_line": sl, "end_line": el, "code": text})
        elif ntype == "struct_specifier":
            chunks.append({"type": "struct", "start_line": sl, "end_line": el, "code": text})
        elif ntype == "enum_specifier":
            chunks.append({"type": "enum", "start_line": sl, "end_line": el, "code": text})
        elif ntype == "type_definition":
            chunks.append({"type": "typedef", "start_line": sl, "end_line": el, "code": text})
        elif ntype == "function_declarator" and text.endswith(";"):
            chunks.append({"type": "function_prototype", "start_line": sl, "end_line": el, "code": text})

        # Extra chunk logic
        if "=" in text and ("->" in text or "." in text) and ";" in text:
            chunks.append({"type": "struct_assignment", "start_line": sl, "end_line": el, "code": text})
        if "=" in text and "(" in text and "->" in text:
            chunks.append({"type": "function_assignment", "start_line": sl, "end_line": el, "code": text})
        if "{" in text and "}" in text and "," in text and "\"" in text and "=" not in text:
            chunks.append({"type": "anonymous_initializer_block", "start_line": sl, "end_line": el, "code": text})
        if "static" in text and "const" in text and "char" in text and "*" in text and "{" in text:
            chunks.append({"type": "static_const_char_pointer_array", "start_line": sl, "end_line": el, "code": text})

        for child in node.children:
            walk(child)

    walk(root)
    return chunks

def parse_codebase(codebase_dir, selective_files=None):
    all_chunks = []
    file_stats = []
    total_files = 0

    os.makedirs(CHUNKS_UPLOADED_DIR, exist_ok=True)

    for root, _, files in os.walk(codebase_dir):
        for filename in files:
            if filename.endswith(('.c', '.cpp', '.h', '.hpp')):
                if selective_files and filename not in selective_files:
                    continue

                filepath = os.path.join(root, filename)
                relpath = os.path.relpath(filepath).replace("\\", "/")
                total_files += 1

                try:
                    lang = get_language_for_file(filename)
                    parser = Parser()
                    parser.set_language(lang)

                    source_code = read_file(filepath)
                    tree = parser.parse(bytes(source_code, "utf8"))

                    chunks = walk_and_extract(source_code, tree.root_node)

                    for chunk in chunks:
                        chunk["file"] = relpath
                        all_chunks.append(chunk)

                    print(f"📄 {relpath} — 🧩 {len(chunks)} chunks")
                    file_stats.append((relpath, len(chunks)))

                    # 🔄 Save individual file chunks to JSON
                    per_file_json = os.path.join(CHUNKS_UPLOADED_DIR, f"{filename}.json")
                    with open(per_file_json, 'w', encoding='utf-8') as f:
                        json.dump(chunks, f, indent=2)

                except Exception as e:
                    print(f"❌ Error parsing {relpath}: {e}")

    return all_chunks, file_stats, total_files

# ===== Main Entrypoint =====
if __name__ == "__main__":
    print("🚀 Tree-sitter Parsing Codebase...\n")
    start = datetime.now()

    os.makedirs("data", exist_ok=True)
    if not FILES_TO_PARSE and os.path.exists(CHUNKS_FILE):
        os.remove(CHUNKS_FILE)
        print("🧹 Removed old chunks.json")

    chunks, stats, total = parse_codebase(CODEBASE_DIR, selective_files=FILES_TO_PARSE)

    # Save combined chunks if not selective
    if not FILES_TO_PARSE:
        with open(CHUNKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2)

    duration = datetime.now() - start

    print("\n📊 Parsing Summary:")
    print(f"📁 Files Parsed       : {total}")
    print(f"🧠 Total Chunks Found : {len(chunks)}")
    print(f"⏱️  Time Taken         : {duration}")
    if not FILES_TO_PARSE:
        print(f"💾 Output written to  : {CHUNKS_FILE}")
    print(f"📂 Per-file chunks in : {CHUNKS_UPLOADED_DIR}")
