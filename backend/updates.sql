-- Run this script to update your existing database with Soft Delete features

-- 1. Add deleted_at column to existing tables
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE sheets ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- 2. Create Recycle Bin table
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

-- 3. Create Indexes for Recycle Bin
CREATE INDEX IF NOT EXISTS idx_recycle_bin_deleted_by ON recycle_bin(deleted_by_id);
CREATE INDEX IF NOT EXISTS idx_recycle_bin_expires_at ON recycle_bin(expires_at);

-- 4. Enable RLS on Recycle Bin
ALTER TABLE recycle_bin ENABLE ROW LEVEL SECURITY;

-- 5. Add RLS Policies for Recycle Bin
-- Note: We drop them first to avoid "policy already exists" errors if you run this multiple times
DROP POLICY IF EXISTS "Users can view their deleted items" ON recycle_bin;
CREATE POLICY "Users can view their deleted items"
    ON recycle_bin FOR SELECT
    USING (deleted_by_id = auth.uid() OR EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'));

DROP POLICY IF EXISTS "Users can insert deleted items" ON recycle_bin;
CREATE POLICY "Users can insert deleted items"
    ON recycle_bin FOR INSERT
    WITH CHECK (deleted_by_id = auth.uid());

DROP POLICY IF EXISTS "Users can delete (restore/permanent) their items" ON recycle_bin;
CREATE POLICY "Users can delete (restore/permanent) their items"
    ON recycle_bin FOR DELETE
    USING (deleted_by_id = auth.uid() OR EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'));

-- 6. Add Indexes for deleted_at columns (Optional but recommended for performance)
CREATE INDEX IF NOT EXISTS idx_clients_deleted_at ON clients(deleted_at);
CREATE INDEX IF NOT EXISTS idx_sheets_deleted_at ON sheets(deleted_at);
CREATE INDEX IF NOT EXISTS idx_transactions_deleted_at ON transactions(deleted_at);
CREATE INDEX IF NOT EXISTS idx_documents_deleted_at ON documents(deleted_at);
