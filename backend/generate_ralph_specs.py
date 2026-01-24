import os
import re
import json

# Use relative path from this script's location
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(CURRENT_DIR, 'openzeppelin', 'contracts')

def parse_fields(fields_str):
    # Check for comments inside fields block not handled by global strip
    # (Though global strip handles // and /* */)
    
    # Split by comma. Assuming no commas in types for now.
    chunks = [c.strip() for c in fields_str.split(',') if c.strip()]
    
    imm = []
    mut = []
    
    for c in chunks:
        # Example: "mut val: U256" or "val: ByteVec"
        # Removing newlines and multiple spaces
        c = ' '.join(c.split())
        
        # Handle trailing comma or empty
        if not c: continue
        
        is_mut = False
        if c.startswith('mut '):
            is_mut = True
            c = c[4:].strip()
            
        if ':' in c:
            # Handle potential attributes @std etc before name
            # strip anything starting with @ until space
            while c.startswith('@'):
                c = c.split(' ', 1)[1].strip() if ' ' in c else c

            parts = c.split(':')
            f_name = parts[0].strip()
            # Type might have trailing stuff? usually no
            f_type = parts[1].strip()
            
            f_obj = {"name": f_name, "type": f_type}
            if is_mut:
                mut.append(f_obj)
            else:
                imm.append(f_obj)
                
    return imm, mut

def parse_ralph_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove comments
    # Remove // comments
    content = re.sub(r'//.*', '', content)
    # Remove /* */ comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    specs = []
    
    # Regex to find definition Start
    # Matches: "Abstract Contract Name", "Contract Name", "Interface Name", "TxScript Name"
    # Ensure word boundary for keywords
    def_pattern = re.compile(r'\b(Abstract\s+Contract|Contract|Interface|TxScript)\s+(\w+)')
    
    for match in def_pattern.finditer(content):
        def_type_raw = match.group(1) # e.g. "Abstract Contract"
        name = match.group(2)
        
        # Determine json type
        json_type = "contract" # Default
        is_abstract = False
        if "Abstract" in def_type_raw:
            is_abstract = True
            
        if "Interface" in def_type_raw:
            json_type = "interface"
        elif "TxScript" in def_type_raw:
            json_type = "tx_script"
        
        # Now parse forward from match.end()
        idx = match.end()
        
        fields_immutable = []
        fields_mutable = []
        parentContracts = []
        parentInterfaces = []
        
        # 1. Check for fields block (...)
        # Skip whitespace
        while idx < len(content) and content[idx].isspace():
            idx += 1
            
        if idx < len(content) and content[idx] == '(':
            # Parse fields
            fields_start = idx + 1
            paren_count = 1
            idx += 1
            while idx < len(content) and paren_count > 0:
                if content[idx] == '(':
                    paren_count += 1
                elif content[idx] == ')':
                    paren_count -= 1
                idx += 1
            
            fields_str = content[fields_start:idx-1]
            fields_immutable, fields_mutable = parse_fields(fields_str)
        
        # 2. Check for inheritance (extends / implements)
        # We need to read until '{'
        # But handle unexpected chars or end of file
        
        rest_of_def = ""
        while idx < len(content) and content[idx] != '{':
            rest_of_def += content[idx]
            idx += 1
            if idx >= len(content): break # Safety
            
        # Parse rest_of_def for 'extends' and 'implements'
        # Remove parent constructor args (...)
        
        simplified = ' '.join(rest_of_def.split())
        
        # Remove parenthesis content
        while '(' in simplified:
            start_p = simplified.find('(')
            p_count = 1
            end_p = start_p + 1
            while end_p < len(simplified) and p_count > 0:
                if simplified[end_p] == '(':
                    p_count += 1
                elif simplified[end_p] == ')':
                    p_count -= 1
                end_p += 1
            if end_p > len(simplified): end_p = len(simplified)
            simplified = simplified[:start_p] + simplified[end_p:]
            
        # Normalize comma to space
        simplified = simplified.replace(',', ' ')
        
        tokens = simplified.split()
        current_mode = None # 'extends' or 'implements'
        
        for token in tokens:
            if token == 'extends':
                current_mode = 'extends'
            elif token == 'implements':
                current_mode = 'implements'
            else:
                p_name = token.strip()
                if p_name and current_mode:
                    if current_mode == 'extends':
                        parentContracts.append(p_name)
                    elif current_mode == 'implements':
                        parentInterfaces.append(p_name)
                    
        specs.append({
            "type": json_type,
            "name": name,
            "abstract": is_abstract,
            "fields_immutable": fields_immutable,
            "fields_mutable": fields_mutable,
            "parent_contracts": parentContracts,
            "parent_interfaces": parentInterfaces
        })
        
    return specs

def main():
    if not os.path.exists(ROOT_DIR):
        print(f"Directory {ROOT_DIR} does not exist. Current dir: {CURRENT_DIR}")
        return

    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith('.ral'):
                file_path = os.path.join(root, file)
                print(f"Processing {file_path}...")
                try:
                    specs = parse_ralph_file(file_path)
                    if specs: # Only write if we found something
                        json_path = file_path + '.json'
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(specs, f, indent=2)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == '__main__':
    main()
