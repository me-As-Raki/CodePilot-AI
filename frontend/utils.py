import re

def extract_functions_from_chunks(chunks):
    """
    Extract unique function names from code chunks.
    Supports static/inline, multi-line, complex return types (e.g., pointers).
    Skips control flow blocks like if/for/switch/while.
    """

    function_names = set()

    # Improved regex for multi-line function declarations with optional qualifiers
    func_pattern = re.compile(
        r'''
        (?:^|\n)                                  # Start of line
        (?:static\s+|inline\s+|extern\s+)?        # Optional qualifiers
        (?:[\w\*\s]+?)                            # Return type
        \b([a-zA-Z_][a-zA-Z0-9_]*)\s*             # Function name (capture group)
        \([^)]*\)                                 # Parameters (non-greedy match)
        \s*\{                                     # Opening brace
        ''', re.VERBOSE
    )

    control_keywords = {"if", "for", "while", "switch", "catch"}

    for chunk in chunks:
        code = chunk.get("code", "")
        matches = func_pattern.findall(code)
        for fn in matches:
            if fn not in control_keywords:
                function_names.add(fn)

    return sorted(function_names)
