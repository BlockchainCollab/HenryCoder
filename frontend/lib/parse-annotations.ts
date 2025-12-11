export interface ParsedCode {
  cleanCode: string;
  annotations: Map<number, string>;
  /**
   * Maps original line numbers to clean line numbers.
   * Used to adjust gas estimation line numbers after annotation removal.
   */
  originalToCleanLineMap: Map<number, number>;
}

/**
 * Strips markdown code block markers from code.
 * Removes ```language and ``` lines that may be present in LLM output.
 */
function stripMarkdownCodeBlocks(code: string): string {
  const lines = code.split("\n");
  const cleanedLines: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();
    // Skip opening code block markers (```ralph, ```typescript, ```, etc.)
    if (/^```\w*$/.test(trimmed)) {
      continue;
    }
    cleanedLines.push(line);
  }

  return cleanedLines.join("\n");
}

/**
 * Parses Ralph code to extract // @@@ annotations
 * Maps annotations to the line number below them
 * Returns clean code without annotation lines
 */
export function parseAnnotations(code: string): ParsedCode {
  if (!code) {
    return { 
      cleanCode: "", 
      annotations: new Map(),
      originalToCleanLineMap: new Map(),
    };
  }

  // First, strip any markdown code block markers from LLM output
  const codeWithoutMarkdown = stripMarkdownCodeBlocks(code);

  const lines = codeWithoutMarkdown.split("\n");
  const cleanLines: string[] = [];
  const annotations = new Map<number, string>();
  const originalToCleanLineMap = new Map<number, number>();

  let cleanLineNumber = 1; // Line numbers for clean code start at 1
  let removedLines = 0;

  for (let i = 0; i < lines.length; i++) {
    const originalLineNumber = i + 1; // 1-indexed
    const line = lines[i] || "";
    const trimmedLine = line.trim();

    // Check if this is an annotation line
    if (trimmedLine.startsWith("// @@@")) {
      // Extract annotation text (remove "// @@@ " prefix)
      const annotationText = trimmedLine.replace(/^\/\/\s*@@@\s*/, "").trim();

      // Map to the next clean line number (the line below this annotation)
      annotations.set(cleanLineNumber, annotationText);

      // Track this removed line
      removedLines++;

      // Don't add this line to cleanLines - it's removed from display
      continue;
    }

    // Map original line number to clean line number
    originalToCleanLineMap.set(originalLineNumber, cleanLineNumber);

    // Add non-annotation lines to clean code (including empty lines)
    cleanLines.push(line);
    cleanLineNumber++;
  }

  return {
    cleanCode: cleanLines.join("\n"),
    annotations,
    originalToCleanLineMap,
  };
}
