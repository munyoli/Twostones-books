// Supabase Configuration
// You need to create a project on supabase.com and get these values from Settings -> API
const SUPABASE_URL = 'https://shhmyyamptradvrootme.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_kLK4HPIaZwm5Rw4a9I5TeQ_WjWNfKio';

// Initialize the Supabase client
window.supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
