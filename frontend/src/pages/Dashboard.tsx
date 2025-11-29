import React, { useState } from 'react';
import { Users, FileText, AlertTriangle, Activity, Link as LinkIcon, Upload, UserPlus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Avatar, AvatarFallback } from '../components/ui/avatar';

const Dashboard: React.FC = () => {
    const [shareLink, setShareLink] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const stats = [
        { label: 'Total Clients', value: '124', icon: Users, color: 'text-blue-600', bg: 'bg-blue-100', border: 'border-blue-200' },
        { label: 'Documents Processed', value: '1,432', icon: FileText, color: 'text-emerald-600', bg: 'bg-emerald-100', border: 'border-emerald-200' },
        { label: 'Pending Reviews', value: '12', icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-100', border: 'border-amber-200' },
        { label: 'System Health', value: '98%', icon: Activity, color: 'text-purple-600', bg: 'bg-purple-100', border: 'border-purple-200' },
    ];

    const handleAccessSharedDocuments = () => {
        if (!shareLink.trim()) {
            // In a real app, use a toast here
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
            className="space-y-8 p-1"
        >
            <motion.div variants={item}>
                <h1 className="text-3xl font-bold tracking-tight mb-2 text-foreground">CA Dashboard</h1>
                <p className="text-muted-foreground">Overview of your compliance activities</p>
            </motion.div>

            <motion.div variants={item} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat) => {
                    const Icon = stat.icon;
                    return (
                        <Card key={stat.label} className={`glass border-border/50 hover:shadow-lg transition-all duration-300 hover:-translate-y-1 ${stat.border}`}>
                            <CardContent className="p-6">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                                        <h3 className="text-2xl font-bold mt-2 text-foreground">{stat.value}</h3>
                                    </div>
                                    <div className={`p-3 rounded-xl ${stat.bg} bg-opacity-50`}>
                                        <Icon className={`w-5 h-5 ${stat.color}`} />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}
            </motion.div>

            {/* Access Shared Documents Section */}
            <motion.div variants={item}>
                <Card className="glass border-border/50 overflow-hidden relative shadow-sm">
                    <CardContent className="p-8 relative z-10">
                        <div className="flex flex-col md:flex-row gap-8 items-center">
                            <div className="flex items-center gap-5 flex-1">
                                <div className="w-14 h-14 bg-purple-50 rounded-2xl flex items-center justify-center shrink-0 border border-purple-100 shadow-sm">
                                    <LinkIcon className="text-purple-600" size={26} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-foreground">Access Shared Documents</h2>
                                    <p className="text-muted-foreground text-sm mt-1">Enter a client's share link to view their documents securely</p>
                                </div>
                            </div>

                            <div className="flex gap-3 w-full md:w-auto min-w-[450px]">
                                <Input
                                    type="text"
                                    value={shareLink}
                                    onChange={(e) => setShareLink(e.target.value)}
                                    placeholder="Paste share link here..."
                                    className="bg-white/80 border-border/60 focus:bg-white h-11"
                                    onKeyPress={(e) => e.key === 'Enter' && handleAccessSharedDocuments()}
                                />
                                <Button
                                    onClick={handleAccessSharedDocuments}
                                    disabled={loading || !shareLink.trim()}
                                    className="bg-purple-600 hover:bg-purple-700 text-white h-11 px-6 shadow-md hover:shadow-lg transition-all"
                                >
                                    {loading ? 'Loading...' : 'Access'}
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <motion.div variants={item}>
                    <Card className="h-full glass border-border/50 shadow-sm">
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg">Recent Activity</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {[1, 2, 3].map((i) => (
                                    <div key={i} className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/60 transition-colors group cursor-pointer border border-transparent hover:border-border/40">
                                        <Avatar className="h-10 w-10 border border-border/50">
                                            <AvatarFallback className="bg-blue-50 text-blue-600 group-hover:bg-blue-100 transition-colors">
                                                <FileText className="w-5 h-5" />
                                            </AvatarFallback>
                                        </Avatar>
                                        <div>
                                            <p className="text-sm font-semibold text-foreground/90 group-hover:text-primary transition-colors">Document uploaded for Client X</p>
                                            <p className="text-xs text-muted-foreground">2 hours ago</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                <motion.div variants={item}>
                    <Card className="h-full glass border-border/50 shadow-sm">
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg">Quick Actions</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 gap-4">
                                <Button
                                    variant="outline"
                                    className="h-auto py-8 flex flex-col items-center gap-3 border-border/60 hover:border-blue-200 hover:bg-blue-50/50 transition-all group rounded-xl"
                                >
                                    <div className="p-3 bg-blue-50 rounded-full group-hover:scale-110 transition-transform duration-300">
                                        <Upload className="w-6 h-6 text-blue-600" />
                                    </div>
                                    <span className="font-medium text-foreground/80">Upload Document</span>
                                </Button>
                                <Button
                                    variant="outline"
                                    className="h-auto py-8 flex flex-col items-center gap-3 border-border/60 hover:border-purple-200 hover:bg-purple-50/50 transition-all group rounded-xl"
                                >
                                    <div className="p-3 bg-purple-50 rounded-full group-hover:scale-110 transition-transform duration-300">
                                        <UserPlus className="w-6 h-6 text-purple-600" />
                                    </div>
                                    <span className="font-medium text-foreground/80">Add Client</span>
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            </div>
        </motion.div>
    );
};

export default Dashboard;
