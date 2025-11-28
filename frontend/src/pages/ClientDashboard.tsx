import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Share2, Upload, FileText, Link as LinkIcon, Clock, CheckCircle } from 'lucide-react';
import api from '../services/api';

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

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">My Dashboard</h1>
                    <p className="text-slate-400">Upload, manage, and share your financial documents</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Upload Section */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="card bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center text-emerald-400">
                                <Upload size={24} />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-white">Upload Documents</h2>
                                <p className="text-slate-400 text-sm">Upload invoices, bank statements, and receipts</p>
                            </div>
                        </div>

                        <button
                            onClick={() => navigate('/upload')}
                            className="w-full py-4 border-2 border-dashed border-slate-600 rounded-xl flex flex-col items-center justify-center text-slate-400 hover:border-emerald-500 hover:text-emerald-500 transition-all group"
                        >
                            <Upload size={32} className="mb-2 group-hover:scale-110 transition-transform" />
                            <span className="font-medium">Click to Upload New Files</span>
                        </button>
                    </div>

                    {/* Recent Files */}
                    <div className="card">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <Clock size={20} className="text-blue-400" />
                                Recent Uploads
                            </h2>
                            <button onClick={() => navigate('/documents')} className="text-sm text-blue-400 hover:text-blue-300">
                                View All
                            </button>
                        </div>

                        <div className="space-y-3">
                            {recentDocs.length === 0 ? (
                                <p className="text-slate-500 text-sm text-center py-4">No documents uploaded yet.</p>
                            ) : (
                                recentDocs.map((doc: any) => (
                                    <div key={doc.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                                        <div className="flex items-center gap-3">
                                            <FileText size={18} className="text-slate-400" />
                                            <div>
                                                <p className="text-white text-sm font-medium">{doc.filename || doc.name}</p>
                                                <p className="text-xs text-slate-500">
                                                    {doc.upload_date ? new Date(doc.upload_date).toLocaleDateString() : 'Uploaded recently'}
                                                </p>
                                            </div>
                                        </div>
                                        <span className="text-xs px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center gap-1">
                                            <CheckCircle size={10} /> {doc.status || 'Processed'}
                                        </span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Share Section */}
                <div className="card h-fit sticky top-6">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center text-purple-400">
                            <Share2 size={20} />
                        </div>
                        <h2 className="text-xl font-bold text-white">Share Access</h2>
                    </div>

                    <div className="space-y-6">
                        <p className="text-slate-400 text-sm">
                            Create a secure link to share your uploaded documents with your Chartered Accountant.
                        </p>

                        {!shareLink ? (
                            <button
                                onClick={handleGenerateShareLink}
                                className="btn-primary w-full"
                            >
                                Generate Share Link
                            </button>
                        ) : (
                            <div className="space-y-4 animate-in fade-in slide-in-from-top-4 duration-500">
                                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                                    <LinkIcon className="text-slate-500 shrink-0" size={14} />
                                    <code className="flex-1 text-blue-400 text-xs overflow-hidden text-ellipsis">
                                        {shareLink}
                                    </code>
                                    <button
                                        onClick={() => navigator.clipboard.writeText(shareLink)}
                                        className="text-xs bg-slate-800 hover:bg-slate-700 px-2 py-1 rounded text-white transition-colors"
                                    >
                                        Copy
                                    </button>
                                </div>

                                <div>
                                    <label className="block text-xs font-medium text-slate-300 mb-1.5">CA's Email</label>
                                    <div className="flex gap-2">
                                        <input
                                            type="email"
                                            value={caEmail}
                                            onChange={(e) => setCaEmail(e.target.value)}
                                            className="input-field py-2 text-sm"
                                            placeholder="ca@example.com"
                                        />
                                        <button
                                            onClick={handleSendEmail}
                                            className="btn-primary py-2 px-4 text-sm"
                                        >
                                            Send
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ClientDashboard;
