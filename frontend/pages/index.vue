<!-- This is now the single root component for the app -->
<template>
  <NuxtLayout name="default">
    <template #header
      ><h1
        :class="{ 'opacity-0 pointer-events-none hidden': isScrolled }"
        class="text-[44px] h-[135px] xs:h-auto xs:text-[48px] leading-none font-extrabold font-bold mb-[60px] text-[#E5DED7] transition-opacity duration-300"
      >
        Translate your EVM code to Ralph
      </h1></template
    >
    <div
      :class="{ 'opacity-0 pointer-events-none hidden': isScrolled }"
      class="absolute w-[calc(100%-1px)] rotate-2 top-[320px] xs:top-[280px] lg:top-[250px] bg-gradient-to-r from-[#EF8510] to-[#FCA545] left-0 right-0 text-[#191817] font-extrabold text-[length:24px] [&>span]:leading-none py-2 sm:py-3 overflow-hidden whitespace-nowrap mb-8 z-10 max-w-full transition-opacity duration-300"
      style="overflow-x: hidden"
    >
      <div class="animate-marquee flex items-center min-w-full w-full">
        <span class="mx-4">V2 RELEASE</span>
        <span class="mx-4 inline-block">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="17"
            height="17"
            viewBox="0 0 17 17"
            fill="none"
          >
            <path
              d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
              fill="#191817"
            />
          </svg>
        </span>
        <span class="mx-4">TRY RALPH'S BEST FRIEND</span>
        <span class="mx-4 inline-block">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="17"
            height="17"
            viewBox="0 0 17 17"
            fill="none"
          >
            <path
              d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
              fill="#191817"
            />
          </svg>
        </span>
        <span class="mx-4">YOUR EVM CODE TO RALPH</span>
        <span class="mx-4 inline-block">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="17"
            height="17"
            viewBox="0 0 17 17"
            fill="none"
          >
            <path
              d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
              fill="#191817"
            />
          </svg>
        </span>
        <span class="mx-4">TRY RALPH'S BEST FRIEND</span>
        <span class="mx-4 inline-block">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="17"
            height="17"
            viewBox="0 0 17 17"
            fill="none"
          >
            <path
              d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
              fill="#191817"
            />
          </svg>
        </span>
        <!-- Repeat for continuous scroll -->
        <span class="mx-4">BETTER AND SMARTER</span>
        <span class="mx-4 inline-block">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="17"
            height="17"
            viewBox="0 0 17 17"
            fill="none"
          >
            <path
              d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
              fill="#191817"
            />
          </svg>
        </span>
        <span class="mx-4">TRY RALPH'S BEST FRIEND</span>
        <span class="mx-4 inline-block">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="17"
            height="17"
            viewBox="0 0 17 17"
            fill="none"
          >
            <path
              d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
              fill="#191817"
            />
          </svg>
        </span>
        <span class="mx-4">YOUR EVM CODE TO RALPH</span>
        <span class="mx-4 inline-block">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="17"
            height="17"
            viewBox="0 0 17 17"
            fill="none"
          >
            <path
              d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
              fill="#191817"
            />
          </svg>
        </span>
        <span class="mx-4">TRY RALPH'S BEST FRIEND</span>
        <span class="mx-4 inline-block">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="17"
            height="17"
            viewBox="0 0 17 17"
            fill="none"
          >
            <path
              d="M12.8003 8.50219L16.2587 11.803L12.6236 15.6236L9.09359 11.5365L6.86821 16.6358L2.38891 14.0424L4.77901 10.1946L0.63489 9.18036L1.94633 4.39234L5.48116 5.61409L4.77367 0.964481L9.94282 0.0931173L10.4181 5.15525L13.4365 2.21153L16.3614 6.53744L12.8003 8.50219Z"
              fill="#191817"
            />
          </svg>
        </span>
      </div>
    </div>
    <!-- Main Content Area -->
    <div
      class="flex-1 flex flex-col lg:flex-row gap-4 lg:gap-8"
      :class="{ 'pt-5 sm:pt-[40px] lg:pt-[60px]': !isScrolled }"
    >
      <!-- Source Code Panel (Left) -->
      <div
        class="flex-1 flex flex-col gap-y-6 overflow-hidden p-1 h-[690px] min-h-[690px]"
      >
        <h2 class="text-[20px] font-medium text-white">EVM Source Code</h2>
        <div
          class="flex-1 flex flex-col p-5 rounded-[12px] border border-[#6D5D5D] bg-[#242322] focus-within:shadow-[0_0_6px_1px_#E5DED7] overflow-hidden"
        >
          <textarea
            v-model="sourceCode"
            class="flex-1 w-full rounded-md placeholder:opacity-60 font-menlo placeholder:font-menlo placeholder:text-[length:18px] text-[length:16px] bg-inherit text-gray-200 resize-none ring-0 outline-none"
            placeholder="Paste your EVM code here ⬇️"
          ></textarea>
          <div
            class="relative mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          >
            <div
              v-if="consentOpen"
              class="absolute -translate-y-[100%] -top-[16px] p-3 pl-6 w-full flex items-center justify-between gap-x-[10px] bg-[#2A231A] rounded-[10px] border border-[#EF8510] shadow-[0_0_6px_1px_rgba(239,133,16,0.70)]"
            >
              <p
                class="text-[#EF8510] text-[length:16px] font-semibold leading-6"
              >
                By clicking <span class="text-[#F3BA7B]">Translate</span>, you
                consent to
                <a
                  href="/tos"
                  target="_blank"
                  class="underline text-[#F3BA7B] hover:text-[#EF8510]"
                  >Terms of Service</a
                >
                and
                <a
                  href="/privacy"
                  target="_blank"
                  class="underline text-[#F3BA7B] hover:text-[#EF8510]"
                  >privacy&nbsp;policy</a
                >.
              </p>
              <button class="h-fit w-fit" @click="closeConsent">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="20"
                  height="21"
                  viewBox="0 0 20 21"
                  fill="none"
                >
                  <path
                    d="M15 5.34399L5 15.344"
                    stroke="#EF8510"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M5 5.34399L15 15.344"
                    stroke="#EF8510"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </button>
            </div>
            <div class="flex items-center gap-x-[18px] text-sm text-gray-400">
              <!-- Translation Options Popover -->
              <div class="relative flex items-center">
                <Popover>
                  <PopoverTrigger
                    class="text-sm text-[#E5DED7] hover:text-[#FF8A00] transition-colors self-end p-1.5 rounded-[10px] border border-[#4C4B4B] hover:border-[#FF8A00] shadow-[0_0_6px_2px_rgba(229,222,215,0.20)]"
                    title="Translation Options"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="24"
                      height="25"
                      viewBox="0 0 24 25"
                      fill="none"
                    >
                      <path
                        d="M11.5 8.84424V4.84424"
                        stroke="currentColor"
                        stroke-linecap="round"
                      />
                      <path
                        d="M6.5 14.8442V18.8442"
                        stroke="currentColor"
                        stroke-linecap="round"
                      />
                      <path
                        d="M16.4996 16.844L16.4996 18.8442"
                        stroke="currentColor"
                        stroke-linecap="round"
                      />
                      <path
                        d="M11.5 18.8442V12.8442"
                        stroke="currentColor"
                        stroke-linecap="round"
                      />
                      <path
                        d="M6.5 4.84424V10.8442"
                        stroke="currentColor"
                        stroke-linecap="round"
                      />
                      <path
                        d="M16.5 4.84424V12.8442"
                        stroke="currentColor"
                        stroke-linecap="round"
                      />
                      <path
                        d="M9.5 8.84424L13.5 8.84424"
                        stroke="currentColor"
                        stroke-linecap="round"
                      />
                      <path
                        d="M4.5 14.8442L8.5 14.8442"
                        stroke="currentColor"
                        stroke-linecap="round"
                      />
                      <path
                        d="M14.5 16.8442H18.5"
                        stroke="currentColor"
                        stroke-linecap="round"
                      />
                    </svg>
                  </PopoverTrigger>

                  <PopoverContent
                    align="start"
                    :side-offset="6"
                    side="top"
                    class="flex flex-col gap-y-4 font-sans text-[#E5DED7] text-[length:16px] p-4 rounded-[10px] border border-[#E5DED7] bg-[#312F2D] shadow-[0_0_6px_2px_rgba(229,222,215,0.20)]"
                  >
                    <div class="flex items-center gap-3">
                      <Checkbox
                        id="optimize"
                        :model-value="options.optimize"
                        @update:model-value="
                          (val) => (options.optimize = Boolean(val))
                        "
                        class="custom-checkbox"
                      />
                      <Label for="optimize" class="checkbox-label"
                        >Optimize Code</Label
                      >
                    </div>
                    <div class="flex items-center gap-3">
                      <Checkbox
                        id="includeComments"
                        :model-value="options.includeComments"
                        @update:model-value="
                          (val) => (options.includeComments = Boolean(val))
                        "
                        class="custom-checkbox"
                      />
                      <Label for="includeComments" class="checkbox-label"
                        >Include Comments</Label
                      >
                    </div>
                    <div class="flex items-center gap-3">
                      <Checkbox
                        id="mimicDefaults"
                        :model-value="options.mimicDefaults"
                        @update:model-value="
                          (val) => (options.mimicDefaults = Boolean(val))
                        "
                        class="custom-checkbox"
                      />
                      <Label for="mimicDefaults" class="checkbox-label"
                        >Mimic Solidity Defaults</Label
                      >
                    </div>
                    <div class="flex items-center gap-3">
                      <Checkbox
                        id="translateERC20"
                        :model-value="options.translateERC20"
                        @update:model-value="
                          (val) => (options.translateERC20 = Boolean(val))
                        "
                        class="custom-checkbox"
                      />
                      <Label for="translateERC20" class="checkbox-label"
                        >Translate ERC20 transfers</Label
                      >
                    </div>
                    <hr class="my-0 border-t border-[#4C4B4B] opacity-60" />
                    <div class="flex items-center gap-3">
                      <Checkbox
                        id="autoCompile"
                        :model-value="options.autoCompile"
                        @update:model-value="
                          (val) => (options.autoCompile = Boolean(val))
                        "
                        class="custom-checkbox"
                      />
                      <Label for="autoCompile" class="checkbox-label"
                        >Auto-compile</Label
                      >
                    </div>
                    <div class="flex items-center gap-3">
                      <Checkbox
                        id="smart"
                        :model-value="options.smart"
                        @update:model-value="
                          (val) => (options.smart = Boolean(val))
                        "
                        class="custom-checkbox"
                      />
                      <Label for="smart" class="checkbox-label"
                        >Smarter (thinking)</Label
                      >
                    </div>
                    <div class="flex items-center gap-3">
                      <Checkbox
                        id="showGasEstimates"
                        :model-value="options.showGasEstimates"
                        @update:model-value="
                          (val) => (options.showGasEstimates = Boolean(val))
                        "
                        class="custom-checkbox"
                      />
                      <Label for="showGasEstimates" class="checkbox-label"
                        >Show gas estimates</Label
                      >
                    </div>
                  </PopoverContent>
                </Popover>
              </div>
              <span class="text-[length:14px] text-[#9E9992]"
                >Ralph version: After Danube</span
              >
            </div>
            <button
              @click="translateCode"
              :disabled="loading"
              :class="[
                'w-full sm:w-[294px] font-bold py-3 px-6 rounded-[10px] shadow-[0_0_6px_2px_rgba(239,133,16,0.7)] focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-opacity-75 transition-all duration-300 ease-in-out',
                !!outputCode && !loading
                  ? 'bg-transparent border-2 border-[#FBA444] text-[#FBA444] hover:bg-[#FBA444] hover:text-black'
                  : 'bg-[#FF8A00] hover:bg-orange-600 text-black',
              ]"
            >
              {{ loading ? "Translating..." : "Translate" }}
            </button>
          </div>
        </div>
      </div>
      <!-- Output Panel (Right) -->
      <div
        class="flex-1 flex flex-col gap-y-6 overflow-hidden p-1 h-[690px] min-h-[690px]"
      >
        <h2 class="text-[20px] font-medium text-white">Ralph Output</h2>
        <div
          class="flex-1 flex flex-col rounded-[12px] p-5 border border-[#6D5D5D] bg-[#242322] overflow-hidden"
        >
          <div class="relative flex-1 flex flex-col overflow-hidden">
             <!-- Progress Overlay -->
            <div 
              v-if="loading && !progressMinimized"
              class="absolute inset-0 z-30 p-0"
            >
              <TranslationProgress
                :status-message="currentActivity"
                :minimized="progressMinimized"
                :mode="progressMode"
                :stage="currentProgressStep"
                @toggle-minimize="progressMinimized = !progressMinimized"
              />
            </div>
            <!-- Minimized Progress Indicator -->
            <TranslationProgress
              v-if="loading && progressMinimized"
              :status-message="currentActivity"
              :minimized="true"
              :mode="progressMode"
              :stage="currentProgressStep"
              @toggle-minimize="progressMinimized = !progressMinimized"
            />

            <!-- Agent Tool Status Overlay (Removed as per user request) -->
            <!-- Simple loading spinner REMOVED -->
            <div
              ref="outputContainer"
              class="flex-1 overflow-auto custom-scrollbar"
            >
              <!-- Show streaming code output during loading -->
              <CodeViewerWithAnnotations 
                v-if="outputCode" 
                :code="outputCode" 
                :loading="loading"
                :gas-annotations="gasLineAnnotations"
                :minimal-gas="gasResponse?.minimal_gas ?? 20000"
                @update:line-map="handleLineMapUpdate"
              />
              <div
                v-if="!outputCode && !loading && !errors.length"
                class="text-gray-500 text-[length:18px] font-menlo"
              >
                Translation will appear here ✨
              </div>
              <!-- Success Display Section -->
              <section v-if="successMessage && !loading" class="mt-2 p-1">
                <div
                  class="absolute bottom-0 left-0 right-0 text-green-400 border-green-400 bg-[#1A2A1A] text-[length:16px] font-semibold rounded-[10px] py-3 px-6 border shadow-[0_0_6px_1px_rgba(239,133,16,0.70)] max-h-32 overflow-y-auto"
                >
                  <ul>
                    <li class="font-mono text-xs">{{ successMessage }}</li>
                  </ul>
                </div>
              </section>
            </div>
            <!-- Messages Section (Pinned to bottom) -->
            <div class="absolute bottom-0 left-0 right-0 flex flex-col gap-1 items-stretch z-10 pointer-events-none">
              <!-- Error Display Section -->
              <div
                v-if="errors.length > 0 && !loading && errorsOpen"
                class="pointer-events-auto p-3 pl-6 flex gap-x-[10px] bg-[#2A1A1A] rounded-[10px] border border-[#E15959] shadow-[0_0_6px_1px_rgba(225,89,89,0.70)] mx-2 mb-1"
              >
                <div class="flex-1 max-h-32 overflow-y-auto">
                  <ul
                    class="text-[#E15959] text-[length:16px] font-semibold leading-6"
                  >
                    <li
                      v-for="(error, index) in errors"
                      :key="index"
                      class="font-mono text-xs"
                    >
                      {{ error }}
                    </li>
                  </ul>
                </div>
                <button class="h-fit w-fit" @click="closeErrors">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="21"
                    viewBox="0 0 20 21"
                    fill="none"
                  >
                    <path
                      d="M15 5.34399L5 15.344"
                      stroke="#E15959"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                    <path
                      d="M5 5.34399L15 15.344"
                      stroke="#E15959"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </button>
              </div>

              <!-- Warning Display Section -->
              <div
                v-if="warnings.length > 0 && !loading && warningsOpen"
                class="pointer-events-auto p-3 pl-6 flex gap-x-[10px] bg-[#2A1A1A] rounded-[10px] border border-[#EF8510] shadow-[0_0_6px_1px_rgba(239,133,16,0.70)] mx-2 mb-2"
              >
                <div class="flex-1 max-h-32 overflow-y-auto">
                  <ul
                    class="text-[#EF8510] text-[length:16px] font-semibold leading-6"
                  >
                    <li
                      v-for="(warning, index) in warnings"
                      :key="index"
                      class="font-mono text-xs"
                    >
                      Warning: {{ warning }}
                    </li>
                  </ul>
                </div>
                <button class="h-fit w-fit" @click="closeWarnings">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="21"
                    viewBox="0 0 20 21"
                    fill="none"
                  >
                    <path
                      d="M15 5.34399L5 15.344"
                      stroke="#EF8510"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                    <path
                      d="M5 5.34399L15 15.344"
                      stroke="#EF8510"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <div
            v-if="outputCode && !loading"
            class="mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          >
            <button
              v-if="outputCode && !loading"
              @click="copyTranslatedCode"
              class="w-fit text-sm text-[#E5DED7] hover:text-[#FF8A00] transition-colors p-1.5 rounded-[10px] border border-[#4C4B4B] hover:border-[#FF8A00] shadow-[0_0_6px_2px_rgba(229,222,215,0.20)]"
              title="Copy to clipboard"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6 inline"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1"
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
            </button>
            <div class="flex flex-row gap-2 w-full sm:w-auto justify-end">
              <button
                v-if="!compiled && !options.autoCompile"
                title="Compile the contract to check for errors"
                @click="compileTranslatedCode"
                :disabled="loading"
                class="w-full sm:w-[180px] bg-[#191817] border-2 border-[#FBA444] text-[#FBA444] hover:bg-[#FBA444] hover:text-black font-bold py-3 px-6 rounded-[10px] shadow-[0_0_6px_2px_rgba(239,133,16,0.70)] focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-opacity-75 transition-all duration-300 ease-in-out"
              >
                {{ "Compile" }}
              </button>
              <button
                v-if="compiled && errors.length > 0"
                title="Try to fix the errors with another iteration"
                @click="upgradeTranslatedCode"
                :disabled="loading"
                class="w-full sm:w-[180px] bg-[#191817] border-2 border-[#FBA444] text-[#FBA444] hover:bg-[#FBA444] hover:text-black font-bold py-3 px-6 rounded-[10px] shadow-[0_0_6px_2px_rgba(239,133,16,0.70)] focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-opacity-75 transition-all duration-300 ease-in-out"
              >
                {{ "Retranslate" }}
              </button>
              <button
                @click="downloadTranslatedCode"
                :disabled="loading"
                class="w-full sm:w-[294px] bg-[#FBA444] hover:bg-[#FF8A00] text-[#191817] font-bold py-3 px-6 rounded-[10px] shadow-[0_0_6px_2px_rgba(239,133,16,0.70)] focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-opacity-75 transition-all duration-300 ease-in-out"
              >
                {{ "Download translated code" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="py-[80px] flex flex-col items-center max-w-[516px] mx-auto">
      <h2
        class="text-[length:28px] xs:text-[length:36px] font-medium text-white mb-5 text-center"
      >
        Looking to build innovative blockchain products?
      </h2>
      <p class="text-white text-[length:16px] mb-[36px] text-center">
        Discover our cutting-edge suite of web3 and AI solutions designed for
        developers and blockchain innovators.
      </p>
      <a
        href="https://blockchain-collab.com/alephium"
        target="_blank"
        rel="noopener noreferrer"
        :class="[
          'w-full sm:w-[294px] text-center font-bold py-3 px-6 rounded-[10px] shadow-[0_0_6px_2px_rgba(239,133,16,0.7)] focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-opacity-75 transition-all duration-300 ease-in-out',
          !!outputCode && !loading
            ? 'bg-transparent border-2 border-[#FBA444] text-[#FBA444] hover:bg-[#FBA444] hover:text-black'
            : 'bg-[#FF8A00] hover:bg-orange-600 text-black',
        ]"
      >
        Explore Blockchain Collab
      </a>
    </div>
    <template #outer-content>
      <div class="absolute top-0 right-0">
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
      <div class="absolute bottom-0 right-0">
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
      <div class="absolute bottom-[200px] right-0">
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
    </template>
  </NuxtLayout>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, computed } from "vue";
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
import {
  translateCode as apiTranslateCode,
  compileTranslatedCode as apiCompileTranslatedCode,
  fixRalphCode,
} from "@/lib/api";
import type { PreviousTranslation } from "@/lib/api";
import CodeViewerWithAnnotations from "@/components/CodeViewerWithAnnotations.vue";
import { useGasEstimation } from "@/composables/useGasEstimation";

