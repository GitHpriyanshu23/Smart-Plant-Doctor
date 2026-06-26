import { useMutation, useQuery } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import MarkdownContent from '../components/MarkdownContent';
import { api } from '../lib/api';
import { loadChatMessages, saveChatMessages, type ChatMessage } from '../lib/chatStore';

interface Plant {
  id: number;
  nickname: string;
  species: string;
}

const SUGGESTIONS = [
  'How often should I water my Rose?',
  'What causes yellow leaves?',
  'Best soil for Aloe Vera?',
  'How to increase humidity for tropical plants?',
  'Signs of overwatering vs underwatering?',
  'How much sunlight do succulents need?',
];

export default function ChatPage() {
  const [plantId, setPlantId] = useState<number | ''>('');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadChatMessages());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    saveChatMessages(messages);
  }, [messages]);

  const { data: plants = [] } = useQuery({
    queryKey: ['plants'],
    queryFn: () => api<Plant[]>('/api/v1/plants'),
  });

  const selectedPlant = plants.find((p) => p.id === plantId);

  const send = useMutation({
    mutationFn: (message: string) =>
      api<{ reply: string }>('/api/v1/chat', {
        method: 'POST',
        body: JSON.stringify({ plant_id: plantId || null, message }),
      }),
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ]);
    },
  });

  const handleSend = (text?: string) => {
    const message = text || input.trim();
    if (!message || send.isPending) return;
    setMessages((prev) => [...prev, { role: 'user', content: message }]);
    setInput('');
    send.mutate(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, send.isPending]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  }, [input]);

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto">
      <div className="flex items-center justify-between pb-4 border-b border-gray-100">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Plant Care Assistant</h1>
          <p className="text-sm text-gray-500">Powered by AI — ask anything about plant health</p>
        </div>
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button
              type="button"
              onClick={() => setMessages([])}
              className="text-xs text-gray-500 hover:text-red-600 px-3 py-2 rounded-lg border border-gray-200 hover:border-red-200 transition-colors"
            >
              Clear chat
            </button>
          )}
          {selectedPlant && (
            <span className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 bg-green-100 text-green-700 rounded-full">
              {selectedPlant.nickname}
            </span>
          )}
          <select
            className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
            value={plantId}
            onChange={(e) => setPlantId(e.target.value ? Number(e.target.value) : '')}
          >
            <option value="">No plant context</option>
            {plants.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nickname} ({p.species})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-5 text-4xl">🌿</div>
            <h2 className="text-lg font-semibold text-gray-800 mb-2">How can I help your plants today?</h2>
            <p className="text-gray-500 text-sm mb-6 max-w-md">
              Ask about watering, diseases, soil, light, or general care tips.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full">
              {SUGGESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="text-left px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-700 hover:border-green-300 hover:bg-green-50 transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-5 py-3.5 ${
                    msg.role === 'user'
                      ? 'bg-green-600 text-white rounded-br-md'
                      : 'bg-white border border-gray-100 shadow-sm rounded-bl-md'
                  }`}
                >
                  {msg.role === 'assistant' && (
                    <div className="flex items-center gap-1.5 mb-2">
                      <span className="text-xs font-medium text-gray-400">Plant Doctor</span>
                    </div>
                  )}
                  {msg.role === 'assistant' ? (
                    <MarkdownContent content={msg.content} />
                  ) : (
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  )}
                </div>
              </div>
            ))}

            {send.isPending && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-bl-md px-4 py-3">
                  <p className="text-xs text-gray-400 mb-2">Plant Doctor is typing...</p>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" />
                    <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <div className="border-t border-gray-100 pt-4 pb-2">
        <div className="flex items-end gap-3 bg-white border border-gray-200 rounded-2xl p-3 shadow-sm focus-within:ring-2 focus-within:ring-green-500">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={selectedPlant ? `Ask about ${selectedPlant.nickname}...` : 'Ask about plant care...'}
            rows={1}
            className="flex-1 resize-none border-0 bg-transparent text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-0"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || send.isPending}
            className="flex-shrink-0 w-9 h-9 bg-green-600 hover:bg-green-700 disabled:bg-gray-200 rounded-xl flex items-center justify-center transition-colors"
          >
            <svg className={`w-4 h-4 ${input.trim() && !send.isPending ? 'text-white' : 'text-gray-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
