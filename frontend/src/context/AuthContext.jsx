import { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '../api/supabase';
import api from '../api/axios';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [mappedUser, setMappedUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initialize session and listen for auth changes
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Axios Interceptor for Bearer Tokens
  useEffect(() => {
    const reqInterceptor = api.interceptors.request.use(async (config) => {
      try {
        console.log("[AuthContext] Interceptor started for URL:", config.url);
        // Fetch current session for latest token
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        
        if (currentSession?.access_token) {
          console.log("[AuthContext] Token found. Setting Authorization Bearer...");
          if (config.headers && typeof config.headers.set === 'function') {
            config.headers.set('Authorization', `Bearer ${currentSession.access_token}`);
          } else {
            config.headers = config.headers || {};
            config.headers['Authorization'] = `Bearer ${currentSession.access_token}`;
          }
        } else {
          console.warn("[AuthContext] VERY IMPORTANT: currentSession is missing or access_token is empty! No Authorization header will be attached. This WILL cause a 401!");
        }
      } catch (e) {
        console.error("Interceptor failed to attach token:", e);
      }
      return config;
    });
    return () => api.interceptors.request.eject(reqInterceptor);
  }, []);

  // Map Supabase User to App format
  useEffect(() => {
    if (session?.user) {
      const su = session.user;
      const em = su.email || '';
      const isAdmin = (em === 'aditya.asb24@gmail.com' || em === 'adtiya.asb24@gmail.com');
      const role = isAdmin ? 'admin' : (su.user_metadata?.role || 'patient');
      const name = su.user_metadata?.full_name || su.user_metadata?.name || em.split('@')[0];

      setMappedUser({
        _id: su.id,
        name: name,
        email: em,
        role: role,
        is_verified: true,
      });
    } else {
      setMappedUser(null);
    }
  }, [session]);

  const logout = async () => {
    try { await supabase.auth.signOut(); } catch {}
  };

  // Keep dummies so any leftover caller doesn't crash before being refactored
  const login = async () => {};
  const signup = async () => {};
  const loginWithGoogle = async () => {};
  const fetchUser = async () => {};

  const value = { user: mappedUser, loading, login, signup, loginWithGoogle, logout, fetchUser };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
