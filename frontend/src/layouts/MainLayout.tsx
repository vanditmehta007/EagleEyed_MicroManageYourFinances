import React, { useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Users, FileText, Upload, Receipt, LogOut, FolderOpen, Settings } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const MainLayout: React.FC = () => {
    const { logout, user } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    useEffect(() => {
        if (user?.role?.toLowerCase() === 'client' && location.pathname === '/') {
            navigate('/client-dashboard');
        }
    }, [user, location.pathname, navigate]);

    const getNavItems = () => {
        const baseItems = [
            { path: '/chat', label: 'AI Assistant', icon: MessageSquare },
            { path: '/documents', label: 'Sheets', icon: FileText },
            { path: '/upload', label: 'Upload', icon: Upload },
            { path: '/settings', label: 'Settings', icon: Settings },
        ];

        if (user?.role?.toLowerCase() === 'client') {
            return [
                { path: '/client-dashboard', label: 'Home', icon: LayoutDashboard },
                ...baseItems
            ];
        }

        // Default (CA / Admin)
        return [
            { path: '/', label: 'Dashboard', icon: LayoutDashboard },
            { path: '/clients', label: 'Client Manager', icon: Users },
            { path: '/shared-documents', label: 'Shared Documents', icon: FolderOpen },
            ...baseItems
        ];
    };

    const navItems = getNavItems();

    return (
        <div className="flex h-screen bg-slate-900 text-slate-100 font-sans">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
                <div className="p-6 border-b border-slate-700">
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
                        Eagle Eyed
                    </h1>
                    <p className="text-xs text-slate-400 mt-1">AI Financial Compliance</p>
                </div>

                <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${isActive
                                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/50'
                                    : 'text-slate-400 hover:bg-slate-700 hover:text-white'
                                    }`}
                            >
                                <Icon size={20} />
                                <span className="font-medium">{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-slate-700">
                    <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-slate-400 hover:bg-red-900/20 hover:text-red-400 transition-colors"
                    >
                        <LogOut size={20} />
                        <span className="font-medium">Sign Out</span>
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto bg-slate-900">
                <div className="p-8 max-w-7xl mx-auto">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default MainLayout;
