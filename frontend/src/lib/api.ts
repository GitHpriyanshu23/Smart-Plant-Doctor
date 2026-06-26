import { supabase } from './supabase';
import { useAuth } from '../contexts/AuthContext';

const API_URL = import.meta.env.VITE_API_URL || '';

export async function getAccessToken(): Promise<string | null> {
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token ?? null;
    if (!token) {
      console.warn('[api] No Supabase session token available');
    }
    return token;
  }
  return localStorage.getItem('access_token');
}

export function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (res.status === 401) {
    const err = await res.json().catch(() => ({ detail: 'Unauthorized' }));
    console.warn('[api] 401 on', path, err.detail);
    if (supabase) {
      await supabase.auth.signOut();
    }
    clearTokens();
    window.location.href = '/login';
    throw new Error(err.detail || 'Session expired — please log in again.');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export function useApiReady() {
  const { session, loading } = useAuth();
  return { ready: !loading && !!session, session };
}
