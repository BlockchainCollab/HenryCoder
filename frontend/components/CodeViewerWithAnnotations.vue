<template>
  <div class="w-full h-full">
    <div
      class="grid grid-cols-[minmax(40px,auto)_24px_1fr] gap-0 font-menlo text-[length:16px] text-gray-200"
    >
      <template v-for="(line, index) in codeLines" :key="index">
        <!-- Line Number -->
        <div
          class="justify-self-end text-[#9E9992] text-right pr-2 pl-4 py-1 select-none border-r border-[#312F2D]"
        >
          {{ index + 1 }}
        </div>

        <!-- Tooltip Icon Column -->
        <div class="flex items-center justify-center ml-1">
          <CodeAnnotationTooltip
            v-if="annotations.has(index + 1)"
            :annotation="annotations.get(index + 1) || ''"
            @open-modal="openModal"
          />
        </div>

        <!-- Code Content -->
        <div
          class="py-1 pl-3 pr-4 whitespace-pre"
          :class="{ 'opacity-50': props.loading }"
          v-html="highlightedLines[index]"
        ></div>
      </template>
    </div>

    <!-- Mobile Modal -->
    <AnnotationModal
      :is-open="modalOpen"
      :annotation="modalAnnotation"
      @update:open="modalOpen = $event"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import hljs from "highlight.js/lib/core";
import rust from "highlight.js/lib/languages/rust";
import { parseAnnotations } from "@/lib/parse-annotations";
import CodeAnnotationTooltip from "@/components/ui/CodeAnnotationTooltip.vue";
import AnnotationModal from "@/components/AnnotationModal.vue";

// Register Rust language for Ralph syntax highlighting
hljs.registerLanguage("rust", rust);

interface Props {
  code: string;
  loading: boolean;
}

const props = defineProps<Props>();

// Modal state
const modalOpen = ref(false);
const modalAnnotation = ref("");

// Parse code and annotations
const parsedCode = computed(() => parseAnnotations(props.code));
const annotations = computed(() => parsedCode.value.annotations);
const cleanCode = computed(() => parsedCode.value.cleanCode);

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

// Open modal with annotation text
const openModal = (annotation: string) => {
  modalAnnotation.value = annotation;
  modalOpen.value = true;
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
