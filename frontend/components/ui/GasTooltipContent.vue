<template>
  <div class="p-3">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3 pb-2 border-b border-[#3D3B39]">
      <div class="flex items-center gap-2">
        <Fuel :size="16" class="text-[#FF8A00]" />
        <span class="font-semibold text-[#E5DED7]">{{ annotation.function_name }}</span>
      </div>
      <span class="text-xs text-[#9E9992]">
        Lines {{ annotation.start_line }}-{{ annotation.end_line }}
      </span>
    </div>

    <!-- Gas Summary -->
    <div class="grid grid-cols-2 gap-3 mb-3">
      <div class="bg-[#2A2928] rounded-lg p-2">
        <div class="text-xs text-[#9E9992] mb-1">Total Gas</div>
        <div class="text-lg font-bold" :class="gasColorClass">
          {{ formattedGas }}
        </div>
      </div>
      <div class="bg-[#2A2928] rounded-lg p-2">
        <div class="text-xs text-[#9E9992] mb-1">Est. Cost</div>
        <div class="text-lg font-bold text-[#E5DED7]">
          {{ formattedAlph }} <span class="text-xs font-normal text-[#9E9992]">ALPH</span>
        </div>
      </div>
    </div>

    <!-- Top Operations -->
    <div v-if="annotation.breakdown.length > 0" class="mb-2">
      <div class="text-xs text-[#9E9992] mb-1.5">Top Operations</div>
      <div class="space-y-1">
        <div
          v-for="(op, index) in annotation.breakdown.slice(0, 3)"
          :key="index"
          class="flex items-center justify-between text-xs"
        >
          <span class="text-[#C5BEB7] truncate max-w-[180px]">{{ op.operation }}</span>
          <span class="text-[#9E9992] font-mono">{{ formatGasValue(op.gas_cost) }}</span>
        </div>
      </div>
    </div>

    <!-- Warnings -->
    <div v-if="annotation.warnings.length > 0" class="mt-2 pt-2 border-t border-[#3D3B39]">
      <div class="flex items-start gap-1.5">
        <AlertTriangle :size="12" class="text-yellow-500 mt-0.5 flex-shrink-0" />
        <span class="text-xs text-yellow-400">
          {{ annotation.warnings[0] }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Fuel, AlertTriangle } from 'lucide-vue-next';
import { formatGas, formatAlph, getGasCostColor, type GasFunctionAnnotation } from '@/lib/gas-types';

interface Props {
  annotation: GasFunctionAnnotation;
  minimalGas?: number;
}

const props = withDefaults(defineProps<Props>(), {
  minimalGas: 20_000,
});

const formattedGas = computed(() => formatGas(props.annotation.total_gas));
const formattedAlph = computed(() => formatAlph(props.annotation.estimated_cost_alph));
const gasColorClass = computed(() => getGasCostColor(props.annotation.total_gas, props.minimalGas));

function formatGasValue(gas: number): string {
  return gas.toLocaleString();
}
</script>
