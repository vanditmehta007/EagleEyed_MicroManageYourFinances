import React, { useState, useRef, useEffect } from 'react';
import { Upload, File, X, CheckCircle, AlertTriangle, Folder, Share2, Eye, Cloud, Key, FileSpreadsheet, Users, Camera, ScanLine } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import DocumentScanner from '../components/DocumentScanner';

const DOCUMENT_CATEGORIES = {
    mandatory: [
        'Bank Statement', 'Sales Invoice', 'Purchase Invoice', 'Expense Bill',
        'Cash Expense Summary', 'Payment Gateway Report', 'UPI Transaction Export', 'Payroll Sheet'
    ],
    gst: ['GSTR-2B JSON', 'GSTR-1 JSON', 'E-Invoice JSON'],
    yearly: ['Fixed Asset Bill', 'Loan Statement', 'Previous Year P&L/BS', 'Investment Proof', 'Insurance Certificate'],
    optional: ['Rent Agreement', 'Tax Deduction Certificate', 'Auditor Query', 'Vendor Master', 'Customer Master']
};

const INTEGRATIONS = [
    { id: 'google-sheets', name: 'Google Sheets', icon: FileSpreadsheet, color: 'emerald', requiresAuth: true },
    { id: 'zoho-books', name: 'Zoho Books', icon: Cloud, color: 'blue', requiresAuth: true },
    { id: 'tally', name: 'Tally', icon: FileSpreadsheet, color: 'orange', requiresAuth: false },
    { id: 'khatabook', name: 'Khatabook', icon: Cloud, color: 'purple', requiresAuth: false },
];

interface UploadedFile {
    file: File;
    category: string;
    status: 'pending' | 'verified' | 'rejected' | 'analyzing';
    path: string;
    extractedText?: string;
}

interface IntegrationModal {
    isOpen: boolean;
    platform: string;
    requiresAuth: boolean;
}

interface Client {
    id: string;
    name: string;
}

