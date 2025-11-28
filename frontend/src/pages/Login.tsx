import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const Login: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const selectedRole = (e.target as any).role.value.toLowerCase();

            // Step 1: Login to get access token
            const response = await api.post('/auth/login', {
                email,
                password
            });

            const { access_token } = response.data;

            // Step 2: Fetch actual user profile from backend using the token
            const profileResponse = await api.get('/auth/me', {
                headers: {
                    'Authorization': `Bearer ${access_token}`
                }
            });

            const userProfile = profileResponse.data;

            // Step 3: Validate that selected role matches database role
            if (userProfile.role !== selectedRole) {
                setError(`You must login with your actual role: ${userProfile.role.toUpperCase()}`);
                setLoading(false);
                return;
            }

            // Step 4: Store user with actual role from database
            const user = {
                id: userProfile.id,
                email: userProfile.email,
                name: userProfile.full_name || 'User',
                role: userProfile.role
            };

            login(access_token, user);

            // Navigate based on role
            if (userProfile.role === 'client') {
                navigate('/client-dashboard');
            } else {
                navigate('/');
            }

        } catch (err: any) {
            console.error('Login error:', err);
            setError(err.response?.data?.detail || 'Invalid credentials');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
            <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent mb-2">
                        Welcome Back
                    </h1>
                    <p className="text-slate-400">Sign in to Eagle Eyed</p>
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
                            <option value="Admin">Admin</option>
                        </select>
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
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>

                <div className="mt-6 text-center text-sm text-slate-400">
                    Don't have an account?{' '}
                    <Link to="/signup" className="text-blue-400 hover:text-blue-300 font-medium">
                        Create one
                    </Link>
                </div>
            </div >
        </div >
    );
};

export default Login;
