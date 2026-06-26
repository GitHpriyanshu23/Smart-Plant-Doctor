import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { api } from '../lib/api';
import MarkdownContent from '../components/MarkdownContent';

const PLANT_IMAGES: Record<string, string> = {
  Rose: 'https://images.unsplash.com/photo-1455659817273-f96807779a8a?w=600&q=80',
  Hibiscus: 'https://images.unsplash.com/photo-1597848212624-a19eb35e2651?w=600&q=80',
  'Aloe Vera': 'https://images.unsplash.com/photo-1567331711402-509c12c41959?w=600&q=80',
  'Money Plant': 'https://images.unsplash.com/photo-1637967886160-fd78dc3ce3f5?w=600&q=80',
  Chrysanthemum: 'https://images.unsplash.com/photo-1504567961542-e24d9439a724?w=600&q=80',
  Turmeric: 'https://images.unsplash.com/photo-1615485500704-8e990f9900f7?w=600&q=80',
};

interface SpeciesProfile {
  species: string;
  care_guide: string;
  seasonal_tips: string;
  thresholds: Record<string, { min: number; max: number; ideal: number }>;
  common_diseases?: Record<string, string>;
}

const METRIC_CONFIG: Record<string, { label: string; unit: string; color: string; icon: string }> = {
  temperature: { label: 'Temperature', unit: '°C', color: 'from-orange-400 to-red-500', icon: '🌡️' },
  humidity: { label: 'Humidity', unit: '%', color: 'from-blue-400 to-cyan-500', icon: '💧' },
  soil_moisture: { label: 'Soil Moisture', unit: '%', color: 'from-amber-500 to-yellow-600', icon: '🌱' },
  light: { label: 'Light', unit: 'lux', color: 'from-yellow-300 to-orange-400', icon: '☀️' },
};

