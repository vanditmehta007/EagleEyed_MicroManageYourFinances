import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';
import api from '../services/api';

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'ai';
    timestamp: Date;
}

const AIChat: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            text: "Hello! I'm your Eagle Eyed AI assistant. How can I help you with your compliance tasks today?",
            sender: 'ai',
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            text: input,
            sender: 'user',
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');

        try {
            // Use the query router endpoint
            const response = await api.post('/query/', {
                query_text: userMessage.text,
                client_id: 'current_client_id', // Ideally from context or selector
                year: 2024 // Default or selector
            });

            const aiText = response.data.answer || "I processed your query but found no specific answer.";

            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                text: aiText,
                sender: 'ai',
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, aiMessage]);

        } catch (err) {
            console.error("AI Chat Error", err);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                text: "Sorry, I encountered an error processing your request.",
                sender: 'ai',
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)]">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2">AI Assistant</h1>
                <p className="text-slate-400">Ask questions about compliance, tax laws, or your documents</p>
            </div>

            <div className="flex-1 card flex flex-col overflow-hidden">
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            <div
                                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.sender === 'user' ? 'bg-blue-600' : 'bg-emerald-600'
                                    }`}
                            >
                                {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
                            </div>
                            <div
                                className={`max-w-[80%] p-3 rounded-2xl ${msg.sender === 'user'
                                    ? 'bg-blue-600/20 text-blue-100 rounded-tr-none'
                                    : 'bg-slate-700/50 text-slate-200 rounded-tl-none'
                                    }`}
                            >
                                <p className="text-sm">{msg.text}</p>
                                <p className="text-xs opacity-50 mt-1">
                                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </p>
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                <form onSubmit={handleSend} className="p-4 border-t border-slate-700 bg-slate-800/50">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your message..."
                            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors"
                        />
                        <button
                            type="submit"
                            className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                        >
                            <Send size={20} />
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AIChat;
