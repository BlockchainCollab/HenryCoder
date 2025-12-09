<template>
  <!-- Desktop: Tooltip on hover -->
  <div class="hidden sm:inline-flex">
    <TooltipProvider :delay-duration="200">
      <Tooltip v-model:open="tooltipOpen">
        <TooltipTrigger as-child>
          <button
            ref="triggerRef"
            class="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-mono rounded transition-colors cursor-pointer hover:bg-[#312F2D] ml-3"
            :class="colorClass"
            :aria-label="`Gas: ${formattedGas}`"
          >
            <Fuel :size="12" :stroke-width="2" />
            <span>{{ formattedGas }}</span>
          </button>
        </TooltipTrigger>
        <TooltipContent
          side="right"
          align="start"
          :side-offset="8"
          class="max-w-[320px] bg-[#1E1D1C] border border-[#3D3B39] text-[#E5DED7] text-sm p-0 rounded-lg shadow-xl z-50"
        >
          <GasTooltipContent :annotation="annotation" :minimal-gas="minimalGas" />
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  </div>

  <!-- Mobile: Badge that opens modal -->
  <span class="inline-flex sm:hidden">
    <button
      @click="emit('open-modal', annotation)"
      class="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-mono rounded transition-colors cursor-pointer active:bg-[#312F2D] ml-3"
      :class="colorClass"
      :aria-label="`View gas details`"
    >
      <Fuel :size="12" :stroke-width="2" />
      <span>{{ formattedGas }}</span>
    </button>
  </span>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { Fuel } from 'lucide-vue-next';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import GasTooltipContent from '@/components/ui/GasTooltipContent.vue';
import { formatGas, getGasCostColor, type GasFunctionAnnotation } from '@/lib/gas-types';

interface Props {
  annotation: GasFunctionAnnotation;
  minimalGas?: number;
}

const props = withDefaults(defineProps<Props>(), {
  minimalGas: 20_000,
});

const emit = defineEmits<{
  'open-modal': [annotation: GasFunctionAnnotation];
}>();

const triggerRef = ref<HTMLElement | null>(null);
const tooltipOpen = ref(false);

const formattedGas = computed(() => formatGas(props.annotation.total_gas));
const colorClass = computed(() => getGasCostColor(props.annotation.total_gas, props.minimalGas));

// Close tooltip on any scroll event
const handleScroll = () => {
  if (tooltipOpen.value) {
    tooltipOpen.value = false;
  }
};

onMounted(() => {
  // Listen to scroll events on window and any scrollable ancestor
  window.addEventListener('scroll', handleScroll, true);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll, true);
});
</script>
