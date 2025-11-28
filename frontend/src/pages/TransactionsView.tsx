import React from 'react';
import { Receipt } from 'lucide-react';

const TransactionsView: React.FC = () => {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">Transactions</h1>
                <p className="text-slate-400">Review and categorize transactions</p>
            </div>

            <div className="card flex flex-col items-center justify-center py-20 text-center">
                <div className="w-20 h-20 rounded-full bg-slate-700/50 flex items-center justify-center mb-6">
                    <Receipt className="w-10 h-10 text-slate-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">No Transactions</h3>
                <p className="text-slate-400 max-w-md mx-auto">
                    Transactions extracted from your documents will appear here.
                </p>
            </div>
        </div>
    );
};

export default TransactionsView;
