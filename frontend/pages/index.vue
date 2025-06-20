<!-- This is now the single root component for the app -->
<template>
  <div class="relative flex flex-col h-screen w-full text-white font-rubik bg-grid-pattern overflow-hidden">
    <div @scroll="handleScroll" class="z-50 flex flex-col flex-1 p-[30px] pb-[0px] relative overflow-y-auto">
      <!-- Header -->
      <header class="pb-8 px-0 sm:px-8 text-center">
        <div class="flex items-center" :class="{ 'mb-[60px]': !isScrolled }">
          <div class="text-[#E5DED7]">
            <p class="text-4xl font-bold leading-[29px] font-paytone">HENRY</p>
            <p class="text-4xl font-bold leading-[29px] font-paytone">CODER</p>
          </div>
          <span class="text-[60px] font-bold text-[#FF8A00] leading-[60px] font-sans">{</span>
        </div>
        <h1 :class="{ 'opacity-0 pointer-events-none hidden': isScrolled }"
          class="text-[44px] h-[135px] xs:h-auto xs:text-[48px] leading-none font-extrabold font-bold mb-[60px] text-[#E5DED7] transition-opacity duration-300">
          Translate your EVM code to Ralph
        </h1>
      </header>
      <!-- Ticker -->
      <div :class="{ 'opacity-0 pointer-events-none hidden': isScrolled }"
        class="absolute w-[calc(100%-1px)] rotate-2 top-[320px] xs:top-[280px] lg:top-[250px] bg-gradient-to-r from-[#EF8510] to-[#FCA545] left-0 right-0 text-[#191817] font-extrabold text-[length:24px] [&>span]:leading-none py-2 sm:py-3 overflow-hidden whitespace-nowrap mb-8 z-10 max-w-full transition-opacity duration-300"
        style="overflow-x: hidden">
        <div class="animate-marquee flex items-center min-w-full w-full">
          <span class="mx-4">EVM CODE TO RALPH</span>
          <span class="mx-4 inline-block">
            <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 17 17" fill="none">
              <path
                d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
                fill="#191817" />
            </svg>
          </span>
          <span class="mx-4">TRY RALPH'S BEST FRIEND</span>
          <span class="mx-4 inline-block">
            <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 17 17" fill="none">
              <path
                d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
                fill="#191817" />
            </svg>
          </span>
          <span class="mx-4">YOUR EVM CODE TO RALPH</span>
          <span class="mx-4 inline-block">
            <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 17 17" fill="none">
              <path
                d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
                fill="#191817" />
            </svg>
          </span>
          <span class="mx-4">TRY RALPH'S BEST FRIEND</span>
          <span class="mx-4 inline-block">
            <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 17 17" fill="none">
              <path
                d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
                fill="#191817" />
            </svg>
          </span>
          <!-- Repeat for continuous scroll -->
          <span class="mx-4">EVM CODE TO RALPH</span>
          <span class="mx-4 inline-block">
            <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 17 17" fill="none">
              <path
                d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
                fill="#191817" />
            </svg>
          </span>
          <span class="mx-4">TRY RALPH'S BEST FRIEND</span>
          <span class="mx-4 inline-block">
            <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 17 17" fill="none">
              <path
                d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
                fill="#191817" />
            </svg>
          </span>
          <span class="mx-4">YOUR EVM CODE TO RALPH</span>
          <span class="mx-4 inline-block">
            <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 17 17" fill="none">
              <path
                d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
                fill="#191817" />
            </svg>
          </span>
          <span class="mx-4">TRY RALPH'S BEST FRIEND</span>
          <span class="mx-4 inline-block">
            <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 17 17" fill="none">
              <path
                d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
                fill="#191817" />
            </svg>
          </span>
        </div>
      </div>
      <!-- Main Content Area -->
      <main class="flex-1 flex flex-col lg:flex-row gap-4 lg:gap-8"
        :class="{ 'pt-5 sm:pt-[40px] lg:pt-[60px]': !isScrolled }">
        <!-- Source Code Panel (Left) -->
        <div class="flex-1 flex flex-col gap-y-6 overflow-hidden p-1 h-[690px] min-h-[690px]">
          <h2 class="text-[20px] font-medium text-white">EVM Source Code</h2>
          <div
            class="flex-1 flex flex-col p-5 rounded-[12px] border border-[#6D5D5D] bg-[#242322] focus-within:shadow-[0_0_6px_1px_#E5DED7] overflow-hidden">
            <textarea v-model="sourceCode"
              class="flex-1 w-full rounded-md placeholder:opacity-60 p-3 font-mono text-sm bg-inherit text-gray-200 resize-none ring-0 outline-none"
              placeholder="Paste your EVM code here ⬇️"></textarea>
            <div class="relative mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div v-if="consentOpen"
                class="absolute -translate-y-[100%] -top-[16px] p-3 pl-6 flex gap-x-[10px] bg-[#2A231A] rounded-[10px] border border-[#EF8510] shadow-[0_0_6px_1px_rgba(239,133,16,0.70)]">
                <p class="text-[#EF8510] text-[length:16px] font-semibold leading-6">
                  By clicking <span class="text-[#F3BA7B]">Translate</span>, you
                  consent to AI analysis and processing of your submitted
                  content.
                </p>
                <button class="h-fit w-fit" @click="closeConsent">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="21" viewBox="0 0 20 21" fill="none">
                    <path d="M15 5.34399L5 15.344" stroke="#EF8510" stroke-width="2" stroke-linecap="round"
                      stroke-linejoin="round" />
                    <path d="M5 5.34399L15 15.344" stroke="#EF8510" stroke-width="2" stroke-linecap="round"
                      stroke-linejoin="round" />
                  </svg>
                </button>
              </div>
              <div class="flex items-center gap-x-[18px] text-sm text-gray-400">
                <!-- Translation Options Popover -->
                <div class="relative flex items-center">
                  <Popover>
                    <PopoverTrigger
                      class="text-sm text-[#E5DED7] hover:text-[#FF8A00] transition-colors self-end p-1.5 rounded-[10px] border border-[#4C4B4B] hover:border-[#FF8A00] shadow-[0_0_6px_2px_rgba(229,222,215,0.20)]"
                      title="Translation Options">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="25" viewBox="0 0 24 25" fill="none">
                        <path d="M11.5 8.84424V4.84424" stroke="currentColor" stroke-linecap="round" />
                        <path d="M6.5 14.8442V18.8442" stroke="currentColor" stroke-linecap="round" />
                        <path d="M16.4996 16.844L16.4996 18.8442" stroke="currentColor" stroke-linecap="round" />
                        <path d="M11.5 18.8442V12.8442" stroke="currentColor" stroke-linecap="round" />
                        <path d="M6.5 4.84424V10.8442" stroke="currentColor" stroke-linecap="round" />
                        <path d="M16.5 4.84424V12.8442" stroke="currentColor" stroke-linecap="round" />
                        <path d="M9.5 8.84424L13.5 8.84424" stroke="currentColor" stroke-linecap="round" />
                        <path d="M4.5 14.8442L8.5 14.8442" stroke="currentColor" stroke-linecap="round" />
                        <path d="M14.5 16.8442H18.5" stroke="currentColor" stroke-linecap="round" />
                      </svg>
                    </PopoverTrigger>

                    <PopoverContent align="start" :side-offset="6" side="top"
                      class="flex flex-col gap-y-4 font-sans text-[#E5DED7] text-[length:16px] p-4 rounded-[10px] border border-[#E5DED7] bg-[#312F2D] shadow-[0_0_6px_2px_rgba(229,222,215,0.20)]">
                      <div class="flex items-center gap-3">
                        <Checkbox id="optimize" :model-value="options.optimize" @update:model-value="
                          (val) => (options.optimize = Boolean(val))
                          " class="custom-checkbox" />
                        <Label for="optimize" class="checkbox-label">Optimize Code</Label>
                      </div>
                      <div class="flex items-center gap-3">
                        <Checkbox id="includeComments" :model-value="options.includeComments" @update:model-value="
                          (val) => (options.includeComments = Boolean(val))
                          " class="custom-checkbox" />
                        <Label for="includeComments" class="checkbox-label">Include Comments</Label>
                      </div>
                      <div class="flex items-center gap-3">
                        <Checkbox id="mimicDefaults" :model-value="options.mimicDefaults" @update:model-value="
                          (val) => (options.mimicDefaults = Boolean(val))
                          " class="custom-checkbox" />
                        <Label for="mimicDefaults" class="checkbox-label">Mimic Solidity Defaults</Label>
                      </div>
                    </PopoverContent>
                  </Popover>
                </div>
                <span class="text-[length:14px] text-[#9E9992]">Ralph version: After Danube</span>
              </div>
              <button @click="translateCode" :disabled="loading" :class="[
                'w-full sm:w-[294px] font-bold py-3 px-6 rounded-[10px] shadow-[0_0_6px_2px_rgba(239,133,16,0.7)] focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-opacity-75 transition-all duration-300 ease-in-out',
                !!outputCode && !loading
                  ? 'bg-transparent border-2 border-[#FBA444] text-[#FBA444] hover:bg-[#FBA444] hover:text-black'
                  : 'bg-[#FF8A00] hover:bg-orange-600 text-black',
                ]">
                {{ loading ? "Translating..." : "Translate" }}
              </button>
            </div>
          </div>
        </div>
        <!-- Output Panel (Right) -->
        <div class="flex-1 flex flex-col gap-y-6 overflow-hidden p-1 h-[690px] min-h-[690px]">
          <h2 class="text-[20px] font-medium text-white">Ralph Output</h2>
          <div
            class="flex-1 flex flex-col rounded-[12px] p-4 bg-[#191817] sm:p-6 border border-[#6D5D5D] overflow-hidden">
            <div ref="outputContainer" class="flex-1 overflow-auto min-w-0">
              <pre v-if="outputCode || loading"
                class="font-mono text-sm whitespace-pre text-gray-300 w-max"><code class="hljs !bg-transparent language-rust" :class="{ 'opacity-50': loading }" v-html="highlightedOutput || (loading ? 'Translating...' : '')"></code></pre>
              <div v-if="!outputCode && !loading && !errors.length" class="text-gray-500">
                Translation will appear here ✨
              </div>
              <!-- Error Display Section (Integrated into Output Panel) -->
              <section v-if="errors.length > 0 && !loading" class="mt-2 p-1">
                <div
                  class="text-[#E15959] text-[length:16px] font-semibold bg-[#2A1A1A] rounded-[10px] py-3 px-6 border border-[#E15959] shadow-[0_0_6px_1px_rgba(239,133,16,0.70)] max-h-32 overflow-y-auto">
                  <ul>
                    <li v-for="(error, index) in errors" :key="index" class="font-mono text-xs">
                      {{ error }}
                    </li>
                  </ul>
                </div>
              </section>
            </div>
            <div v-if="outputCode && !loading"
              class="mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <button v-if="outputCode && !loading" @click="copyTranslatedCode"
                class="w-fit text-sm text-[#E5DED7] hover:text-[#FF8A00] transition-colors p-1.5 rounded-[10px] border border-[#4C4B4B] hover:border-[#FF8A00] shadow-[0_0_6px_2px_rgba(229,222,215,0.20)]"
                title="Copy to clipboard">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 inline" fill="none" viewBox="0 0 24 24"
                  stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1"
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
              <button @click="downloadTranslatedCode" :disabled="loading"
                class="w-full sm:w-[294px] bg-[#FBA444] hover:bg-[#FF8A00] text-[#191817] font-bold py-3 px-6 rounded-[10px] shadow-[0_0_6px_2px_rgba(239,133,16,0.70)] focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-opacity-75 transition-all duration-300 ease-in-out">
                {{ "Download translated code" }}
              </button>
            </div>
          </div>
        </div>
      </main>
      <div class="py-[80px] flex flex-col items-center max-w-[516px] mx-auto">
        <h2 class="text-[length:28px] xs:text-[length:36px] font-medium text-white mb-5 text-center">
          Looking for more innovative blockchain products?
        </h2>
        <p class="text-white text-[length:16px] mb-[36px] text-center">
          Browse our expanded ecosystem of blockchain and AI-driven products for
          power users and developers.
        </p>
        <a href="https://blockchain-collab.com/" target="_blank" rel="noopener noreferrer" :class="[
          'w-full sm:w-[294px] text-center font-bold py-3 px-6 rounded-[10px] shadow-[0_0_6px_2px_rgba(239,133,16,0.7)] focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-opacity-75 transition-all duration-300 ease-in-out',
          !!outputCode && !loading
            ? 'bg-transparent border-2 border-[#FBA444] text-[#FBA444] hover:bg-[#FBA444] hover:text-black'
            : 'bg-[#FF8A00] hover:bg-orange-600 text-black',
          ]">
          Explore Blockchain Collab
        </a>
      </div>
      <!-- Footer -->
      <footer class="w-full shrink-0 px-0 sm:px-8 pb-6 pt-4">
        <div class="flex justify-between items-center">
          <div class="flex items-center gap-x-2">
            <span class="text-sm text-gray-400">Powered by</span>
            <div class="flex items-center gap-x-1">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="49" viewBox="0 0 12 49" fill="none">
                <path
                  d="M5.97098 48.546H1.04833C0.784143 48.546 0.610245 48.4992 0.526641 48.4056C0.44638 48.3086 0.40625 48.1297 0.40625 47.8705V1.27929C0.40625 1.02178 0.44638 0.844541 0.526641 0.750904C0.610245 0.653923 0.784143 0.60376 1.04833 0.60376H6.15156C8.17145 0.60376 9.65627 1.17562 10.606 2.31598C11.0107 2.7942 11.3083 3.31757 11.4956 3.88775C11.6862 4.45961 11.7832 5.02979 11.7832 5.59998V18.8697C11.7832 19.4633 11.7648 20.0051 11.7297 20.495C11.6929 20.9816 11.6528 21.4247 11.6093 21.826C11.4387 22.8259 11.0224 23.5884 10.3586 24.1134C11.0224 24.6134 11.4387 25.3273 11.6093 26.2537C11.6528 26.6115 11.6929 27.0095 11.7297 27.4509C11.7648 27.889 11.7832 28.3672 11.7832 28.8889V43.5498C11.7832 44.0983 11.6862 44.6584 11.4956 45.2286C11.3083 45.8005 11.0107 46.3238 10.606 46.8004C9.58437 47.9641 8.03936 48.546 5.97098 48.546ZM6.07799 3.78074H4.01128V22.6152H6.29202C7.19662 22.6152 7.77851 22.234 8.03769 21.4715C8.15808 21.0936 8.21827 20.6655 8.21827 20.1873C8.21827 19.7108 8.21827 19.4248 8.21827 19.3312V5.63342C8.21827 5.11172 8.03936 4.67364 7.6832 4.31581C7.32537 3.95965 6.7903 3.78074 6.07799 3.78074ZM6.29202 25.645H4.01128V45.3691H6.07799C6.7903 45.3691 7.32537 45.1918 7.6832 44.834C8.03936 44.4778 8.21827 44.0381 8.21827 43.5164V28.929C8.21827 28.832 8.21827 28.5394 8.21827 28.0529C8.21827 27.5679 8.15808 27.1332 8.03769 26.7486C7.80025 26.0129 7.21836 25.645 6.29202 25.645Z"
                  fill="white" />
              </svg>
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="51" viewBox="0 0 12 51" fill="none">
                <path
                  d="M6.11363 0.928223C7.80244 0.928223 9.19362 1.4031 10.2872 2.35285C11.2854 3.28086 11.7854 4.46972 11.7854 5.91775V22.01C11.7854 22.3411 11.5847 22.5049 11.1834 22.5049H9.68522C9.32739 22.5049 8.99297 22.4113 8.68196 22.224C8.3743 22.0334 8.22046 21.7341 8.22046 21.3278V6.02476C8.22046 5.50307 8.04155 5.06498 7.68539 4.70715C7.32757 4.351 6.7925 4.17208 6.08018 4.17208C5.3662 4.17208 4.83615 4.351 4.48835 4.70715C4.1439 5.06498 3.97335 5.50307 3.97335 6.02476V45.125C3.97335 45.6467 4.15059 46.0814 4.50842 46.4292C4.86457 46.7737 5.39964 46.9442 6.11363 46.9442C6.85269 46.9442 7.38776 46.767 7.71884 46.4092C8.05325 46.053 8.22046 45.625 8.22046 45.125V29.8554C8.22046 29.4508 8.3743 29.1532 8.68196 28.9659C8.99297 28.7753 9.32739 28.6783 9.68522 28.6783H11.1433C11.5713 28.6783 11.7854 28.8455 11.7854 29.1799V45.1919C11.7854 46.6466 11.267 47.8371 10.2337 48.7635C9.19864 49.6898 7.80244 50.1547 6.04674 50.1547C4.30776 50.1547 2.92661 49.6764 1.90664 48.7234C0.884988 47.8455 0.375 46.6683 0.375 45.1919V5.91775C0.375 4.41955 0.884988 3.23237 1.90664 2.35285C2.95337 1.4031 4.35626 0.928223 6.11363 0.928223Z"
                  fill="#F08507" />
              </svg>
            </div>
          </div>
          <div>
            <a href="#" class="text-sm text-[#FCA545] hover:underline">Privacy Policy</a>
          </div>
        </div>
      </footer>
    </div>
    <div class="absolute top-0 right-0">
      <svg xmlns="http://www.w3.org/2000/svg" width="187" height="236" viewBox="0 0 187 236" fill="none">
        <path
          d="M231.922 54.9325L178.866 106.177L239.39 113.691L239.984 113.765L239.806 114.336L216.964 187.695L216.802 188.218L216.296 188.009L161.628 165.396L155.528 234.789L155.485 235.287L154.987 235.243L77.6806 228.573L77.1305 228.525L77.2316 227.983L91.6237 150.642L13.341 171.714L12.8004 171.86L12.7168 171.305L1.36659 95.9994L1.28944 95.4892L1.80141 95.4286L67.2971 87.6247L41.1666 31.3059L40.9508 30.8399L41.4226 30.6364L108.498 1.7156L108.987 1.50487L109.166 2.00756L127.326 53.0749L173.7 2.8341L174.034 2.47245L174.4 2.80014L231.908 54.1999L232.309 54.558L231.922 54.9325Z"
          stroke="#EF8510" />
      </svg>
    </div>
    <div class="absolute bottom-0 right-0">
      <svg xmlns="http://www.w3.org/2000/svg" width="355" height="319" viewBox="0 0 355 319" fill="none">
        <path
          d="M397.894 92.2581L306.008 181.007L410.958 194.036L411.551 194.11L411.373 194.68L372.049 320.978L371.886 321.5L371.379 321.291L276.807 282.173L266.264 402.132L266.22 402.629L265.722 402.586L132.63 391.1L132.08 391.052L132.181 390.51L157.063 256.797L21.7365 293.222L21.1959 293.368L21.1116 292.814L1.57096 163.166L1.49381 162.655L2.00577 162.595L115.259 149.1L70.0629 51.6897L69.8471 51.2236L70.3189 51.0201L185.797 1.23033L186.286 1.01893L186.465 1.52162L217.93 90.0051L298.172 3.06845L298.506 2.7068L298.873 3.03448L397.88 91.5256L398.281 91.8837L397.894 92.2581Z"
          stroke="#EF8510" />
      </svg>
    </div>
    <div class="absolute bottom-[200px] right-0">
      <svg xmlns="http://www.w3.org/2000/svg" width="227" height="236" viewBox="0 0 227 236" fill="none">
        <path
          d="M231.362 54.752L178.306 105.997L238.83 113.511L239.424 113.585L239.246 114.156L216.404 187.515L216.242 188.037L215.736 187.829L161.068 165.215L154.968 234.609L154.925 235.106L154.427 235.063L77.1205 228.392L76.5705 228.344L76.6716 227.802L91.0636 150.462L12.781 171.534L12.2403 171.679L12.1568 171.125L0.806535 95.819L0.729386 95.3088L1.24135 95.2482L66.7371 87.4443L40.6065 31.1255L40.3907 30.6594L40.8625 30.456L107.938 1.53518L108.427 1.32445L108.606 1.82714L126.766 52.8945L173.14 2.65368L173.474 2.29203L173.84 2.61972L231.348 54.0195L231.749 54.3776L231.362 54.752Z"
          stroke="#EF8510" stroke-opacity="0.5" />
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from "vue";
import { useMediaQuery } from "@vueuse/core";
import { createError, useRuntimeConfig } from "#imports";
import hljs from "highlight.js/lib/core";
import rust from "highlight.js/lib/languages/rust";
import "highlight.js/styles/github-dark.css";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

