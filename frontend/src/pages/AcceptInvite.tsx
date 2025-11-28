import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, Building, UserCheck } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

const AcceptInvite: React.FC = () => {
    const { token } = useParams<{ token: string }>();
    const navigate = useNavigate();
    const { isAuthenticated, user } = useAuth();

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [inviteData, setInviteData] = useState<any>(null);
    const [accepting, setAccepting] = useState(false);

    useEffect(() => {
        if (!token) {
            setError("Invalid invite link");
            setLoading(false);
            return;
        }
        verifyToken();
    }, [token]);

    const verifyToken = async () => {
        try {
            // First, resolve the token to see what it is
            const res = await api.get(`/share/resolve/${token}`);

            if (!res.data) {
                setError("Failed to verify invitation - no response from server");
                setLoading(false);
                return;
            }

            if (!res.data.valid) {
                setError(res.data.error || "Invalid or expired link");
                setLoading(false);
                return;
            }

            if (res.data.resource_type !== 'client') {
                setError("This link is not for a client invitation");
                setLoading(false);
                return;
            }

            setInviteData(res.data);
        } catch (err) {
            console.error("Failed to verify token", err);
            setError("Failed to verify invitation");
        } finally {
            setLoading(false);
        }
    };

    const handleAccept = async () => {
        if (!isAuthenticated) {
            // Redirect to login, preserving the return URL
            navigate(`/login?returnUrl=/share/invite/${token}`);
            return;
        }

        if (user?.role !== 'ca') {
            setError("Only Chartered Accountants can accept client invitations.");
            return;
        }

        setAccepting(true);
        try {
            // Check if client is already assigned to this CA
            const clientResponse = await api.get(`/clients/${inviteData.resource_id}`);
            const client = clientResponse.data;

            if (client.assigned_ca_id === user.id) {
                // Client is already assigned to this CA, skip accept and go directly to documents
                navigate(`/share/documents/${inviteData.resource_id}`);
                return;
            }

            // Client not assigned yet, proceed with assignment
            await api.post('/clients/accept-invite', {
                token: token,
                client_id: inviteData.resource_id
            });

            // Success! Redirect to view this client's documents
            navigate(`/share/documents/${inviteData.resource_id}`);
        } catch (err: any) {
            console.error("Failed to accept invite", err);
            setError(err.response?.data?.detail || "Failed to accept invitation");
        } finally {
            setAccepting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">
                <div className="animate-pulse">Verifying invitation...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
                <div className="card max-w-md w-full text-center p-8">
                    <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                    <h2 className="text-xl font-bold text-white mb-2">Invitation Error</h2>
                    <p className="text-slate-400 mb-6">{error}</p>
                    <button onClick={() => navigate('/')} className="btn-primary w-full">
                        Go Home
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
            <div className="card max-w-md w-full p-8">
                <div className="text-center mb-8">
                    <div className="w-20 h-20 bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4 text-blue-400">
                        <UserCheck size={40} />
                    </div>
                    <h1 className="text-2xl font-bold text-white mb-2">Client Invitation</h1>
                    <p className="text-slate-400">
                        You have been invited to manage financial documents for:
                    </p>
                </div>

                <div className="bg-slate-900 rounded-xl p-6 border border-slate-800 mb-8 flex items-center gap-4">
                    <div className="w-12 h-12 bg-slate-800 rounded-lg flex items-center justify-center text-slate-400">
                        <Building size={24} />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-white">
                            {inviteData?.resource_data?.name || "Unknown Business"}
                        </h3>
                        <p className="text-sm text-slate-500">
                            {inviteData?.resource_data?.gstin || "No GSTIN"}
                        </p>
                    </div>
                </div>

                <div className="space-y-4">
                    {!isAuthenticated ? (
                        <button
                            onClick={handleAccept}
                            className="btn-primary w-full py-3 text-lg"
                        >
                            Login to Accept
                        </button>
                    ) : (
                        <button
                            onClick={handleAccept}
                            disabled={accepting}
                            className="btn-primary w-full py-3 text-lg flex items-center justify-center gap-2"
                        >
                            {accepting ? 'Accessing...' : (
                                <>
                                    <CheckCircle size={20} />
                                    {inviteData?.resource_data?.assigned_ca_id === user?.id ? 'View Documents' : 'Accept Client'}
                                </>
                            )}
                        </button>
                    )}

                    <button
                        onClick={() => navigate('/')}
                        className="w-full py-3 text-slate-400 hover:text-white transition-colors"
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AcceptInvite;
