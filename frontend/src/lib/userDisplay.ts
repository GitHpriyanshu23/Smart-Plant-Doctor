import type { User } from '@supabase/supabase-js';

export function getUserDisplayName(user: User | null | undefined): string {
  if (!user) return '';

  const meta = user.user_metadata ?? {};
  const fullName = meta.full_name || meta.name;
  if (typeof fullName === 'string' && fullName.trim()) {
    return fullName.trim();
  }

  if (user.email) {
    const local = user.email.split('@')[0] ?? '';
    const cleaned = local.replace(/[._-]+/g, ' ').trim();
    if (!cleaned) return user.email;
    return cleaned
      .split(' ')
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }

  return 'User';
}

export function getUserInitial(user: User | null | undefined): string {
  const name = getUserDisplayName(user);
  return name.charAt(0).toUpperCase() || '?';
}
