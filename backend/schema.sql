-- Eagle Eyed Database Schema for Supabase
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector for RAG (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Users table (synced with Supabase Auth)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT CHECK (role IN ('client', 'ca', 'admin')) DEFAULT 'client',
    phone TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Clients table
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    gstin TEXT,
    pan TEXT,
    business_type TEXT,
    assigned_ca_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Chartered Accountants table
CREATE TABLE IF NOT EXISTS cas (
    id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    firm_name TEXT,
    registration_number TEXT,
    phone TEXT,
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Financial Sheets table
CREATE TABLE IF NOT EXISTS sheets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    financial_year INTEGER NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sheet_id UUID REFERENCES sheets(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    description TEXT,
    amount DECIMAL(15,2) NOT NULL,
    type TEXT CHECK (type IN ('credit', 'debit')) NOT NULL,
    ledger TEXT DEFAULT 'Uncategorized',
    vendor TEXT,
    invoice_number TEXT,
    gstin TEXT,
    pan TEXT,
    gst_applicable BOOLEAN DEFAULT FALSE,
    tds_applicable BOOLEAN DEFAULT FALSE,
    capital_expense BOOLEAN DEFAULT FALSE,
    recurring BOOLEAN DEFAULT FALSE,
    ai_confidence DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    folder_category TEXT DEFAULT 'Uncategorized',
    file_size INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- RECYCLE BIN
-- =====================================================

CREATE TABLE IF NOT EXISTS recycle_bin (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    original_table TEXT NOT NULL,
    original_id UUID NOT NULL,
    deleted_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    deleted_by_role TEXT,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    item_metadata JSONB
);

-- =====================================================
-- RAG TABLES
-- =====================================================

-- Embeddings table for RAG
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_text TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 dimension
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- COMPLIANCE & AUDIT TABLES
-- =====================================================

-- Red Flags table
CREATE TABLE IF NOT EXISTS red_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    transaction_id UUID REFERENCES transactions(id) ON DELETE CASCADE,
    flag_type TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Admin Logs table
CREATE TABLE IF NOT EXISTS admin_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    details JSONB,
    ip_address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Share Tokens table
CREATE TABLE IF NOT EXISTS share_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token TEXT UNIQUE NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE CASCADE,
    password_hash TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Share Access Logs table
CREATE TABLE IF NOT EXISTS share_access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_id UUID REFERENCES share_tokens(id) ON DELETE CASCADE,
    ip_address TEXT,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Clients indexes
CREATE INDEX IF NOT EXISTS idx_clients_assigned_ca ON clients(assigned_ca_id);
CREATE INDEX IF NOT EXISTS idx_clients_created_by ON clients(created_by);
CREATE INDEX IF NOT EXISTS idx_clients_deleted_at ON clients(deleted_at);

-- Sheets indexes
CREATE INDEX IF NOT EXISTS idx_sheets_client ON sheets(client_id);
CREATE INDEX IF NOT EXISTS idx_sheets_deleted_at ON sheets(deleted_at);

-- Transactions indexes
CREATE INDEX IF NOT EXISTS idx_transactions_sheet ON transactions(sheet_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_ledger ON transactions(ledger);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_deleted_at ON transactions(deleted_at);

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_client ON documents(client_id);
CREATE INDEX IF NOT EXISTS idx_documents_deleted_at ON documents(deleted_at);

-- Recycle Bin indexes
CREATE INDEX IF NOT EXISTS idx_recycle_bin_deleted_by ON recycle_bin(deleted_by_id);
CREATE INDEX IF NOT EXISTS idx_recycle_bin_expires_at ON recycle_bin(expires_at);

-- Embeddings indexes (for vector similarity search)
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);

-- Red Flags indexes
CREATE INDEX IF NOT EXISTS idx_redflags_client ON red_flags(client_id);
CREATE INDEX IF NOT EXISTS idx_redflags_resolved ON red_flags(resolved);

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE sheets ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE red_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE recycle_bin ENABLE ROW LEVEL SECURITY;

-- Users RLS Policies
CREATE POLICY "Users can view own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON users FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Clients RLS Policies
CREATE POLICY "Clients can view own data"
    ON clients FOR SELECT
    USING (
        created_by = auth.uid() OR
        assigned_ca_id = auth.uid() OR
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "CAs and Admins can create clients"
    ON clients FOR INSERT
    WITH CHECK (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('ca', 'admin'))
        OR
        (auth.uid() = created_by) -- Allow self-registration
    );

CREATE POLICY "CAs and Admins can update clients"
    ON clients FOR UPDATE
    USING (
        assigned_ca_id = auth.uid() OR
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );

-- CAs RLS Policies
CREATE POLICY "CAs can view own profile"
    ON cas FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "CAs can update own profile"
    ON cas FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "CAs can insert own profile"
    ON cas FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Sheets RLS Policies
CREATE POLICY "Users can view sheets for their clients"
    ON sheets FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM clients
            WHERE clients.id = sheets.client_id
            AND (clients.created_by = auth.uid() OR clients.assigned_ca_id = auth.uid())
        ) OR
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "CAs can create sheets"
    ON sheets FOR INSERT
    WITH CHECK (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('ca', 'admin'))
    );

-- Transactions RLS Policies
CREATE POLICY "Users can view transactions for their sheets"
    ON transactions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM sheets
            JOIN clients ON sheets.client_id = clients.id
            WHERE sheets.id = transactions.sheet_id
            AND (clients.created_by = auth.uid() OR clients.assigned_ca_id = auth.uid())
        ) OR
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );

