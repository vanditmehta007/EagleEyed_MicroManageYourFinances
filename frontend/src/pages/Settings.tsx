import React, { useState, useEffect } from 'react';
import { Key, Save, Eye, EyeOff, Cloud, CheckCircle, AlertCircle } from 'lucide-react';
import api from '../services/api';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';

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
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
        >
            <div>
                <h1 className="text-3xl font-bold tracking-tight mb-2">Settings</h1>
                <p className="text-muted-foreground">Configure your accounting platform integrations</p>
            </div>

            {message && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className={`p-4 rounded-lg border flex items-center gap-2 ${message.type === 'success'
                        ? 'bg-emerald-50 border-emerald-200 text-emerald-600'
                        : 'bg-destructive/10 border-destructive/20 text-destructive'
                        }`}
                >
                    {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
                    <span>{message.text}</span>
                </motion.div>
            )}

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Cloud className="w-5 h-5 text-blue-600" />
                        Integration Credentials
                    </CardTitle>
                    <CardDescription>
                        Save your API credentials once to enable seamless imports from accounting platforms.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {Object.entries(credentials).map(([key, cred]) => (
                        <div key={key} className="p-6 bg-muted rounded-lg border border-border">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold flex items-center gap-2">
                                    <Key size={20} className="text-blue-600" />
                                    {cred.platform}
                                </h3>
                                {cred.isConfigured && (
                                    <Badge variant="success" className="gap-1">
                                        <CheckCircle size={12} />
                                        Configured
                                    </Badge>
                                )}
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <Label>API Key</Label>
                                    <div className="relative">
                                        <Input
                                            type={showKeys[key] ? 'text' : 'password'}
                                            className="pr-12"
                                            placeholder="Enter your API key"
                                            value={cred.apiKey}
                                            onChange={(e) => setCredentials(prev => ({
                                                ...prev,
                                                [key]: { ...prev[key], apiKey: e.target.value }
                                            }))}
                                        />
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => toggleShowKey(key)}
                                            className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                                        >
                                            {showKeys[key] ? <EyeOff size={16} /> : <Eye size={16} />}
                                        </Button>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label>Organization ID</Label>
                                    <Input
                                        type="text"
                                        placeholder="Enter your organization ID"
                                        value={cred.organizationId || ''}
                                        onChange={(e) => setCredentials(prev => ({
                                            ...prev,
                                            [key]: { ...prev[key], organizationId: e.target.value }
                                        }))}
                                    />
                                </div>

                                <Button
                                    onClick={() => handleSave(key)}
                                    disabled={saving === key || !cred.apiKey}
                                    className="w-full"
                                >
                                    {saving === key ? (
                                        <div className="flex items-center gap-2">
                                            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                                            Saving...
                                        </div>
                                    ) : (
                                        <>
                                            <Save className="mr-2 w-4 h-4" />
                                            Save Credentials
                                        </>
                                    )}
                                </Button>
                            </div>

                            <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                                <p className="text-xs text-blue-700">
                                    <strong>How to get your API credentials:</strong><br />
                                    {key === 'zoho-books' && 'Visit Zoho Developer Console → Create a Server-based Application → Copy Client ID and Secret'}
                                    {key === 'google-sheets' && 'Visit Google Cloud Console → Enable Sheets API → Create OAuth 2.0 credentials'}
                                </p>
                            </div>
                        </div>
                    ))}
                </CardContent>
            </Card>

            <Card className="bg-muted border-none">
                <CardContent className="p-6">
                    <h3 className="text-lg font-bold mb-3">Security Note</h3>
                    <p className="text-muted-foreground text-sm">
                        Your API credentials are encrypted and stored securely in the database.
                        They are only used to import data from your accounting platforms and are never shared with third parties.
                    </p>
                </CardContent>
            </Card>
        </motion.div>
    );
};

export default Settings;
