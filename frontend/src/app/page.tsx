import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [messages, setMessages] = useState<{ role: 'user' | 'ai'; content: string }[]>([
    { role: 'ai', content: 'Hello! I’m your personal AI assistant with long-term memory. Ask me anything.' }
  ]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user' as const, content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsSending(true);

    try {
      const res = await axios.post('http://localhost:8000/chat', {
        message: input,
        session_id: 'test-session-' + Date.now()
      });

      const aiReply = res.data.reply;
      const memorySuggestions = res.data.memory_suggestions;

      // Simulate memory approval UI later
      console.log('Memory suggestions:', memorySuggestions);

      setMessages(prev => [...prev, { role: 'ai', content: aiReply }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'ai', content: 'Error connecting to AI service.' }]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4 bg-gray-50">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-2 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white rounded-br-none'
                  : 'bg-white text-gray-800 rounded-bl-none shadow'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 border border-gray-300 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
          disabled={isSending}
        />
        <button
          type="submit"
          disabled={isSending}
          className="px-6 py-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 transition"
        >
          {isSending ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
