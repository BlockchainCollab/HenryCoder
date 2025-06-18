<template>
    <div class="flex h-screen w-full bg-gradient-to-br from-base to-gray-900 font-sans">
      <!-- Collapsible Sidebar for Options -->
      <div class="flex flex-col transition-all duration-300 ease-in-out" :class="{ 'w-64': sidebarOpen, 'w-12': !sidebarOpen }">
        <div class="flex h-full flex-col bg-base bg-opacity-80 backdrop-blur-md shadow-neon-blue rounded-r-lg text-gray-300">
          <!-- Sidebar Toggle Button -->
          <div class="flex items-center p-4 border-b border-gray-700">
            <button @click="toggleSidebar" class="focus:outline-none text-neon-pink hover:text-neon-blue transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path v-if="sidebarOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            </button>
            <h1 class="ml-2 text-xl font-semibold text-gradient-neon" v-if="sidebarOpen">Options</h1>
          </div>
          
          <!-- Sidebar Content -->
          <div class="overflow-y-auto flex-grow" v-if="sidebarOpen">
            <div class="p-4 text-gray-300">
              <div class="mb-6">
                <h2 class="font-medium mb-3 text-neon-blue">Translation Settings</h2>
                <div class="space-y-3">
                  <div class="flex items-center">
                    <input id="optimize" type="checkbox" v-model="options.optimize" 
                      class="mr-2 h-4 w-4 text-neon-pink focus:ring-neon-pink border-gray-600 rounded bg-gray-700 checked:bg-neon-pink transition-all">
                    <label for="optimize" class="hover:text-neon-pink cursor-pointer">Optimize Code</label>
                  </div>
                  <div class="flex items-center">
                    <input id="comments" type="checkbox" v-model="options.includeComments" 
                      class="mr-2 h-4 w-4 text-neon-pink focus:ring-neon-pink border-gray-600 rounded bg-gray-700 checked:bg-neon-pink transition-all">
                    <label for="comments" class="hover:text-neon-pink cursor-pointer">Include Comments</label>
                  </div>
                  <div class="flex items-center">
                    <input id="mimic-defaults" type="checkbox" v-model="options.mimicDefaults" 
                      class="mr-2 h-4 w-4 text-neon-pink focus:ring-neon-pink border-gray-600 rounded bg-gray-700 checked:bg-neon-pink transition-all">
                    <label for="mimic-defaults" class="hover:text-neon-pink cursor-pointer">Mimic Solidity Defaults</label>
                  </div>
                </div>
              </div>
              
              <div class="mb-6">
                <h2 class="font-medium mb-3 text-neon-blue">Additional Options</h2>
                <div class="space-y-2">
                  <select v-model="options.targetVersion" 
                    class="block w-full border-gray-600 rounded-md shadow-sm focus:border-neon-blue focus:ring focus:ring-neon-blue focus:ring-opacity-50 bg-gray-700 text-gray-200 py-2 px-3 hover:border-neon-pink transition-colors">
                    <option value="latest">Latest Ralph Version</option>
                    <option value="stable">Stable Ralph Version</option>
                    <option value="legacy">Legacy Version</option>
                  </select>
                </div>
              </div>
              
              <button 
                @click="translateCode" 
                :disabled="loading"
                class="w-full bg-gradient-to-r from-neon-pink to-neon-blue hover:from-pink-500 hover:to-blue-400 text-white font-bold py-3 px-4 rounded-lg shadow-md hover:shadow-neon-pink focus:outline-none focus:ring-2 focus:ring-neon-blue focus:ring-opacity-75 transition-all duration-300 ease-in-out transform hover:scale-105">
                {{ loading ? 'Translating...' : 'Translate' }}
              </button>
            </div>
          </div>
        </div>
      </div>
  
      <!-- Main Content Area -->
      <div class="flex flex-1 flex-col overflow-hidden p-4">
        <!-- Header -->
        <header class="bg-base bg-opacity-50 backdrop-blur-sm shadow-neon-pink rounded-lg mb-4">
          <div class="px-6 py-4">
            <h1 class="text-3xl font-bold text-gradient-neon">HenryCoder: Ralph's Best Friend</h1>
          </div>
        </header>
  
        <!-- Main Content -->
        <main class="flex flex-1 overflow-hidden gap-4">
          <!-- Source Code Panel (Left) -->
          <div class="w-1/2 overflow-y-auto border border-neon-blue rounded-lg p-4 bg-base bg-opacity-70 backdrop-blur-md shadow-lg">
            <h2 class="mb-3 text-lg font-medium text-neon-blue">EVM Source Code</h2>
            <textarea 
              v-model="sourceCode" 
              class="h-full w-full rounded-md border border-gray-600 p-3 font-mono text-sm focus:border-neon-pink focus:ring-1 focus:ring-neon-pink focus:outline-none bg-gray-800 text-gray-200 resize-none"
              placeholder="Paste your EVM code here..."></textarea>
          </div>
  
          <!-- Output Panel (Right) -->
          <div class="w-1/2 overflow-y-auto border border-neon-pink rounded-lg p-4 bg-base bg-opacity-70 backdrop-blur-md shadow-lg">
            <div class="flex items-center mb-3">
              <h2 class="text-lg font-medium text-neon-pink">Ralph Output</h2>
              <button
                v-if="outputCode"
                @click="copyTranslatedCode"
                class="bg-gradient-to-r from-neon-blue to-neon-pink hover:from-blue-400 hover:to-pink-500 text-white font-bold py-2 px-4 rounded-lg shadow-md hover:shadow-neon-pink focus:outline-none focus:ring-2 focus:ring-neon-pink focus:ring-opacity-75 transition-all duration-300 ease-in-out transform hover:scale-105 ml-auto"
              >
                {{ copied ? 'Copied!' : 'Copy' }}
              </button>
            </div>
            <div class="h-[calc(100%-2.5rem)] overflow-auto rounded-md border border-gray-600 bg-gray-800 p-3">
              <pre class="font-mono text-sm whitespace-pre-wrap text-gray-300"><code class="hljs language-rust" v-html="highlightedOutput || 'Translation will appear here...'"></code></pre>
            </div>
          </div>
        </main>
  
        <!-- Error Display Section -->
        <section v-if="errors.length > 0" class="mt-4 p-4 bg-red-900 bg-opacity-70 backdrop-blur-md border border-red-500 rounded-lg shadow-lg text-red-300">
          <h2 class="text-xl font-semibold mb-2 text-red-400">Errors / Warnings</h2>
          <div class="max-h-40 overflow-y-auto">
            <ul>
              <li v-for="(error, index) in errors" :key="index" class="font-mono text-sm">{{ error }}</li>
            </ul>
          </div>
        </section>
  
        <!-- Download Option Section -->
        <section v-if="outputCode && !errors.some(e => !e.toLowerCase().startsWith('warning:'))" class="mt-4 p-4 bg-base bg-opacity-50 backdrop-blur-sm rounded-lg">
          <button
            @click="downloadTranslatedCode"
            class="bg-gradient-to-r from-green-400 to-blue-500 hover:from-green-500 hover:to-blue-600 text-white font-bold py-3 px-4 rounded-lg shadow-md hover:shadow-neon-blue focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-75 transition-all duration-300 ease-in-out transform hover:scale-105"
          >
            Download Translated Code
          </button>
        </section>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, watch, nextTick } from 'vue';
  import hljs from 'highlight.js/lib/core';
  import rust from 'highlight.js/lib/languages/rust';
  import 'highlight.js/styles/cybertopia-dimmer.css';
  
  hljs.registerLanguage('rust', rust);
  
  // State
  const sidebarOpen = ref(true);
  const sourceCode = ref('');
  const outputCode = ref('');
  const highlightedOutput = ref('');
  const loading = ref(false);
  const errors = ref<string[]>([]); // Explicitly type errors as string array
  const options = ref({
    optimize: false,
    includeComments: true,
    targetVersion: 'latest',
    mimicDefaults: false
  });
  const copied = ref(false);
  
  // Functions
  const toggleSidebar = () => {
    sidebarOpen.value = !sidebarOpen.value;
  };
  
  const config = useRuntimeConfig();
  
  const translateCode = async () => {
    loading.value = true;
    outputCode.value = '';
    errors.value = [];
  
    try {
      const response = await fetch(`${config.public.apiBase}/translate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_code: sourceCode.value,
          options: {
            optimize: options.value.optimize,
            include_comments: options.value.includeComments, // maps to include_comments for the API
            target_version: options.value.targetVersion,
            mimic_defaults: options.value.mimicDefaults,
          },
        }),
      });
  
      if (!response.ok || !response.body) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Translation failed');
      }
  
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let buffer = '';
      outputCode.value = '';
      errors.value = [];
  
      while (!done) {
        const { value, done: streamDone } = await reader.read();
        done = streamDone;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          let lines = buffer.split('\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const data = JSON.parse(line);
              if (data.translated_code) {
                outputCode.value += data.translated_code;
              }
              if (data.warnings && data.warnings.length > 0) {
                errors.value = [...errors.value, ...data.warnings.map((w: string) => `Warning: ${w}`)];
              }
              if (data.errors && data.errors.length > 0) {
                errors.value = [...errors.value, ...data.errors.map((e: string) => String(e))];
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
            errors.value = [...errors.value, ...data.warnings.map((w: string) => `Warning: ${w}`)];
          }
          if (data.errors && data.errors.length > 0) {
            errors.value = [...errors.value, ...data.errors.map((e: string) => String(e))];
          }
        } catch (e) {
          // Ignore
        }
      }
    } catch (error: unknown) {
      let message = 'Translation failed';
      if (typeof error === 'object' && error !== null && 'message' in error && typeof (error as any).message === 'string') {
        message = (error as any).message;
      }
      outputCode.value = message;
      errors.value = [message];
    } finally {
      loading.value = false;
    }
  };
  
  watch(outputCode, async (newCode) => {
    await nextTick();
    if (newCode) {
      highlightedOutput.value = hljs.highlight(newCode, { language: 'rust' }).value;
    } else {
      highlightedOutput.value = '';
    }
  });
  
  function downloadTranslatedCode() {
    if (!outputCode.value) return;
  
    const blob = new Blob([outputCode.value], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'translated_code.ralph'; // Suggested filename
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  }
  
  function copyTranslatedCode() {
    if (!outputCode.value) return;
    navigator.clipboard.writeText(outputCode.value).then(() => {
      copied.value = true;
      setTimeout(() => copied.value = false, 1500);
    });
  }
  </script>
  
  <style scoped>
  /* Scoped styles for the page */
  /* Removed bg-base and bg-secondary as they are handled by Tailwind utilities or inline styles now */
  
  /* Ensure full height for textarea if not expanding correctly */
  textarea {
    min-height: 300px; /* Adjust as needed, or use flex-grow if parent is flex */
  }
  
  /* Custom scrollbar styling (optional, for a more polished look) */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  ::-webkit-scrollbar-track {
    background: rgba(0,0,0,0.1);
    border-radius: 10px;
  }
  ::-webkit-scrollbar-thumb {
    background: linear-gradient(to bottom, #FF00FF, #00FFFF); /* Neon gradient for scrollbar */
    border-radius: 10px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(to bottom, #00FFFF, #FF00FF); /* Swap gradient on hover */
  }
  </style>