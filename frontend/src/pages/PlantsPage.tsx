import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';

interface Plant {
  id: number;
  species: string;
  nickname: string;
  device_id: number | null;
  created_at?: string;
}

const SPECIES = ['Rose', 'Hibiscus', 'Aloe Vera', 'Money Plant', 'Chrysanthemum', 'Turmeric'];

const PLANT_IMAGES: Record<string, string> = {
  Rose: 'https://images.unsplash.com/photo-1455659817273-f96807779a8a?w=600&q=80',
  Hibiscus: 'https://images.unsplash.com/photo-1597848212624-a19eb35e2651?w=600&q=80',
  'Aloe Vera': 'https://images.unsplash.com/photo-1567331711402-509c12c41959?w=600&q=80',
  'Money Plant': 'https://images.unsplash.com/photo-1637967886160-fd78dc3ce3f5?w=600&q=80',
  Chrysanthemum: 'https://images.unsplash.com/photo-1504567961542-e24d9439a724?w=600&q=80',
  Turmeric: 'https://images.unsplash.com/photo-1615485500704-8e990f9900f7?w=600&q=80',
};

export default function PlantsPage() {
  const qc = useQueryClient();
  const [nickname, setNickname] = useState('');
  const [species, setSpecies] = useState(SPECIES[0]);
  const [showForm, setShowForm] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const { data: plants = [], isLoading } = useQuery({
    queryKey: ['plants'],
    queryFn: () => api<Plant[]>('/api/v1/plants'),
  });

  const create = useMutation({
    mutationFn: () =>
      api<Plant>('/api/v1/plants', {
        method: 'POST',
        body: JSON.stringify({ nickname, species }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['plants'] });
      setNickname('');
      setShowForm(false);
    },
  });

  const remove = useMutation({
    mutationFn: (id: number) => api(`/api/v1/plants/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['plants'] });
      setDeletingId(null);
    },
  });

  const handleDelete = (id: number) => {
    setDeletingId(id);
    setTimeout(() => remove.mutate(id), 300);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-leaf-800">My Plants</h1>
          <p className="text-gray-500 mt-1">Manage your plant collection</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-2 bg-leaf-700 hover:bg-leaf-800 text-white px-5 py-2.5 rounded-xl font-medium shadow-lg shadow-leaf-700/25 transition-all hover:shadow-xl hover:shadow-leaf-700/30 hover:-translate-y-0.5"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Plant
        </button>
      </div>

      {/* Add Plant Form */}
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          showForm ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <form
          className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Add a New Plant</h2>
          <div className="flex flex-col md:flex-row gap-6">
            {/* Species Preview */}
            <div className="md:w-48 flex-shrink-0">
              <div className="relative rounded-xl overflow-hidden aspect-square">
                <img
                  src={PLANT_IMAGES[species] || 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400'}
                  alt={species}
                  className="w-full h-full object-cover transition-all duration-300"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
                <span className="absolute bottom-2 left-3 text-white text-sm font-medium">{species}</span>
              </div>
            </div>

            {/* Form Fields */}
            <div className="flex-1 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nickname</label>
                <input
                  required
                  placeholder="e.g. Kitchen Rose, Balcony Aloe..."
                  className="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-leaf-500 focus:border-leaf-500 outline-none transition-all"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Species</label>
                <select
                  className="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-leaf-500 focus:border-leaf-500 outline-none transition-all bg-white"
                  value={species}
                  onChange={(e) => setSpecies(e.target.value)}
                >
                  {SPECIES.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={create.isPending}
                  className="bg-leaf-700 hover:bg-leaf-800 disabled:opacity-60 text-white px-6 py-2.5 rounded-xl font-medium transition-colors"
                >
                  {create.isPending ? 'Adding...' : 'Add Plant'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="text-gray-600 hover:text-gray-800 px-4 py-2.5 rounded-xl font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>

      {/* Plants Grid */}
      {isLoading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-2xl shadow-sm animate-pulse">
              <div className="h-40 bg-gray-200 rounded-t-2xl" />
              <div className="p-5 space-y-3">
                <div className="h-5 bg-gray-200 rounded w-2/3" />
                <div className="h-4 bg-gray-100 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : plants.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">🌱</div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No plants yet</h3>
          <p className="text-gray-500 max-w-sm mx-auto">
            Start building your plant collection. Click "Add Plant" above to register your first green companion.
          </p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {plants.map((p) => (
            <div
              key={p.id}
              className={`bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 ${
                deletingId === p.id ? 'opacity-0 scale-95 transition-all duration-300' : ''
              }`}
            >
              <div className="relative h-40 overflow-hidden">
                <img
                  src={PLANT_IMAGES[p.species] || 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400'}
                  alt={p.species}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                <div className="absolute top-3 right-3">
                  <span className="inline-flex items-center gap-1 bg-white/90 backdrop-blur-sm text-xs font-medium text-leaf-700 px-2.5 py-1 rounded-full">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    Active
                  </span>
                </div>
              </div>
              <div className="p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="font-bold text-lg text-gray-800">{p.nickname}</h2>
                    <p className="text-gray-500 text-sm">{p.species}</p>
                    {p.created_at && (
                      <p className="text-gray-400 text-xs mt-1">
                        Added {new Date(p.created_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-50">
                  <Link
                    to={`/care-log/${p.id}`}
                    className="inline-flex items-center gap-1 text-sm font-medium text-leaf-700 hover:text-leaf-800 transition-colors"
                  >
                    Care log
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>
                  <button
                    onClick={() => handleDelete(p.id)}
                    className="text-sm text-gray-400 hover:text-red-600 transition-colors p-1"
                    title="Delete plant"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
