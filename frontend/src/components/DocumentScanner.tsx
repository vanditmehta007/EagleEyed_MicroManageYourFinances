import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import Tesseract from 'tesseract.js';
import { Camera, X, Check, RefreshCw, FileText, Loader2, Table as TableIcon } from 'lucide-react';
import { Button } from './ui/button';
import { motion } from 'framer-motion';
import api from '../services/api';

interface DocumentScannerProps {
    onCapture: (file: File, text: string) => void;
    onClose: () => void;
}

interface Transaction {
    date: string;
    description: string;
    amount: number;
    type: string;
    balance?: number;
    is_flagged?: boolean;
    flag_reason?: string;
}

const DocumentScanner: React.FC<DocumentScannerProps> = ({ onCapture, onClose }) => {
    const webcamRef = useRef<Webcam>(null);
    const [imgSrc, setImgSrc] = useState<string | null>(null);
    const [scanning, setScanning] = useState(false);
    const [parsing, setParsing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [scannedText, setScannedText] = useState<string>('');
    const [parsedTransactions, setParsedTransactions] = useState<Transaction[]>([]);
    const [viewMode, setViewMode] = useState<'text' | 'table'>('text');

    const capture = useCallback(() => {
        if (webcamRef.current) {
            const imageSrc = webcamRef.current.getScreenshot();
            setImgSrc(imageSrc);
            if (imageSrc) {
                processImage(imageSrc);
            }
        }
    }, [webcamRef]);

    const processImage = async (imageSrc: string) => {
        setScanning(true);
        setProgress(0);
        setParsedTransactions([]);
        setViewMode('text');
        try {
            const result = await Tesseract.recognize(
                imageSrc,
                'eng',
                {
                    logger: m => {
                        if (m.status === 'recognizing text') {
                            setProgress(Math.round(m.progress * 100));
                        }
                    }
                }
            );
            setScannedText(result.data.text);
        } catch (error) {
            console.error("OCR Error:", error);
            setScannedText("Failed to extract text. Please try again.");
        } finally {
            setScanning(false);
        }
    };

    const parseTransactions = async () => {
        if (!scannedText) return;
        setParsing(true);
        try {
            const res = await api.post('/agent/parse-transactions', { text: scannedText });
            if (res.data && res.data.transactions) {
                setParsedTransactions(res.data.transactions);
                setViewMode('table');
            }
        } catch (error) {
            console.error("Parsing failed", error);
            alert("Failed to parse transactions from text.");
        } finally {
            setParsing(false);
        }
    };

    const handleRetake = () => {
        setImgSrc(null);
        setScannedText('');
        setParsedTransactions([]);
        setProgress(0);
        setViewMode('text');
    };

    const handleConfirm = async () => {
        if (imgSrc) {
            // Convert base64 to File
            const res = await fetch(imgSrc);
            const blob = await res.blob();
            const file = new File([blob], `scanned_doc_${Date.now()}.jpg`, { type: 'image/jpeg' });
            // Pass the JSON string of transactions if parsed, else just text
            const textToPass = parsedTransactions.length > 0
                ? JSON.stringify(parsedTransactions)
                : scannedText;

            onCapture(file, textToPass);
        }
    };

    return (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-5xl bg-card border border-border rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
            >
                {/* Header */}
                <div className="p-4 border-b border-border flex items-center justify-between bg-muted/30">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <Camera className="w-5 h-5 text-blue-600" />
                        Scan Document
                    </h3>
                    <Button variant="ghost" size="icon" onClick={onClose}>
                        <X className="w-5 h-5" />
                    </Button>
                </div>

                <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
                    {/* Camera/Image Area */}
                    <div className="flex-1 bg-black relative flex items-center justify-center min-h-[400px]">
                        {!imgSrc ? (
                            <Webcam
                                audio={false}
                                ref={webcamRef}
                                screenshotFormat="image/jpeg"
                                className="w-full h-full object-contain"
                                videoConstraints={{ facingMode: "environment" }}
                            />
                        ) : (
                            <img src={imgSrc} alt="Captured" className="w-full h-full object-contain" />
                        )}

                        {/* Camera Controls */}
                        {!imgSrc && (
                            <div className="absolute bottom-6 left-0 right-0 flex justify-center">
                                <Button
                                    onClick={capture}
                                    size="lg"
                                    className="rounded-full w-16 h-16 p-0 border-4 border-white/30 bg-red-600 hover:bg-red-700 shadow-lg"
                                >
                                    <div className="w-full h-full rounded-full border-2 border-white" />
                                </Button>
                            </div>
                        )}
                    </div>

                    {/* Sidebar / Results */}
                    {imgSrc && (
                        <div className="w-full md:w-[500px] border-l border-border bg-card flex flex-col">
                            <div className="p-4 border-b border-border bg-muted/30 flex items-center justify-between">
                                <h4 className="font-medium flex items-center gap-2">
                                    {viewMode === 'text' ? <FileText className="w-4 h-4" /> : <TableIcon className="w-4 h-4" />}
                                    {viewMode === 'text' ? 'Extracted Text' : 'Parsed Transactions'}
                                </h4>
                                {scannedText && !scanning && (
                                    <div className="flex gap-1">
                                        <Button
                                            variant={viewMode === 'text' ? 'secondary' : 'ghost'}
                                            size="sm"
                                            onClick={() => setViewMode('text')}
                                        >
                                            Text
                                        </Button>
                                        <Button
                                            variant={viewMode === 'table' ? 'secondary' : 'ghost'}
                                            size="sm"
                                            onClick={() => {
                                                if (parsedTransactions.length === 0) parseTransactions();
                                                else setViewMode('table');
                                            }}
                                            disabled={parsing}
                                        >
                                            Table
                                        </Button>
                                    </div>
                                )}
                            </div>

                            <div className="flex-1 p-4 overflow-y-auto min-h-[200px]">
                                {scanning ? (
                                    <div className="flex flex-col items-center justify-center h-full gap-4 text-muted-foreground">
                                        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                                        <div className="text-center">
                                            <p className="font-medium text-foreground">Analyzing...</p>
                                            <p className="text-xs">Recognizing text ({progress}%)</p>
                                        </div>
                                        <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-blue-600 transition-all duration-300"
                                                style={{ width: `${progress}%` }}
                                            />
                                        </div>
                                    </div>
                                ) : parsing ? (
                                    <div className="flex flex-col items-center justify-center h-full gap-4 text-muted-foreground">
                                        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
                                        <p>Parsing transactions with AI...</p>
                                    </div>
                                ) : viewMode === 'table' && parsedTransactions.length > 0 ? (
                                    <div className="border rounded-md overflow-hidden">
                                        <table className="w-full text-sm">
                                            <thead className="bg-muted">
                                                <tr>
                                                    <th className="p-2 text-left">Date</th>
                                                    <th className="p-2 text-left">Desc</th>
                                                    <th className="p-2 text-right">Amount</th>
                                                    <th className="p-2 w-8"></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {parsedTransactions.map((tx, i) => (
                                                    <tr key={i} className={`border-t border-border ${tx.is_flagged ? 'bg-red-50 dark:bg-red-900/20' : ''}`}>
                                                        <td className="p-2 whitespace-nowrap">{tx.date}</td>
                                                        <td className="p-2 truncate max-w-[150px]" title={tx.description}>{tx.description}</td>
                                                        <td className={`p-2 text-right ${tx.type === 'credit' ? 'text-emerald-600' : 'text-red-600'}`}>
                                                            {tx.amount.toFixed(2)}
                                                        </td>
                                                        <td className="p-2 text-center">
                                                            {tx.is_flagged && (
                                                                <div className="group relative">
                                                                    <div className="w-4 h-4 rounded-full bg-red-100 text-red-600 flex items-center justify-center cursor-help">
                                                                        !
                                                                    </div>
                                                                    <div className="absolute right-full mr-2 top-1/2 -translate-y-1/2 bg-black text-white text-xs px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-10">
                                                                        {tx.flag_reason}
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                ) : (
                                    <div className="prose prose-sm dark:prose-invert max-w-none">
                                        <pre className="whitespace-pre-wrap text-sm text-muted-foreground font-mono bg-muted/20 p-2 rounded-md">
                                            {scannedText || "No text detected."}
                                        </pre>
                                    </div>
                                )}
                            </div>

                            <div className="p-4 border-t border-border bg-muted/30 space-y-3">
                                {viewMode === 'text' && scannedText && parsedTransactions.length === 0 && (
                                    <Button
                                        onClick={parseTransactions}
                                        className="w-full bg-purple-600 hover:bg-purple-700"
                                        disabled={scanning || parsing}
                                    >
                                        <TableIcon className="w-4 h-4 mr-2" />
                                        Extract as Table (AI)
                                    </Button>
                                )}

                                <div className="flex gap-3">
                                    <Button
                                        onClick={handleRetake}
                                        variant="outline"
                                        className="flex-1"
                                    >
                                        <RefreshCw className="w-4 h-4 mr-2" />
                                        Retake
                                    </Button>
                                    <Button
                                        onClick={handleConfirm}
                                        className="flex-1"
                                        disabled={scanning || parsing}
                                    >
                                        <Check className="w-4 h-4 mr-2" />
                                        Use This Scan
                                    </Button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </motion.div>
        </div>
    );
};

export default DocumentScanner;