hljs.registerLanguage("rust", rust);

// State
const sourceCode = ref("");
const outputCode = ref(``);
const highlightedOutput = ref("");
const loading = ref(false);
const errors = ref<string[]>([]);
const options = ref({
  optimize: false,
  includeComments: true,
  mimicDefaults: false,
});
const copied = ref(false);
const isScrolled = ref(false);
const consentOpen = ref(true);
const isLargeScreen = useMediaQuery("(min-width: 1024px)");
const outputContainer = ref<HTMLElement | null>(null);

const runtimeConfig = useRuntimeConfig();

const handleScroll = (event: Event) => {
  // turn in on once animations are added
  return null; // Prevent default scroll behavior

  if (isLargeScreen.value) {
    const target = event.target as HTMLElement;
    isScrolled.value = target.scrollTop > 20;
  } else {
    isScrolled.value = false;
  }
};

// Watch for changes in outputCode to update highlightedOutput
watch(
  outputCode,
  (newValue) => {
    const el = outputContainer.value;
    // Stay at bottom if already there, otherwise stay where user scrolled to.
    // Check before DOM update.
    const isScrolledToBottom = el
      ? el.scrollHeight - el.scrollTop <= el.clientHeight + 10 // 10px tolerance
      : true;

    if (newValue) {
      try {
        highlightedOutput.value = hljs.highlight(newValue, {
          language: "rust",
          ignoreIllegals: true,
        }).value;
      } catch (e) {
        console.error("Highlighting error:", e);
        highlightedOutput.value = newValue; // Fallback to non-highlighted text
      }
    } else {
      highlightedOutput.value = "";
    }

    if (isScrolledToBottom) {
      // After DOM is updated, scroll to bottom.
      nextTick(() => {
        if (el) {
          el.scrollTop = el.scrollHeight;
        }
      });
    }
  },
  { immediate: true }
);

