<template>
  <!-- Desktop: Tooltip on hover -->
  <div class="hidden sm:block">
    <TooltipProvider :delay-duration="200">
      <Tooltip>
        <TooltipTrigger as-child>
          <button
            class="flex items-center justify-center w-5 h-5 text-[#9E9992] hover:text-[#FF8A00] transition-colors cursor-pointer"
            :aria-label="`Annotation: ${annotation}`"
          >
            <Info :size="16" :stroke-width="2" />
          </button>
        </TooltipTrigger>
        <TooltipContent
          side="top"
          align="center"
          :side-offset="8"
          class="max-w-[300px] bg-[#312F2D] border border-[#E5DED7] text-[#E5DED7] text-sm p-3 rounded-lg shadow-lg z-50"
        >
          <p class="leading-relaxed">{{ annotation }}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  </div>

  <!-- Mobile: Icon that opens modal -->
  <div class="block sm:hidden">
    <button
      @click="emit('open-modal', annotation)"
      class="flex items-center justify-center w-5 h-5 text-[#9E9992] active:text-[#FF8A00] transition-colors cursor-pointer"
      :aria-label="`View annotation`"
    >
      <Info :size="16" :stroke-width="2" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { Info } from 'lucide-vue-next';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface Props {
  annotation: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'open-modal': [annotation: string];
}>();
</script>
