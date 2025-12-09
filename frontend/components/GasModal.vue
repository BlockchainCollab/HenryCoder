<template>
  <Sheet :open="isOpen" @update:open="emit('update:open', $event)">
    <SheetContent side="bottom" class="bg-[#1E1D1C] border-t border-[#3D3B39] rounded-t-2xl max-h-[70vh]">
      <SheetHeader class="pb-2">
        <SheetTitle class="flex items-center gap-2 text-[#E5DED7]">
          <Fuel :size="20" class="text-[#FF8A00]" />
          Gas Estimation
        </SheetTitle>
      </SheetHeader>

      <div v-if="annotation" class="overflow-y-auto">
        <!-- Function Name -->
        <div class="mb-4">
          <div class="text-sm text-[#9E9992] mb-1">Function</div>
          <div class="text-lg font-semibold text-[#E5DED7] font-mono">
            {{ annotation.function_name }}
          </div>
          <div class="text-xs text-[#9E9992]">
            Lines {{ annotation.start_line }} - {{ annotation.end_line }}
          </div>
        </div>

        <!-- Gas Summary Cards -->
        <div class="grid grid-cols-2 gap-3 mb-4">
          <div class="bg-[#2A2928] rounded-xl p-3">
            <div class="text-xs text-[#9E9992] mb-1">Total Gas</div>
            <div class="text-2xl font-bold" :class="gasColorClass">
              {{ formattedGas }}
            </div>
          </div>
          <div class="bg-[#2A2928] rounded-xl p-3">
            <div class="text-xs text-[#9E9992] mb-1">Est. Cost</div>
            <div class="text-2xl font-bold text-[#E5DED7]">
              {{ formattedAlph }}
            </div>
            <div class="text-xs text-[#9E9992]">ALPH</div>
          </div>
        </div>

        <!-- Operations Breakdown -->
        <div v-if="annotation.breakdown.length > 0" class="mb-4">
          <div class="text-sm text-[#9E9992] mb-2">Operations Breakdown</div>
          <div class="bg-[#2A2928] rounded-xl overflow-hidden">
            <div
              v-for="(op, index) in annotation.breakdown"
              :key="index"
              class="flex items-center justify-between px-3 py-2 border-b border-[#3D3B39] last:border-b-0"
            >
              <div class="flex items-center gap-2">
                <span class="text-sm text-[#C5BEB7]">{{ op.operation }}</span>
                <span class="text-xs text-[#9E9992] bg-[#1E1D1C] px-1.5 py-0.5 rounded">
                  ×{{ op.count }}
                </span>
              </div>
              <span class="text-sm font-mono text-[#E5DED7]">
                {{ op.gas_cost.toLocaleString() }}
              </span>
            </div>
          </div>
        </div>

        <!-- Warnings -->
        <div v-if="annotation.warnings.length > 0">
          <div class="text-sm text-[#9E9992] mb-2">Notes</div>
          <div class="space-y-2">
            <div
              v-for="(warning, index) in annotation.warnings"
              :key="index"
              class="flex items-start gap-2 bg-[#2A2720] rounded-xl p-3"
            >
              <AlertTriangle :size="16" class="text-yellow-500 mt-0.5 flex-shrink-0" />
              <span class="text-sm text-yellow-400">{{ warning }}</span>
            </div>
          </div>
        </div>
      </div>
    </SheetContent>
  </Sheet>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Fuel, AlertTriangle } from 'lucide-vue-next';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { formatGas, formatAlph, getGasCostColor, type GasFunctionAnnotation } from '@/lib/gas-types';

interface Props {
  isOpen: boolean;
  annotation: GasFunctionAnnotation | null;
  minimalGas?: number;
}

const props = withDefaults(defineProps<Props>(), {
  minimalGas: 20_000,
});

const emit = defineEmits<{
  'update:open': [value: boolean];
}>();

const formattedGas = computed(() => 
  props.annotation ? formatGas(props.annotation.total_gas) : ''
);

const formattedAlph = computed(() => 
  props.annotation ? formatAlph(props.annotation.estimated_cost_alph) : ''
);

const gasColorClass = computed(() => 
  props.annotation ? getGasCostColor(props.annotation.total_gas, props.minimalGas) : ''
);
</script>
