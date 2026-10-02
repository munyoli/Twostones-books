-- Supabase Schema for Twostones Studio Books
-- Run this in your Supabase SQL Editor

-- 1. Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Create tables

CREATE TABLE pricing_settings (
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  name TEXT DEFAULT 'Twostones',
  cur TEXT DEFAULT 'KES',
  labour NUMERIC DEFAULT 500,
  oh NUMERIC DEFAULT 215,
  margin NUMERIC DEFAULT 30,
  markup NUMERIC DEFAULT 30,
  wm NUMERIC DEFAULT 40,
  rm NUMERIC DEFAULT 50,
  mode TEXT DEFAULT 'margin',
  opening_cash_balance NUMERIC DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE clients (
  id TEXT PRIMARY KEY, -- using short string IDs for easy migration, or could use UUID
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  phone TEXT,
  email TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE products (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  fab_qty NUMERIC DEFAULT 0,
  fab_cost NUMERIC DEFAULT 0,
  hours NUMERIC DEFAULT 0,
  trims NUMERIC DEFAULT 0,
  pack NUMERIC DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orders (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  no TEXT NOT NULL,
  date DATE NOT NULL,
  client_id TEXT REFERENCES clients(id) ON DELETE RESTRICT,
  type TEXT, -- Order-level classification (RTW, Custom, Bridal, Other)
  due DATE,
  status TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE order_items (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  order_id TEXT REFERENCES orders(id) ON DELETE CASCADE NOT NULL,
  type TEXT, -- Item-level classification
  name TEXT NOT NULL, -- Garment / product name
  qty NUMERIC DEFAULT 1,
  price NUMERIC DEFAULT 0,
  hours NUMERIC DEFAULT 0, -- Estimated hours
  est_mat NUMERIC DEFAULT 0,
  est_other NUMERIC DEFAULT 0,
  act_hours NUMERIC, -- Actual hours (new)
  act_lab_override NUMERIC, -- Explicit override (new)
  act_mat NUMERIC DEFAULT 0, -- Extra unrecorded actual materials
  act_other NUMERIC DEFAULT 0,
  design TEXT,
  fabric TEXT,
  fab_qty NUMERIC,
  measure TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payments (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  order_id TEXT REFERENCES orders(id) ON DELETE CASCADE NOT NULL,
  date DATE NOT NULL,
  amt NUMERIC NOT NULL,
  method TEXT,
  ref TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE materials (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  date DATE NOT NULL,
  supplier TEXT,
  name TEXT NOT NULL,
  cat TEXT,
  qty NUMERIC DEFAULT 0,
  unit TEXT,
  cpu NUMERIC DEFAULT 0,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE material_usage (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  mat_id TEXT REFERENCES materials(id) ON DELETE CASCADE NOT NULL,
  order_id TEXT REFERENCES orders(id) ON DELETE CASCADE NOT NULL,
  qty NUMERIC DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE expenses (
  id TEXT PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  date DATE NOT NULL,
  desc_text TEXT NOT NULL,
  cat TEXT,
  amt NUMERIC NOT NULL,
  method TEXT,
  payee TEXT,
  order_id TEXT REFERENCES orders(id) ON DELETE SET NULL,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Row Level Security (RLS)

ALTER TABLE pricing_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;
ALTER TABLE material_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

-- Create policies so users can only access their own data

CREATE POLICY "Users can view own pricing_settings" ON pricing_settings FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own pricing_settings" ON pricing_settings FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own pricing_settings" ON pricing_settings FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own clients" ON clients FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own clients" ON clients FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own clients" ON clients FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own clients" ON clients FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own products" ON products FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own products" ON products FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own products" ON products FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own products" ON products FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own orders" ON orders FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own orders" ON orders FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own orders" ON orders FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own orders" ON orders FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own order_items" ON order_items FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own order_items" ON order_items FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own order_items" ON order_items FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own order_items" ON order_items FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own payments" ON payments FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own payments" ON payments FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own payments" ON payments FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own payments" ON payments FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own materials" ON materials FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own materials" ON materials FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own materials" ON materials FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own materials" ON materials FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own material_usage" ON material_usage FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own material_usage" ON material_usage FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own material_usage" ON material_usage FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own material_usage" ON material_usage FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own expenses" ON expenses FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own expenses" ON expenses FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own expenses" ON expenses FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own expenses" ON expenses FOR DELETE USING (auth.uid() = user_id);