export default function EncyclopediaPage() {
  const { data: species = [], isLoading } = useQuery({
    queryKey: ['encyclopedia'],
    queryFn: () => api<SpeciesProfile[]>('/api/v1/encyclopedia'),
  });

  return (
    <div className="space-y-8">
      <div className="text-center max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-leaf-800 mb-3">Plant Encyclopedia</h1>
        <p className="text-gray-600 leading-relaxed">
          Explore our curated collection of plant profiles. Learn about ideal growing conditions,
          seasonal care tips, and common diseases for each species.
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-2xl shadow-sm animate-pulse">
              <div className="h-48 bg-gray-200 rounded-t-2xl" />
              <div className="p-5 space-y-3">
                <div className="h-5 bg-gray-200 rounded w-2/3" />
                <div className="h-4 bg-gray-100 rounded w-full" />
                <div className="h-4 bg-gray-100 rounded w-4/5" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {species.map((s) => (
            <Link
              key={s.species}
              to={`/encyclopedia/${encodeURIComponent(s.species)}`}
              className="group bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 hover:border-leaf-200 hover:-translate-y-1"
            >
              <div className="relative h-48 overflow-hidden">
                <img
                  src={PLANT_IMAGES[s.species] || 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400'}
                  alt={s.species}
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                <span className="absolute bottom-3 left-4 text-white font-bold text-lg drop-shadow-lg">
                  {s.species}
                </span>
              </div>
              <div className="p-5">
                <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">{s.seasonal_tips}</p>
                <span className="inline-flex items-center gap-1 mt-3 text-sm font-medium text-leaf-700 group-hover:text-leaf-600 transition-colors">
                  Learn more
                  <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export function EncyclopediaDetailPage({ species: speciesProp }: { species?: string }) {
  const params = useParams<{ species: string }>();
  const decodedSpecies = speciesProp || decodeURIComponent(params.species || '');

  const { data: profile, isLoading } = useQuery({
    queryKey: ['encyclopedia', decodedSpecies],
    queryFn: () => api<SpeciesProfile>(`/api/v1/encyclopedia/${encodeURIComponent(decodedSpecies)}`),
    enabled: !!decodedSpecies,
  });

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto animate-pulse space-y-6">
        <div className="h-6 bg-gray-200 rounded w-24" />
        <div className="h-64 bg-gray-200 rounded-2xl" />
        <div className="space-y-3">
          <div className="h-5 bg-gray-200 rounded w-1/3" />
          <div className="h-4 bg-gray-100 rounded w-full" />
          <div className="h-4 bg-gray-100 rounded w-4/5" />
        </div>
      </div>
    );
  }

  if (!profile) return <p className="text-center text-gray-500 py-12">Species not found.</p>;

  const imageUrl = PLANT_IMAGES[profile.species] || 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400';

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <Link
        to="/encyclopedia"
        className="inline-flex items-center gap-2 text-leaf-700 hover:text-leaf-800 font-medium transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Encyclopedia
      </Link>

      {/* Hero */}
      <div className="relative rounded-2xl overflow-hidden shadow-lg">
        <img src={imageUrl} alt={profile.species} className="w-full h-64 md:h-80 object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
        <div className="absolute bottom-6 left-6">
          <h1 className="text-3xl md:text-4xl font-bold text-white drop-shadow-lg">{profile.species}</h1>
        </div>
      </div>

      {/* Care Guide */}
      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 md:p-8">
        <h2 className="text-xl font-bold text-leaf-800 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-leaf-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          Care Guide
        </h2>
        <MarkdownContent content={profile.care_guide} />
      </section>

      {/* Ideal Conditions */}
      {profile.thresholds && Object.keys(profile.thresholds).length > 0 && (
        <section>
          <h2 className="text-xl font-bold text-leaf-800 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-leaf-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Ideal Conditions
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {Object.entries(profile.thresholds).map(([key, val]) => {
              const config = METRIC_CONFIG[key] || { label: key, unit: '', color: 'from-gray-400 to-gray-500', icon: '📊' };
              return (
                <div key={key} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-2xl">{config.icon}</span>
                    <h3 className="font-semibold text-gray-800">{config.label}</h3>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-500">
                      <span>Min: {val.min}{config.unit}</span>
                      <span className="font-semibold text-leaf-700">Ideal: {val.ideal}{config.unit}</span>
                      <span>Max: {val.max}{config.unit}</span>
                    </div>
                    <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`absolute inset-y-0 rounded-full bg-gradient-to-r ${config.color} opacity-30`}
                        style={{ left: '0%', right: '0%' }}
                      />
                      <div
                        className={`absolute inset-y-0 rounded-full bg-gradient-to-r ${config.color}`}
                        style={{
                          left: `${((val.min) / (val.max * 1.2)) * 100}%`,
                          right: `${100 - ((val.max) / (val.max * 1.2)) * 100}%`,
                        }}
                      />
                      <div
                        className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-leaf-600 rounded-full shadow"
                        style={{ left: `${((val.ideal) / (val.max * 1.2)) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Seasonal Tips */}
      {profile.seasonal_tips && (
        <section className="bg-gradient-to-br from-leaf-50 to-emerald-50 rounded-2xl p-6 md:p-8 border border-leaf-100">
          <h2 className="text-xl font-bold text-leaf-800 mb-3 flex items-center gap-2">
            <svg className="w-5 h-5 text-leaf-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Seasonal Tips
          </h2>
          <MarkdownContent content={profile.seasonal_tips} />
        </section>
      )}

      {/* Common Diseases */}
      {profile.common_diseases && Object.keys(profile.common_diseases).length > 0 && (
        <section>
          <h2 className="text-xl font-bold text-leaf-800 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            Common Diseases
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {Object.entries(profile.common_diseases).map(([name, description]) => (
              <div key={name} className="bg-white rounded-2xl shadow-sm border border-red-100 p-5">
                <h3 className="font-semibold text-red-700 mb-2">{name}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
