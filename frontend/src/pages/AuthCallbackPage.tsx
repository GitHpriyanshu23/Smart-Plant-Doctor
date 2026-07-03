import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export default function AuthCallbackPage() {
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    if (!supabase) {
      navigate('/login', { replace: true });
      return;
    }

    const client = supabase;
    let cancelled = false;

    const finish = (session: { access_token: string } | null, message?: string) => {
      if (cancelled) return;
      if (message) setError(message);
      navigate(session ? '/dashboard' : '/login', { replace: true });
    };

    const { data: { subscription } } = client.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session) {
        finish(session);
      }
    });

    const handleCallback = async () => {
      const query = new URLSearchParams(window.location.search);
      const code = query.get('code');
      const oauthError = query.get('error_description') || query.get('error');

      if (oauthError) {
        finish(null, decodeURIComponent(oauthError));
        return;
      }

      if (code) {
        const { error: exchangeError } = await client.auth.exchangeCodeForSession(code);
        if (exchangeError) {
          finish(null, exchangeError.message);
          return;
        }
      }

      const { data: { session }, error: sessionError } = await client.auth.getSession();
      if (sessionError) {
        finish(null, sessionError.message);
        return;
      }
      finish(session);
    };

    void handleCallback();

    return () => {
      cancelled = true;
      subscription.unsubscribe();
    };
  }, [navigate]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4">
      <p className="text-leaf-700">{error ? 'Sign-in failed' : 'Signing you in…'}</p>
      {error && (
        <>
          <p className="text-red-600 text-sm text-center max-w-md">{error}</p>
          <Link to="/login" className="text-leaf-700 underline text-sm">
            Back to login
          </Link>
        </>
      )}
    </div>
  );
}
