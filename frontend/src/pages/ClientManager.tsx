import React, { useState, useEffect } from 'react';
import { Search, Plus, Trash2, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

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
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
        >
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight mb-2">Client Manager</h1>
                    <p className="text-muted-foreground">Manage your clients and their documents</p>
                </div>
                <Button className="flex items-center gap-2">
                    <Plus size={16} />
                    Add Client
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>Clients</CardTitle>
                        <div className="relative w-64">
                            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input placeholder="Search clients..." className="pl-8" />
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Name</TableHead>
                                    <TableHead>Email/GSTIN</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Documents</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="h-24 text-center">
                                            Loading clients...
                                        </TableCell>
                                    </TableRow>
                                ) : clients.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="h-24 text-center">
                                            No clients found.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    clients.map((client) => (
                                        <TableRow key={client.id}>
                                            <TableCell className="font-medium">
                                                <div className="flex items-center gap-3">
                                                    <Avatar className="h-8 w-8">
                                                        <AvatarFallback className="bg-primary/10 text-primary">
                                                            {client.name.substring(0, 2).toUpperCase()}
                                                        </AvatarFallback>
                                                    </Avatar>
                                                    {client.name}
                                                </div>
                                            </TableCell>
                                            <TableCell>{client.email}</TableCell>
                                            <TableCell>
                                                <Badge className={client.status === 'Active' ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200 border-emerald-200' : 'bg-muted text-muted-foreground'}>
                                                    {client.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>{client.documents}</TableCell>
                                            <TableCell className="text-right">
                                                <div className="flex items-center justify-end gap-2">
                                                    <Button variant="ghost" size="icon" title="View Details">
                                                        <Eye size={16} className="text-blue-600" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => handleDelete(client.id)}
                                                        title="Delete Client"
                                                    >
                                                        <Trash2 size={16} className="text-destructive" />
                                                    </Button>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
};

export default ClientManager;
