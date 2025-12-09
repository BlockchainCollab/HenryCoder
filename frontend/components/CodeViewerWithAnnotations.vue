<template>
  <div class="w-full h-full">
    <div
      class="grid gap-0 font-menlo text-[length:16px] text-gray-200 grid-cols-[minmax(40px,auto)_24px_1fr]"
    >
      <template v-for="(line, index) in codeLines" :key="index">
        <!-- Line Number -->
        <div
          class="justify-self-end text-[#9E9992] text-right pr-2 pl-4 py-1 select-none border-r border-[#312F2D]"
        >
          {{ index + 1 }}
        </div>

        <!-- Tooltip Icon Column (Code Annotations) -->
        <div class="flex items-center justify-center ml-1">
          <CodeAnnotationTooltip
            v-if="annotations.has(index + 1)"
            :annotation="annotations.get(index + 1) || ''"
            @open-modal="openAnnotationModal"
          />
        </div>

        <!-- Code Content with inline gas badge for function definitions -->
        <div
          class="py-1 pl-3 pr-4 whitespace-pre flex items-center"
          :class="{ 'opacity-50': props.loading }"
        >
          <span v-html="highlightedLines[index]"></span>
          <GasGutterDecoration
            v-if="gasAnnotations.has(index + 1) && codeLines[index] && isFunctionDefinitionLine(codeLines[index])"
            :annotation="gasAnnotations.get(index + 1)!"
            :minimal-gas="minimalGas"
            @open-modal="openGasModal"
          />
        </div>
      </template>
    </div>

    <!-- Mobile Modal for Code Annotations -->
    <AnnotationModal
      :is-open="annotationModalOpen"
      :annotation="annotationModalText"
      @update:open="annotationModalOpen = $event"
    />

    <!-- Mobile Modal for Gas Annotations -->
    <GasModal
      :is-open="gasModalOpen"
      :annotation="gasModalAnnotation"
      :minimal-gas="minimalGas"
      @update:open="gasModalOpen = $event"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import hljs from "highlight.js/lib/core";
import rust from "highlight.js/lib/languages/rust";
import { parseAnnotations } from "@/lib/parse-annotations";
import type { GasLineAnnotations, GasFunctionAnnotation } from "@/lib/gas-types";
import CodeAnnotationTooltip from "@/components/ui/CodeAnnotationTooltip.vue";
import GasGutterDecoration from "@/components/ui/GasGutterDecoration.vue";
import AnnotationModal from "@/components/AnnotationModal.vue";
import GasModal from "@/components/GasModal.vue";

// Register Rust language for Ralph syntax highlighting
hljs.registerLanguage("rust", rust);

interface Props {
  code: string;
  loading: boolean;
  gasAnnotations?: GasLineAnnotations;
  minimalGas?: number;
}

const props = withDefaults(defineProps<Props>(), {
  gasAnnotations: () => new Map(),
  minimalGas: 20_000,
});

// Emit the line mapping when annotations are parsed
const emit = defineEmits<{
  'update:lineMap': [lineMap: Map<number, number>];
}>();

// Check if we have gas annotations to show
const hasGasAnnotations = computed(() => props.gasAnnotations.size > 0);

// Regex to detect Ralph function definition lines
// Matches: pub fn name(...), fn name(...), @using(...) pub fn name(...), etc.
const fnDefinitionRegex = /^\s*(?:@\w+(?:\([^)]*\))?\s*)*(?:pub\s+)?fn\s+\w+/;

// Check if a line is a function definition
const isFunctionDefinitionLine = (line: string): boolean => {
  return fnDefinitionRegex.test(line);
};

// Code annotation modal state
const annotationModalOpen = ref(false);
const annotationModalText = ref("");

// Gas modal state
const gasModalOpen = ref(false);
const gasModalAnnotation = ref<GasFunctionAnnotation | null>(null);

// Parse code and annotations
const parsedCode = computed(() => parseAnnotations(props.code));
const annotations = computed(() => parsedCode.value.annotations);
const cleanCode = computed(() => parsedCode.value.cleanCode);
const originalToCleanLineMap = computed(() => parsedCode.value.originalToCleanLineMap);

// Emit line mapping when it changes
watch(originalToCleanLineMap, (lineMap) => {
  emit('update:lineMap', lineMap);
}, { immediate: true });

// Split code into lines
const codeLines = computed(() => {
  if (!cleanCode.value) return [];
  return cleanCode.value.split("\n");
});

// Highlight each line individually
const highlightedLines = computed(() => {
  return codeLines.value.flatMap((line, index) => {
    if (!line.trim()) {
      return "&nbsp;"; // Preserve empty lines
    }
    if (line.includes("```")) {
      // Handle code block delimiters
      return [];
    }
    try {
      // Replace leading spaces with non-breaking spaces to preserve indentation
      const leadingSpaces = line.match(/^\s*/)?.[0] || "";
      const codeContent = line.slice(leadingSpaces.length);

      if (!codeContent) {
        return "&nbsp;";
      }

      const result = hljs.highlight(codeContent, { language: "rust" });
      // Convert leading spaces to HTML entities to preserve indentation
      const indentation = leadingSpaces.replace(/ /g, "&nbsp;");
      return indentation + result.value;
    } catch (e) {
      // If highlighting fails, return escaped HTML with preserved spaces
      return escapeHtml(line).replace(/ /g, "&nbsp;");
    }
  });
});

// Open modal for code annotations
const openAnnotationModal = (annotation: string) => {
  annotationModalText.value = annotation;
  annotationModalOpen.value = true;
};

// Open modal for gas annotations
const openGasModal = (annotation: GasFunctionAnnotation) => {
  gasModalAnnotation.value = annotation;
  gasModalOpen.value = true;
};

// Helper to escape HTML
const escapeHtml = (text: string): string => {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
};
</script>

<style scoped>
/* Ensure grid layout doesn't break and allow horizontal scroll if needed */
.grid {
  min-width: fit-content;
  width: 100%;
}
</style>