watch(isLargeScreen, (isLarge) => {
  if (!isLarge) {
    isScrolled.value = false;
  }
});

onMounted(() => {
  // Add marquee animation style to the document head once component is mounted
  const styleId = "custom-component-styles"; // Use a more generic ID for all custom styles
  if (!document.getElementById(styleId)) {
    const styleElement = document.createElement("style");
    styleElement.id = styleId;
    styleElement.innerHTML = `
      @keyframes marquee {
        0% { transform: translateX(0%); }
        100% { transform: translateX(-50%); }
      }
      .animate-marquee {
        display: inline-block;
        white-space: nowrap;
        animation: marquee 30s linear infinite;
      }
      .bg-grid-pattern {
        background-color: #191817; /* Base dark background */
      }
    `;
    document.head.appendChild(styleElement);
  }
});

// Functions
const closeConsent = () => {
  consentOpen.value = false;
};

const translateCode = async () => {
  loading.value = true;
  outputCode.value = ""; // Watcher will clear highlightedOutput
  errors.value = [];
  // highlightedOutput.value = ""; // No longer needed, watcher handles it

  try {
    const response = await fetch(
      `${runtimeConfig.public.apiBase}/translate/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          source_code: sourceCode.value,
          options: {
            optimize: options.value.optimize,
            include_comments: options.value.includeComments, // maps to include_comments for the API
            mimic_defaults: options.value.mimicDefaults,
          },
        }),
      }
    );

    if (!response.ok || !response.body) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Translation failed with non-JSON response" }));
      throw new Error(errorData.detail || "Translation failed");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    let buffer = "";
    outputCode.value = "";
    errors.value = [];

    while (!done) {
      const { value, done: streamDone } = await reader.read();
      done = streamDone;
      if (value) {
        buffer += decoder.decode(value, { stream: true });
        let lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.translated_code) {
              outputCode.value += data.translated_code;
            }
            if (data.warnings && data.warnings.length > 0) {
              errors.value = [
                ...errors.value,
                ...data.warnings.map((w: string) => `Warning: ${w}`),
              ];
            }
            if (data.errors && data.errors.length > 0) {
              errors.value = [
                ...errors.value,
                ...data.errors.map((e: string) => String(e)),
              ];
            }
          } catch (e) {
            // Ignore JSON parse errors for incomplete lines
          }
        }
      }
    }
    // Handle any remaining buffered line
    if (buffer.trim()) {
      try {
        const data = JSON.parse(buffer);
        if (data.translated_code) {
          outputCode.value += data.translated_code;
        }
        if (data.warnings && data.warnings.length > 0) {
          errors.value = [
            ...errors.value,
            ...data.warnings.map((w: string) => `Warning: ${w}`),
          ];
        }
        if (data.errors && data.errors.length > 0) {
          errors.value = [
            ...errors.value,
            ...data.errors.map((e: string) => String(e)),
          ];
        }
      } catch (e) {
        // Ignore
      }
    }
    // The watcher handles final highlighting based on outputCode.value
    // No need for manual highlightedOutput.value assignment here.
  } catch (e: any) {
    console.error("Translation error:", e);
    const errorMessage = e instanceof Error ? e.message : String(e);
    if (!errors.value.includes(errorMessage)) {
      errors.value.push(errorMessage);
    }
    // outputCode.value is already empty or will be set by the watcher if cleared.
    // If an error occurs, outputCode might have partial data or be empty.
    // The watcher ensures highlightedOutput reflects the current state of outputCode.
    // No need for: highlightedOutput.value = "";
  } finally {
    loading.value = false;
  }
};

const copyTranslatedCode = () => {
  if (outputCode.value) {
    navigator.clipboard
      .writeText(outputCode.value)
      .then(() => {
        copied.value = true;
        setTimeout(() => {
          copied.value = false;
        }, 2000);
      })
      .catch((err) => {
        console.error("Failed to copy: ", err);
        errors.value.push("Failed to copy code to clipboard.");
      });
  }
};

const downloadTranslatedCode = () => {
  if (outputCode.value) {
    const blob = new Blob([outputCode.value], {
      type: "text/plain;charset=utf-8",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "translated_code.ralph";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  }
};
</script>

<style scoped>
/* Scoped styles for the page */
/* Removed bg-base and bg-secondary as they are handled by Tailwind utilities or inline styles now */

/* Ensure full height for textarea if not expanding correctly */
textarea {
  min-height: 300px;
  /* Adjust as needed, or use flex-grow if parent is flex */
}

/* Custom scrollbar styling (optional, for a more polished look) */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #565656;
  border-radius: 10px;
}

::-webkit-scrollbar-thumb {
  background: #9e9992;
  /* Neon gradient for scrollbar */
  border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9e9992;
  /* Swap gradient on hover */
}

::-webkit-scrollbar-corner {
  background: rgba(0, 0, 0, 0);
}

/* Fix for ShadCN Checkbox visibility */
.custom-checkbox[data-state] {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid #4c4b4b;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, border 0.2s;
  box-shadow: 0px 0px 6px 1px rgba(229, 222, 215, 0.2);
}

.custom-checkbox[data-state="checked"] {
  background-color: #ef8510;
  border-color: #312f2d;
  box-shadow: 0 0 10px 1px rgba(239, 133, 16, 0.2);
  color: #191817;
}

.custom-checkbox .shadcn-checkbox-indicator {
  color: #312f2d;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox-label {
  font-size: 16px;
  font-weight: 400;
  color: #fff;
  user-select: none;
}

/* Global style to clip horizontal overflow for html, body, and main containers */
html,
body,
#__nuxt,
#__layout,
.app-root,
.bg-grid-pattern {
  overflow-x: hidden !important;
}
</style>
