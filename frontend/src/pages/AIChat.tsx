import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { ScrollArea } from '../components/ui/scroll-area';
import { Avatar, AvatarFallback } from '../components/ui/avatar';

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'ai';
    timestamp: Date;
}

const AIChat: React.FC = () => {
    const { user } = useAuth();
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
    const [sessionId] = useState(() => Math.random().toString(36).substring(2) + Date.now().toString(36));

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
            const response = await api.post('/agent/chat', {
                session_id: sessionId,
                message: userMessage.text,
                user_role: user?.role || 'CA',
                client_id: selectedClientId !== 'all' ? selectedClientId : undefined,
                mode: selectedMode
            });

            const aiText = response.data.response || "I processed your query but found no specific answer.";

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

    const [clients, setClients] = useState<any[]>([]);
    const [selectedClientId, setSelectedClientId] = useState<string>('all');
    const [selectedMode, setSelectedMode] = useState<string>('general');

    useEffect(() => {
        const fetchClients = async () => {
            try {
                const res = await api.get('/clients');
                setClients(res.data);
            } catch (err) {
                console.error("Failed to fetch clients", err);
            }
        };
        fetchClients();
    }, []);

    return (
        <div className="relative h-[calc(100vh-2rem)] w-full overflow-hidden flex flex-col items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, y: 20, rotateX: 10 }}
                animate={{ opacity: 1, y: 0, rotateX: 0 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                className="z-10 w-full max-w-4xl h-full flex flex-col perspective-1000"
            >
                <Card className="flex-1 flex flex-col glass border-border/50 shadow-xl overflow-hidden h-full">
                    <CardHeader className="border-b border-border/50 bg-white/40 backdrop-blur-md pb-4">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-primary/10 rounded-xl">
                                    <Sparkles className="w-6 h-6 text-primary" />
                                </div>
                                <div>
                                    <CardTitle className="text-xl font-bold text-foreground">Eagle Eyed AI</CardTitle>
                                    <CardDescription>Your intelligent compliance assistant</CardDescription>
                                </div>
                            </div>

                            <div className="flex items-center gap-2">
                                {/* Client Selection Label */}
                                <div className="relative group">
                                    <select
                                        value={selectedClientId}
                                        onChange={(e) => setSelectedClientId(e.target.value)}
                                        className="appearance-none bg-blue-50 hover:bg-blue-100 text-blue-700 px-4 py-1.5 rounded-full text-xs font-semibold border border-blue-200 outline-none cursor-pointer transition-colors pr-8 min-w-[120px]"
                                    >
                                        <option value="all">All Clients</option>
                                        {clients.map(c => (
                                            <option key={c.id} value={c.id}>{c.name}</option>
                                        ))}
                                    </select>
                                    <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-blue-500">
                                        <User size={12} />
                                    </div>
                                </div>

                                {/* Mode Selection Label */}
                                <div className="relative group">
                                    <select
                                        value={selectedMode}
                                        onChange={(e) => setSelectedMode(e.target.value)}
                                        className="appearance-none bg-purple-50 hover:bg-purple-100 text-purple-700 px-4 py-1.5 rounded-full text-xs font-semibold border border-purple-200 outline-none cursor-pointer transition-colors pr-8 min-w-[120px]"
                                    >
                                        <option value="general">General Assistant</option>
                                        <option value="audit">Audit & Compliance</option>
                                        <option value="tax">Tax Planning</option>
                                        <option value="report">Report Generation</option>
                                    </select>
                                    <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-purple-500">
                                        <Bot size={12} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </CardHeader>

                    <CardContent className="flex-1 overflow-hidden p-0 relative">
                        <ScrollArea className="h-full p-4">
                            <div className="space-y-6 pb-4">
                                <AnimatePresence initial={false}>
                                    {messages.map((msg) => (
                                        <motion.div
                                            key={msg.id}
                                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                            animate={{ opacity: 1, y: 0, scale: 1 }}
                                            transition={{ duration: 0.3 }}
                                            className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
                                        >
                                            <Avatar className={`w-8 h-8 border ${msg.sender === 'user' ? 'border-blue-200' : 'border-emerald-200'}`}>
                                                <AvatarFallback className={msg.sender === 'user' ? 'bg-blue-100 text-blue-600' : 'bg-emerald-100 text-emerald-600'}>
                                                    {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                                                </AvatarFallback>
                                            </Avatar>

                                            <div
                                                className={`max-w-[80%] p-4 rounded-2xl shadow-sm ${msg.sender === 'user'
                                                    ? 'bg-primary text-primary-foreground rounded-tr-none'
                                                    : 'bg-muted border border-border text-foreground rounded-tl-none'
                                                    }`}
                                            >
                                                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                                                <p className="text-[10px] opacity-70 mt-2 text-right">
                                                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </p>
                                            </div>
                                        </motion.div>
                                    ))}
                                </AnimatePresence>
                                <div ref={messagesEndRef} />
                            </div>
                        </ScrollArea>
                    </CardContent>

                    <div className="p-4 border-t border-border bg-muted/30">
                        <form onSubmit={handleSend} className="flex gap-3">
                            <Input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask about compliance, tax laws, or upload a document..."
                                className="flex-1 bg-background border-input focus-visible:ring-primary/50"
                            />
                            <Button
                                type="submit"
                                size="icon"
                                className="bg-primary hover:bg-primary/90 shadow-lg shadow-primary/20 transition-all hover:scale-105 active:scale-95"
                                disabled={!input.trim()}
                            >
                                <Send size={18} />
                            </Button>
                        </form>
                    </div>
                </Card>
            </motion.div>
        </div>
    );
};

export default AIChat;
