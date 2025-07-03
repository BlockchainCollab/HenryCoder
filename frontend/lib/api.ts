export type PreviousTranslation = {
  source_code: string;
  warnings: string[];
  errors: string[];
};

export async function translateCode({
  sourceCode,
  options,
  runtimeConfig,
  initialOutputCode,
  previousTranslation,
  setOutputCode,
  setErrors,
}: {
  sourceCode: string;
  options: any;
  runtimeConfig: any;
  initialOutputCode: string;
  previousTranslation?: PreviousTranslation;
  setOutputCode: (val: string) => void;
  setErrors: (val: string[]) => void;
}) {
  setOutputCode(initialOutputCode);
  setErrors([]);
  let output = initialOutputCode;
  try {
    const response = await fetch(
      `${runtimeConfig.public.apiBase}/translate/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source_code: sourceCode,
          options: {
            optimize: options.optimize,
            include_comments: options.includeComments,
            mimic_defaults: options.mimicDefaults,
          },
          previous_translation: previousTranslation,
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
    setOutputCode("");
    setErrors([]);
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
            const data = JSON.parse(line);
            if (data.translated_code) {
              output += data.translated_code;
              setOutputCode(output);
            }
            if (data.warnings && data.warnings.length > 0) {
              errorsArr = [
                ...errorsArr,
                ...data.warnings.map((w: string) => `Warning: ${w}`),
              ];
            }
            if (data.errors && data.errors.length > 0) {
              errorsArr = [
                ...errorsArr,
                ...data.errors.map((e: string) => String(e)),
              ];
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
        const data = JSON.parse(buffer);
        if (data.translated_code) {
          output += data.translated_code;
        }
        if (data.warnings && data.warnings.length > 0) {
          errorsArr = [
            ...errorsArr,
            ...data.warnings.map((w: string) => `Warning: ${w}`),
          ];
        }
        if (data.errors && data.errors.length > 0) {
          errorsArr = [
            ...errorsArr,
            ...data.errors.map((e: string) => String(e)),
          ];
        }
      } catch (e) {
        // Ignore
      }
    }
    setOutputCode(output);
    setErrors(errorsArr);
  } catch (e: any) {
    console.error("Translation error:", e);
    const errorMessage = e instanceof Error ? e.message : String(e);
    setErrors([errorMessage]);
  }
}

export async function compileTranslatedCode({
  outputCode,
  runtimeConfig,
  onError,
  onSuccess
}: {
  outputCode: string;
  runtimeConfig: any;
  onError: (val: string[]) => void;
  onSuccess: () => void;
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