hljs.registerLanguage("rust", rust);

// State
const sourceCode = ref("");
const outputCode = ref(``);
const highlightedOutput = ref("");
const loading = ref(false);
const loadingStatus = ref("");
type ActiveTool = { id: string; name: string; input: string; };
const activeTools = ref<ActiveTool[]>([]);
const compiled = ref(false);
const upgradeCounter = ref(0);
const errors = ref<string[]>([]);
const warnings = ref<string[]>([]);
const successMessage = ref<string | null>(null);
const currentProgressStep = ref(1);
const reasoningContent = ref("");
const isThinking = ref(false);
const options = ref({
  // translation options
  optimize: false,
  includeComments: true,
  mimicDefaults: false,
  translateERC20: true, // new option for ERC20 translation
  // peripheral options
  autoCompile: false,
  smart: false,
  showGasEstimates: true, // show gas cost annotations
});
const copied = ref(false);
const isScrolled = ref(false);
const consentOpen = ref(true);
const errorsOpen = ref(true);
const warningsOpen = ref(true);
const progressMinimized = ref(false);
const progressMode = ref<"translate" | "fix">("translate");
const isLargeScreen = useMediaQuery("(min-width: 1024px)");
const outputContainer = ref<HTMLElement | null>(null);

const currentActivity = computed(() => {
  if (activeTools.value.length > 0) {
    const tool = activeTools.value[activeTools.value.length - 1];
    // Show thinking indicator for translateFunctions when reasoning is being received (but not after content starts)
    if (tool?.name === 'translateFunctions' && isThinking.value) {
      return `Thinking... (${reasoningContent.value.length} chars)`;
    }
    // Shorten input if too long
    const input = tool?.input?.length > 40 ? tool.input.substring(0, 40) + '...' : tool?.input || '';
    return `${tool?.name} (${input})`;
  }
  return loadingStatus.value;
});

