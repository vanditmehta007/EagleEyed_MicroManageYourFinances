import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, Building, UserCheck, ArrowRight } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Avatar, AvatarFallback } from '../components/ui/avatar';

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
            <div className="min-h-screen bg-background flex items-center justify-center text-foreground">
                <div className="flex flex-col items-center gap-4 animate-pulse">
                    <div className="w-12 h-12 rounded-full bg-muted" />
                    <div className="h-4 w-32 bg-muted rounded" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="w-full max-w-md"
                >
                    <Card className="border-destructive/50">
                        <CardHeader className="text-center">
                            <div className="mx-auto w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mb-4">
                                <XCircle className="w-8 h-8 text-destructive" />
                            </div>
                            <CardTitle className="text-destructive">Invitation Error</CardTitle>
                            <CardDescription>{error}</CardDescription>
                        </CardHeader>
                        <CardFooter>
                            <Button onClick={() => navigate('/')} className="w-full" variant="outline">
                                Go Home
                            </Button>
                        </CardFooter>
                    </Card>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4 relative overflow-hidden">
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="w-full max-w-md z-10"
            >
                <Card className="shadow-xl border-border bg-card">
                    <CardHeader className="text-center pb-8">
                        <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-6 text-blue-600 ring-8 ring-blue-100">
                            <UserCheck size={40} />
                        </div>
                        <CardTitle className="text-2xl">Client Invitation</CardTitle>
                        <CardDescription>
                            You have been invited to manage financial documents for:
                        </CardDescription>
                    </CardHeader>

                    <CardContent className="pb-8">
                        <div className="bg-muted rounded-xl p-6 border border-border flex items-center gap-4 mb-8">
                            <Avatar className="h-12 w-12 rounded-lg">
                                <AvatarFallback className="rounded-lg bg-background border border-border">
                                    <Building className="w-6 h-6 text-muted-foreground" />
                                </AvatarFallback>
                            </Avatar>
                            <div>
                                <h3 className="text-lg font-bold">
                                    {inviteData?.resource_data?.name || "Unknown Business"}
                                </h3>
                                <p className="text-sm text-muted-foreground font-mono">
                                    {inviteData?.resource_data?.gstin || "No GSTIN"}
                                </p>
                            </div>
                        </div>

                        <div className="space-y-4">
                            {!isAuthenticated ? (
                                <Button
                                    onClick={handleAccept}
                                    className="w-full h-12 text-lg"
                                >
                                    Login to Accept <ArrowRight className="ml-2 w-4 h-4" />
                                </Button>
                            ) : (
                                <Button
                                    onClick={handleAccept}
                                    disabled={accepting}
                                    className="w-full h-12 text-lg"
                                >
                                    {accepting ? (
                                        <div className="flex items-center gap-2">
                                            <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                                            Accessing...
                                        </div>
                                    ) : (
                                        <>
                                            <CheckCircle className="mr-2 w-5 h-5" />
                                            {inviteData?.resource_data?.assigned_ca_id === user?.id ? 'View Documents' : 'Accept Client'}
                                        </>
                                    )}
                                </Button>
                            )}

                            <Button
                                variant="ghost"
                                onClick={() => navigate('/')}
                                className="w-full"
                            >
                                Cancel
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    );
};

export default AcceptInvite;
