<template>
  <!-- Minimized Mode -->
  <div
    v-if="minimized"
    @click="$emit('toggle-minimize')"
    class="absolute bottom-4 right-4 flex items-center gap-3 px-4 py-2 rounded-full bg-[#312F2D] border border-[#FF8A00] shadow-[0_0_10px_2px_rgba(239,133,16,0.4)] cursor-pointer hover:shadow-[0_0_14px_3px_rgba(239,133,16,0.6)] transition-all duration-300 z-20"
    role="button"
    aria-label="Expand progress indicator"
  >
    <!-- Pulsing dot -->
    <div class="relative">
      <div class="w-3 h-3 rounded-full bg-[#FF8A00] animate-pulse"></div>
      <div class="absolute inset-0 w-3 h-3 rounded-full bg-[#FF8A00] animate-ping opacity-75"></div>
    </div>
    <!-- Status text -->
    <span class="text-sm font-medium text-[#E5DED7] truncate max-w-[150px]">
      {{ currentStageLabel }}
    </span>
    <!-- Expand icon -->
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="h-4 w-4 text-[#FF8A00]"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M5 15l7-7 7 7"
      />
    </svg>
  </div>

  <!-- Expanded Mode -->
  <div v-else class="flex flex-col items-center justify-center relative w-full h-full bg-[#242322]/40 backdrop-blur-md z-30 overflow-y-auto custom-scrollbar">
    <!-- Minimize button -->
    <button
      @click="$emit('toggle-minimize')"
      class="absolute top-4 right-4 p-2 rounded-full bg-[#312F2D] border border-[#4C4B4B] hover:border-[#FF8A00] text-[#9E9992] hover:text-[#FF8A00] transition-all duration-200 z-20"
      aria-label="Minimize progress indicator"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-5 w-5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </button>

    <!-- Henry Robot Animation -->
    <div class="mb-8 relative flex-shrink-0">
      <div class="w-24 h-24 sm:w-32 sm:h-32 relative animate-bounce-slow">
        <!-- Robot Icon with Coding Animation -->
        <div class="absolute inset-0 flex items-center justify-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 200 200"
            class="w-full h-full"
          >
            <!-- Robot Body -->
            <rect
              x="60"
              y="80"
              width="80"
              height="90"
              rx="8"
              fill="#FF8A00"
              class="animate-pulse-subtle"
            />
            <!-- Robot Head -->
            <rect x="70" y="50" width="60" height="50" rx="8" fill="#FBA444" />
            <!-- Eyes -->
            <circle
              cx="85"
              cy="70"
              r="6"
              fill="#191817"
              class="animate-blink"
            />
            <circle
              cx="115"
              cy="70"
              r="6"
              fill="#191817"
              class="animate-blink"
            />
            <!-- Antenna -->
            <line
              x1="100"
              y1="50"
              x2="100"
              y2="30"
              stroke="#FBA444"
              stroke-width="4"
            />
            <circle
              cx="100"
              cy="25"
              r="5"
              fill="#E15959"
              class="animate-ping-slow"
            />
            <!-- Mouth/Screen -->
            <rect
              x="75"
              y="110"
              width="50"
              height="40"
              rx="4"
              fill="#312F2D"
            />
            <!-- Code Lines Animation -->
            <line
              x1="80"
              y1="120"
              x2="120"
              y2="120"
              stroke="#43A047"
              stroke-width="2"
              class="animate-typing-1"
            />
            <line
              x1="80"
              y1="130"
              x2="110"
              y2="130"
              stroke="#43A047"
              stroke-width="2"
              class="animate-typing-2"
            />
            <line
              x1="80"
              y1="140"
              x2="115"
              y2="140"
              stroke="#43A047"
              stroke-width="2"
              class="animate-typing-3"
            />
            <!-- Arm Left -->
            <path
              d="M60 100 L40 120"
              stroke="#FF8A00"
              stroke-width="8"
              stroke-linecap="round"
            />
            <!-- Arm Right -->
            <path
              d="M140 100 L160 120"
              stroke="#FF8A00"
              stroke-width="8"
              stroke-linecap="round"
            />
          </svg>
        </div>
      </div>
    </div>

    <!-- Progress Steps -->
    <div class="w-full max-w-md px-4 flex flex-col items-center">
      <div v-for="(stage, index) in stages" :key="stage.id" class="mb-6 last:mb-0 relative w-full">
        <div class="flex items-center gap-4 relative z-10 w-full">
          <!-- Status Icon/Indicator -->
          <div class="relative flex-shrink-0">
            <div
              class="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 border-2"
              :class="[
                index < currentStage
                  ? 'bg-[#43A047] border-[#43A047] text-black shadow-[0_0_8px_1px_rgba(67,160,71,0.5)]'
                  : index === currentStage
                  ? 'bg-[#FF8A00] border-[#FF8A00] text-black shadow-[0_0_8px_1px_rgba(255,138,0,0.5)] animate-pulse'
                  : 'bg-[#312F2D] border-[#4C4B4B] text-[#6D5D5D]',
              ]"
            >
              <svg
                v-if="index < currentStage"
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
              <svg
                  v-else-if="index === currentStage"
                  class="h-6 w-6 text-black animate-spin-slow"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
              >
                  <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
              </svg>
              <span v-else class="text-sm font-mono font-bold">{{ index + 1 }}</span>
            </div>
          </div>

          <!-- Stage Info -->
          <div class="flex-1 min-w-0">
            <h3
              class="font-medium text-lg transition-colors duration-300 truncate"
              :class="[
                index === currentStage
                  ? 'text-[#FF8A00]'
                  : index < currentStage
                  ? 'text-[#43A047]'
                  : 'text-[#6D5D5D]',
              ]"
            >
              {{ stage.label }}
            </h3>
            <p
              v-if="index === currentStage"
              class="text-sm text-[#E5DED7] mt-1 font-mono break-words"
            >
              {{ statusMessage || "Working..." }}
            </p>
          </div>
        </div>
        
        <!-- Connecting Line -->
        <div
            v-if="index < stages.length - 1"
            class="absolute top-10 left-5 -translate-x-1/2 w-0.5 h-[calc(100%+8px)] transition-colors duration-500 z-0"
            :class="[
              index < currentStage ? 'bg-[#43A047]' : 'bg-[#4C4B4B]',
            ]"
          ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  statusMessage: string;
  minimized?: boolean;
  mode?: "translate" | "fix";
  stage?: number; // Added explicit stage control (1-based)
}>();

