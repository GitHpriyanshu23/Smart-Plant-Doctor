# Supabase setup — Smart Plant Doctor

Project URL: `https://yzpjyhrnkwmtsviysnre.supabase.co`

## 1. Frontend (done)

`frontend/.env` is configured with `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.

Restart the dev server after any env change:

```bash
cd frontend && npm run dev
```

## 2. Backend — still required

Open [Supabase Dashboard](https://supabase.com/dashboard/project/yzpjyhrnkwmtsviysnre/settings/api) and add to `backend/.env`:

| Variable | Where to find it |
|----------|------------------|
| `SUPABASE_JWT_SECRET` | Settings → API → **JWT Secret** |
| `DATABASE_URL` | Settings → Database → **Connection string** → URI (use **Session pooler**, port 6543) |

Then restart the backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## 3. Google sign-in (fix `redirect_uri_mismatch`)

Google OAuth goes **through Supabase**, not directly to your app. You must add Supabase’s callback URL in **Google Cloud Console**.

### Step A — Google Cloud Console

1. Open [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Edit your **OAuth 2.0 Client ID** (Web application)
3. Under **Authorized redirect URIs**, add **exactly**:

   ```
   https://yzpjyhrnkwmtsviysnre.supabase.co/auth/v1/callback
   ```

4. Under **Authorized JavaScript origins**, add:

   ```
   http://localhost:5173
   https://yzpjyhrnkwmtsviysnre.supabase.co
   ```

5. Save. Changes can take a few minutes to apply.

### Step B — Supabase Dashboard

1. [Authentication → Providers → Google](https://supabase.com/dashboard/project/yzpjyhrnkwmtsviysnre/auth/providers) — enable, paste **Client ID** and **Client Secret** from Google
2. [Authentication → URL configuration](https://supabase.com/dashboard/project/yzpjyhrnkwmtsviysnre/auth/url-configuration):
   - **Site URL:** `http://localhost:5173`
   - **Redirect URLs:** add `http://localhost:5173/auth/callback`

### Why the error happens

`Error 400: redirect_uri_mismatch` means Google received a redirect URI that is **not** in your OAuth client’s allowed list. With Supabase, that URI is always:

`https://<your-project-ref>.supabase.co/auth/v1/callback`

—not `http://localhost:5173/auth/callback` (that URL is only used by Supabase **after** Google redirects back).

## 4. Email sign-in

Enabled by default. For local dev, you may disable email confirmation under **Authentication → Providers → Email**.

## Security note

The **anon key** is safe to use in the browser. Never put the **service role key** or **JWT secret** in the frontend.
