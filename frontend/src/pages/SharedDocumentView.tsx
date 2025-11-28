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
            <div className="min-h-screen bg-background flex items-center justify-center text-foreground">
                <div className="animate-pulse text-muted-foreground">Loading documents...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <button
                        onClick={() => navigate('/')}
                        className="text-muted-foreground hover:text-primary mb-4 flex items-center gap-2 transition-colors font-medium"
                    >
                        ← Back to Dashboard
                    </button>
                    <h1 className="text-3xl font-bold text-foreground mb-2 tracking-tight">
                        {client?.name || 'Client'} Documents
                    </h1>
                    <div className="flex items-center gap-3 text-muted-foreground text-sm">
                        {client?.gstin && (
                            <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded-md border border-blue-100 font-medium">
                                GSTIN: {client.gstin}
                            </span>
                        )}
                        {client?.pan && (
                            <span className="bg-emerald-50 text-emerald-700 px-2 py-1 rounded-md border border-emerald-100 font-medium">
                                PAN: {client.pan}
                            </span>
                        )}
                        <span className="ml-auto font-medium">Total Documents: {documents.length}</span>
                    </div>
                </div>

                {/* Document Tree */}
                <div className="glass border border-border/50 rounded-xl shadow-sm overflow-hidden">
                    {Object.keys(organizedDocs).length === 0 ? (
                        <div className="text-center py-16 text-muted-foreground">
                            <div className="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Folder className="w-8 h-8 text-muted-foreground/50" />
                            </div>
                            <p className="text-lg font-medium text-foreground/80">No documents found</p>
                            <p className="text-sm">Documents uploaded by this client will appear here.</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-border/50">
                            {Object.keys(organizedDocs).sort((a, b) => parseInt(b) - parseInt(a)).map((year) => (
                                <div key={year} className="bg-white/40">
                                    {/* Year Header */}
                                    <button
                                        onClick={() => toggleYear(year)}
                                        className="w-full flex items-center gap-4 p-5 hover:bg-white/60 transition-all text-left group"
                                    >
                                        <ChevronRight
                                            className={`text-muted-foreground transition-transform duration-200 ${expandedYears.has(year) ? 'rotate-90' : ''}`}
                                            size={20}
                                        />
                                        <div className="p-2 bg-blue-100 text-blue-600 rounded-lg group-hover:scale-105 transition-transform">
                                            <Calendar size={20} />
                                        </div>
                                        <span className="text-foreground font-bold text-lg">{year}</span>
                                        <span className="text-muted-foreground text-sm ml-auto bg-white/50 px-3 py-1 rounded-full border border-border/50">
                                            {Object.values(organizedDocs[year]).flat().length} documents
                                        </span>
                                    </button>

                                    {/* Months */}
                                    {expandedYears.has(year) && (
                                        <div className="bg-muted/30 border-t border-border/50">
                                            {Object.keys(organizedDocs[year]).map((month) => {
                                                const yearMonth = `${year}-${month}`;
                                                return (
                                                    <div key={month} className="border-t border-border/50 first:border-0">
                                                        {/* Month Header */}
                                                        <button
                                                            onClick={() => toggleMonth(yearMonth)}
                                                            className="w-full flex items-center gap-3 p-4 pl-12 hover:bg-white/50 transition-colors text-left group"
                                                        >
                                                            <ChevronRight
                                                                className={`text-muted-foreground transition-transform duration-200 ${expandedMonths.has(yearMonth) ? 'rotate-90' : ''}`}
                                                                size={18}
                                                            />
                                                            <Folder className="text-emerald-600 group-hover:text-emerald-500 transition-colors" size={18} />
                                                            <span className="text-foreground font-semibold">{month}</span>
                                                            <span className="text-muted-foreground text-xs ml-auto">
                                                                {organizedDocs[year][month].length} files
                                                            </span>
                                                        </button>

                                                        {/* Documents */}
                                                        {expandedMonths.has(yearMonth) && (
                                                            <div className="pl-16 pr-4 pb-3 space-y-1">
                                                                {organizedDocs[year][month].map((doc: Document) => (
                                                                    <div
                                                                        key={doc.id}
                                                                        className="flex items-center gap-4 p-3 hover:bg-white rounded-xl border border-transparent hover:border-blue-100 hover:shadow-sm transition-all group cursor-default"
                                                                    >
                                                                        <div className="p-2 bg-white border border-border/50 rounded-lg text-muted-foreground group-hover:text-blue-600 group-hover:border-blue-100 transition-colors">
                                                                            <FileText size={18} />
                                                                        </div>
                                                                        <div className="flex-1 min-w-0">
                                                                            <p className="text-foreground text-sm font-semibold truncate group-hover:text-primary transition-colors">
                                                                                {doc.original_filename}
                                                                            </p>
                                                                            <p className="text-muted-foreground text-xs flex items-center gap-2 mt-0.5">
                                                                                <span className="uppercase tracking-wider text-[10px] font-bold bg-muted px-1.5 py-0.5 rounded text-muted-foreground/70">
                                                                                    {doc.file_type?.replace('_', ' ')}
                                                                                </span>
                                                                                <span>•</span>
                                                                                <span>
                                                                                    {doc.file_size
                                                                                        ? `${(doc.file_size / 1024).toFixed(1)} KB`
                                                                                        : 'Unknown size'}
                                                                                </span>
                                                                            </p>
                                                                        </div>
                                                                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                            <button
                                                                                onClick={() => handleView(doc)}
                                                                                className="p-2 hover:bg-blue-50 hover:text-blue-600 rounded-lg text-muted-foreground transition-colors"
                                                                                title="View"
                                                                            >
                                                                                <Eye size={18} />
                                                                            </button>
                                                                            <button
                                                                                onClick={() => handleDownload(doc)}
                                                                                className="p-2 hover:bg-blue-50 hover:text-blue-600 rounded-lg text-muted-foreground transition-colors"
                                                                                title="Download"
                                                                            >
                                                                                <Download size={18} />
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