defineEmits(["toggle-minimize"]);

// Enhanced translate stages based on user request
const translateStages = [
  {
    id: "analyzing",
    label: "Analyzing",
    keywords: ["reading", "detecting", "analysing", "processing", "analyzing"],
  },
  {
    id: "resolving",
    label: "Resolving Imports",
    keywords: ["resolving", "import"],
  },
  {
    id: "structure",
    label: "Building Contract Structure",
    keywords: ["structure", "contract", "interface"],
  },
  {
    id: "translating",
    label: "Translating Functions",
    keywords: ["translating", "function", "translate_evm_to_ralph"],
  },
];

// Fix mode stages
const fixStages = [
  { id: "analysing", label: "Analysing Error", keywords: ["analysing", "🔍"] },
  { id: "fixing1", label: "Fix Attempt 1", keywords: ["iteration 1"] },
  { id: "fixing2", label: "Fix Attempt 2", keywords: ["iteration 2"] },
  { id: "fixing3", label: "Fix Attempt 3", keywords: ["iteration 3"] },
  { id: "complete", label: "Complete", keywords: ["✅", "complete", "⚠️", "done"] },
];

// Select stages based on mode
const stages = computed(() => {
  return props.mode === "fix" ? fixStages : translateStages;
});

// Detect current stage based on props.stage OR status message
const currentStage = computed(() => {
  // If explicit stage is provided, use it (0-based index)
  if (props.stage !== undefined && props.stage !== null) {
      return Math.max(0, props.stage - 1); // Convert 1-based to 0-based
  }

  const message = props.statusMessage.toLowerCase();
  const currentStages = stages.value;
  
  // For fix mode, check stages in reverse order
  if (props.mode === "fix") {
    if (message.includes("✅") || message.includes("complete") || message.includes("⚠️") || message.includes("done")) {
      return 4; // Complete stage
    }
    if (message.includes("iteration 3") || message.includes("3/3")) {
      return 3;
    }
    if (message.includes("iteration 2") || message.includes("2/3")) {
      return 2;
    }
    if (message.includes("iteration 1") || message.includes("1/3") || message.includes("🔧")) {
      return 1;
    }
    if (message.includes("🔍") || message.includes("analysing")) {
      return 0;
    }
    return 0;
  }
  
  // For translate mode, use keyword matching
  for (let i = currentStages.length - 1; i >= 0; i--) {
    const stage = currentStages[i];
    if (stage && stage.keywords.some((keyword) => message.includes(keyword))) {
      return i;
    }
  }

  return 0; // Default to first stage
});

const currentStageLabel = computed(() => {
  return stages.value[currentStage.value]?.label || "Processing";
});
</script>

<style scoped>
@keyframes pulse-subtle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}
@keyframes blink {
  0%, 90%, 100% { transform: scaleY(1); }
  95% { transform: scaleY(0.1); }
}
@keyframes ping-slow {
  0% { transform: scale(1); opacity: 1; }
  75%, 100% { transform: scale(2); opacity: 0; }
}
@keyframes typing-1 {
  0%, 100% { stroke-dasharray: 0 40; }
  33% { stroke-dasharray: 40 0; }
}
@keyframes typing-2 {
  0%, 100% { stroke-dasharray: 0 30; }
  66% { stroke-dasharray: 30 0; }
}
@keyframes typing-3 {
  0%, 100% { stroke-dasharray: 0 35; }
  99% { stroke-dasharray: 35 0; }
}
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-pulse-subtle { animation: pulse-subtle 3s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
.animate-blink { animation: blink 4s infinite; transform-origin: center; }
.animate-ping-slow { animation: ping-slow 2s cubic-bezier(0, 0, 0.2, 1) infinite; }
.animate-typing-1 { animation: typing-1 2s infinite; }
.animate-typing-2 { animation: typing-2 2s infinite 0.5s; }
.animate-typing-3 { animation: typing-3 2s infinite 1s; }
.animate-spin-slow { animation: spin-slow 3s linear infinite; }
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #4C4B4B; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #6D5D5D; }
</style>
