import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import MainLayout from './layouts/MainLayout';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import AIChat from './pages/AIChat';
import ClientManager from './pages/ClientManager';
import DocumentUpload from './pages/DocumentUpload';
import SheetsView from './pages/SheetsView';
import SharedDocumentView from './pages/SharedDocumentView';
import SharedDocumentsList from './pages/SharedDocumentsList';
import ClientDashboard from './pages/ClientDashboard';
import AcceptInvite from './pages/AcceptInvite';
import Settings from './pages/Settings';
import LandingPage from './pages/LandingPage';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { isAuthenticated } = useAuth();

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
};

const AppRoutes: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/share/:id" element={<SharedDocumentView />} />
            <Route path="/share/documents/:clientId" element={<SharedDocumentView />} />
            <Route path="/share/invite/:token" element={<AcceptInvite />} />

            <Route element={
                <ProtectedRoute>
                    <MainLayout />
                </ProtectedRoute>
            }>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="chat" element={<AIChat />} />
                <Route path="clients" element={<ClientManager />} />
                <Route path="shared-documents" element={<SharedDocumentsList />} />
                <Route path="upload" element={<DocumentUpload />} />
                <Route path="documents" element={<SheetsView />} />
                <Route path="client-dashboard" element={<ClientDashboard />} />
                <Route path="settings" element={<Settings />} />
            </Route>
        </Routes>
    );
};

const App: React.FC = () => {
    return (
        <Router>
            <AuthProvider>
                <AppRoutes />
            </AuthProvider>
        </Router>
    );
};

export default App;
