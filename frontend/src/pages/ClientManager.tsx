import React, { useState, useEffect } from 'react';
import { Search, Plus, Trash2, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

interface Client {
    id: string;
    name: string;
    email: string;
    status: 'Active' | 'Inactive';
    documents: number;
}

const ClientManager: React.FC = () => {
    const [clients, setClients] = useState<Client[]>([]);
    const [loading, setLoading] = useState(true);
    const { user } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (user?.role === 'client') {
            navigate('/client-dashboard');
            return;
        }
        fetchClients();
    }, [user, navigate]);

    const fetchClients = async () => {
        try {
            const response = await api.get('/clients/');
            // Map backend response to frontend interface
            const mappedClients = response.data.map((c: any) => ({
                id: c.id,
                name: c.business_name || 'Unnamed Client',
                email: c.gstin || 'No GSTIN', // Using GSTIN as secondary info for now
                status: 'Active', // Mock status
                documents: 0 // Mock count
            }));
            setClients(mappedClients);
        } catch (err) {
            console.error('Failed to fetch clients:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (window.confirm('Are you sure you want to delete this client?')) {
            // await api.delete(`/clients/${id}`); // If endpoint exists
            setClients(clients.filter(c => c.id !== id));
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Client Manager</h1>
                    <p className="text-slate-400">Manage your clients and their documents</p>
                </div>
                <button className="btn-primary flex items-center gap-2">
                    <Plus size={20} />
                    Add Client
                </button>
            </div>

            <div className="card">
                <div className="flex items-center gap-4 mb-6">
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                        <input
                            type="text"
                            placeholder="Search clients..."
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-blue-500"
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-700 text-slate-400 text-sm">
                                <th className="p-4 font-medium">Name</th>
                                <th className="p-4 font-medium">Email/GSTIN</th>
                                <th className="p-4 font-medium">Status</th>
                                <th className="p-4 font-medium">Documents</th>
                                <th className="p-4 font-medium text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="text-slate-300">
                            {loading ? (
                                <tr><td colSpan={5} className="p-4 text-center">Loading clients...</td></tr>
                            ) : clients.length === 0 ? (
                                <tr><td colSpan={5} className="p-4 text-center">No clients found.</td></tr>
                            ) : (
                                clients.map((client) => (
                                    <tr key={client.id} className="border-b border-slate-700/50 hover:bg-slate-700/20 transition-colors">
                                        <td className="p-4 font-medium text-white">{client.name}</td>
                                        <td className="p-4">{client.email}</td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${client.status === 'Active' ? 'bg-emerald-900/30 text-emerald-400' : 'bg-slate-700 text-slate-400'
                                                }`}>
                                                {client.status}
                                            </span>
                                        </td>
                                        <td className="p-4">{client.documents}</td>
                                        <td className="p-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <button className="p-2 hover:bg-slate-700 rounded-lg text-blue-400 transition-colors" title="View Details">
                                                    <Eye size={18} />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(client.id)}
                                                    className="p-2 hover:bg-red-900/20 rounded-lg text-red-400 transition-colors"
                                                    title="Delete Client"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                )))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default ClientManager;
