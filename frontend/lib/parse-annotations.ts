export interface ParsedCode {
  cleanCode: string;
  annotations: Map<number, string>;
}

/**
 * Parses Ralph code to extract // @@@ annotations
 * Maps annotations to the line number below them
 * Returns clean code without annotation lines
 */
export function parseAnnotations(code: string): ParsedCode {
  if (!code) {
    return { cleanCode: "", annotations: new Map() };
  }

  const lines = code.split("\n");
  const cleanLines: string[] = [];
  const annotations = new Map<number, string>();

  let lineNumber = 1; // Line numbers for clean code start at 1

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] || "";
    const trimmedLine = line.trim();

    // Check if this is an annotation line
    if (trimmedLine.startsWith("// @@@")) {
      // Extract annotation text (remove "// @@@ " prefix)
      const annotationText = trimmedLine.replace(/^\/\/\s*@@@\s*/, "").trim();

      // Map to the next line number (the line below this annotation)
      annotations.set(lineNumber, annotationText);

      // Don't add this line to cleanLines - it's removed from display
      continue;
    }

    // Add non-annotation lines to clean code (including empty lines)
    cleanLines.push(line);
    lineNumber++;
  }

  console.log({
    cleanCode: cleanLines.join("\n"),
    annotations,
  });

  return {
    cleanCode: cleanLines.join("\n"),
    annotations,
  };
}
