import React, { useState, useRef, useEffect } from 'react';
import { Upload, File, X, CheckCircle, AlertTriangle, Folder, Share2, Eye, Cloud, Key, FileSpreadsheet, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

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

    const processFiles = async (newFiles: File[]) => {
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
            path: `Client/${selectedCategory}/${file.name}`
        }));

        setFiles(prev => [...prev, ...processed]);

        for (const fileObj of processed) {
            const formData = new FormData();
            formData.append('file', fileObj.file);
            formData.append('client_id', selectedClientId);
            formData.append('folder_category', selectedCategory);

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
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">Upload Documents</h1>
                <p className="text-slate-400">Upload financial documents or import from accounting platforms</p>
            </div>

            {/* Integration Options */}
            <div className="card">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <Cloud size={20} className="text-blue-400" />
                    Import from Accounting Platforms
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {INTEGRATIONS.map((integration) => {
                        const Icon = integration.icon;
                        return (
                            <button
                                key={integration.id}
                                onClick={() => openIntegrationModal(integration.id)}
                                className={`p-4 rounded-lg border-2 border-${integration.color}-500/30 bg-${integration.color}-900/10 hover:bg-${integration.color}-900/20 hover:border-${integration.color}-500/50 transition-all group`}
                            >
                                <Icon className={`w-8 h-8 text-${integration.color}-400 mx-auto mb-2 group-hover:scale-110 transition-transform`} />
                                <p className="text-sm font-medium text-white text-center">{integration.name}</p>
                                {integration.requiresAuth && (
                                    <p className="text-xs text-slate-500 text-center mt-1 flex items-center justify-center gap-1">
                                        <Key size={10} /> API Required
                                    </p>
                                )}
                            </button>
                        );
                    })}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <div className="card">
                        <div className="mb-4 space-y-4">
                            {isCA && (
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                                        <Users size={16} className="text-blue-400" />
                                        Select Client
                                    </label>
                                    <select
                                        className="input-field"
                                        value={selectedClientId}
                                        onChange={(e) => setSelectedClientId(e.target.value)}
                                    >
                                        <option value="">Select a client...</option>
                                        {clients.map(client => (
                                            <option key={client.id} value={client.id}>{client.name}</option>
                                        ))}
                                    </select>
                                </div>
                            )}

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">Document Category</label>
                                <select
                                    className="input-field"
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

                        <div
                            className={`border-2 border-dashed rounded-xl p-10 text-center transition-all ${dragActive
                                ? 'border-blue-500 bg-blue-900/10'
                                : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800/50'
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
                                <div className="w-16 h-16 rounded-full bg-slate-700 flex items-center justify-center">
                                    <Upload className="w-8 h-8 text-blue-400" />
                                </div>
                                <div>
                                    <p className="text-lg font-medium text-white">
                                        Drag & drop files here, or{' '}
                                        <button
                                            onClick={() => inputRef.current?.click()}
                                            className="text-blue-400 hover:text-blue-300 underline"
                                        >
                                            browse
                                        </button>
                                    </p>
                                    <p className="text-sm text-slate-400 mt-1">
                                        Select a category above before uploading
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {files.length > 0 && (
                        <div className="space-y-3">
                            <h3 className="text-lg font-medium text-white">Uploaded Files</h3>
                            {files.map((fileObj, index) => (
                                <div key={index} className="card p-4 flex items-center justify-between group">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-lg bg-slate-700 flex items-center justify-center">
                                            <File className="w-5 h-5 text-slate-400" />
                                        </div>
                                        <div>
                                            <p className="font-medium text-white">{fileObj.file.name}</p>
                                            <div className="flex items-center gap-2 text-xs text-slate-400">
                                                <Folder size={12} />
                                                <span>{fileObj.path}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        {fileObj.status === 'analyzing' && (
                                            <span className="text-amber-400 text-sm flex items-center gap-1">
                                                <AlertTriangle size={14} /> Uploading...
                                            </span>
                                        )}
                                        {fileObj.status === 'verified' && (
                                            <span className="text-emerald-400 text-sm flex items-center gap-1">
                                                <CheckCircle size={14} /> Uploaded
                                            </span>
                                        )}
                                        {fileObj.status === 'rejected' && (
                                            <span className="text-red-400 text-sm flex items-center gap-1">
                                                <X size={14} /> Failed
                                            </span>
                                        )}

                                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button onClick={() => handleView(fileObj)} className="p-2 hover:bg-slate-700 rounded-lg text-blue-400" title="View">
                                                <Eye size={18} />
                                            </button>
                                            <button onClick={() => handleShare(fileObj)} className="p-2 hover:bg-slate-700 rounded-lg text-purple-400" title="Share">
                                                <Share2 size={18} />
                                            </button>
                                            <button onClick={() => removeFile(index)} className="p-2 hover:bg-slate-700 rounded-lg text-red-400" title="Remove">
                                                <X size={18} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="space-y-6">
                    <div className="card bg-slate-800/50 border-slate-700">
                        <h3 className="text-lg font-bold text-white mb-4">Required Documents</h3>

                        <div className="space-y-4">
                            <div>
                                <h4 className="text-sm font-semibold text-blue-400 mb-2">Mandatory Monthly</h4>
                                <ul className="text-sm text-slate-400 space-y-1 list-disc list-inside">
                                    {DOCUMENT_CATEGORIES.mandatory.slice(0, 5).map(d => <li key={d}>{d}</li>)}
                                    <li>...and more</li>
                                </ul>
                            </div>

                            <div>
                                <h4 className="text-sm font-semibold text-emerald-400 mb-2">GST Related</h4>
                                <ul className="text-sm text-slate-400 space-y-1 list-disc list-inside">
                                    {DOCUMENT_CATEGORIES.gst.map(d => <li key={d}>{d}</li>)}
                                </ul>
                            </div>

                            <div className="p-3 bg-blue-900/20 rounded-lg border border-blue-900/50">
                                <p className="text-xs text-blue-300">
                                    <strong>Tip:</strong> AI will automatically sort your files into: <br />
                                    <span className="font-mono mt-1 block">Client / Year / Month / Category</span>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Integration Modal */}
            {integrationModal.isOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="card max-w-md w-full">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-xl font-bold text-white">
                                Import from {INTEGRATIONS.find(i => i.id === integrationModal.platform)?.name}
                            </h3>
                            <button onClick={closeIntegrationModal} className="text-slate-400 hover:text-white">
                                <X size={24} />
                            </button>
                        </div>

                        <div className="space-y-4">
                            {integrationModal.requiresAuth ? (
                                <>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            API Key
                                        </label>
                                        <input
                                            type="text"
                                            className="input-field w-full"
                                            placeholder="Enter your API key"
                                            value={integrationData.apiKey}
                                            onChange={(e) => setIntegrationData(prev => ({ ...prev, apiKey: e.target.value }))}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            Organization ID
                                        </label>
                                        <input
                                            type="text"
                                            className="input-field w-full"
                                            placeholder="Enter organization ID"
                                            value={integrationData.organizationId}
                                            onChange={(e) => setIntegrationData(prev => ({ ...prev, organizationId: e.target.value }))}
                                        />
                                    </div>
                                </>
                            ) : (
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Upload Export File
                                    </label>
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
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="w-full p-4 border-2 border-dashed border-slate-600 rounded-lg hover:border-slate-500 transition-colors"
                                    >
                                        {integrationData.file ? (
                                            <div className="flex items-center justify-center gap-2 text-white">
                                                <File size={20} />
                                                <span>{integrationData.file.name}</span>
                                            </div>
                                        ) : (
                                            <div className="text-slate-400">
                                                Click to select file (CSV, Excel)
                                            </div>
                                        )}
                                    </button>
                                </div>
                            )}

                            <div className="flex gap-3 mt-6">
                                <button
                                    onClick={closeIntegrationModal}
                                    className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleIntegrationImport}
                                    disabled={importing}
                                    className="flex-1 btn-primary"
                                >
                                    {importing ? 'Importing...' : 'Import'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DocumentUpload;