const runtimeConfig = useRuntimeConfig();

// Gas estimation composable
const showGasEstimatesRef = computed(() => options.value.showGasEstimates);
const {
  lineAnnotations: gasLineAnnotations,
  response: gasResponse,
  loading: gasLoading,
  estimate: estimateGas,
  updateLineMapping,
} = useGasEstimation({
  code: outputCode,
  apiBase: runtimeConfig.public.apiBase,
  enabled: showGasEstimatesRef,
  debounceMs: 1500,
});

// Handle line mapping updates from CodeViewerWithAnnotations
// This adjusts gas line numbers when // @@@ annotation lines are removed
const handleLineMapUpdate = (lineMap: Map<number, number>) => {
  updateLineMapping(lineMap);
};

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

const closeErrors = () => {
  errorsOpen.value = false;
};

const closeWarnings = () => {
  warningsOpen.value = false;
};

const translateCodeInner = async (
  initialOutputCode: string,
  previousTranslation?: PreviousTranslation
) => {
  loading.value = true;
  loadingStatus.value = "";
  compiled.value = false;
  errors.value = [];
  warnings.value = [];
  errorsOpen.value = true;
  warningsOpen.value = true;
  successMessage.value = null;
  progressMinimized.value = false;
  currentProgressStep.value = 1;
  reasoningContent.value = "";
  isThinking.value = false;
  await apiTranslateCode({
    sourceCode: sourceCode.value,
    options: options.value,
    runtimeConfig,
    previousTranslation,
    initialOutputCode,
    setOutputCode: (val: string) => {
      outputCode.value = val;
      // Once content starts coming in, we're no longer in "thinking" mode
      if (val && val !== initialOutputCode) {
        isThinking.value = false;
      }
    },
    setLoadingStatus: (val: string) => (loadingStatus.value = val),
    setErrors: (val: string[]) => (errors.value = val),
    onReasoningChunk: (chunk: string) => {
      reasoningContent.value += chunk;
      isThinking.value = true;
    },
    onToolStart: (tool: string, input: string, run_id?: string) => {
      const id = run_id || `${tool}-${Date.now()}-${Math.random()}`;
      activeTools.value.push({ id, name: tool, input });

      // Update progress step based on tool being started
      if (tool === 'loadPreTranslatedLibrary') {
        currentProgressStep.value = 2;
      } else if (tool === 'createContract' || tool === 'createInterface') {
        currentProgressStep.value = 3;
      } else if (tool === 'translateFunctions') {
        currentProgressStep.value = 4;
      }
    },
    onToolEnd: (tool: string, success: boolean, run_id?: string) => {
      if (run_id) {
         const index = activeTools.value.findIndex(t => t.id === run_id);
         if (index > -1) activeTools.value.splice(index, 1);
      } else {
         // Fallback if no run_id (should not happen with new backend)
         const index = activeTools.value.findIndex(t => t.name === tool);
         if (index > -1) activeTools.value.splice(index, 1);
      }
    }
  });
  loading.value = false;
  activeTools.value = [];
  if (options.value.autoCompile && errors.value.length === 0) {
    await compileTranslatedCode();
  }
};

