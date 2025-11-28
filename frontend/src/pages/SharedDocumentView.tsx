import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FileText, Folder, ChevronRight, Download, Eye, Calendar } from 'lucide-react';
import api from '../services/api';

interface Document {
    id: string;
    original_filename: string;
    file_type: string;
    created_at: string;
    file_size?: number;
}

const SharedDocumentView: React.FC = () => {
    const { clientId } = useParams<{ clientId: string }>();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [client, setClient] = useState<any>(null);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [organizedDocs, setOrganizedDocs] = useState<any>({});
    const [expandedYears, setExpandedYears] = useState<Set<string>>(new Set());
    const [expandedMonths, setExpandedMonths] = useState<Set<string>>(new Set());

    useEffect(() => {
        fetchData();
    }, [clientId]);

    const fetchData = async () => {
        try {
            setLoading(true);

            // Fetch client details
            const clientRes = await api.get(`/clients/${clientId}`);
            setClient(clientRes.data);

            // Fetch documents
            const docsRes = await api.get(`/documents/?client_id=${clientId}`);
            const docs = docsRes.data;
            setDocuments(docs);

            // Organize documents by year and month
            const organized: any = {};
            docs.forEach((doc: Document) => {
                const date = new Date(doc.created_at);
                const year = date.getFullYear().toString();
                const month = date.toLocaleString('default', { month: 'long' });

                if (!organized[year]) {
                    organized[year] = {};
                }
                if (!organized[year][month]) {
                    organized[year][month] = [];
                }
                organized[year][month].push(doc);
            });

            setOrganizedDocs(organized);
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setLoading(false);
        }
    };

    const toggleYear = (year: string) => {
        const newExpanded = new Set(expandedYears);
        if (newExpanded.has(year)) {
            newExpanded.delete(year);
        } else {
            newExpanded.add(year);
        }
        setExpandedYears(newExpanded);
    };

    const toggleMonth = (yearMonth: string) => {
        const newExpanded = new Set(expandedMonths);
        if (newExpanded.has(yearMonth)) {
            newExpanded.delete(yearMonth);
        } else {
            newExpanded.add(yearMonth);
        }
        setExpandedMonths(newExpanded);
    };

    const handleView = async (doc: Document) => {
        try {
            const res = await api.get(`/documents/${doc.id}/preview`);
            if (res.data.url) {
                window.open(res.data.url, '_blank');
            }
        } catch (error) {
            console.error("Failed to preview document", error);
            alert("Failed to preview document");
        }
    };

    const handleDownload = async (doc: Document) => {
        try {
            const response = await api.get(`/documents/${doc.id}/download`, {
                responseType: 'blob'
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', doc.original_filename);
            document.body.appendChild(link);
            link.click();
            link.parentNode?.removeChild(link);
        } catch (error) {
            console.error("Failed to download document", error);
            alert("Failed to download document");
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">
                <div className="animate-pulse">Loading documents...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <button
                        onClick={() => navigate('/')}
                        className="text-slate-400 hover:text-white mb-4 flex items-center gap-2"
                    >
                        ← Back to Dashboard
                    </button>
                    <h1 className="text-3xl font-bold text-white mb-2">
                        {client?.name || 'Client'} Documents
                    </h1>
                    <p className="text-slate-400">
                        {client?.gstin && `GSTIN: ${client.gstin}`}
                        {client?.gstin && client?.pan && ' • '}
                        {client?.pan && `PAN: ${client.pan}`}
                    </p>
                    <p className="text-slate-500 text-sm mt-2">
                        Total Documents: {documents.length}
                    </p>
                </div>

                {/* Document Tree */}
                <div className="card">
                    {Object.keys(organizedDocs).length === 0 ? (
                        <div className="text-center py-12 text-slate-400">
                            No documents found for this client.
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {Object.keys(organizedDocs).sort((a, b) => parseInt(b) - parseInt(a)).map((year) => (
                                <div key={year} className="border-b border-slate-700/50 last:border-0">
                                    {/* Year Header */}
                                    <button
                                        onClick={() => toggleYear(year)}
                                        className="w-full flex items-center gap-3 p-4 hover:bg-slate-800/50 transition-colors text-left"
                                    >
                                        <ChevronRight
                                            className={`text-slate-400 transition-transform ${expandedYears.has(year) ? 'rotate-90' : ''
                                                }`}
                                            size={20}
                                        />
                                        <Calendar className="text-blue-400" size={20} />
                                        <span className="text-white font-semibold text-lg">{year}</span>
                                        <span className="text-slate-500 text-sm ml-auto">
                                            {Object.values(organizedDocs[year]).flat().length} documents
                                        </span>
                                    </button>

                                    {/* Months */}
                                    {expandedYears.has(year) && (
                                        <div className="pl-8 bg-slate-900/30">
                                            {Object.keys(organizedDocs[year]).map((month) => {
                                                const yearMonth = `${year}-${month}`;
                                                return (
                                                    <div key={month} className="border-t border-slate-700/30">
                                                        {/* Month Header */}
                                                        <button
                                                            onClick={() => toggleMonth(yearMonth)}
                                                            className="w-full flex items-center gap-3 p-3 hover:bg-slate-800/30 transition-colors text-left"
                                                        >
                                                            <ChevronRight
                                                                className={`text-slate-400 transition-transform ${expandedMonths.has(yearMonth) ? 'rotate-90' : ''
                                                                    }`}
                                                                size={18}
                                                            />
                                                            <Folder className="text-emerald-400" size={18} />
                                                            <span className="text-white font-medium">{month}</span>
                                                            <span className="text-slate-500 text-sm ml-auto">
                                                                {organizedDocs[year][month].length} files
                                                            </span>
                                                        </button>

                                                        {/* Documents */}
                                                        {expandedMonths.has(yearMonth) && (
                                                            <div className="pl-8 space-y-1 pb-2">
                                                                {organizedDocs[year][month].map((doc: Document) => (
                                                                    <div
                                                                        key={doc.id}
                                                                        className="flex items-center gap-3 p-3 hover:bg-slate-800/30 rounded-lg transition-colors group"
                                                                    >
                                                                        <FileText className="text-slate-400" size={16} />
                                                                        <div className="flex-1 min-w-0">
                                                                            <p className="text-white text-sm font-medium truncate">
                                                                                {doc.original_filename}
                                                                            </p>
                                                                            <p className="text-slate-500 text-xs">
                                                                                {doc.file_type?.replace('_', ' ')} •{' '}
                                                                                {doc.file_size
                                                                                    ? `${(doc.file_size / 1024).toFixed(1)} KB`
                                                                                    : 'Unknown size'}
                                                                            </p>
                                                                        </div>
                                                                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                            <button
                                                                                onClick={() => handleView(doc)}
                                                                                className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors"
                                                                                title="View"
                                                                            >
                                                                                <Eye size={16} />
                                                                            </button>
                                                                            <button
                                                                                onClick={() => handleDownload(doc)}
                                                                                className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors"
                                                                                title="Download"
                                                                            >
                                                                                <Download size={16} />
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SharedDocumentView;
