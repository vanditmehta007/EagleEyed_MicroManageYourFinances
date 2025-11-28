import React, { useState, useEffect } from 'react';
import { Key, Save, Eye, EyeOff, Cloud, CheckCircle, AlertCircle } from 'lucide-react';
import api from '../services/api';

interface IntegrationCredentials {
    platform: string;
    apiKey: string;
    organizationId?: string;
    isConfigured: boolean;
}

const Settings: React.FC = () => {
    const [credentials, setCredentials] = useState<Record<string, IntegrationCredentials>>({
        'zoho-books': { platform: 'Zoho Books', apiKey: '', organizationId: '', isConfigured: false },
        'google-sheets': { platform: 'Google Sheets', apiKey: '', organizationId: '', isConfigured: false },
    });
    const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
    const [saving, setSaving] = useState<string | null>(null);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    useEffect(() => {
        fetchCredentials();
    }, []);

    const fetchCredentials = async () => {
        try {
            const res = await api.get('/settings/integrations');
            if (res.data) {
                const updated = { ...credentials };
                Object.keys(res.data).forEach(key => {
                    if (updated[key]) {
                        updated[key] = {
                            ...updated[key],
                            ...res.data[key],
                            isConfigured: true
                        };
                    }
                });
                setCredentials(updated);
            }
        } catch (error) {
            console.error('Failed to fetch credentials', error);
        }
    };

    const handleSave = async (platform: string) => {
        setSaving(platform);
        setMessage(null);

        try {
            await api.post('/settings/integrations', {
                platform,
                apiKey: credentials[platform].apiKey,
                organizationId: credentials[platform].organizationId
            });

            setCredentials(prev => ({
                ...prev,
                [platform]: { ...prev[platform], isConfigured: true }
            }));

            setMessage({ type: 'success', text: `${credentials[platform].platform} credentials saved successfully!` });
        } catch (error: any) {
            setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save credentials' });
        } finally {
            setSaving(null);
        }
    };

    const toggleShowKey = (platform: string) => {
        setShowKeys(prev => ({ ...prev, [platform]: !prev[platform] }));
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
                <p className="text-slate-400">Configure your accounting platform integrations</p>
            </div>

            {message && (
                <div className={`p-4 rounded-lg border ${message.type === 'success'
                        ? 'bg-emerald-900/20 border-emerald-500/50 text-emerald-300'
                        : 'bg-red-900/20 border-red-500/50 text-red-300'
                    }`}>
                    <div className="flex items-center gap-2">
                        {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
                        <span>{message.text}</span>
                    </div>
                </div>
            )}

            <div className="card">
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <Cloud size={24} className="text-blue-400" />
                    Integration Credentials
                </h2>
                <p className="text-slate-400 text-sm mb-6">
                    Save your API credentials once to enable seamless imports from accounting platforms.
                </p>

                <div className="space-y-6">
                    {Object.entries(credentials).map(([key, cred]) => (
                        <div key={key} className="p-6 bg-slate-800/50 rounded-lg border border-slate-700">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                    <Key size={20} className="text-blue-400" />
                                    {cred.platform}
                                </h3>
                                {cred.isConfigured && (
                                    <span className="text-xs bg-emerald-900/30 text-emerald-400 px-3 py-1 rounded-full flex items-center gap-1">
                                        <CheckCircle size={14} />
                                        Configured
                                    </span>
                                )}
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        API Key
                                    </label>
                                    <div className="relative">
                                        <input
                                            type={showKeys[key] ? 'text' : 'password'}
                                            className="input-field w-full pr-12"
                                            placeholder="Enter your API key"
                                            value={cred.apiKey}
                                            onChange={(e) => setCredentials(prev => ({
                                                ...prev,
                                                [key]: { ...prev[key], apiKey: e.target.value }
                                            }))}
                                        />
                                        <button
                                            onClick={() => toggleShowKey(key)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                                        >
                                            {showKeys[key] ? <EyeOff size={18} /> : <Eye size={18} />}
                                        </button>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-2">
                                        Organization ID
                                    </label>
                                    <input
                                        type="text"
                                        className="input-field w-full"
                                        placeholder="Enter your organization ID"
                                        value={cred.organizationId || ''}
                                        onChange={(e) => setCredentials(prev => ({
                                            ...prev,
                                            [key]: { ...prev[key], organizationId: e.target.value }
                                        }))}
                                    />
                                </div>

                                <button
                                    onClick={() => handleSave(key)}
                                    disabled={saving === key || !cred.apiKey}
                                    className="btn-primary w-full flex items-center justify-center gap-2"
                                >
                                    <Save size={18} />
                                    {saving === key ? 'Saving...' : 'Save Credentials'}
                                </button>
                            </div>

                            <div className="mt-4 p-3 bg-blue-900/20 rounded-lg border border-blue-900/50">
                                <p className="text-xs text-blue-300">
                                    <strong>How to get your API credentials:</strong><br />
                                    {key === 'zoho-books' && 'Visit Zoho Developer Console → Create a Server-based Application → Copy Client ID and Secret'}
                                    {key === 'google-sheets' && 'Visit Google Cloud Console → Enable Sheets API → Create OAuth 2.0 credentials'}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="card bg-slate-800/30">
                <h3 className="text-lg font-bold text-white mb-3">Security Note</h3>
                <p className="text-slate-400 text-sm">
                    Your API credentials are encrypted and stored securely in the database.
                    They are only used to import data from your accounting platforms and are never shared with third parties.
                </p>
            </div>
        </div>
    );
};

export default Settings;