const translateCode = async () => {
  upgradeCounter.value = 0;
  return translateCodeInner("");
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
    link.download = "translated_code.ral";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  }
};

const compileTranslatedCode = async () => {
  successMessage.value = null;
  warnings.value = [];
  await apiCompileTranslatedCode({
    outputCode: outputCode.value,
    runtimeConfig,
    onError: (val: string[]) => (errors.value = val),
    onSuccess: (message?: string) => {
      errors.value = [];
      successMessage.value = message || "Compilation successful!";
    },
    onWarning: (val: string[]) => {
      warnings.value = val;
      warningsOpen.value = true;
    },
  });
  compiled.value = true;
  nextTick(() => {
    if (outputContainer.value) {
      outputContainer.value.scrollTop = outputContainer.value.scrollHeight;
    }
  });
};

const upgradeTranslatedCode = async () => {
  upgradeCounter.value++;
  
  // Use the fix API instead of retranslating from scratch
  if (errors.value.length === 0) {
    return; // No errors to fix
  }

  loading.value = true;
  progressMode.value = "fix"; // Set fix mode
  loadingStatus.value = "🔍 Analysing the error...";
  currentProgressStep.value = 1; // Reset progress step for fix mode
  compiled.value = false;
  successMessage.value = null;

  try {
    const result = await fixRalphCode({
      ralphCode: outputCode.value,
      error: errors.value.join("\n"),
      solidityCode: sourceCode.value,
      runtimeConfig,
      onCodeUpdate: (code) => {
        outputCode.value = code;
      },
      onStageUpdate: (stage, message) => {
        loadingStatus.value = message;
        
        // Update progress step based on fix stage
        if (stage === "analysing") {
          currentProgressStep.value = 1;
        } else if (message.toLowerCase().includes("iteration 1")) {
          currentProgressStep.value = 2;
        } else if (message.toLowerCase().includes("iteration 2")) {
          currentProgressStep.value = 3;
        } else if (message.toLowerCase().includes("iteration 3")) {
          currentProgressStep.value = 4;
        } else if (stage === "done") {
          currentProgressStep.value = 5;
        }
      },
    });

    outputCode.value = result.fixedCode;
    errors.value = [];
    
    if (result.success) {
      // compiled.value = true;
      successMessage.value = `Code fixed and compiled successfully in ${result.iterations} iteration(s)!`;
    } else {
      // Auto-compile to check if there are remaining errors
      if (options.value.autoCompile) {
        await compileTranslatedCode();
      }
    }
  } catch (e: any) {
    console.error("Fix error:", e);
    const errorMessage = e instanceof Error ? e.message : String(e);
    errors.value = [errorMessage];
    
    // Fallback to retranslation if fix API fails
    if (upgradeCounter.value >= 3) {
      progressMode.value = "translate"; // Switch back to translate mode
      let code = "// Not all EVM features are supported on Alephium\n";
      code += "// In some cases compiler error messages may not be sufficient to debug the issue\n";
      code += "// If you encounter problems, see supported features on GitHub or try building locally\n";
      return translateCodeInner(code, {
        source_code: outputCode.value,
        warnings: [],
        errors: errors.value,
      });
    }
  } finally {
    loading.value = false;
    progressMode.value = "translate"; // Reset to translate mode after completion
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
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: #312f2d;
  border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #9e9992;
  border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #e5ded7;
}

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
</style>
