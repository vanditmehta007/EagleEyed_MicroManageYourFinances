import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Eye, EyeOff, Lock, Mail, UserCircle } from 'lucide-react';

const Login: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
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
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="w-full max-w-md z-10"
            >
                <Card className="border-border shadow-xl bg-card">
                    <CardHeader className="space-y-1 text-center">
                        <CardTitle className="text-3xl font-bold text-primary">
                            Welcome Back
                        </CardTitle>
                        <CardDescription>
                            Sign in to your Eagle Eyed account
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    className="bg-destructive/15 text-destructive text-sm p-3 rounded-md border border-destructive/20"
                                >
                                    {error}
                                </motion.div>
                            )}

                            <div className="space-y-2">
                                <Label htmlFor="role">Select Role</Label>
                                <div className="relative">
                                    <UserCircle className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <select
                                        id="role"
                                        name="role"
                                        className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 pl-9 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 appearance-none"
                                        defaultValue="CA"
                                    >
                                        <option value="CA">Chartered Accountant (CA)</option>
                                        <option value="Client">Client</option>
                                        <option value="Admin">Admin</option>
                                    </select>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="email"
                                        type="email"
                                        placeholder="name@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="pl-9"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="password">Password</Label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="password"
                                        type={showPassword ? "text" : "password"}
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="pl-9 pr-9"
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                    </button>
                                </div>
                            </div>

                            <Button
                                type="submit"
                                className="w-full bg-primary hover:bg-primary/90 transition-all duration-300"
                                disabled={loading}
                            >
                                {loading ? (
                                    <div className="flex items-center gap-2">
                                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                                        Signing in...
                                    </div>
                                ) : 'Sign In'}
                            </Button>
                        </form>
                    </CardContent>
                    <CardFooter className="flex justify-center">
                        <p className="text-sm text-muted-foreground">
                            Don't have an account?{' '}
                            <Link to="/signup" className="text-primary hover:underline font-medium">
                                Create one
                            </Link>
                        </p>
                    </CardFooter>
                </Card>
            </motion.div>
        </div>
    );
};

export default Login;
