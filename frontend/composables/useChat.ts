import { ref, computed } from 'vue';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  isStreaming?: boolean;
}

export type AgentStage = 
  | 'thinking'
  | 'using_tool'
  | 'reading_code'
  | 'translating'
  | 'generating'
  | 'fetching_docs'
  | 'completing'
  | 'done';

export interface StageInfo {
  stage: AgentStage;
  message: string;
}

export interface StreamEvent {
  type: 'content' | 'stage' | 'tool_start' | 'tool_end' | 'error';
  data: any;
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function useChat() {
  const messages = ref<ChatMessage[]>([]);
  const isLoading = ref(false);
  const sessionId = ref<string>(generateId());
  const currentStage = ref<StageInfo | null>(null);
  const currentTool = ref<string | null>(null);
  const runtimeConfig = useRuntimeConfig();

  const addMessage = (role: 'user' | 'assistant', content: string, isStreaming = false) => {
    const message: ChatMessage = {
      id: generateId(),
      role,
      content,
      timestamp: new Date().toISOString(),
      isStreaming,
    };
    messages.value.push(message);
    return message;
  };

  const updateLastMessage = (content: string) => {
    if (messages.value.length > 0) {
      const lastMessage = messages.value[messages.value.length - 1];
      lastMessage.content = content;
    }
  };

  const handleStreamEvent = (event: StreamEvent, assistantMessage: ChatMessage) => {
    switch (event.type) {
      case 'content':
        // Append content to assistant message
        assistantMessage.content += event.data;
        break;

      case 'stage':
        // Update current stage
        currentStage.value = {
          stage: event.data.stage,
          message: event.data.message
        };
        
        // Clear stage when done
        if (event.data.stage === 'done') {
          setTimeout(() => {
            currentStage.value = null;
            currentTool.value = null;
          }, 1000);
        }
        break;

      case 'tool_start':
        // Show which tool is being used
        currentTool.value = event.data.tool;
        break;

      case 'tool_end':
        // Clear tool indicator
        setTimeout(() => {
          currentTool.value = null;
        }, 500);
        break;

      case 'error':
        // Handle error
        console.error('Chat error:', event.data.message);
        assistantMessage.content = `❌ Error: ${event.data.message}`;
        currentStage.value = null;
        currentTool.value = null;
        break;
    }
  };

  const sendMessage = async (userMessage: string, context?: Record<string, any>) => {
    if (!userMessage.trim()) return;

    isLoading.value = true;
    currentStage.value = null;
    currentTool.value = null;

    // Add user message
    addMessage('user', userMessage);

    // Add streaming assistant message
    const assistantMessage = addMessage('assistant', '', true);

    try {
      const response = await fetch(`${runtimeConfig.public.apiBase}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId.value,
          context,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error('Chat request failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          
          try {
            const event: StreamEvent = JSON.parse(line);
            handleStreamEvent(event, assistantMessage);
          } catch (e) {
            console.error('Error parsing event:', e, line);
          }
        }
      }

      assistantMessage.isStreaming = false;
      currentStage.value = null;
      currentTool.value = null;
    } catch (error) {
      console.error('Chat error:', error);
      assistantMessage.content = '❌ Sorry, I encountered an error. Please try again.';
      assistantMessage.isStreaming = false;
      currentStage.value = null;
      currentTool.value = null;
    } finally {
      isLoading.value = false;
    }
  };

  const clearChat = async () => {
    try {
      await fetch(`${runtimeConfig.public.apiBase}/chat/session/${sessionId.value}`, {
        method: 'DELETE',
      });
      messages.value = [];
      sessionId.value = generateId();
      currentStage.value = null;
      currentTool.value = null;
    } catch (error) {
      console.error('Error clearing chat:', error);
    }
  };

  return {
    messages: computed(() => messages.value),
    isLoading: computed(() => isLoading.value),
    currentStage: computed(() => currentStage.value),
    currentTool: computed(() => currentTool.value),
    sendMessage,
    clearChat,
  };
}
