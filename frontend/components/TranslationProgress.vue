<template>
  <div class="flex flex-col items-center justify-center h-full py-12">
    <!-- Henry Robot Animation -->
    <div class="mb-8 relative">
      <div class="w-32 h-32 relative animate-bounce-slow">
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
              y2="35"
              stroke="#FF8A00"
              stroke-width="3"
            />
            <circle
              cx="100"
              cy="30"
              r="5"
              fill="#FF8A00"
              class="animate-ping-slow"
            />
            <!-- Arms -->
            <rect x="45" y="95" width="15" height="40" rx="4" fill="#FBA444" />
            <rect x="140" y="95" width="15" height="40" rx="4" fill="#FBA444" />
            <!-- Coding symbols -->
            <text
              x="75"
              y="110"
              font-family="monospace"
              font-size="16"
              fill="#191817"
              class="animate-typing"
            >
              &lt;/&gt;
            </text>
          </svg>
        </div>
      </div>

      <!-- Floating code symbols -->
      <div
        class="absolute -top-4 -right-4 text-[#FF8A00] text-2xl animate-float"
      >
        { }
      </div>
      <div
        class="absolute -bottom-4 -left-4 text-[#FBA444] text-2xl animate-float-delayed"
      >
        [ ]
      </div>
    </div>

    <!-- Stage Label -->
    <div class="text-center mb-6">
      <h3 class="text-xl font-semibold text-[#E5DED7] mb-2">
        {{ currentStageLabel }}
      </h3>
      <!-- <p class="text-sm text-[#9E9992]">
        {{ statusMessage }}
      </p> -->
    </div>

    <!-- Progress Bar -->
    <div class="w-full max-w-md">
      <div class="h-2 bg-[#312F2D] rounded-full overflow-hidden">
        <div
          class="h-full bg-gradient-to-r from-[#FF8A00] to-[#FBA444] rounded-full transition-all duration-500 ease-out"
          :style="{ width: `${progress}%` }"
        >
          <div
            class="h-full w-full bg-gradient-to-r from-transparent via-white to-transparent opacity-50 animate-shimmer"
          ></div>
        </div>
      </div>

      <!-- Stage Indicators -->
      <div class="flex justify-between mt-4 text-xs">
        <div
          v-for="(stage, index) in stages"
          :key="stage.id"
          class="flex flex-col items-center"
          :class="[currentStage >= index ? 'text-[#FF8A00]' : 'text-[#9E9992]']"
        >
          <div
            class="w-8 h-8 rounded-full border-2 flex items-center justify-center mb-1 transition-all duration-300"
            :class="[
              currentStage > index
                ? 'bg-[#FF8A00] border-[#FF8A00] text-[#191817]'
                : currentStage === index
                ? 'border-[#FF8A00] text-[#FF8A00] animate-pulse'
                : 'border-[#9E9992] text-[#9E9992]',
            ]"
          >
            <svg
              v-if="currentStage > index"
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clip-rule="evenodd"
              />
            </svg>
            <span v-else class="text-xs font-bold">{{ index + 1 }}</span>
          </div>
          <span class="text-center max-w-[80px]">{{ stage.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  statusMessage: string;
}

const props = defineProps<Props>();

const stages = [
  { id: "thinking", label: "Thinking", keywords: ["thinking", "analyzing"] },
  {
    id: "reading",
    label: "Reading Code",
    keywords: ["reading", "detecting", "generating", "processing"],
  },
  {
    id: "resolving",
    label: "Resolving Imports",
    keywords: ["resolving", "resolve_solidity_imports", "preparing tools"],
  },
  {
    id: "translating",
    label: "Translating",
    keywords: ["translating", "translate_evm_to_ralph"],
  },
];

// Detect current stage based on status message
const currentStage = computed(() => {
  const message = props.statusMessage.toLowerCase();
  console.log("Status Message:", message);
  for (let i = stages.length - 1; i >= 0; i--) {
    const stage = stages[i];
    if (stage && stage.keywords.some((keyword) => message.includes(keyword))) {
      return i;
    }
  }

  return 0; // Default to first stage
});

const currentStageLabel = computed(() => {
  return stages[currentStage.value]?.label || "Processing";
});

// Calculate progress (0-100)
const progress = computed(() => {
  const stageProgress = (currentStage.value / (stages.length - 1)) * 100;
  return Math.min(Math.max(stageProgress, 10), 95); // Keep between 10-95% while processing
});
</script>

<style scoped>
@keyframes bounce-slow {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes pulse-subtle {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

@keyframes blink {
  0%,
  90%,
  100% {
    opacity: 1;
  }
  95% {
    opacity: 0;
  }
}

@keyframes ping-slow {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes typing {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-15px) rotate(5deg);
  }
}

@keyframes float-delayed {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-10px) rotate(-5deg);
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.animate-bounce-slow {
  animation: bounce-slow 2s ease-in-out infinite;
}

.animate-pulse-subtle {
  animation: pulse-subtle 2s ease-in-out infinite;
}

.animate-blink {
  animation: blink 3s ease-in-out infinite;
}

.animate-ping-slow {
  animation: ping-slow 2s ease-in-out infinite;
}

.animate-typing {
  animation: typing 1.5s ease-in-out infinite;
}

.animate-float {
  animation: float 3s ease-in-out infinite;
}

.animate-float-delayed {
  animation: float-delayed 3s ease-in-out infinite 1s;
}

.animate-shimmer {
  animation: shimmer 2s ease-in-out infinite;
}
</style>
