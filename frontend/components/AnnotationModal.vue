<template>
  <Sheet :open="isOpen" @update:open="emit('update:open', $event)">
    <SheetContent side="bottom" class="bg-[#1C1A19] border-t border-[#E5DED7]">
      <SheetHeader>
        <SheetTitle class="text-[#E5DED7] text-lg font-semibold">
          Code Annotation
        </SheetTitle>
      </SheetHeader>
      <div class="mt-4 mb-6">
        <p class="text-[#E5DED7] text-[16px] leading-relaxed">
          {{ annotation }}
        </p>
      </div>
      <SheetClose as-child>
        <button
          class="w-full py-3 bg-[#FF8A00] text-white font-medium rounded-lg hover:bg-[#FF8A00]/90 transition-colors"
        >
          Close
        </button>
      </SheetClose>
    </SheetContent>
  </Sheet>
</template>

<script setup lang="ts">
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetClose,
} from '@/components/ui/sheet';

interface Props {
  isOpen: boolean;
  annotation: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:open': [value: boolean];
}>();
</script>
