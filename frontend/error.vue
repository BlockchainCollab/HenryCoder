<!-- ./error.vue -->
<template>
  <div class="relative h-screen bg-[#191817] p-[30px] pb-[60px] font-rubik">
    <div class="fixed top-[30px] flex items-center">
      <div class="text-[#E5DED7]">
        <p class="text-4xl font-bold leading-[29px] font-paytone">HENRY</p>
        <p class="text-4xl font-bold leading-[29px] font-paytone">CODER</p>
      </div>
      <span
        class="text-[60px] font-bold text-[#FF8A00] leading-[60px] font-sans"
        >{</span
      >
    </div>
    <div class="flex flex-col items-center justify-center h-full">
      <h1 class="text-[length:128px] font-black leading-none">
        {{ error.statusCode }}
      </h1>
      <p class="text-[length:48px] font-black leading-none">
        {{
          error.statusCode === 404 ? "Not found" : "Unexpected error occured"
        }}
      </p>
      <button
        @click="handleError"
        :class="[
          'mt-7 w-full sm:w-[294px] font-bold py-3 px-6 rounded-[10px] shadow-[0_0_6px_2px_rgba(239,133,16,0.7)] focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-opacity-75 transition-all duration-300 ease-in-out bg-transparent border-2 border-[#FBA444] text-[#FBA444] hover:bg-[#FBA444] hover:text-black',
        ]"
      >
        Go back to Henry
      </button>
    </div>
    <div class="fixed top-0 right-0">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="187"
        height="236"
        viewBox="0 0 187 236"
        fill="none"
      >
        <path
          d="M231.922 54.9325L178.866 106.177L239.39 113.691L239.984 113.765L239.806 114.336L216.964 187.695L216.802 188.218L216.296 188.009L161.628 165.396L155.528 234.789L155.485 235.287L154.987 235.243L77.6806 228.573L77.1305 228.525L77.2316 227.983L91.6237 150.642L13.341 171.714L12.8004 171.86L12.7168 171.305L1.36659 95.9994L1.28944 95.4892L1.80141 95.4286L67.2971 87.6247L41.1666 31.3059L40.9508 30.8399L41.4226 30.6364L108.498 1.7156L108.987 1.50487L109.166 2.00756L127.326 53.0749L173.7 2.8341L174.034 2.47245L174.4 2.80014L231.908 54.1999L232.309 54.558L231.922 54.9325Z"
          stroke="#EF8510"
        />
      </svg>
    </div>
    <div class="fixed bottom-0 right-0">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="355"
        height="319"
        viewBox="0 0 355 319"
        fill="none"
      >
        <path
          d="M397.894 92.2581L306.008 181.007L410.958 194.036L411.551 194.11L411.373 194.68L372.049 320.978L371.886 321.5L371.379 321.291L276.807 282.173L266.264 402.132L266.22 402.629L265.722 402.586L132.63 391.1L132.08 391.052L132.181 390.51L157.063 256.797L21.7365 293.222L21.1959 293.368L21.1116 292.814L1.57096 163.166L1.49381 162.655L2.00577 162.595L115.259 149.1L70.0629 51.6897L69.8471 51.2236L70.3189 51.0201L185.797 1.23033L186.286 1.01893L186.465 1.52162L217.93 90.0051L298.172 3.06845L298.506 2.7068L298.873 3.03448L397.88 91.5256L398.281 91.8837L397.894 92.2581Z"
          stroke="#EF8510"
        />
      </svg>
    </div>
    <div class="fixed bottom-[200px] right-0">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="227"
        height="236"
        viewBox="0 0 227 236"
        fill="none"
      >
        <path
          d="M231.362 54.752L178.306 105.997L238.83 113.511L239.424 113.585L239.246 114.156L216.404 187.515L216.242 188.037L215.736 187.829L161.068 165.215L154.968 234.609L154.925 235.106L154.427 235.063L77.1205 228.392L76.5705 228.344L76.6716 227.802L91.0636 150.462L12.781 171.534L12.2403 171.679L12.1568 171.125L0.806535 95.819L0.729386 95.3088L1.24135 95.2482L66.7371 87.4443L40.6065 31.1255L40.3907 30.6594L40.8625 30.456L107.938 1.53518L108.427 1.32445L108.606 1.82714L126.766 52.8945L173.14 2.65368L173.474 2.29203L173.84 2.61972L231.348 54.0195L231.749 54.3776L231.362 54.752Z"
          stroke="#EF8510"
          stroke-opacity="0.5"
        />
      </svg>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  error: Object,
});

const handleError = () => clearError({ redirect: "/" });
</script>
