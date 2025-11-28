import React, { useEffect, useState } from 'react';
import { Calendar, ChevronRight, Folder, Download, FileText, Building, FileSpreadsheet, Eye } from 'lucide-react';
import api from '../services/api';

interface Transaction {
    date: string;
    description: string;
    debit?: number;
    credit?: number;
    balance?: number;
    is_flagged?: boolean;
    flag_reason?: string;
}

interface Document {
    id: string;
    original_filename: string;
    file_type: string;
    created_at: string;
}

interface Client {
    id: string;
    name: string;
}

const SheetsView: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [clients, setClients] = useState<Client[]>([]);
    const [documentsMap, setDocumentsMap] = useState<Record<string, any>>({});
    const [transactionsMap, setTransactionsMap] = useState<Record<string, Transaction[]>>({});

    const [expandedClients, setExpandedClients] = useState<Set<string>>(new Set());
    const [expandedYears, setExpandedYears] = useState<Set<string>>(new Set());
    const [expandedMonths, setExpandedMonths] = useState<Set<string>>(new Set());
    const [expandedDocuments, setExpandedDocuments] = useState<Set<string>>(new Set());

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);

            // Get all clients
            const clientsRes = await api.get('/clients/');
            const clientsList = clientsRes.data || [];
            setClients(clientsList);

            // Fetch documents for each client
            const docsMap: Record<string, any> = {};

            for (const client of clientsList) {
                const docsRes = await api.get(`/documents/?client_id=${client.id}`);
                const docs = docsRes.data || [];

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

                docsMap[client.id] = organized;
            }

            setDocumentsMap(docsMap);
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchDocumentTransactions = async (documentId: string) => {
        if (transactionsMap[documentId]) {
            return; // Already loaded
        }

        try {
            const res = await api.get(`/transactions/extract/document/${documentId}`);
            setTransactionsMap(prev => ({
                ...prev,
                [documentId]: res.data.transactions || []
            }));
        } catch (error) {
            console.error(`Failed to fetch transactions for document ${documentId}`, error);
            setTransactionsMap(prev => ({
                ...prev,
                [documentId]: []
            }));
        }
    };

    const toggleClient = (clientId: string) => {
        const newExpanded = new Set(expandedClients);
        if (newExpanded.has(clientId)) {
            newExpanded.delete(clientId);
        } else {
            newExpanded.add(clientId);
        }
        setExpandedClients(newExpanded);
    };

    const toggleYear = (clientYear: string) => {
        const newExpanded = new Set(expandedYears);
        if (newExpanded.has(clientYear)) {
            newExpanded.delete(clientYear);
        } else {
            newExpanded.add(clientYear);
        }
        setExpandedYears(newExpanded);
    };

    const toggleMonth = (clientYearMonth: string) => {
        const newExpanded = new Set(expandedMonths);
        if (newExpanded.has(clientYearMonth)) {
            newExpanded.delete(clientYearMonth);
        } else {
            newExpanded.add(clientYearMonth);
        }
        setExpandedMonths(newExpanded);
    };

    const toggleDocument = async (documentId: string, doc: Document) => {
        const newExpanded = new Set(expandedDocuments);
        if (newExpanded.has(documentId)) {
            newExpanded.delete(documentId);
        } else {
            newExpanded.add(documentId);

            // Fetch transactions if it's a bank statement or xlsx
            if (doc.file_type === 'bank_statement' || doc.original_filename?.endsWith('.xlsx')) {
                await fetchDocumentTransactions(documentId);
            }
        }
        setExpandedDocuments(newExpanded);
    };

    const formatCurrency = (amount?: number) => {
        if (!amount) return '-';
        return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    const shouldShowTransactions = (doc: Document) => {
        return doc.file_type === 'bank_statement' || doc.original_filename?.endsWith('.xlsx');
    };

    const handleView = async (doc: Document, e: React.MouseEvent) => {
        e.stopPropagation();
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

    const handleDownload = async (doc: Document, e: React.MouseEvent) => {
        e.stopPropagation();
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
            <div className="flex items-center justify-center py-12">
                <div className="animate-pulse text-muted-foreground">Loading sheets...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-foreground mb-2">Transaction Sheets</h1>
                    <p className="text-muted-foreground">
                        View transactions from bank statements and Excel sheets, organized by client
                    </p>
                </div>
            </div>

            {/* Hierarchical Tree */}
            <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
                {clients.length === 0 ? (
                    <div className="text-center py-12">
                        <FileText className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                        <h3 className="text-xl font-bold text-foreground mb-2">No Clients Found</h3>
                        <p className="text-muted-foreground">
                            Add clients and upload their documents to view transaction sheets
                        </p>
                    </div>
                ) : (
                    <div className="space-y-0">
                        {clients.map((client) => {
                            const clientDocs = documentsMap[client.id] || {};
                            const totalDocs = Object.values(clientDocs).flat(2).length;

                            return (
                                <div key={client.id} className="border-b border-border last:border-0">
                                    {/* Client Header */}
                                    <button
                                        onClick={() => toggleClient(client.id)}
                                        className="w-full flex items-center gap-3 p-4 hover:bg-muted/50 transition-colors text-left"
                                    >
                                        <ChevronRight
                                            className={`text-muted-foreground transition-transform ${expandedClients.has(client.id) ? 'rotate-90' : ''
                                                }`}
                                            size={20}
                                        />
                                        <Building className="text-purple-600" size={20} />
                                        <span className="text-foreground font-bold text-lg">{client.name}</span>
                                        <span className="text-muted-foreground text-sm ml-auto">
                                            {totalDocs} documents
                                        </span>
                                    </button>

                                    {/* Years */}
                                    {expandedClients.has(client.id) && (
                                        <div className="pl-8 bg-muted/30 border-t border-border">
                                            {Object.keys(clientDocs).sort((a, b) => parseInt(b) - parseInt(a)).map((year) => {
                                                const clientYear = `${client.id}-${year}`;

                                                return (
                                                    <div key={year} className="border-t border-border first:border-0">
                                                        {/* Year Header */}
                                                        <button
                                                            onClick={() => toggleYear(clientYear)}
                                                            className="w-full flex items-center gap-3 p-3 hover:bg-muted/50 transition-colors text-left"
                                                        >
                                                            <ChevronRight
                                                                className={`text-muted-foreground transition-transform ${expandedYears.has(clientYear) ? 'rotate-90' : ''
                                                                    }`}
                                                                size={18}
                                                            />
                                                            <Calendar className="text-blue-600" size={18} />
                                                            <span className="text-foreground font-semibold">{year}</span>
                                                            <span className="text-muted-foreground text-sm ml-auto">
                                                                {Object.values(clientDocs[year]).flat().length} documents
                                                            </span>
                                                        </button>

                                                        {/* Months */}
                                                        {expandedYears.has(clientYear) && (
                                                            <div className="pl-8 bg-muted/30 border-t border-border">
                                                                {Object.keys(clientDocs[year]).map((month) => {
                                                                    const clientYearMonth = `${client.id}-${year}-${month}`;
                                                                    const monthDocs = clientDocs[year][month];

                                                                    return (
                                                                        <div key={month} className="border-t border-border first:border-0">
                                                                            {/* Month Header */}
                                                                            <button
                                                                                onClick={() => toggleMonth(clientYearMonth)}
                                                                                className="w-full flex items-center gap-3 p-3 hover:bg-muted/50 transition-colors text-left"
                                                                            >
                                                                                <ChevronRight
                                                                                    className={`text-muted-foreground transition-transform ${expandedMonths.has(clientYearMonth) ? 'rotate-90' : ''
                                                                                        }`}
                                                                                    size={16}
                                                                                />
                                                                                <Folder className="text-emerald-600" size={16} />
                                                                                <span className="text-foreground font-medium text-sm">{month}</span>
                                                                                <span className="text-muted-foreground text-xs ml-auto">
                                                                                    {monthDocs.length} files
                                                                                </span>
                                                                            </button>

                                                                            {/* Documents */}
                                                                            {expandedMonths.has(clientYearMonth) && (
                                                                                <div className="pl-8 space-y-0 pb-2 border-t border-border">
                                                                                    {monthDocs.map((doc: Document) => (
                                                                                        <div key={doc.id} className="border-l-2 border-border ml-2 my-1">
                                                                                            {/* Document Header */}
                                                                                            <div className="flex items-center w-full hover:bg-muted/50 transition-colors pr-2 rounded-r-lg">
                                                                                                <button
                                                                                                    onClick={() => toggleDocument(doc.id, doc)}
                                                                                                    className="flex-1 flex items-center gap-3 p-2 text-left"
                                                                                                >
                                                                                                    <ChevronRight
                                                                                                        className={`text-muted-foreground transition-transform ${expandedDocuments.has(doc.id) ? 'rotate-90' : ''
                                                                                                            }`}
                                                                                                        size={14}
                                                                                                    />
                                                                                                    {doc.file_type === 'bank_statement' || doc.original_filename?.endsWith('.xlsx') ? (
                                                                                                        <FileSpreadsheet className="text-emerald-600" size={14} />
                                                                                                    ) : (
                                                                                                        <FileText className="text-muted-foreground" size={14} />
                                                                                                    )}
                                                                                                    <span className="text-foreground text-sm truncate">
                                                                                                        {doc.original_filename}
                                                                                                    </span>
                                                                                                </button>
                                                                                                <div className="flex items-center gap-1">
                                                                                                    <button
                                                                                                        onClick={(e) => handleView(doc, e)}
                                                                                                        className="p-1.5 hover:bg-muted rounded text-muted-foreground hover:text-foreground transition-colors"
                                                                                                        title="View Original"
                                                                                                    >
                                                                                                        <Eye size={14} />
                                                                                                    </button>
                                                                                                    <button
                                                                                                        onClick={(e) => handleDownload(doc, e)}
                                                                                                        className="p-1.5 hover:bg-muted rounded text-muted-foreground hover:text-foreground transition-colors"
                                                                                                        title="Download"
                                                                                                    >
                                                                                                        <Download size={14} />
                                                                                                    </button>
                                                                                                </div>
                                                                                            </div>

                                                                                            {/* Transactions Table */}
                                                                                            {expandedDocuments.has(doc.id) && shouldShowTransactions(doc) && (
                                                                                                <div className="pl-6 pr-2 pb-3 pt-2">
                                                                                                    {transactionsMap[doc.id] === undefined ? (
                                                                                                        <div className="text-center py-4 text-muted-foreground text-sm">
                                                                                                            Loading transactions...
                                                                                                        </div>
                                                                                                    ) : transactionsMap[doc.id].length === 0 ? (
                                                                                                        <div className="text-center py-4 text-muted-foreground text-sm">
                                                                                                            No transactions found
                                                                                                        </div>
                                                                                                    ) : (
                                                                                                        <div className="overflow-x-auto rounded-lg border border-border bg-card">
                                                                                                            <table className="w-full text-left border-collapse text-sm">
                                                                                                                <thead className="bg-muted">
                                                                                                                    <tr className="text-muted-foreground text-xs">
                                                                                                                        <th className="p-2 font-medium">Date</th>
                                                                                                                        <th className="p-2 font-medium">Description</th>
                                                                                                                        <th className="p-2 font-medium text-right">Debit</th>
                                                                                                                        <th className="p-2 font-medium text-right">Credit</th>
                                                                                                                        <th className="p-2 font-medium text-right">Balance</th>
                                                                                                                    </tr>
                                                                                                                </thead>
                                                                                                                <tbody>
                                                                                                                    {transactionsMap[doc.id]
                                                                                                                        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
                                                                                                                        .map((txn: Transaction, idx: number) => (
                                                                                                                            <tr
                                                                                                                                key={idx}
                                                                                                                                className={`border-t border-border hover:bg-muted/50 transition-colors ${txn.is_flagged ? 'bg-red-50 dark:bg-red-900/20' : ''}`}
                                                                                                                            >
                                                                                                                                <td className="p-2 text-foreground whitespace-nowrap">
                                                                                                                                    {new Date(txn.date).toLocaleDateString('en-IN')}
                                                                                                                                </td>
                                                                                                                                <td className="p-2 text-foreground relative group">
                                                                                                                                    <div className="flex items-center gap-2">
                                                                                                                                        {txn.description}
                                                                                                                                        {txn.is_flagged && (
                                                                                                                                            <div className="relative">
                                                                                                                                                <div className="w-4 h-4 rounded-full bg-red-100 text-red-600 flex items-center justify-center cursor-help text-xs font-bold border border-red-200">
                                                                                                                                                    !
                                                                                                                                                </div>
                                                                                                                                                <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 bg-black text-white text-xs px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-10 shadow-lg">
                                                                                                                                                    {txn.flag_reason}
                                                                                                                                                </div>
                                                                                                                                            </div>
                                                                                                                                        )}
                                                                                                                                    </div>
                                                                                                                                </td>
                                                                                                                                <td className="p-2 text-red-600 text-right font-mono">
                                                                                                                                    {txn.debit ? formatCurrency(txn.debit) : '-'}
                                                                                                                                </td>
                                                                                                                                <td className="p-2 text-emerald-600 text-right font-mono">
                                                                                                                                    {txn.credit ? formatCurrency(txn.credit) : '-'}
                                                                                                                                </td>
                                                                                                                                <td className="p-2 text-blue-600 text-right font-mono font-semibold">
                                                                                                                                    {formatCurrency(txn.balance)}
                                                                                                                                </td>
                                                                                                                            </tr>
                                                                                                                        ))}
                                                                                                                </tbody>
                                                                                                            </table>
                                                                                                        </div>
                                                                                                    )}
                                                                                                </div>
                                                                                            )}
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
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};

export default SheetsView;
