import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

const Signup: React.FC = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const roleSelect = (e.target as any).role;
            const role = roleSelect.value.toLowerCase(); // Ensure lowercase for backend enum

            // Map "admin" to "ca" or "client" if backend doesn't support admin signup directly yet, 
            // or ensure backend supports "admin". The model says Literal["client", "ca"].
            // So we should restrict to client/ca for now or update backend.
            // Let's assume we map Admin -> CA for now or just pass it if we update backend.
            // Actually, let's stick to what the model supports: client or ca.

            let finalRole = role;
            if (role !== 'client' && role !== 'ca') {
                finalRole = 'ca'; // Default fallback or handle error
            }

            const response = await api.post('/auth/signup', {
                name,
                email,
                password,
                role: finalRole
            });

            // Auto login after signup
            const { access_token } = response.data;
            const user = {
                id: 'new_user',
                email,
                name,
                role: finalRole
            };

            // We might want to just navigate to login, but auto-login is nicer
            // login(access_token, user); 
            navigate('/login'); // Let's force login to be safe

        } catch (err: any) {
            console.error('Signup error:', err);
            setError(err.response?.data?.detail || 'Failed to create account');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
            <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent mb-2">
                        Get Started
                    </h1>
                    <p className="text-slate-400">Create your Eagle Eyed account</p>
                </div>

                {error && (
                    <div className="bg-red-900/20 border border-red-900/50 text-red-400 p-3 rounded-lg mb-6 text-sm text-center">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Select Role</label>
                        <select
                            className="input-field appearance-none"
                            defaultValue="CA"
                            name="role"
                        >
                            <option value="CA">Chartered Accountant (CA)</option>
                            <option value="Client">Client</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Full Name</label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="input-field"
                            placeholder="John Doe"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Email Address</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="input-field"
                            placeholder="you@example.com"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="input-field"
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full btn-primary py-3 text-lg shadow-lg shadow-blue-900/20"
                    >
                        {loading ? 'Creating Account...' : 'Create Account'}
                    </button>
                </form>

                <div className="mt-6 text-center text-sm text-slate-400">
                    Already have an account?{' '}
                    <Link to="/login" className="text-blue-400 hover:text-blue-300 font-medium">
                        Sign in
                    </Link>
                </div>
            </div >
        </div >
    );
};

export default Signup;
