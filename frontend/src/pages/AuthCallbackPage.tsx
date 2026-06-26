import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export default function AuthCallbackPage() {
  const navigate = useNavigate();

  useEffect(() => {
    if (!supabase) {
      navigate('/login');
      return;
    }
    supabase.auth.getSession().then(({ data }) => {
      navigate(data.session ? '/dashboard' : '/login');
    });
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-leaf-700">Signing you in…</p>
    </div>
  );
}
