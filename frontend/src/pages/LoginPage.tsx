import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { supabase, supabaseConfigured } from '../lib/supabase';

export default function LoginPage() {
  const navigate = useNavigate();
  const { session } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (session) navigate('/dashboard', { replace: true });
  }, [session, navigate]);

  const googleLogin = async () => {
    if (!supabase) return;
    setError('');
    setLoading(true);
    const { error: err } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (err) setError(err.message);
    setLoading(false);
  };

  const emailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supabase) {
      setError('Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        const { error: err } = await supabase.auth.signUp({ email, password });
        if (err) throw err;
        setError('Check your email to confirm your account, then sign in.');
      } else {
        const { error: err } = await supabase.auth.signInWithPassword({ email, password });
        if (err) throw err;
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-leaf-50">
      <header className="px-4 py-4">
        <Link to="/" className="text-leaf-800 font-semibold hover:text-leaf-600">
          ← Back to home
        </Link>
      </header>

      <div className="flex-1 flex items-center justify-center px-4 pb-12">
        <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md">
          <h1 className="text-2xl font-bold text-leaf-800 mb-2">Welcome back</h1>
          <p className="text-sm text-gray-500 mb-6">Sign in to manage your plants</p>

          {!supabaseConfigured && (
            <p className="text-amber-700 bg-amber-50 border border-amber-200 rounded p-3 text-sm mb-4">
              Add <code className="text-xs">VITE_SUPABASE_URL</code> and{' '}
              <code className="text-xs">VITE_SUPABASE_ANON_KEY</code> to enable auth.
            </p>
          )}

          {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

          <button
            type="button"
            onClick={googleLogin}
            disabled={!supabaseConfigured || loading}
            className="w-full flex items-center justify-center gap-3 border border-gray-300 rounded-lg py-2.5 mb-6 hover:bg-gray-50 disabled:opacity-50"
          >
            <GoogleIcon />
            Continue with Google
          </button>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-2 text-gray-400">or email</span>
            </div>
          </div>

          <form onSubmit={emailSubmit} className="space-y-4">
            <label className="block">
              <span className="text-sm text-gray-600">Email</span>
              <input
                type="email"
                required
                className="mt-1 w-full border rounded-lg px-3 py-2"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <label className="block">
              <span className="text-sm text-gray-600">Password</span>
              <input
                type="password"
                required
                minLength={6}
                className="mt-1 w-full border rounded-lg px-3 py-2"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-leaf-700 text-white py-2.5 rounded-lg font-medium disabled:opacity-50"
            >
              {loading ? 'Please wait…' : isRegister ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <button
            type="button"
            className="w-full mt-4 text-sm text-leaf-700"
            onClick={() => setIsRegister(!isRegister)}
          >
            {isRegister ? 'Already have an account? Sign in' : 'Need an account? Register'}
          </button>
        </div>
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  );
}
