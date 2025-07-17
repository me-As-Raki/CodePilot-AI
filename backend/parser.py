# backend/parser.py

import os
import re
import json
from hashlib import md5

def is_comment(line):
    stripped = line.strip()
    return stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*")

def is_blank(line):
    return line.strip() == ""

def get_chunk_hash(chunk):
    return md5((chunk['file'] + chunk['type'] + chunk['code']).encode('utf-8')).hexdigest()

def append_unique_chunk(chunk, chunks, seen):
    if chunk["code"].strip() == "":
        return
    hash_key = get_chunk_hash(chunk)
    if hash_key not in seen:
        chunks.append(chunk)
        seen.add(hash_key)

def extract_chunks_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    chunks = []
    seen = set()
    comment_buffer = []
    code_buffer = []

    collecting_macro = False
    collecting_struct = False
    collecting_class = False
    collecting_function_signature = False
    inside_function = False
    collecting_preproc = False

    preproc_buffer = []
    brace_balance = 0
    start_line = 0
    inside_tspl_init = False
    tspl_assignments = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if is_comment(line):
            comment_buffer.append(stripped)
            i += 1
            continue
        if is_blank(line):
            i += 1
            continue

        

        # Macros
        if stripped.startswith("#define") or collecting_macro:
            code_buffer.append(line)
            if stripped.endswith("\\"):
                collecting_macro = True
                i += 1
                continue
            else:
                collecting_macro = False
                chunk = {
                    "file": file_path,
                    "type": "macro",
                    "start_line": i - len(code_buffer) + 2,
                    "end_line": i + 1,
                    "comments": "\n".join(comment_buffer),
                    "code": "".join(code_buffer)
                }
                append_unique_chunk(chunk, chunks, seen)
                comment_buffer = []
                code_buffer = []
                i += 1
                continue

        # Preprocessor block
        if re.match(r'^\s*#(if|ifdef|ifndef)\b', stripped):
            collecting_preproc = True
            preproc_buffer = [line]
            start_line = i + 1
            i += 1
            continue
        if collecting_preproc:
            preproc_buffer.append(line)
            if re.match(r'^\s*#endif\b', stripped):
                collecting_preproc = False
                chunk = {
                    "file": file_path,
                    "type": "preprocessor_block",
                    "start_line": start_line,
                    "end_line": i + 1,
                    "comments": "\n".join(comment_buffer),
                    "code": "".join(preproc_buffer)
                }
                append_unique_chunk(chunk, chunks, seen)
                preproc_buffer = []
                comment_buffer = []
            i += 1
            continue

        # Static const pointer array
        if re.match(r'^\s*static\s+const\s+char\s*(\*\s*const|\*\s*)?\s*\w+\s*\[\s*\]\s*=\s*{', stripped):
            code_buffer = [line]
            start_line = i + 1
            brace_balance = line.count("{") - line.count("}")
            i += 1
            while i < len(lines) and brace_balance > 0:
                line = lines[i]
                brace_balance += line.count("{") - line.count("}")
                code_buffer.append(line)
                i += 1
            chunk = {
                "file": file_path,
                "type": "static_const_char_pointer_array",
                "start_line": start_line,
                "end_line": i,
                "comments": "\n".join(comment_buffer),
                "code": "".join(code_buffer)
            }
            append_unique_chunk(chunk, chunks, seen)
            comment_buffer = []
            code_buffer = []
            continue

        # Static const array block (driver table etc.)
        if re.match(r'^\s*static\s+const\s+\w+\s+\w+\s*\[\s*\]\s*=\s*{', stripped):
            code_buffer = [line]
            start_line = i + 1
            brace_balance = line.count("{") - line.count("}")
            i += 1
            while i < len(lines) and brace_balance > 0:
                line = lines[i]
                brace_balance += line.count("{") - line.count("}")
                code_buffer.append(line)
                i += 1
            chunk = {
                "file": file_path,
                "type": "driver_table_block",
                "start_line": start_line,
                "end_line": i,
                "comments": "\n".join(comment_buffer),
                "code": "".join(code_buffer)
            }
            append_unique_chunk(chunk, chunks, seen)
            comment_buffer = []
            code_buffer = []
            continue

        # Typedef struct
        if re.match(r'^\s*typedef\s+struct\b', stripped):
            collecting_struct = True
            code_buffer = [line]
            start_line = i + 1
            brace_balance = line.count("{") - line.count("}")
            i += 1
            continue
        if collecting_struct:
            code_buffer.append(line)
            brace_balance += line.count("{") - line.count("}")
            if brace_balance == 0 and re.search(r'}\s*\w*;', line):
                collecting_struct = False
                chunk = {
                    "file": file_path,
                    "type": "typedef_struct",
                    "start_line": start_line,
                    "end_line": i + 1,
                    "comments": "\n".join(comment_buffer),
                    "code": "".join(code_buffer)
                }
                append_unique_chunk(chunk, chunks, seen)
                code_buffer = []
                comment_buffer = []
            i += 1
            continue

        # Enum
        if stripped.startswith("enum ") or stripped.startswith("typedef enum "):
            code_buffer = [line]
            start_line = i + 1
            i += 1
            brace_balance = line.count("{") - line.count("}")
            while i < len(lines) and brace_balance > 0:
                line = lines[i]
                brace_balance += line.count("{") - line.count("}")
                code_buffer.append(line)
                i += 1
            while i < len(lines) and not lines[i].strip().endswith(";"):
                code_buffer.append(lines[i])
                i += 1
            if i < len(lines):
                code_buffer.append(lines[i])
                i += 1
            chunk = {
                "file": file_path,
                "type": "enum",
                "start_line": start_line,
                "end_line": i,
                "comments": "\n".join(comment_buffer),
                "code": "".join(code_buffer)
            }
            append_unique_chunk(chunk, chunks, seen)
            comment_buffer = []
            code_buffer = []
            continue
