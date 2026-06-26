import { useMutation, useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import { api, getAccessToken } from '../lib/api';

interface Plant {
  id: number;
  nickname: string;
  species: string;
}

interface DiagnosisResult {
  status: string;
  message?: string;
  plant?: string;
  disease?: string;
  confidence?: number;
  treatment?: {
    name: string;
    symptoms: string;
    home_remedies: string[];
    prevention: string;
  };
  image_url?: string;
}

interface HistoryItem {
  id: number;
  image_url: string;
  disease: string;
  confidence: number;
  created_at: string;
}

function confidenceColor(conf: number) {
  if (conf >= 80) return { bg: 'bg-green-500', text: 'text-green-700', label: 'High Confidence' };
  if (conf >= 60) return { bg: 'bg-yellow-500', text: 'text-yellow-700', label: 'Moderate Confidence' };
  return { bg: 'bg-red-500', text: 'text-red-700', label: 'Low Confidence' };
}

export default function DiagnosePage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [plantId, setPlantId] = useState<number | ''>('');
  const [result, setResult] = useState<DiagnosisResult | null>(null);
  const [shareLocation, setShareLocation] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const { data: plants = [] } = useQuery({
    queryKey: ['plants'],
    queryFn: () => api<Plant[]>('/api/v1/plants'),
  });

  const handleFile = (f: File) => {
    setFile(f);
    setResult(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(f);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const f = e.dataTransfer.files[0];
    if (f && f.type.startsWith('image/')) handleFile(f);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragActive(false), []);

  const diagnose = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('Select an image');
      const form = new FormData();
      form.append('file', file);
      if (plantId) form.append('plant_id', String(plantId));
      const token = await getAccessToken();
      const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/diagnose`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      });
      if (!res.ok) throw new Error('Diagnosis failed');
      return res.json() as Promise<DiagnosisResult>;
    },
    onSuccess: async (data) => {
      setResult(data);
      if (shareLocation && data.status === 'success' && data.disease) {
        navigator.geolocation.getCurrentPosition(async (pos) => {
          await api('/api/v1/disease-reports', {
            method: 'POST',
            body: JSON.stringify({
              disease: data.disease,
              species: data.plant,
              latitude: pos.coords.latitude,
              longitude: pos.coords.longitude,
            }),
          });
        });
      }
    },
  });

  const { data: history = [] } = useQuery({
    queryKey: ['diagnosis-history', plantId],
    queryFn: () =>
      api<HistoryItem[]>(
        plantId ? `/api/v1/diagnose/plants/${plantId}/diagnoses` : '/api/v1/diagnose/history',
      ),
  });

  const conf = result?.confidence ? confidenceColor(result.confidence) : null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Disease Detection</h1>
        <p className="text-gray-500 text-sm mt-1">Upload a photo of your plant's leaf to identify diseases and get treatment recommendations.</p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <div className="flex flex-wrap items-center gap-4 mb-5">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Plant (optional)</label>
            <select
              className="w-full max-w-xs bg-white border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
              value={plantId}
              onChange={(e) => setPlantId(e.target.value ? Number(e.target.value) : '')}
            >
              <option value="">Auto-detect from image</option>
              {plants.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nickname} ({p.species})
                </option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={shareLocation}
              onChange={(e) => setShareLocation(e.target.checked)}
              className="w-4 h-4 text-green-600 rounded border-gray-300 focus:ring-green-500"
            />
            Share anonymously on disease map
          </label>
        </div>

        {/* Drop zone */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
            dragActive
              ? 'border-green-500 bg-green-50'
              : file
              ? 'border-green-300 bg-green-50/30'
              : 'border-gray-200 hover:border-green-400 hover:bg-green-50/30'
          }`}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <input
            id="file-input"
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />
          {!file ? (
            <div className="space-y-3">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              </div>
              <div>
                <p className="text-gray-700 font-medium">Drop your leaf photo here</p>
                <p className="text-gray-400 text-sm mt-1">or click to browse files • JPG, PNG up to 10MB</p>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3 justify-center">
              <svg className="w-5 h-5 text-green-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-left">
                <p className="text-sm font-medium text-gray-700">{file.name}</p>
                <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                  setPreview(null);
                  setResult(null);
                }}
                className="ml-2 text-gray-400 hover:text-red-500 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
        </div>

        {/* Analyze button */}
        <div className="mt-5 flex items-center gap-4">
          <button
            disabled={!file || diagnose.isPending}
            onClick={() => diagnose.mutate()}
            className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium px-6 py-3 rounded-xl transition-all shadow-lg shadow-green-600/20"
          >
            {diagnose.isPending ? (
              <>
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Analyzing...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Analyze Image
              </>
            )}
          </button>
          {diagnose.isError && (
            <p className="text-sm text-red-600">Analysis failed. Please try again with a clearer image.</p>
          )}
        </div>
      </div>

      {/* Results */}
      {result && result.status !== 'error' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Image preview */}
          {preview && (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
              <img
                src={preview}
                alt="Uploaded leaf"
                className="w-full h-80 object-contain rounded-xl bg-gray-50"
              />
            </div>
          )}

          {/* Analysis results */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            {result.status === 'low_confidence' ? (
              <div className="flex items-start gap-3 p-4 bg-yellow-50 rounded-xl border border-yellow-200">
                <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <div>
                  <p className="font-medium text-yellow-800">Low Confidence Result</p>
                  <p className="text-sm text-yellow-700 mt-1">{result.message}</p>
                </div>
              </div>
            ) : (
              <div className="space-y-5">
                <div>
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Detected Disease</p>
                  <h2 className="text-xl font-bold text-gray-900 mt-1">{result.treatment?.name || result.disease}</h2>
                  <p className="text-sm text-gray-500 mt-0.5">on <span className="font-medium text-green-700">{result.plant}</span></p>
                </div>

                {/* Confidence bar */}
                {result.confidence != null && conf && (
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-medium text-gray-500">Confidence</span>
                      <span className={`text-xs font-semibold ${conf.text}`}>
                        {result.confidence.toFixed(1)}% — {conf.label}
                      </span>
                    </div>
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${conf.bg}`}
                        style={{ width: `${result.confidence}%` }}
                      />
                    </div>
                  </div>
                )}

                {result.disease && (
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg">
                    <span className="text-xs text-gray-500">Class:</span>
                    <span className="text-xs font-mono font-medium text-gray-700">{result.disease}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Treatment Recommendations */}
      {result?.treatment && result.status === 'success' && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-5 flex items-center gap-2">
            <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Treatment Recommendations
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Symptoms */}
            <div className="bg-red-50 rounded-xl p-4 border border-red-100">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-7 h-7 bg-red-200 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-red-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </span>
                <h4 className="font-semibold text-red-800 text-sm">Symptoms</h4>
              </div>
              <p className="text-sm text-red-700 leading-relaxed">{result.treatment.symptoms}</p>
            </div>

            {/* Home Remedies */}
            <div className="bg-green-50 rounded-xl p-4 border border-green-100">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-7 h-7 bg-green-200 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-green-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                  </svg>
                </span>
                <h4 className="font-semibold text-green-800 text-sm">Home Remedies</h4>
              </div>
              <ol className="space-y-2">
                {result.treatment.home_remedies.map((remedy, i) => (
                  <li key={i} className="flex gap-2 text-sm text-green-700">
                    <span className="flex-shrink-0 w-5 h-5 bg-green-200 rounded-full flex items-center justify-center text-xs font-bold text-green-800">
                      {i + 1}
                    </span>
                    <span className="leading-relaxed">{remedy}</span>
                  </li>
                ))}
              </ol>
            </div>

            {/* Prevention */}
            <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-7 h-7 bg-blue-200 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-blue-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </span>
                <h4 className="font-semibold text-blue-800 text-sm">Prevention</h4>
              </div>
              <p className="text-sm text-blue-700 leading-relaxed">{result.treatment.prevention}</p>
            </div>
          </div>
        </div>
      )}

      {/* Diagnosis History */}
      {history.length > 0 && (
        <div>
          <h3 className="text-lg font-bold text-gray-900 mb-4">Diagnosis History</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {history.map((h) => {
              const hConf = confidenceColor(h.confidence);
              return (
                <div
                  key={h.id}
                  className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow"
                >
                  {h.image_url && (
                    <img
                      src={`${import.meta.env.VITE_API_URL || ''}${h.image_url}`}
                      alt={h.disease}
                      className="w-full h-32 object-cover"
                    />
                  )}
                  <div className="p-3">
                    <p className="font-medium text-sm text-gray-900 truncate">{h.disease}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className={`text-xs font-medium ${hConf.text}`}>
                        {h.confidence?.toFixed(0)}%
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(h.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${hConf.bg}`}
                        style={{ width: `${h.confidence}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