const DocumentUpload: React.FC = () => {
    const { user } = useAuth();
    const [dragActive, setDragActive] = useState(false);
    const [files, setFiles] = useState<UploadedFile[]>([]);
    const [selectedCategory, setSelectedCategory] = useState<string>('');
    const [selectedClientId, setSelectedClientId] = useState<string>('');
    const [clients, setClients] = useState<Client[]>([]);
    const [integrationModal, setIntegrationModal] = useState<IntegrationModal>({ isOpen: false, platform: '', requiresAuth: false });
    const [integrationData, setIntegrationData] = useState({ apiKey: '', organizationId: '', file: null as File | null });
    const [importing, setImporting] = useState(false);
    const [showScanner, setShowScanner] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const navigate = useNavigate();

    const isCA = user?.role?.toLowerCase() === 'ca';

    useEffect(() => {
        const fetchProfileData = async () => {
            try {
                if (isCA) {
                    // Fetch all clients for CA
                    const res = await api.get('/clients/');
                    setClients(res.data || []);
                } else {
                    // Fetch the current user's client profile
                    const res = await api.get('/clients/');
                    if (res.data && res.data.length > 0) {
                        setSelectedClientId(res.data[0].id);
                    } else {
                        console.warn("No client profile found for this user");
                    }
                }
            } catch (e) {
                console.error("Failed to fetch profile data", e);
            }
        };
        fetchProfileData();
    }, [isCA]);

    const openIntegrationModal = async (platformId: string) => {
        const platform = INTEGRATIONS.find(i => i.id === platformId);
        if (platform) {
            setIntegrationModal({ isOpen: true, platform: platformId, requiresAuth: platform.requiresAuth });
            setIntegrationData({ apiKey: '', organizationId: '', file: null });

            // If platform requires auth, check if we have saved credentials
            if (platform.requiresAuth) {
                try {
                    const res = await api.get('/settings/integrations');
                    if (res.data && res.data[platformId]) {
                        const saved = res.data[platformId];
                        setIntegrationData({
                            apiKey: saved.apiKey || '',
                            organizationId: saved.organizationId || '',
                            file: null
                        });
                    }
                } catch (error) {
                    console.error('Failed to fetch saved credentials', error);
                }
            }
        }
    };

    const closeIntegrationModal = () => {
        setIntegrationModal({ isOpen: false, platform: '', requiresAuth: false });
        setIntegrationData({ apiKey: '', organizationId: '', file: null });
    };

    const handleIntegrationImport = async () => {
        if (!selectedClientId) {
            alert('Client profile not found');
            return;
        }

        setImporting(true);
        try {
            const platform = integrationModal.platform;

            if (platform === 'zoho-books') {
                if (!integrationData.apiKey || !integrationData.organizationId) {
                    alert('Please provide API Key and Organization ID');
                    return;
                }
                await api.post('/import/zoho-books', {
                    client_id: selectedClientId,
                    api_key: integrationData.apiKey,
                    organization_id: integrationData.organizationId
                });
                alert('Successfully imported from Zoho Books!');
            } else if (platform === 'khatabook' || platform === 'tally' || platform === 'google-sheets') {
                if (!integrationData.file) {
                    alert('Please select a file to import');
                    return;
                }
                const formData = new FormData();
                formData.append('file', integrationData.file);
                formData.append('client_id', selectedClientId);

                const endpoint = platform === 'khatabook' ? '/import/khatabook' : '/import/excel-csv';
                await api.post(endpoint, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                alert(`Successfully imported from ${INTEGRATIONS.find(i => i.id === platform)?.name}!`);
            }

            closeIntegrationModal();
        } catch (error: any) {
            console.error('Import failed', error);
            alert(`Import failed: ${error.response?.data?.detail || error.message}`);
        } finally {
            setImporting(false);
        }
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            processFiles(Array.from(e.dataTransfer.files));
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            processFiles(Array.from(e.target.files));
        }
    };

    const handleScanCapture = (file: File, text: string) => {
        setShowScanner(false);
        processFiles([file], text);
    };

    const processFiles = async (newFiles: File[], extractedText?: string) => {
        if (!selectedCategory) {
            alert('Please select a document category first!');
            return;
        }
        if (!selectedClientId) {
            alert('Client profile not found. Please ensure you have created a profile in the dashboard.');
            return;
        }

        const processed = newFiles.map(file => ({
            file,
            category: selectedCategory,
            status: 'analyzing' as const,
            path: `Client/${selectedCategory}/${file.name}`,
            extractedText
        }));

        setFiles(prev => [...prev, ...processed]);

        for (const fileObj of processed) {
            const formData = new FormData();
            formData.append('file', fileObj.file);
            formData.append('client_id', selectedClientId);
            formData.append('folder_category', selectedCategory);
            if (fileObj.extractedText) {
                formData.append('extracted_text', fileObj.extractedText);
            }

            try {
                await api.post('/documents/upload', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });

                setFiles(current => current.map(f =>
                    f.file === fileObj.file ? { ...f, status: 'verified' } : f
                ));

            } catch (error) {
                console.error("Upload failed", error);
                setFiles(current => current.map(f =>
                    f.file === fileObj.file ? { ...f, status: 'rejected' } : f
                ));
            }
        }
    };

    const removeFile = (index: number) => {
        setFiles((prev) => prev.filter((_, i) => i !== index));
    };

    const handleShare = (file: UploadedFile) => {
        const shareId = Math.random().toString(36).substring(7);
        const link = `${window.location.origin}/share/${shareId}`;
        prompt('Share this link (requires login to view):', link);
    };

    const handleView = (file: UploadedFile) => {
        const url = URL.createObjectURL(file.file);
        window.open(url, '_blank');
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
        >
            <div>
                <h1 className="text-3xl font-bold tracking-tight mb-2">Upload Documents</h1>
                <p className="text-muted-foreground">Upload financial documents or import from accounting platforms</p>
            </div>

            {/* Integration Options */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Cloud className="w-5 h-5 text-blue-600" />
                        Import from Accounting Platforms
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {INTEGRATIONS.map((integration) => {
                            const Icon = integration.icon;
                            return (
                                <Button
                                    key={integration.id}
                                    variant="outline"
                                    className={`h-auto py-6 flex flex-col gap-2 hover:border-${integration.color}-200 hover:bg-${integration.color}-50`}
                                    onClick={() => openIntegrationModal(integration.id)}
                                >
                                    <Icon className={`w-8 h-8 text-${integration.color}-600`} />
                                    <span className="font-medium">{integration.name}</span>
                                    {integration.requiresAuth && (
                                        <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                                            <Key size={10} /> API Required
                                        </span>
                                    )}
                                </Button>
                            );
                        })}
                    </div>
                </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <Card>
                        <CardContent className="p-6 space-y-6">
                            {/* Selectors */}
                            <div className="space-y-4">
                                {isCA && (
                                    <div className="space-y-2">
                                        <Label>Select Client</Label>
                                        <div className="relative">
                                            <Users className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                            <select
                                                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 pl-9 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 appearance-none"
                                                value={selectedClientId}
                                                onChange={(e) => setSelectedClientId(e.target.value)}
                                            >
                                                <option value="">Select a client...</option>
                                                {clients.map(client => (
                                                    <option key={client.id} value={client.id}>{client.name}</option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                )}

                                <div className="space-y-2">
                                    <Label>Document Category</Label>
                                    <select
                                        className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 appearance-none"
                                        value={selectedCategory}
                                        onChange={(e) => setSelectedCategory(e.target.value)}
                                    >
                                        <option value="">Select Category...</option>
                                        <optgroup label="Mandatory Monthly">
                                            {DOCUMENT_CATEGORIES.mandatory.map(c => <option key={c} value={c}>{c}</option>)}
                                        </optgroup>
                                        <optgroup label="GST Related">
                                            {DOCUMENT_CATEGORIES.gst.map(c => <option key={c} value={c}>{c}</option>)}
                                        </optgroup>
                                        <optgroup label="Yearly">
                                            {DOCUMENT_CATEGORIES.yearly.map(c => <option key={c} value={c}>{c}</option>)}
                                        </optgroup>
                                        <optgroup label="Optional">
                                            {DOCUMENT_CATEGORIES.optional.map(c => <option key={c} value={c}>{c}</option>)}
                                        </optgroup>
                                    </select>
                                </div>
                            </div>

                            {/* Scan Button */}
                            <div className="flex justify-end">
                                <Button
                                    onClick={() => {
                                        if (!selectedCategory) {
                                            alert('Please select a document category first!');
                                            return;
                                        }
                                        setShowScanner(true);
                                    }}
                                    className="gap-2 bg-blue-600 hover:bg-blue-700"
                                >
                                    <ScanLine size={18} />
                                    Scan Document
                                </Button>
                            </div>

                            {/* Drop Zone */}
                            <div
                                className={`border-2 border-dashed rounded-xl p-10 text-center transition-all duration-200 ${dragActive
                                    ? 'border-primary bg-primary/5'
                                    : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted'
                                    }`}
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                            >
                                <input
                                    ref={inputRef}
                                    type="file"
                                    multiple
                                    className="hidden"
                                    onChange={handleChange}
                                />

                                <div className="flex flex-col items-center gap-4">
                                    <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
                                        <Upload className="w-8 h-8 text-muted-foreground" />
                                    </div>
                                    <div>
                                        <p className="text-lg font-medium">
                                            Drag & drop files here, or{' '}
                                            <button
                                                onClick={() => inputRef.current?.click()}
                                                className="text-primary hover:underline"
                                            >
                                                browse
                                            </button>
                                        </p>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            Select a category above before uploading
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* File List */}
                    <AnimatePresence>
                        {files.length > 0 && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                className="space-y-3"
                            >
                                <h3 className="text-lg font-medium">Uploaded Files</h3>
                                {files.map((fileObj, index) => (
                                    <motion.div
                                        key={index}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: 20 }}
                                        className="bg-card border rounded-lg p-4 flex items-center justify-between group hover:shadow-md transition-all"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
                                                <File className="w-5 h-5 text-muted-foreground" />
                                            </div>
                                            <div>
                                                <p className="font-medium">{fileObj.file.name}</p>
                                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                    <Folder size={12} />
                                                    <span>{fileObj.path}</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-4">
                                            {fileObj.status === 'analyzing' && (
                                                <span className="text-amber-600 text-sm flex items-center gap-1">
                                                    <AlertTriangle size={14} /> Uploading...
                                                </span>
                                            )}
                                            {fileObj.status === 'verified' && (
                                                <span className="text-emerald-600 text-sm flex items-center gap-1">
                                                    <CheckCircle size={14} /> Uploaded
                                                </span>
                                            )}
                                            {fileObj.status === 'rejected' && (
                                                <span className="text-destructive text-sm flex items-center gap-1">
                                                    <X size={14} /> Failed
                                                </span>
                                            )}

                                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <Button variant="ghost" size="icon" onClick={() => handleView(fileObj)} title="View">
                                                    <Eye size={16} className="text-blue-600" />
                                                </Button>
                                                <Button variant="ghost" size="icon" onClick={() => handleShare(fileObj)} title="Share">
                                                    <Share2 size={16} className="text-purple-600" />
                                                </Button>
                                                <Button variant="ghost" size="icon" onClick={() => removeFile(index)} title="Remove">
                                                    <X size={16} className="text-destructive" />
                                                </Button>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                <div className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Required Documents</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <h4 className="text-sm font-semibold text-blue-600 mb-2">Mandatory Monthly</h4>
                                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                                    {DOCUMENT_CATEGORIES.mandatory.slice(0, 5).map(d => <li key={d}>{d}</li>)}
                                    <li>...and more</li>
                                </ul>
                            </div>

                            <div>
                                <h4 className="text-sm font-semibold text-emerald-600 mb-2">GST Related</h4>
                                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                                    {DOCUMENT_CATEGORIES.gst.map(d => <li key={d}>{d}</li>)}
                                </ul>
                            </div>

                            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                                <p className="text-xs text-blue-700">
                                    <strong>Tip:</strong> AI will automatically sort your files into: <br />
                                    <span className="font-mono mt-1 block">Client / Year / Month / Category</span>
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Integration Modal */}
            <AnimatePresence>
                {integrationModal.isOpen && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="w-full max-w-md"
                        >
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-xl font-bold">
                                        Import from {INTEGRATIONS.find(i => i.id === integrationModal.platform)?.name}
                                    </CardTitle>
                                    <Button variant="ghost" size="icon" onClick={closeIntegrationModal}>
                                        <X size={20} />
                                    </Button>
                                </CardHeader>
                                <CardContent className="space-y-4 pt-4">
                                    {integrationModal.requiresAuth ? (
                                        <>
                                            <div className="space-y-2">
                                                <Label>API Key</Label>
                                                <Input
                                                    placeholder="Enter your API key"
                                                    value={integrationData.apiKey}
                                                    onChange={(e) => setIntegrationData(prev => ({ ...prev, apiKey: e.target.value }))}
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label>Organization ID</Label>
                                                <Input
                                                    placeholder="Enter organization ID"
                                                    value={integrationData.organizationId}
                                                    onChange={(e) => setIntegrationData(prev => ({ ...prev, organizationId: e.target.value }))}
                                                />
                                            </div>
                                        </>
                                    ) : (
                                        <div className="space-y-2">
                                            <Label>Upload Export File</Label>
                                            <input
                                                ref={fileInputRef}
                                                type="file"
                                                accept=".csv,.xlsx,.xls"
                                                className="hidden"
                                                onChange={(e) => {
                                                    if (e.target.files && e.target.files[0]) {
                                                        setIntegrationData(prev => ({ ...prev, file: e.target.files![0] }));
                                                    }
                                                }}
                                            />
                                            <Button
                                                variant="outline"
                                                className="w-full h-auto py-8 border-dashed"
                                                onClick={() => fileInputRef.current?.click()}
                                            >
                                                {integrationData.file ? (
                                                    <div className="flex items-center justify-center gap-2">
                                                        <File size={20} />
                                                        <span>{integrationData.file.name}</span>
                                                    </div>
                                                ) : (
                                                    <div className="text-muted-foreground">
                                                        Click to select file (CSV, Excel)
                                                    </div>
                                                )}
                                            </Button>
                                        </div>
                                    )}

                                    <div className="flex gap-3 mt-6">
                                        <Button variant="outline" className="flex-1" onClick={closeIntegrationModal}>
                                            Cancel
                                        </Button>
                                        <Button
                                            className="flex-1"
                                            onClick={handleIntegrationImport}
                                            disabled={importing}
                                        >
                                            {importing ? 'Importing...' : 'Import'}
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            {/* Document Scanner */}
            {showScanner && (
                <DocumentScanner
                    onCapture={handleScanCapture}
                    onClose={() => setShowScanner(false)}
                />
            )}
        </motion.div>
    );
};

export default DocumentUpload;
