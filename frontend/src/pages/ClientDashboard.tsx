import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Share2, Upload, FileText, Link as LinkIcon, Clock, CheckCircle, Copy, Mail } from 'lucide-react';
import api from '../services/api';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';

const ClientDashboard: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [shareLink, setShareLink] = useState('');
    const [caEmail, setCaEmail] = useState('');
    const [recentDocs, setRecentDocs] = useState<any[]>([]);
    const [clientId, setClientId] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const loadDashboardData = async () => {
            try {
                const clientsRes = await api.get('/clients/');
                if (clientsRes.data && clientsRes.data.length > 0) {
                    const client = clientsRes.data[0];
                    setClientId(client.id);

                    // Fetch documents for this client
                    const docsRes = await api.get(`/documents/?client_id=${client.id}`);
                    if (docsRes.data) {
                        setRecentDocs(docsRes.data.slice(0, 5));
                    }
                }
            } catch (error) {
                console.error("Failed to load dashboard data", error);
            }
        };
        loadDashboardData();
    }, []);

    const handleGenerateShareLink = async () => {
        try {
            let id = clientId;
            if (!id) {
                // Fallback if clientId is not set yet
                const res = await api.get('/clients/');
                if (!res.data || res.data.length === 0) {
                    alert("No client profile found. Please contact support.");
                    return;
                }
                id = res.data[0].id;
            }

            const shareRes = await api.post('/share/create', {
                resource_type: 'client',
                resource_id: id,
                expires_in_hours: 72
            });

            const link = `${window.location.origin}/share/invite/${shareRes.data.token}`;
            setShareLink(link);
        } catch (error) {
            console.error("Failed to generate link", error);
            alert("Failed to generate share link");
        }
    };

    const handleSendEmail = () => {
        if (!caEmail || !shareLink) return;
        const subject = `Invitation to manage financial documents`;
        const body = `Hello,\n\nI have uploaded my financial documents to Eagle Eyed. Please use the following link to access them:\n\n${shareLink}\n\nRegards`;
        window.open(`mailto:${caEmail}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`);
    };

    const container = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    };

    const item = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0 }
    };

    return (
        <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="space-y-8"
        >
            <motion.div variants={item} className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight mb-2">Client Dashboard</h1>
                    <p className="text-muted-foreground">Upload, manage, and share your financial documents</p>
                </div>
            </motion.div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Upload Section */}
                <div className="lg:col-span-2 space-y-6">
                    <motion.div variants={item}>
                        <Card className="bg-card border-border overflow-hidden relative">
                            <CardHeader>
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center text-emerald-600">
                                        <Upload size={24} />
                                    </div>
                                    <div>
                                        <CardTitle>Upload Documents</CardTitle>
                                        <CardDescription>Upload invoices, bank statements, and receipts</CardDescription>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <button
                                    onClick={() => navigate('/upload')}
                                    className="w-full py-8 border-2 border-dashed border-muted-foreground/25 rounded-xl flex flex-col items-center justify-center text-muted-foreground hover:border-emerald-500 hover:text-emerald-600 hover:bg-emerald-50 transition-all group"
                                >
                                    <Upload size={32} className="mb-2 group-hover:scale-110 transition-transform" />
                                    <span className="font-medium">Click to Upload New Files</span>
                                </button>
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Recent Files */}
                    <motion.div variants={item}>
                        <Card className="glass border-border/50 shadow-sm hover:shadow-md transition-all duration-300">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="flex items-center gap-2 text-lg font-semibold">
                                    <Clock size={20} className="text-blue-600" />
                                    Recent Uploads
                                </CardTitle>
                                <Button variant="link" onClick={() => navigate('/documents')} className="text-blue-600 hover:text-blue-700 font-medium">
                                    View All
                                </Button>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-3">
                                    {recentDocs.length === 0 ? (
                                        <div className="flex flex-col items-center justify-center py-8 text-center space-y-2">
                                            <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center">
                                                <FileText className="w-6 h-6 text-muted-foreground/50" />
                                            </div>
                                            <p className="text-muted-foreground text-sm">No documents uploaded yet.</p>
                                        </div>
                                    ) : (
                                        recentDocs.map((doc: any) => (
                                            <div key={doc.id} className="flex items-center justify-between p-3 bg-white/50 hover:bg-white/80 border border-transparent hover:border-blue-100 rounded-xl transition-all duration-200 group cursor-default">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg group-hover:scale-105 transition-transform">
                                                        <FileText size={18} />
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-semibold text-foreground/90">{doc.filename || doc.name}</p>
                                                        <p className="text-xs text-muted-foreground">
                                                            {doc.upload_date ? new Date(doc.upload_date).toLocaleDateString() : 'Uploaded recently'}
                                                        </p>
                                                    </div>
                                                </div>
                                                <Badge variant="secondary" className="gap-1.5 bg-emerald-50 text-emerald-700 border-emerald-100">
                                                    <CheckCircle size={10} /> {doc.status || 'Processed'}
                                                </Badge>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                </div>

                {/* Share Section */}
                <motion.div variants={item} className="h-fit lg:sticky lg:top-6">
                    <Card className="border-border bg-card">
                        <CardHeader>
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600">
                                    <Share2 size={20} />
                                </div>
                                <CardTitle>Share Access</CardTitle>
                            </div>
                            <CardDescription>
                                Create a secure link to share your uploaded documents with your Chartered Accountant.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            {!shareLink ? (
                                <Button
                                    onClick={handleGenerateShareLink}
                                    className="w-full bg-purple-600 hover:bg-purple-700 text-white"
                                >
                                    Generate Share Link
                                </Button>
                            ) : (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    className="space-y-4"
                                >
                                    <div className="space-y-2">
                                        <Label className="text-xs">Share Link</Label>
                                        <div className="flex gap-2">
                                            <div className="flex-1 bg-muted rounded-md border px-3 py-2 text-xs font-mono text-muted-foreground truncate flex items-center gap-2">
                                                <LinkIcon size={12} />
                                                {shareLink}
                                            </div>
                                            <Button
                                                variant="outline"
                                                size="icon"
                                                onClick={() => navigator.clipboard.writeText(shareLink)}
                                                className="shrink-0"
                                            >
                                                <Copy size={14} />
                                            </Button>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <Label className="text-xs">CA's Email</Label>
                                        <div className="flex gap-2">
                                            <div className="relative flex-1">
                                                <Mail className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                                                <Input
                                                    type="email"
                                                    value={caEmail}
                                                    onChange={(e) => setCaEmail(e.target.value)}
                                                    className="pl-9 h-9 text-sm"
                                                    placeholder="ca@example.com"
                                                />
                                            </div>
                                            <Button
                                                onClick={handleSendEmail}
                                                size="sm"
                                                className="bg-purple-600 hover:bg-purple-700 text-white"
                                            >
                                                Send
                                            </Button>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>
        </motion.div>
    );
};

export default ClientDashboard;
