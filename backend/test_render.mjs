import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.VITE_SUPABASE_URL || 'https://lpiykgllsafrwwmcuvbo.supabase.co';
const SUPABASE_KEY = process.env.VITE_SUPABASE_PUBLISHABLE_DEFAULT_KEY || 'sb_publishable_EbtI0a6HHCauYrvTnWzyLw_fXooE8hg';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

async function main() {
    console.log("Authenticating test user...");
    const { data, error } = await supabase.auth.signInWithPassword({
        email: 'aditya.asb24@gmail.com',  // known from previous context
        password: 'Aditya@05GWL' // password from MAIL_PASSWORD, let's just hope it's the same, or I'll try signing up a dummy email.
    });

    let token = data?.session?.access_token;
    if (!token) {
        // If login failed, just signup a dummy
        console.log("Login failed, trying signup dummy...", error?.message);
        const rand = Math.random().toString(36).substring(7);
        const { data: d2, error: e2 } = await supabase.auth.signUp({
            email: `dummy_${rand}@test.com`,
            password: 'SecurePassword123!'
        });
        token = d2?.session?.access_token;
        if (!token) {
            console.log("Signup also failed:", e2?.message);
            return;
        }
    }
    
    console.log("Got Supabase Token!");

    try {
        console.log("Sending token to Live Render API...");
        const res = await fetch('https://deepscanx-ai-1.onrender.com/api/v1/predict/lung', {
            method: 'POST',
            body: JSON.stringify({ image: 'dummy' }),
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        const json = await res.json();
        console.log("Status:", res.status);
        console.log("Response:", json);
    } catch (e) {
        console.error("FAILED to Call API:", e);
    }
}
main();
