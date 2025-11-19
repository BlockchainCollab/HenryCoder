<template>
  <div class="fixed bottom-4 right-4 z-50 flex flex-col items-end">
    <!-- Chat Toggle Button -->
    <button
      v-if="!isOpen"
      @click="toggleChat"
      class="bg-[#FF8A00] hover:bg-[#FCA545] text-white rounded-full p-4 shadow-lg transition-all duration-300 hover:scale-110"
      title="Open AI Assistant"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
        />
      </svg>
    </button>

    <!-- Chat Window -->
    <div
      v-if="isOpen"
      class="bg-[#191817] border border-[#6D5D5D] rounded-xl shadow-2xl w-96 h-[600px] flex flex-col overflow-hidden"
    >
      <!-- Header -->
      <div
        class="bg-gradient-to-r from-[#EF8510] to-[#FCA545] p-4 flex justify-between items-center"
      >
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          <h3 class="text-white font-bold">HenryBot AI</h3>
        </div>
        <div class="flex gap-2">
          <button
            @click="clearChat"
            class="text-white hover:text-gray-200 transition-colors p-1 rounded hover:bg-white/10"
            title="Clear chat"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
          <button
            @click="toggleChat"
            class="text-white hover:text-gray-200 transition-colors p-1 rounded hover:bg-white/10"
            title="Close"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Stage Indicator -->
      <transition name="slide-down">
        <div
          v-if="currentStage"
          class="bg-[#312F2D] border-b border-[#6D5D5D] px-4 py-3"
        >
          <div class="flex items-center gap-2">
            <div class="relative flex items-center justify-center">
              <div class="w-4 h-4 bg-[#FF8A00] rounded-full animate-ping absolute"></div>
              <div class="w-4 h-4 bg-[#FF8A00] rounded-full"></div>
            </div>
            <div class="flex-1">
              <p class="text-sm text-gray-300">{{ currentStage.message }}</p>
              <p v-if="currentTool" class="text-xs text-gray-500 mt-1">
                Using: {{ currentTool }}
              </p>
            </div>
          </div>
        </div>
      </transition>

      <!-- Messages -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- Welcome Message -->
        <div v-if="messages.length === 0" class="text-gray-400 text-center py-8">
          <div class="mb-4 text-4xl">🤖</div>
          <p class="mb-2 font-semibold">Hi! I'm HenryBot.</p>
          <p class="text-sm">
            Ask me anything about Ralph, Alephium, or smart contract development!
          </p>
          
          <!-- Quick Actions -->
          <div class="mt-6 space-y-2">
            <p class="text-xs text-gray-500 mb-2">Quick actions:</p>
            <button
              v-for="suggestion in suggestions"
              :key="suggestion"
              @click="handleSuggestion(suggestion)"
              class="w-full text-left bg-[#312F2D] hover:bg-[#4C4B4B] text-gray-200 rounded-lg p-3 border border-[#4C4B4B] transition-colors text-sm"
            >
              {{ suggestion }}
            </button>
          </div>
        </div>

        <!-- Messages -->
        <div
          v-for="message in messages"
          :key="message.id"
          :class="[
            'flex',
            message.role === 'user' ? 'justify-end' : 'justify-start',
          ]"
        >
          <div
            :class="[
              'max-w-[80%] rounded-lg p-3',
              message.role === 'user'
                ? 'bg-gradient-to-r from-[#FF8A00] to-[#FCA545] text-white'
                : 'bg-[#312F2D] text-gray-200 border border-[#4C4B4B]',
            ]"
          >
            <div class="prose prose-invert prose-sm max-w-none">
              <div v-html="renderMarkdown(message.content)"></div>
            </div>
            <div
              v-if="message.isStreaming"
              class="flex items-center gap-1 mt-2"
            >
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div
                class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                style="animation-delay: 0.1s"
              ></div>
              <div
                class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                style="animation-delay: 0.2s"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="p-4 border-t border-[#6D5D5D]">
        <form @submit.prevent="handleSend" class="flex gap-2">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="Ask me anything..."
            :disabled="isLoading"
            class="flex-1 bg-[#312F2D] text-gray-200 rounded-lg px-4 py-2 border border-[#4C4B4B] focus:outline-none focus:ring-2 focus:ring-[#FF8A00] disabled:opacity-50 transition-all"
          />
          <button
            type="submit"
            :disabled="isLoading || !inputMessage.trim()"
            class="bg-[#FF8A00] hover:bg-[#FCA545] text-white rounded-lg px-4 py-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue';
import { useChat } from '@/composables/useChat';
import { marked } from 'marked';

const { messages, isLoading, currentStage, currentTool, sendMessage, clearChat: clearChatHistory } = useChat();

const isOpen = ref(false);
const inputMessage = ref('');
const messagesContainer = ref<HTMLElement | null>(null);

const suggestions = [
  '✨ Generate a token contract',
  '🔄 Translate my Solidity code',
  '📚 Explain Ralph syntax',
  '💡 Best practices for Ralph?',
];

const toggleChat = () => {
  isOpen.value = !isOpen.value;
};

const handleSend = async () => {
  const message = inputMessage.value.trim();
  if (!message) return;

  inputMessage.value = '';
  await sendMessage(message);
};

const handleSuggestion = (suggestion: string) => {
  inputMessage.value = suggestion;
  handleSend();
};

const clearChat = async () => {
  if (confirm('Are you sure you want to clear the chat history?')) {
    await clearChatHistory();
  }
};

const renderMarkdown = (content: string) => {
  if (!content) return '';
  try {
    return marked.parse(content);
  } catch (e) {
    console.error('Markdown parsing error:', e);
    return content;
  }
};

// Auto-scroll to bottom when new messages arrive
watch(
  () => messages.value.length,
  async () => {
    await nextTick();
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  }
);

// Also watch message content for streaming updates
watch(
  () => messages.value.map(m => m.content).join(''),
  async () => {
    await nextTick();
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  }
);
</script>

<style scoped>
/* Animations */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  transform: translateY(-100%);
  opacity: 0;
}

.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #191817;
}

::-webkit-scrollbar-thumb {
  background: #6D5D5D;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9E9992;
}

/* Markdown styling */
:deep(.prose) {
  font-size: 0.875rem;
  line-height: 1.5;
}

:deep(.prose code) {
  background-color: rgba(0, 0, 0, 0.3);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 0.85em;
  font-family: 'Menlo', monospace;
}

:deep(.prose pre) {
  background-color: rgba(0, 0, 0, 0.5);
  padding: 1em;
  border-radius: 6px;
  overflow-x: auto;
  border: 1px solid #4C4B4B;
}

:deep(.prose pre code) {
  background-color: transparent;
  padding: 0;
}

:deep(.prose p) {
  margin-bottom: 0.5em;
}

:deep(.prose p:last-child) {
  margin-bottom: 0;
}

:deep(.prose ul),
:deep(.prose ol) {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
  padding-left: 1.5em;
}

:deep(.prose li) {
  margin-bottom: 0.25em;
}

:deep(.prose strong) {
  color: #FCA545;
}

:deep(.prose a) {
  color: #FF8A00;
  text-decoration: underline;
}

:deep(.prose a:hover) {
  color: #FCA545;
}
</style>
