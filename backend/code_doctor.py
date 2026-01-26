import re
from typing import Set, Optional

class CodeDoctor:
    def __init__(self, source_code: str, external_mappings: Optional[Set[str]] = None):
        self.source_code = source_code
        self.mutable_fields = set()
        self.external_mappings = external_mappings or set()

    def fix_all(self) -> str:
        self.extract_mutable_fields()
        self.source_code = self.fix_enums(self.source_code)
        self.source_code = self.fix_underscores(self.source_code)
        self.source_code = self.fix_map_insert(self.source_code)
        self.source_code = self.fix_annotations(self.source_code)
        return self.source_code

    def extract_mutable_fields(self):
        # Find all contracts and extract mutable fields from each
        # Store as dict: {contract_name: set of mutable field names}
        self.contract_mutable_fields = {}
        # Also store mapping names per contract
        self.contract_mappings = {}
        
        # Regex to find Contract definitions
        contract_pattern = re.compile(r'(?:Abstract\s+)?Contract\s+(\w+)\s*\((.*?)\)\s*(?:extends[^{]*)?\s*(?:implements[^{]*)?\s*\{', re.DOTALL)
        
        for match in contract_pattern.finditer(self.source_code):
            contract_name = match.group(1)
            fields_block = match.group(2)
            # Find all 'mut fieldName'
            mut_fields = re.findall(r'mut\s+(\w+)', fields_block)
            self.contract_mutable_fields[contract_name] = set(mut_fields)
            
            # Find the contract body to extract mappings
            contract_start = match.end()
            contract_end = self.find_matching_brace(self.source_code, contract_start - 1)
            if contract_end != -1:
                contract_body = self.source_code[contract_start:contract_end-1]
                # Find all mapping declarations: mapping[KeyType, ValueType] mapName
                mapping_names = re.findall(r'mapping\s*\[[^\]]+\]\s+(\w+)', contract_body)
                self.contract_mappings[contract_name] = set(mapping_names)
            else:
                self.contract_mappings[contract_name] = set()
        
        # For backward compatibility, also set self.mutable_fields as union of all
        self.mutable_fields = set()
        for fields in self.contract_mutable_fields.values():
            self.mutable_fields.update(fields)

    def fix_enums(self, code: str) -> str:
        lines = code.split('\n')
        new_lines = []
        in_enum = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('enum ') and stripped.endswith('{'):
                in_enum = True
                new_lines.append(line)
                continue
            
            if in_enum:
                if stripped == '}':
                    in_enum = False
                    new_lines.append(line)
                    continue
                # Remove trailing comma if present
                if line.rstrip().endswith(','):
                    # Find the last comma and remove it
                    idx = line.rfind(',')
                    line = line[:idx] + line[idx+1:]
            
            new_lines.append(line)
        return '\n'.join(new_lines)

    def fix_underscores(self, code: str) -> str:
        # Iterate and rebuild string, skipping strings and comments
        result = []
        i = 0
        n = len(code)
        
        while i < n:
            # Check for string start (double quotes)
            if code[i] == '"':
                # Find end of string
                result.append('"')
                i += 1
                while i < n:
                    result.append(code[i])
                    if code[i] == '"' and code[i-1] != '\\':
                        i += 1
                        break
                    i += 1
                continue
            
            # Check for backtick string (b`...`)
            if code[i:i+2] == 'b`':
                result.append('b`')
                i += 2
                while i < n:
                    result.append(code[i])
                    if code[i] == '`':
                        i += 1
                        break
                    i += 1
                continue
                
            # Check for comment //
            if code[i:i+2] == '//':
                # Read until newline
                while i < n and code[i] != '\n':
                    result.append(code[i])
                    i += 1
                continue
                
            # Check for identifier starting with _
            # We need to check if we are at a word boundary
            if code[i] == '_':
                # Check previous char
                prev_char = code[i-1] if i > 0 else ' '
                if not prev_char.isalnum() and prev_char != '_':
                    # It is a start of an identifier?
                    # Check next char
                    if i+1 < n and code[i+1].isalnum():
                        # Found _Identifier
                        # Capture identifier
                        j = i + 1
                        ident = ""
                        while j < n and (code[j].isalnum() or code[j] == '_'):
                            ident += code[j]
                            j += 1
                        
                        # Append Identifier_
                        result.append(ident + "_")
                        i = j
                        continue
            
            result.append(code[i])
            i += 1
            
        return "".join(result)

    def fix_map_insert(self, code: str) -> str:
        # <map>.insert!{...}(...) -> <map>.insert!(...)
        return re.sub(r'\.insert!\{[^}]*\}\(', '.insert!(', code)

    def find_containing_contract(self, code: str, position: int) -> str | None:
        """Find which contract contains the given position."""
        # Find all contract starts before this position
        contract_pattern = re.compile(r'(?:Abstract\s+)?Contract\s+(\w+)\s*\(.*?\)\s*(?:extends[^{]*)?\s*(?:implements[^{]*)?\s*\{', re.DOTALL)
        
        best_contract = None
        best_start = -1
        
        for match in contract_pattern.finditer(code):
            if match.end() <= position:
                # This contract starts before our position
                # Check if it also ends after our position
                contract_end = self.find_matching_brace(code, match.end() - 1)
                if contract_end == -1 or contract_end > position:
                    # This contract contains our position
                    if match.start() > best_start:
                        best_contract = match.group(1)
                        best_start = match.start()
        
        return best_contract

    def fix_annotations(self, code: str) -> str:
        # We need to iterate over functions, identify their body, and apply rules.
        # Regex to find functions:
        # (@using\(...\)\s*)?(pub\s+)?fn\s+(\w+)\s*\(.*?\)\s*(->\s*.*?)?\s*\{
        
        # We will split the code into chunks or use a scanner.
        # Since we need to modify the @using part which is BEFORE the function, 
        # and the decision depends on the body, we need to parse the function first.
        
        # Let's find all function starts.
        func_pattern = re.compile(r'((?:@using\([^)]+\)\s*)?)(pub\s+)?fn\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*[^{]+)?\s*\{')
        
        # We'll iterate through matches, find the matching closing brace for the body,
        # analyze the body, and reconstruct the function header.
        
        # To do this safely, we can't just replace in place easily because lengths change.
        # We will build a new code string.
        
        new_code = ""
        last_pos = 0
        
        for match in func_pattern.finditer(code):
            start_pos = match.start()
            
            full_header = match.group(0)
            existing_annotation = match.group(1)
            is_public = bool(match.group(2))
            func_name = match.group(3)
            params = match.group(4)
            
            # Find body end with safe brace counting
            body_start = match.end()
            body_end = self.find_matching_brace(code, body_start - 1)
            
            if body_end == -1:
                # Error finding brace, just append rest
                new_code += code[last_pos:]
                return new_code
            
            body_content = code[body_start:body_end-1]
            
            # Find which contract this function belongs to
            containing_contract = self.find_containing_contract(code, start_pos)
            contract_mutable_fields = set()
            contract_mappings = set()
            if containing_contract:
                if containing_contract in self.contract_mutable_fields:
                    contract_mutable_fields = self.contract_mutable_fields[containing_contract]
                if containing_contract in self.contract_mappings:
                    contract_mappings = self.contract_mappings[containing_contract]
            
            # Analyze body
            analysis = self.analyze_function(body_content, params, contract_mutable_fields, contract_mappings)
            
            # Construct new annotation
            new_annotation = self.construct_annotation(analysis, existing_annotation, is_public)
            
            # Determine indentation by looking at the line start of the function (not annotation)
            # Find where the actual fn keyword starts
            fn_pos = match.start(2) if match.group(2) else match.start(3) - 3  # "fn " is 3 chars before func name
            if existing_annotation:
                # The fn keyword position is after the annotation
                fn_match = re.search(r'(pub\s+)?fn\s+', full_header)
                if fn_match:
                    fn_pos = start_pos + len(existing_annotation) + fn_match.start()
            
            line_start = code.rfind('\n', 0, start_pos) + 1
            indent = ""
            for c in code[line_start:]:
                if c in ' \t':
                    indent += c
                else:
                    break
            
            # Append everything before this function
            new_code += code[last_pos:line_start]
            
            # Reconstruct header
            # Remove existing annotation from header if it was captured
            header_without_annotation = full_header
            if existing_annotation:
                header_without_annotation = full_header[len(existing_annotation):].lstrip()
            
            if new_annotation:
                new_code += f"{indent}{new_annotation}\n{indent}{header_without_annotation}"
            else:
                new_code += f"{indent}{header_without_annotation}"
                
            # Append body
            new_code += body_content + "}"
            
            last_pos = body_end
            
        new_code += code[last_pos:]
        return new_code

    def find_matching_brace(self, code: str, start_index: int) -> int:
        # start_index is the index of '{'
        count = 0
        i = start_index
        n = len(code)
        
        while i < n:
            char = code[i]
            
            if char == '"':
                i += 1
                while i < n:
                    if code[i] == '"' and code[i-1] != '\\':
                        break
                    i += 1
            elif char == '/' and i+1 < n and code[i+1] == '/':
                i += 2
                while i < n and code[i] != '\n':
                    i += 1
            elif char == '{':
                count += 1
            elif char == '}':
                count -= 1
                if count == 0:
                    return i + 1 # Return index after '}'
            
            i += 1
        return -1

    def strip_comments_and_strings(self, code: str) -> str:
        result = []
        i = 0
        n = len(code)
        while i < n:
            # Double-quoted strings
            if code[i] == '"':
                i += 1
                while i < n:
                    if code[i] == '"' and code[i-1] != '\\':
                        i += 1
                        break
                    i += 1
                result.append(" ") # Replace string with space
            # Backtick strings (b`...`)
            elif code[i:i+2] == 'b`':
                i += 2
                while i < n:
                    if code[i] == '`':
                        i += 1
                        break
                    i += 1
                result.append(" ") # Replace string with space
            # Comments
            elif code[i:i+2] == '//':
                while i < n and code[i] != '\n':
                    i += 1
                result.append(" ") # Replace comment with space
            else:
                result.append(code[i])
                i += 1
        return "".join(result)

    def has_assignment_at_main_scope(self, body: str, pattern: str) -> bool:
        """Check if pattern matches at main scope (brace depth 0) of function body."""
        # Scan through body tracking brace depth
        # When at depth 0, check if current position matches the pattern
        
        depth = 0
        i = 0
        n = len(body)
        
        while i < n:
            char = body[i]
            
            if char == '{':
                depth += 1
                i += 1
            elif char == '}':
                depth -= 1
                i += 1
            elif depth == 0:
                # At main scope - check if pattern matches here
                match = re.match(pattern, body[i:])
                if match:
                    return True
                i += 1
            else:
                i += 1
        
        return False

    def analyze_function(self, body: str, params: str, mutable_fields: set = None, mappings: set = None) -> dict:
        if mutable_fields is None:
            mutable_fields = self.mutable_fields
        if mappings is None:
            mappings = set()
        # Include external mappings (passed from outside when contract context is known)
        mappings = mappings | self.external_mappings
            
        flags = {
            'assetsInContract': False,
            'preapprovedAssets': False,
            'updateFields': False,
            'checkCaller': False,
            'hasInsert': False,
            'hasTransferTokenToSelf': False
        }
        
        clean_body = self.strip_comments_and_strings(body)
        
        # Rule 1: tokenRemaining with selfAddress!()
        if re.search(r'tokenRemaining!\s*\(\s*selfAddress!\s*\(\s*\)', clean_body):
            flags['assetsInContract'] = True
            
        # Rule 2: transferTokenFromSelf!
        if 'transferTokenFromSelf!' in clean_body:
            flags['assetsInContract'] = True
            
        # Rule 3: transferTokenToSelf!
        if 'transferTokenToSelf!' in clean_body:
            flags['preapprovedAssets'] = True
            flags['hasTransferTokenToSelf'] = True
            
        # transferToken! requires preapprovedAssets = true
        if 'transferToken!' in clean_body and 'transferTokenFromSelf!' not in clean_body and 'transferTokenToSelf!' not in clean_body:
            flags['preapprovedAssets'] = True
            
        # burnToken! requires preapprovedAssets = true (when burning from external caller)
        # or assetsInContract = true (when burning contract's own assets)
        # We'll assume preapprovedAssets for safety as it's more common
        if 'burnToken!' in clean_body:
            # Check if burning from selfAddress
            if re.search(r'burnToken!\s*\(\s*selfAddress!\s*\(\s*\)', clean_body):
                flags['assetsInContract'] = True
            else:
                flags['preapprovedAssets'] = True
                
        # lockApprovedAssets! requires preapprovedAssets = true
        if 'lockApprovedAssets!' in clean_body:
            flags['preapprovedAssets'] = True
            
        # createContract! with asset transfer requires preapprovedAssets = true
        if re.search(r'createContract!\s*\{', clean_body):
            flags['preapprovedAssets'] = True
            
        # createSubContract! with asset transfer requires preapprovedAssets = true
        if re.search(r'createSubContract!\s*\{', clean_body):
            flags['preapprovedAssets'] = True
            
        # Rule 7: insert! requires preapprovedAssets
        if 'insert!' in clean_body:
            flags['preapprovedAssets'] = True
            flags['hasInsert'] = True
            
        # Rule 4: Assigns to mutable field - ALWAYS requires updateFields (any scope)
        for field in mutable_fields:
            # Check for assignment: field = ... or field[...] = ... or field.property = ...
            # Split by lines and check if field appears on left side of assignment
            for line in clean_body.split('\n'):
                # Skip if line doesn't contain the field name
                if field not in line:
                    continue
                # Check if there's an assignment (= but not ==, !=, <=, >=)
                if '=' not in line:
                    continue
                # Find all = signs that are not part of ==, !=, <=, >=
                parts = re.split(r'([!=<>]=|=)', line)
                for i, part in enumerate(parts):
                    if part == '=' and i > 0:
                        # Check if field appears before this =
                        left_side = ''.join(parts[:i])
                        if re.search(rf'\b{field}\b', left_side):
                            flags['updateFields'] = True
                            break
        
        # Mapping modifications only require updateFields at MAIN SCOPE
        for mapping_name in mappings:
            # Check for assignment: mapping[...] = ...
            if self.has_assignment_at_main_scope(clean_body, rf'\b{mapping_name}\s*\[.*?\]\s*=[^=]'):
                flags['updateFields'] = True
            # Check for mapping.insert!(...) - modifies mapping state
            if self.has_assignment_at_main_scope(clean_body, rf'\b{mapping_name}\.insert!\s*\('):
                flags['updateFields'] = True
            # Check for mapping.remove!(...) - modifies mapping state
            if self.has_assignment_at_main_scope(clean_body, rf'\b{mapping_name}\.remove!\s*\('):
                flags['updateFields'] = True
        
        # If no contract context, check for any .insert!() or .remove!() calls on unknown mappings at main scope
        if not mappings:
            if self.has_assignment_at_main_scope(clean_body, r'\w+\.insert!\s*\('):
                flags['updateFields'] = True
            if self.has_assignment_at_main_scope(clean_body, r'\w+\.remove!\s*\('):
                flags['updateFields'] = True
                
        # Check for checkCaller!
        if 'checkCaller!' in clean_body:
            flags['checkCaller'] = True
            
        return flags

    def construct_annotation(self, analysis: dict, existing_annotation_str: str, is_public: bool) -> str:
        # Parse existing annotation if any
        current_props = {}
        if existing_annotation_str:
            # Extract content inside @using(...)
            match = re.search(r'@using\((.*)\)', existing_annotation_str)
            if match:
                content = match.group(1)
                parts = content.split(',')
                for part in parts:
                    if '=' in part:
                        key, val = part.split('=')
                        current_props[key.strip()] = val.strip()

        # Apply rules to update props
        if analysis['assetsInContract']:
            current_props['assetsInContract'] = 'true'
            
        if analysis['preapprovedAssets']:
            current_props['preapprovedAssets'] = 'true'
            
        if analysis['updateFields']:
            current_props['updateFields'] = 'true'
        elif 'updateFields' in current_props:
            del current_props['updateFields']
            
        # Rule 9: If preapprovedAssets = true but not assetsInContract = true AND there is transferTokenToSelf!, payToContractOnly = true must be added.
        if (current_props.get('preapprovedAssets') == 'true' and 
            current_props.get('assetsInContract') != 'true' and
            analysis.get('hasTransferTokenToSelf', False)):
            current_props['payToContractOnly'] = 'true'
            
        # Rule 5 & 6: checkExternalCaller
        # If (assetsInContract or updateFields or preapprovedAssets) and doesn't contain checkCaller! statement it MUST have checkExternalCaller = false.
        # BUT only if public (Rule 6 says private must not use it, implying public should/can).
        
        needs_check_external = (
            current_props.get('assetsInContract') == 'true' or
            current_props.get('updateFields') == 'true' or
            current_props.get('preapprovedAssets') == 'true'
        )
        
        if needs_check_external and not analysis['checkCaller']:
            if is_public:
                current_props['checkExternalCaller'] = 'false'
            else:
                # Private function, remove it if present
                if 'checkExternalCaller' in current_props:
                    del current_props['checkExternalCaller']
        
        # If no properties, return empty string (no annotation)
        if not current_props:
            return ""
            
        # Construct string
        # Sort keys to ensure deterministic output, or just iterate
        # We want to keep existing order if possible? No, just rebuild.
        props_list = [f"{k} = {v}" for k, v in current_props.items()]
        return f"@using({', '.join(props_list)})"

def fix_common_errors(ralph_code: str, mappings: Optional[Set[str]] = None) -> str:
    doctor = CodeDoctor(ralph_code, external_mappings=mappings)
    return doctor.fix_all()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python code_doctor.py <file.ral>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        with open(file_path, 'r') as f:
            original_code = f.read()
        
        # Run code doctor
        fixed_code = fix_common_errors(original_code)
        
        # Check if changes were made
        if fixed_code == original_code:
            print(f"✓ No changes needed for {file_path}")
        else:
            # Write back to file
            with open(file_path, 'w') as f:
                f.write(fixed_code)
            print(f"✓ Fixed and updated {file_path}")
    except FileNotFoundError:
        print(f"✗ Error: File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error processing {file_path}: {str(e)}")
        sys.exit(1)
