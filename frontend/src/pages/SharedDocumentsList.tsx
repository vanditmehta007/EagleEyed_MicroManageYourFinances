import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderOpen, Building, FileText, Calendar, ChevronRight } from 'lucide-react';
import api from '../services/api';

interface Client {
    id: string;
    name: string;
    gstin?: string;
    pan?: string;
    created_at: string;
}

const SharedDocumentsList: React.FC = () => {
    const navigate = useNavigate();
    const [clients, setClients] = useState<Client[]>([]);
    const [loading, setLoading] = useState(true);
    const [documentCounts, setDocumentCounts] = useState<Record<string, number>>({});

    useEffect(() => {
        fetchClients();
    }, []);

    const fetchClients = async () => {
        try {
            setLoading(true);
            // Fetch all clients assigned to this CA
            const clientsRes = await api.get('/clients/');
            const clientsList = clientsRes.data;
            setClients(clientsList);

            // Fetch document counts for each client
            const counts: Record<string, number> = {};
            await Promise.all(
                clientsList.map(async (client: Client) => {
                    try {
                        const docsRes = await api.get(`/documents/?client_id=${client.id}`);
                        counts[client.id] = docsRes.data?.length || 0;
                    } catch (error) {
                        counts[client.id] = 0;
                    }
                })
            );
            setDocumentCounts(counts);
        } catch (error) {
            console.error("Failed to fetch clients", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-pulse text-slate-400">Loading clients...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">Shared Documents</h1>
                <p className="text-slate-400">View documents shared by your clients</p>
            </div>

            {clients.length === 0 ? (
                <div className="card text-center py-12">
                    <FolderOpen className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">No Clients Yet</h3>
                    <p className="text-slate-400">
                        Accept client invitations to view their shared documents
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {clients.map((client) => (
                        <div
                            key={client.id}
                            onClick={() => navigate(`/share/documents/${client.id}`)}
                            className="card hover:border-blue-500/50 transition-all cursor-pointer group"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="w-12 h-12 bg-blue-900/30 rounded-lg flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
                                    <Building size={24} />
                                </div>
                                <ChevronRight className="text-slate-600 group-hover:text-blue-400 transition-colors" size={20} />
                            </div>

                            <h3 className="text-lg font-bold text-white mb-2 truncate">
                                {client.name}
                            </h3>

                            <div className="space-y-1 text-sm text-slate-400 mb-4">
                                {client.gstin && (
                                    <p className="truncate">GSTIN: {client.gstin}</p>
                                )}
                                {client.pan && (
                                    <p className="truncate">PAN: {client.pan}</p>
                                )}
                            </div>

                            <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                                <div className="flex items-center gap-2 text-slate-400">
                                    <FileText size={16} />
                                    <span className="text-sm">
                                        {documentCounts[client.id] || 0} documents
                                    </span>
                                </div>
                                <div className="flex items-center gap-2 text-slate-500 text-xs">
                                    <Calendar size={14} />
                                    <span>
                                        {new Date(client.created_at).toLocaleDateString()}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default SharedDocumentsList;