# Check for return type on its own line, then function header next line
        if (not inside_function and re.match(r'^\s*(static\s+)?(bool|int|void|char|float|double|[\w_]+)\s*$', stripped)):
            if i + 1 < len(lines) and re.match(r'^\s*\**\w+\s*\([^)]*$', lines[i+1].strip()):
                collecting_function_signature = True
                code_buffer = [line, lines[i+1]]
                start_line = i + 1
                i += 2
                continue

        # Function definition (multi-line header)
        if not inside_function and re.match(r'^\s*(static\s+)?[\w\s\*\&]+\s+\**\w+\s*\([^)]*$', stripped):
            collecting_function_signature = True
            code_buffer = [line]
            start_line = i + 1
            i += 1
            continue
        if collecting_function_signature:
            code_buffer.append(line)
            if "{" in line:
                collecting_function_signature = False
                inside_function = True
                brace_balance = 1
            i += 1
            continue
        if inside_function:
            code_buffer.append(line)
            brace_balance += line.count("{") - line.count("}")
            if re.match(r'^\s*\w+->\w+_cb\s*=\s*\w+;', stripped):
                chunk = {
                    "file": file_path,
                    "type": "function_assignment",
                    "start_line": i + 1,
                    "end_line": i + 1,
                    "comments": "",
                    "code": line
                }
                append_unique_chunk(chunk, chunks, seen)
            if brace_balance == 0:
                inside_function = False
                chunk = {
                    "file": file_path,
                    "type": "function",
                    "start_line": start_line,
                    "end_line": i + 1,
                    "comments": "\n".join(comment_buffer),
                    "code": "".join(code_buffer)
                }
                append_unique_chunk(chunk, chunks, seen)
                code_buffer = []
                comment_buffer = []
            i += 1
            continue

        if re.match(r'^\s*\w+(->|\.)\w+\s*=\s*[^;]+;', stripped):
            chunk = {
                "file": file_path,
                "type": "struct_assignment",
                "start_line": i + 1,
                "end_line": i + 1,
                "comments": "\n".join(comment_buffer),
                "code": line
            }
            append_unique_chunk(chunk, chunks, seen)
            comment_buffer = []
            i += 1
            continue


        # Function prototype
        if re.match(r'^\s*(static\s+)?(bool|void|int|float|char|double|[\w_]+)\s+[\w_]+\s*\([^;]*\)\s*;', stripped):
            chunk = {
                "file": file_path,
                "type": "function_prototype",
                "start_line": i + 1,
                "end_line": i + 1,
                "comments": "\n".join(comment_buffer),
                "code": line
            }
            append_unique_chunk(chunk, chunks, seen)
            comment_buffer = []
            i += 1
            continue

        # Global assignment
        if re.match(r'.+\s*=\s*&?\s*\w+\s*;', stripped):
            chunk = {
                "file": file_path,
                "type": "assignment",
                "start_line": i + 1,
                "end_line": i + 1,
                "comments": "\n".join(comment_buffer),
                "code": line
            }
            append_unique_chunk(chunk, chunks, seen)
            comment_buffer = []
            i += 1
            continue

        elif stripped.startswith("#define"):
            macro_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("#define"):
                macro_lines.append(lines[i])
                i += 1
            chunk = {
                "type": "macro_group",
                "name": macro_lines[0].split()[1],
                "start_line": start_line,
                "end_line": i,
                "code": "\n".join(macro_lines)
            }
            chunks.append(chunk)
            continue

        elif re.match(r'(static\s+)?const\s+char\s*\*\s*const\s+\w+\s*\[\s*\]\s*=\s*\{', stripped):
            array_lines = [line]
            i += 1
            while i < len(lines):
                array_lines.append(lines[i])
                if "};" in lines[i]:
                    break
                i += 1
            chunk = {
                "type": "const_array",
                "name": re.findall(r'(\w+)\s*\[', stripped)[0],
                "start_line": start_line,
                "end_line": i,
                "code": "\n".join(array_lines)
            }
            chunks.append(chunk)
            continue

        elif stripped.endswith(";") and re.match(r'.+\)\s*;', stripped):
            proto_lines = [line]
            # check for #if/#endif before and after
            j = i - 1
            while j >= 0 and lines[j].strip().startswith("#"):
                proto_lines.insert(0, lines[j])
                j -= 1
            k = i + 1
            while k < len(lines) and lines[k].strip().startswith("#"):
                proto_lines.append(lines[k])
                k += 1

            chunk = {
                "type": "function_prototype",
                "name": re.findall(r'\b(\w+)\s*\(', stripped)[-1],
                "start_line": j + 1 if j >= 0 else i + 1,
                "end_line": k if k > i else i,
                "code": "\n".join(proto_lines)
            }
            chunks.append(chunk)
            i = k
            continue

        # Anonymous initializers
        if stripped.startswith('{') and not stripped.endswith('};'):
            code_buffer = [line]
            start_line = i + 1
            i += 1
            while i < len(lines):
                code_buffer.append(lines[i])
                if lines[i].strip().endswith('},'):
                    i += 1
                    break
                i += 1
            chunk = {
                "file": file_path,
                "type": "anonymous_initializer_block",
                "start_line": start_line,
                "end_line": i,
                "comments": "\n".join(comment_buffer),
                "code": "".join(code_buffer)
            }
            append_unique_chunk(chunk, chunks, seen)
            comment_buffer = []
            code_buffer = []
            continue

        # Section-style comment (like '// Local globals...')
        if re.match(r'^\s*//.*\.\.\.\s*$', stripped):
            chunk = {
                "file": file_path,
                "type": "section_comment",
                "start_line": i + 1,
                "end_line": i + 1,
                "comments": "",
                "code": line
            }
            append_unique_chunk(chunk, chunks, seen)
            i += 1
            continue

        # Preprocessor directive (single line)
        if stripped.startswith("#"):
            chunk = {
                "file": file_path,
                "type": "preprocessor_directive",
                "start_line": i + 1,
                "end_line": i + 1,
                "comments": "",
                "code": line
            }
            append_unique_chunk(chunk, chunks, seen)
            i += 1
            continue

        # Driver entry (e.g., { "...", "...", "...", NULL },)
        if re.match(r'^\s*{\s*".+?",\s*".+?".*NULL.*},?\s*$', stripped) or (stripped.startswith('{') and 'NULL' in stripped):
            code_buffer = [line]
            start_line = i + 1
            i += 1
            while i < len(lines):
                code_buffer.append(lines[i])
                if lines[i].strip().endswith('},'):
                    i += 1
                    break
                i += 1
            chunk = {
                "file": file_path,
                "type": "driver_entry",
                "start_line": start_line,
                "end_line": i,
                "comments": "\n".join(comment_buffer),
                "code": "".join(code_buffer)
            }
            append_unique_chunk(chunk, chunks, seen)
            comment_buffer = []
            code_buffer = []
            continue


        i += 1

    return chunks


def parse_codebase(codebase_dir):
    print(f"📂 Starting parse of: {codebase_dir}")
    all_chunks = []
    count = 0
    for root, _, files in os.walk(codebase_dir):
        for file in files:
            if file.endswith(('.c', '.cpp', '.h', '.hpp')):
                full_path = os.path.join(root, file)
                print(f"🔍 Parsing: {full_path}")
                count += 1
                chunks = extract_chunks_from_file(full_path)
                all_chunks.extend(chunks)
    print(f"✅ Parsed {count} files. Extracted {len(all_chunks)} unique chunks.")
    return all_chunks

def save_chunks_to_json(chunks, output_path="data/chunks.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    print(f"💾 Saved to: {output_path}")

if __name__ == "__main__":
    codebase_dir = "data/codebase"
    chunks = parse_codebase(codebase_dir)
    save_chunks_to_json(chunks)
    print("🎉 Done!")
