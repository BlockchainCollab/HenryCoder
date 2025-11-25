export type PreviousTranslation = {
  source_code: string;
  warnings: string[];
  errors: string[];
};

type AgentChunk = 
  | { type: "stage"; data: { stage: string; message: string } }
  | { type: "tool_start"; data: { tool: string; input: string } }
  | { type: "tool_end"; data: { tool: string; success: boolean } }
  | { type: "content"; data: string };

// Helper function to extract Ralph code from content
function extractRalphCode(content: string): string {
  // Remove "Translated Ralph code:" prefix if present
  let cleaned = content.replace(/^Translated Ralph code:\s*\n?/i, '');
  
  // Extract code between ```ralph and ```
  const ralphMatch = cleaned.match(/```ralph\s*\n([\s\S]*?)```/);
  if (ralphMatch && ralphMatch[1]) {
    return ralphMatch[1].trim();
  }
  
  // Fallback: try to remove any markdown code blocks
  cleaned = cleaned.replace(/```ralph\s*\n?/g, '');
  cleaned = cleaned.replace(/```\s*$/g, '');
  
  return cleaned.trim();
}

export async function translateCode({
  sourceCode,
  options,
  runtimeConfig,
  initialOutputCode,
  previousTranslation,
  setOutputCode,
  setLoadingStatus,
  setErrors,
}: {
  sourceCode: string;
  options: any;
  runtimeConfig: any;
  initialOutputCode: string;
  previousTranslation?: PreviousTranslation;
  setOutputCode: (val: string) => void;
  setLoadingStatus: (val: string) => void;
  setErrors: (val: string[]) => void;
  }) {
  const sessionId = ref<string>(crypto.randomUUID());
  setOutputCode(initialOutputCode);
  setErrors([]);
  setLoadingStatus("");
  
  let accumulatedContent = "";
  
  try {
    const response = await fetch(
      `${runtimeConfig.public.apiBase}/chat/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: sourceCode,
          session_id: sessionId.value,
          // options: {
          //   optimize: options.optimize,
          //   include_comments: options.includeComments,
          //   mimic_defaults: options.mimicDefaults,
          //   smart: options.smart,
          //   translate_erc20: options.translateERC20,
          // },
          // previous_translation: previousTranslation,
        }),
      }
    );
    
    if (!response.ok || !response.body) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Translation failed with non-JSON response" }));
      throw new Error(errorData.detail || "Translation failed");
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    let buffer = "";
    let errorsArr: string[] = [];
    
    while (!done) {
      const { value, done: streamDone } = await reader.read();
      done = streamDone;
      
      if (value) {
        buffer += decoder.decode(value, { stream: true });
        let lines = buffer.split("\n");
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (!line.trim()) continue;
          
          try {
            const chunk = JSON.parse(line) as AgentChunk;
            
            // Handle stage updates for progress indicator
            if (chunk.type === "stage") {
              setLoadingStatus(chunk.data.message);
            }
            
            // Accumulate content chunks
            if (chunk.type === "content") {
              accumulatedContent += chunk.data;
              
              // Try to extract and display Ralph code if we have the full code block
              if (accumulatedContent.includes("```ralph") && accumulatedContent.includes("```\n")) {
                const ralphCode = extractRalphCode(accumulatedContent);
                if (ralphCode) {
                  setOutputCode(ralphCode);
                }
              }
            }
            
            // Handle tool execution (for future agentic view)
            if (chunk.type === "tool_start") {
              setLoadingStatus(`🔧 Using tool: ${chunk.data.tool}`);
            }
            
          } catch (e) {
            // Ignore JSON parse errors for incomplete lines
          }
        }
      }
    }
    
    // Handle any remaining buffered line
    if (buffer.trim()) {
      try {
        const chunk = JSON.parse(buffer) as AgentChunk;
        if (chunk.type === "content") {
          accumulatedContent += chunk.data;
        }
      } catch (e) {
        // Ignore
      }
    }
    
    // Final extraction of Ralph code
    const finalRalphCode = extractRalphCode(accumulatedContent);
    if (finalRalphCode) {
      setOutputCode(finalRalphCode);
    }
    
    setLoadingStatus("✅ Translation complete");
    setErrors(errorsArr);
    
  } catch (e: any) {
    console.error("Translation error:", e);
    const errorMessage = e instanceof Error ? e.message : String(e);
    setErrors([errorMessage]);
    setLoadingStatus("");
  }
}

export async function compileTranslatedCode({
  outputCode,
  runtimeConfig,
  onError,
  onSuccess,
}: {
  outputCode: string;
  runtimeConfig: any;
  onError: (val: string[]) => void;
  onSuccess: (message?: string) => void;
}) {
  let node_endpoint = "/contracts/compile-contract";
  let url = `${runtimeConfig.public.nodeUrl}${node_endpoint}`;
  let queryJson = {
    code: outputCode,
    compilerOptions: {
      ignoreUnusedConstantsWarnings: true,
      ignoreUnusedVariablesWarnings: true,
      ignoreUnusedFieldsWarnings: true,
      ignoreUnusedPrivateFunctionsWarnings: true,
      ignoreUnusedFunctionReturnWarnings: true,
    },
  };
  return fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(queryJson),
  })
    .then(async (response) => {
      if (!response.ok) {
        let errorMsg = "Compilation failed.";
        try {
          const errJson = await response.json();
          if (errJson && errJson.detail) {
            errorMsg = errJson.detail;
          }
        } catch (e) {
          errorMsg = response.statusText || errorMsg;
        }

        if (
          errorMsg.includes("Code generation is not supported for abstract contract")
        ) {
          onSuccess(
            "No syntax errors, but code generation is not supported for abstract contracts - please try locally"
          );
          return;
        }
        onError([errorMsg]);
        return;
      }
      // Success: show green message
      onSuccess();
    })
    .catch((error) => {
      console.error("Compilation error:", error);
      onError([String(error)]);
    });
}
