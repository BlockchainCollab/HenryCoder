export type PreviousTranslation = {
  source_code: string;
  warnings: string[];
  errors: string[];
};

type AgentChunk =
  | { type: "stage"; data: { stage: string; message: string } }
  | { type: "tool_start"; data: { tool: string; input: string } }
  | { type: "tool_end"; data: { tool: string; success: boolean } }
  | { type: "content"; data: string }
  | { type: "translation_chunk"; data: string }
  | { type: "error"; data: { message: string } };

/**
 * Cleans markdown code block wrappers from translated code.
 * Removes patterns like: ```ralph, ```solidity, ```, and standalone "ralph" or "solidity" lines.
 */
function cleanMarkdownFromCode(code: string): string {
  // Remove opening markdown code fence with optional language
  let cleaned = code.replace(/^```(?:ralph|solidity)?\s*\n?/i, "");
  // Remove standalone language identifier at start (ralph or solidity on its own line)
  cleaned = cleaned.replace(/^(?:ralph|solidity)\s*\n/i, "");
  // Remove closing markdown code fence
  cleaned = cleaned.replace(/\n?```\s*$/g, "");
  // Trim leading/trailing whitespace
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

  let streamedTranslationCode = initialOutputCode;

  try {
    // Create AbortController for timeout handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout

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
          options: {
            optimize: options.optimize,
            include_comments: options.includeComments,
            mimic_defaults: options.mimicDefaults,
            smart: options.smart,
            translate_erc20: options.translateERC20,
          },
        }),
        signal: controller.signal,
      }
    );

    clearTimeout(timeoutId);

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

            // Handle translation chunks - streamed directly from translator
            if (chunk.type === "translation_chunk") {
              // Stream the translation chunk directly to the output
              streamedTranslationCode += chunk.data;
              console.log(`[Stream] Accumulated length: ${streamedTranslationCode.length}, chunk: "${chunk.data.slice(0, 50)}..."`);
              setOutputCode(streamedTranslationCode);
            }

            // Handle tool execution (for future agentic view)
            if (chunk.type === "tool_start") {
              setLoadingStatus(`🔧 Using tool: ${chunk.data.tool}`);
            }

            // Handle errors from backend
            if (chunk.type === "error") {
              const errorMsg = chunk.data?.message || "Unknown error";
              errorsArr.push(errorMsg);
            }
          } catch (e) {
            // Ignore JSON parse errors for incomplete lines
          }
        }
      }
    }

    // Clean up any markdown artifacts from the final output
    const cleanedCode = cleanMarkdownFromCode(streamedTranslationCode);
    if (cleanedCode !== streamedTranslationCode) {
      setOutputCode(cleanedCode);
    }
    
    setLoadingStatus("✅ Translation complete");
    setErrors(errorsArr);
  } catch (e: any) {
    console.error("Translation error:", e);
    let errorMessage: string;
    
    if (e.name === 'AbortError') {
      errorMessage = "Translation timed out. Please try again with a smaller contract.";
    } else if (
      e.message === 'network error' || 
      e.message?.includes('network') ||
      e.message?.includes('Failed to fetch') ||
      e.name === 'TypeError'
    ) {
      // Check if we received partial data (indicates chunked encoding issue)
      if (streamedTranslationCode && streamedTranslationCode !== initialOutputCode) {
        errorMessage = "The connection was interrupted during translation. The server may have timed out. Partial translation is shown above - you can try again or work with the partial result.";
      } else {
        errorMessage = "Connection error - the server connection was lost. This may be due to a timeout on long translations. Please try again, or try with a smaller contract.";
      }
    } else {
      errorMessage = e instanceof Error ? e.message : String(e);
    }
    
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
  let node_endpoint = "/contracts/compile-project";
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
          errorMsg.includes(
            "Code generation is not supported for abstract contract"
          )
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

// Fix Ralph code based on compilation error
export type FixCodeResult = {
  fixedCode: string;
  iterations: number;
  success: boolean;
};

type FixStreamEvent =
  | { type: "stage"; data: { stage: string; message: string } }
  | { type: "result"; data: { fixed_code: string; iterations: number; success: boolean } }
  | { type: "error"; data: { message: string } };

export async function fixRalphCode({
  ralphCode,
  error,
  solidityCode,
  runtimeConfig,
  onStageUpdate,
}: {
  ralphCode: string;
  error: string;
  solidityCode?: string;
  runtimeConfig: any;
  onStageUpdate?: (stage: string, message: string) => void;
}): Promise<FixCodeResult> {
  const response = await fetch(`${runtimeConfig.public.apiBase}/chat/fix`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ralph_code: ralphCode,
      error: error,
      solidity_code: solidityCode,
    }),
  });

  if (!response.ok || !response.body) {
    const errorData = await response
      .json()
      .catch(() => ({ detail: "Fix request failed" }));
    throw new Error(errorData.detail || "Failed to fix code");
  }

  // Parse streaming response
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: FixCodeResult | null = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const event = JSON.parse(line) as FixStreamEvent;

        if (event.type === "stage" && onStageUpdate) {
          onStageUpdate(event.data.stage, event.data.message);
        } else if (event.type === "result") {
          result = {
            fixedCode: event.data.fixed_code,
            iterations: event.data.iterations,
            success: event.data.success,
          };
        } else if (event.type === "error") {
          throw new Error(event.data.message);
        }
      } catch (e) {
        // Ignore JSON parse errors for incomplete lines
        if (e instanceof SyntaxError) continue;
        throw e;
      }
    }
  }

  if (!result) {
    throw new Error("No result received from fix endpoint");
  }

  return result;
}
