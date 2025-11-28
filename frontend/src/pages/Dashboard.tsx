import React, { useState } from 'react';
import { Users, FileText, AlertTriangle, Activity, Link as LinkIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
    const [shareLink, setShareLink] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const stats = [
        { label: 'Total Clients', value: '124', icon: Users, color: 'text-blue-400', bg: 'bg-blue-900/20' },
        { label: 'Documents Processed', value: '1,432', icon: FileText, color: 'text-emerald-400', bg: 'bg-emerald-900/20' },
        { label: 'Pending Reviews', value: '12', icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-900/20' },
        { label: 'System Health', value: '98%', icon: Activity, color: 'text-purple-400', bg: 'bg-purple-900/20' },
    ];

    const handleAccessSharedDocuments = () => {
        if (!shareLink.trim()) {
            alert('Please enter a valid share link');
            return;
        }

        // Extract token from the share link
        const tokenMatch = shareLink.match(/\/share\/invite\/([^\/\?]+)/);
        if (tokenMatch && tokenMatch[1]) {
            const token = tokenMatch[1];
            navigate(`/share/invite/${token}`);
        } else {
            alert('Invalid share link format');
        }
    };

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
                <p className="text-slate-400">Overview of your compliance activities</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat) => {
                    const Icon = stat.icon;
                    return (
                        <div key={stat.label} className="card hover:border-slate-600 transition-colors">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-slate-400 text-sm font-medium">{stat.label}</p>
                                    <h3 className="text-2xl font-bold text-white mt-2">{stat.value}</h3>
                                </div>
                                <div className={`p-3 rounded-lg ${stat.bg}`}>
                                    <Icon className={`w-6 h-6 ${stat.color}`} />
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Access Shared Documents Section */}
            <div className="card bg-gradient-to-br from-purple-900/20 to-slate-900 border-purple-700/50">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                        <LinkIcon className="text-purple-400" size={20} />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white">Access Shared Documents</h2>
                        <p className="text-slate-400 text-sm">Enter a client's share link to view their documents</p>
                    </div>
                </div>

                <div className="flex gap-3">
                    <input
                        type="text"
                        value={shareLink}
                        onChange={(e) => setShareLink(e.target.value)}
                        placeholder="Paste share link here (e.g., https://example.com/share/invite/abc123)"
                        className="input-field flex-1"
                        onKeyPress={(e) => e.key === 'Enter' && handleAccessSharedDocuments()}
                    />
                    <button
                        onClick={handleAccessSharedDocuments}
                        disabled={loading || !shareLink.trim()}
                        className="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Loading...' : 'Access'}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="card">
                    <h2 className="text-xl font-bold text-white mb-4">Recent Activity</h2>
                    <div className="space-y-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="flex items-center gap-4 p-3 rounded-lg hover:bg-slate-700/50 transition-colors">
                                <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center">
                                    <FileText className="w-5 h-5 text-slate-400" />
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-white">Document uploaded for Client X</p>
                                    <p className="text-xs text-slate-400">2 hours ago</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="card">
                    <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
                    <div className="grid grid-cols-2 gap-4">
                        <button className="p-4 rounded-lg bg-slate-700/50 hover:bg-slate-700 border border-slate-600 hover:border-blue-500/50 transition-all text-left group">
                            <FileText className="w-6 h-6 text-blue-400 mb-2 group-hover:scale-110 transition-transform" />
                            <span className="block font-medium text-white">Upload Document</span>
                        </button>
                        <button className="p-4 rounded-lg bg-slate-700/50 hover:bg-slate-700 border border-slate-600 hover:border-purple-500/50 transition-all text-left group">
                            <Users className="w-6 h-6 text-purple-400 mb-2 group-hover:scale-110 transition-transform" />
                            <span className="block font-medium text-white">Add Client</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