-- Recycle Bin RLS Policies
CREATE POLICY "Users can view their deleted items"
    ON recycle_bin FOR SELECT
    USING (deleted_by_id = auth.uid() OR EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'));

CREATE POLICY "Users can insert deleted items"
    ON recycle_bin FOR INSERT
    WITH CHECK (deleted_by_id = auth.uid());

CREATE POLICY "Users can delete (restore/permanent) their items"
    ON recycle_bin FOR DELETE
    USING (deleted_by_id = auth.uid() OR EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'));

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function for vector similarity search
CREATE OR REPLACE FUNCTION match_embeddings(
    query_embedding vector(1536),
    match_threshold float,
    match_count int
)
RETURNS TABLE (
    id uuid,
    chunk_text text,
    source text,
    source_type text,
    metadata jsonb,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        id,
        chunk_text,
        source,
        source_type,
        metadata,
        1 - (embedding <=> query_embedding) as similarity
    FROM embeddings
    WHERE 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cas_updated_at BEFORE UPDATE ON cas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sheets_updated_at BEFORE UPDATE ON sheets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- STORAGE BUCKETS (Run in Supabase Dashboard)
-- =====================================================

-- Create storage bucket for documents
-- INSERT INTO storage.buckets (id, name, public) VALUES ('documents', 'documents', false);

-- Storage RLS policies
-- CREATE POLICY "Users can upload documents"
-- ON storage.objects FOR INSERT
-- WITH CHECK (bucket_id = 'documents' AND auth.role() = 'authenticated');

-- CREATE POLICY "Users can view own documents"
-- ON storage.objects FOR SELECT
-- USING (bucket_id = 'documents' AND auth.role() = 'authenticated');

-- =====================================================
-- SEED DATA (Optional - for testing)
-- =====================================================

-- Insert admin user (update with actual user ID from Supabase Auth)
-- INSERT INTO users (id, email, full_name, role) VALUES
-- ('YOUR-ADMIN-USER-ID', 'admin@eagleeyed.com', 'Admin User', 'admin');

COMMENT ON TABLE users IS 'User profiles synced with Supabase Auth';
COMMENT ON TABLE clients IS 'Client entities managed by CAs';
COMMENT ON TABLE sheets IS 'Financial sheets per client per year';
COMMENT ON TABLE transactions IS 'Individual financial transactions';
COMMENT ON TABLE embeddings IS 'Vector embeddings for RAG system';
COMMENT ON TABLE red_flags IS 'Compliance and anomaly alerts';
COMMENT ON TABLE recycle_bin IS 'Soft-deleted items with 30-day retention';

-- =====================================================
-- DOCUMENTS RLS POLICIES (Added)
-- =====================================================

CREATE POLICY "Users can view documents for their clients"
    ON documents FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM clients
            WHERE clients.id = documents.client_id
            AND (clients.created_by = auth.uid() OR clients.assigned_ca_id = auth.uid())
        ) OR
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "Users can insert documents for their clients"
    ON documents FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM clients
            WHERE clients.id = documents.client_id
            AND (clients.created_by = auth.uid() OR clients.assigned_ca_id = auth.uid())
        ) OR
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('ca', 'admin'))
    );

CREATE POLICY "Users can delete documents for their clients"
    ON documents FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM clients
            WHERE clients.id = documents.client_id
            AND (clients.created_by = auth.uid() OR clients.assigned_ca_id = auth.uid())
        ) OR
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );
    
CREATE POLICY "Users can update documents for their clients"
    ON documents FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM clients
            WHERE clients.id = documents.client_id
            AND (clients.created_by = auth.uid() OR clients.assigned_ca_id = auth.uid())
        ) OR
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );

-- =====================================================
-- INTEGRATION CREDENTIALS TABLES
-- =====================================================

-- Table to store integration credentials
CREATE TABLE IF NOT EXISTS integration_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL, -- 'zoho-books', 'google-sheets', etc.
    api_key TEXT NOT NULL,
    organization_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, platform)
);

-- RLS Policies
ALTER TABLE integration_credentials ENABLE ROW LEVEL SECURITY;

-- Users can only see their own credentials
CREATE POLICY "Users can view own integration credentials"
    ON integration_credentials
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own credentials
CREATE POLICY "Users can insert own integration credentials"
    ON integration_credentials
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own credentials
CREATE POLICY "Users can update own integration credentials"
    ON integration_credentials
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete their own credentials
CREATE POLICY "Users can delete own integration credentials"
    ON integration_credentials
    FOR DELETE
    USING (auth.uid() = user_id);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_integration_credentials_user_platform 
    ON integration_credentials(user_id, platform);
