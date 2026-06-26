export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

const STORAGE_KEY = 'spd_chat_messages';

export function loadChatMessages(): ChatMessage[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveChatMessages(messages: ChatMessage[]) {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
}

export function clearChatMessages() {
  sessionStorage.removeItem(STORAGE_KEY);
}
