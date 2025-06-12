import os

TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), "translations")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "documentation")

def load_ralph_details() -> str:
    """
    Loads and concatenates markdown files in the documentation directory
    in a specific order, followed by any remaining markdown files.
    """
    if not os.path.exists(DOCS_DIR):
        return "Ralph language details not found. Please ensure documentation directory exists."
    
    markdown_content = []
    
    # Define priority order for documentation files
    priority_files = [
        "types.md", 
        "operators.md", 
        "functions.md", 
        "contracts.md", 
        "built-in-functions.md"
    ]
    
    try:
        # First add priority files in specified order
        for filename in priority_files:
            file_path = os.path.join(DOCS_DIR, filename)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    markdown_content.append(f"--- {filename} ---\n{content}")
            else:
                print(f"Warning: {filename} not found in documentation directory.")
        
        # Then add any remaining markdown files
        for filename in sorted(os.listdir(DOCS_DIR)):
            if filename.endswith('.md') and filename not in priority_files:
                file_path = os.path.join(DOCS_DIR, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    markdown_content.append(f"--- {filename} ---\n{content}")
        
        if not markdown_content:
            return "No markdown files found in documentation directory."
            
        return "\n\n".join(markdown_content)
    except Exception as e:
        print(f"Error loading documentation: {e}")
        raise RuntimeError("Failed to load Ralph details") from e

def load_example_translations() -> str:
    """     
    Loads example translations from the translations directory.
    Files are expected to be named in1.sol, out1.sol, in2.sol, out2.sol, etc.
    Returns a concatenated string of all examples with clear separators.
    """
    concat_parts = []
    
    if not os.path.exists(TRANSLATIONS_DIR):
        print(f"Translations directory not found: {TRANSLATIONS_DIR}")
        return ""
    
    i = 1
    while True:
        in_path = os.path.join(TRANSLATIONS_DIR, f"in{i}.sol")
        out_path = os.path.join(TRANSLATIONS_DIR, f"out{i}.ral")
        
        if not (os.path.exists(in_path) and os.path.exists(out_path)):
            break
            
        try:
            with open(in_path, "r", encoding="utf-8") as f_in, open(out_path, "r", encoding="utf-8") as f_out:
                input_content = f_in.read()
                output_content = f_out.read()
                
                # Add to concat parts with clear separators
                concat_parts.append(f"--- Example {i} Input (in{i}.sol) ---\n{input_content}")
                concat_parts.append(f"--- Example {i} Output (out{i}.ral) ---\n{output_content}")
            
            i += 1
        except Exception as e:
            print(f"Error loading example translation pair {i}: {e}")
            raise RuntimeError("Failed to load example translations") from e
    
    if not concat_parts:
        return "No example translations found."
        
    return "\n\n".join(concat_parts)

RALPH_DETAILS = load_ralph_details()
EXAMPLE_TRANSLATIONS = load_example_translations()

print(RALPH_DETAILS)
print(EXAMPLE_TRANSLATIONS)
