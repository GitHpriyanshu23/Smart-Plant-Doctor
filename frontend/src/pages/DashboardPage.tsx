import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { usePlantWebSocket } from '../hooks/useWebSocket';
import { api } from '../lib/api';

interface Plant {
  id: number;
  species: string;
  nickname: string;
}

interface Reading {
  id: number;
  ts: number;
  temperature: number;
  humidity: number;
  light: number;
  soil_moisture: number;
  ph: number;
  soil_status?: string;
}

interface BlynkPayload {
  connected: boolean;
  source: string;
  latest: Reading;
  readings: Reading[];
}

function generateMockReadings(): Reading[] {
  const now = Math.floor(Date.now() / 1000);
  const readings: Reading[] = [];
  for (let i = 47; i >= 0; i--) {
    const ts = now - i * 1800;
    const hour = new Date(ts * 1000).getHours();
    const isDay = hour >= 6 && hour <= 20;
    readings.push({
      id: 1000 + i,
      ts,
      temperature: 24 + 4 * Math.sin((hour - 6) * Math.PI / 14) + (Math.random() - 0.5) * 2,
      humidity: 55 + 15 * Math.sin((hour - 2) * Math.PI / 12) + (Math.random() - 0.5) * 5,
      light: isDay ? 400 + 300 * Math.sin((hour - 6) * Math.PI / 14) + (Math.random() - 0.5) * 80 : 5 + Math.random() * 15,
      soil_moisture: 52 - i * 0.3 + (Math.random() - 0.5) * 4,
      ph: 6.3 + (Math.random() - 0.5) * 0.4,
    });
  }
  return readings;
}

const MOCK_PLANTS: Plant[] = [
  { id: -1, species: 'Rose', nickname: 'Balcony Rose' },
  { id: -2, species: 'Aloe Vera', nickname: 'Kitchen Aloe' },
  { id: -3, species: 'Money Plant', nickname: 'Office Buddy' },
];

const BLYNK_PLANTS: Plant[] = [
  { id: -10, species: 'Live Sensor', nickname: 'Smart Plant Doctor' },
];

function soilStatus(moisture: number, blynkRaw = false, statusLabel?: string) {
  if (statusLabel) {
    const label = statusLabel;
    if (label === 'Dry') return { label, color: 'bg-orange-100 text-orange-700', icon: '⚠️' };
    if (label === 'Moist') return { label, color: 'bg-green-100 text-green-700', icon: '💧' };
    if (label === 'Wet') return { label, color: 'bg-blue-100 text-blue-700', icon: '🌱' };
  }

  if (blynkRaw) {
    if (moisture >= 2500) return { label: 'Dry', color: 'bg-orange-100 text-orange-700', icon: '⚠️' };
    if (moisture >= 1500) return { label: 'Moist', color: 'bg-green-100 text-green-700', icon: '💧' };
    return { label: 'Wet', color: 'bg-blue-100 text-blue-700', icon: '🌱' };
  }

  if (moisture < 30) return { label: 'Dry', color: 'bg-orange-100 text-orange-700', icon: '🏜️' };
  if (moisture < 60) return { label: 'Moist', color: 'bg-green-100 text-green-700', icon: '💧' };
  return { label: 'Wet', color: 'bg-blue-100 text-blue-700', icon: '🌊' };
}

function soilMoisturePercent(moisture: number, blynkRaw: boolean) {
  if (!blynkRaw) return moisture;
  const dryAdc = 3200;
  const wetAdc = 1200;
  const pct = ((dryAdc - moisture) / (dryAdc - wetAdc)) * 100;
  return Math.max(0, Math.min(100, pct));
}

function healthScore(r: Reading, blynkRaw = false) {
  const soilPct = soilMoisturePercent(r.soil_moisture, blynkRaw);
  const lightValue = blynkRaw ? (r.light / 4095) * 1200 : r.light;
  let score = 100;
  if (r.temperature < 15 || r.temperature > 32) score -= 20;
  if (r.humidity < 30 || r.humidity > 85) score -= 15;
  if (soilPct < 25 || soilPct > 80) score -= 25;
  if (lightValue < 200) score -= 10;
  return Math.max(0, score);
}

function getMetricStatus(label: string, value: number, blynkRaw = false): { status: 'good' | 'warning' | 'critical'; delta: string } {
  if (blynkRaw && label === 'soil_moisture') {
    if (value >= 3000) return { status: 'critical', delta: '↓ Dry' };
    if (value >= 2500) return { status: 'warning', delta: '↓ Dry' };
    if (value < 1200) return { status: 'warning', delta: '↑ Wet' };
    return { status: 'good', delta: '✓ Optimal' };
  }
  if (blynkRaw && label === 'light') {
    if (value < 300) return { status: 'critical', delta: '↓ Too dark' };
    if (value < 800) return { status: 'warning', delta: '↓ Low light' };
    return { status: 'good', delta: '✓ Good light' };
  }

  switch (label) {
    case 'temperature':
      if (value < 10 || value > 38) return { status: 'critical', delta: value > 38 ? '↑ High' : '↓ Low' };
      if (value < 15 || value > 32) return { status: 'warning', delta: value > 32 ? '↑ Warm' : '↓ Cool' };
      return { status: 'good', delta: '✓ Optimal' };
    case 'humidity':
      if (value < 20 || value > 90) return { status: 'critical', delta: value > 90 ? '↑ High' : '↓ Low' };
      if (value < 30 || value > 80) return { status: 'warning', delta: value > 80 ? '↑ High' : '↓ Low' };
      return { status: 'good', delta: '✓ Optimal' };
    case 'soil_moisture':
      if (value < 15 || value > 90) return { status: 'critical', delta: value > 90 ? '↑ Saturated' : '↓ Parched' };
      if (value < 30 || value > 75) return { status: 'warning', delta: value > 75 ? '↑ High' : '↓ Low' };
      return { status: 'good', delta: '✓ Optimal' };
    case 'light':
      if (value < 100) return { status: 'critical', delta: '↓ Too dark' };
      if (value < 300) return { status: 'warning', delta: '↓ Low light' };
      return { status: 'good', delta: '✓ Good light' };
    case 'health':
      if (value < 50) return { status: 'critical', delta: '↓ Poor' };
      if (value < 75) return { status: 'warning', delta: '~ Fair' };
      return { status: 'good', delta: '✓ Healthy' };
    default:
      return { status: 'good', delta: '' };
  }
}

function getRecommendations(r: Reading, blynkRaw = false): Array<{ text: string; type: 'good' | 'warning' | 'critical' }> {
  const tips: Array<{ text: string; type: 'good' | 'warning' | 'critical' }> = [];
  const soilPct = soilMoisturePercent(r.soil_moisture, blynkRaw);
  const lightValue = blynkRaw ? (r.light / 4095) * 1200 : r.light;
  if (r.temperature >= 15 && r.temperature <= 32)
    tips.push({ text: 'Temperature is in the optimal range for most houseplants.', type: 'good' });
  else if (r.temperature > 32)
    tips.push({ text: 'Temperature is high — move the plant away from direct heat sources.', type: 'warning' });
  else
    tips.push({ text: 'Temperature is low — consider moving your plant to a warmer spot.', type: 'warning' });

  if (soilPct > 75)
    tips.push({ text: 'Soil moisture is high — reduce watering frequency to prevent root rot.', type: 'warning' });
  else if (soilPct < 25)
    tips.push({ text: 'Soil is dry — water your plant soon.', type: 'critical' });
  else
    tips.push({ text: 'Soil moisture is at a healthy level.', type: 'good' });

  if (r.humidity < 30)
    tips.push({ text: 'Humidity is low — consider misting or using a humidifier.', type: 'warning' });
  else if (r.humidity > 80)
    tips.push({ text: 'Humidity is very high — ensure good air circulation.', type: 'warning' });
  else
    tips.push({ text: 'Humidity levels are comfortable for your plant.', type: 'good' });

  if (lightValue < 200)
    tips.push({ text: 'Light levels are low — move to a brighter location or supplement with grow lights.', type: 'warning' });
  else
    tips.push({ text: 'Light intensity is adequate for healthy growth.', type: 'good' });

  return tips;
}

const statusColors = {
  good: 'border-green-200 bg-green-50',
  warning: 'border-yellow-200 bg-yellow-50',
  critical: 'border-red-200 bg-red-50',
};

const statusTextColors = {
  good: 'text-green-600',
  warning: 'text-yellow-600',
  critical: 'text-red-600',
};

const statusDotColors = {
  good: 'bg-green-500',
  warning: 'bg-yellow-500',
  critical: 'bg-red-500',
};

export default function DashboardPage() {
  const [plantId, setPlantId] = useState<number | null>(null);

  const { data: blynkData, isSuccess: blynkReady, isError: blynkError } = useQuery({
    queryKey: ['blynk-readings'],
    queryFn: () => api<BlynkPayload>('/api/v1/sensors/blynk/readings?hours=1'),
    refetchInterval: 5000,
    retry: false,
  });

  const usingBlynk = blynkReady && !!blynkData && blynkData.readings.length > 0;

  const { data: apiPlants, isError: plantsError } = useQuery({
    queryKey: ['plants'],
    queryFn: () => api<Plant[]>('/api/v1/plants'),
    retry: false,
    enabled: !usingBlynk,
  });

  const noPlants = !usingBlynk && (plantsError || !apiPlants || apiPlants.length === 0);
  const plants: Plant[] = usingBlynk ? BLYNK_PLANTS : noPlants ? MOCK_PLANTS : apiPlants ?? [];

  const selectedId = plantId ?? plants[0]?.id ?? null;

  const { data: apiReadings = [], isFetched: readingsFetched } = useQuery({
    queryKey: ['readings', selectedId],
    queryFn: () => api<Reading[]>(`/api/v1/plants/${selectedId}/readings?limit=200`),
    enabled: !!selectedId && !noPlants && !usingBlynk,
    refetchInterval: 30000,
    retry: false,
  });

  const mockReadings = useMemo(() => generateMockReadings(), []);
  const usingMockReadings = !usingBlynk && (noPlants || (readingsFetched && apiReadings.length === 0));
  const readings = usingBlynk ? blynkData!.readings : usingMockReadings ? mockReadings : apiReadings;
  const isDemo = !usingBlynk && (noPlants || usingMockReadings);
  const isBlynkLive = usingBlynk && blynkData!.connected;

  const realPlantId = noPlants || usingBlynk ? null : selectedId;
  const { reading: liveReading, connected } = usePlantWebSocket(realPlantId);

  const latest = usingBlynk ? blynkData!.latest : liveReading || readings[0];
  const blynkRaw = usingBlynk;
  const chartData = [...readings].reverse().map((r) => ({
    time: new Date(r.ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    temp: +r.temperature.toFixed(1),
    humidity: +r.humidity.toFixed(1),
    soil: +r.soil_moisture.toFixed(0),
    light: +r.light.toFixed(0),
  }));

  const soil = latest
    ? soilStatus(
        latest.soil_moisture,
        blynkRaw,
        'soil_status' in latest ? latest.soil_status : undefined,
      )
    : null;
  const health = latest ? healthScore(latest, blynkRaw) : 0;
  const recommendations = latest ? getRecommendations(latest, blynkRaw) : [];
  const lastUpdated = latest ? new Date(latest.ts * 1000).toLocaleString() : null;
  const soilBarWidth = latest ? soilMoisturePercent(latest.soil_moisture, blynkRaw) : 0;

  return (
    <div className="space-y-6">
      {/* Top bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Plant Dashboard</h1>
          {lastUpdated && (
            <p className="text-sm text-gray-500 mt-0.5">Last updated: {lastUpdated}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <select
            className="bg-white border border-gray-200 rounded-lg px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
            value={selectedId ?? ''}
            onChange={(e) => setPlantId(Number(e.target.value))}
          >
            {plants.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nickname} ({p.species})
              </option>
            ))}
          </select>
          <span
            className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full ${
              isBlynkLive
                ? 'bg-green-100 text-green-700 ring-1 ring-green-200'
                : isDemo
                ? 'bg-amber-100 text-amber-700 ring-1 ring-amber-200'
                : connected
                  ? 'bg-green-100 text-green-700 ring-1 ring-green-200'
                  : 'bg-gray-100 text-gray-600 ring-1 ring-gray-200'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${
              isBlynkLive || connected
                ? 'bg-green-500 animate-pulse'
                : isDemo
                  ? 'bg-amber-500 animate-pulse'
                  : 'bg-gray-400'
            }`} />
            {isBlynkLive ? 'Blynk Live' : isDemo ? 'Demo' : connected ? 'Live' : usingBlynk ? 'Blynk' : 'Polling'}
          </span>
        </div>
      </div>

      {blynkError && !usingBlynk && (
        <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
          Live Blynk sensor feed is unavailable. Showing demo data until `BLYNK_AUTH_TOKEN` is configured on the backend.
        </p>
      )}

      {latest && (
        <>
          {/* Metric cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <MetricCard
              label="Temperature"
              value={`${latest.temperature.toFixed(1)}°C`}
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
              metric="temperature"
              rawValue={latest.temperature}
            />
            <MetricCard
              label="Humidity"
              value={`${latest.humidity.toFixed(0)}%`}
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
                </svg>
              }
              metric="humidity"
              rawValue={latest.humidity}
            />
            <MetricCard
              label="Light"
              value={`${latest.light.toFixed(0)} lx`}
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                </svg>
              }
              metric="light"
              rawValue={latest.light}
              blynkRaw={blynkRaw}
            />
            <MetricCard
              label={blynkRaw ? 'Soil' : 'Soil Moisture'}
              value={blynkRaw ? `${latest.soil_moisture.toFixed(0)}` : `${latest.soil_moisture.toFixed(0)}%`}
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 12c0 4.97-4.03 9-9 9s-9-4.03-9-9c0-3.728 4.5-9.5 9-14 4.5 4.5 9 10.272 9 14z" />
                </svg>
              }
              metric="soil_moisture"
              rawValue={latest.soil_moisture}
              badge={soil}
              blynkRaw={blynkRaw}
            />
            <MetricCard
              label="Plant Health"
              value={`${health}%`}
              icon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
                </svg>
              }
              metric="health"
              rawValue={health}
            />
          </div>

          {/* Main content grid */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Charts - 3 columns */}
            <div className="lg:col-span-3 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Temperature & Humidity chart */}
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                  <h3 className="text-sm font-semibold text-gray-700 mb-4">Temperature & Humidity</h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#9ca3af" />
                        <YAxis stroke="#9ca3af" tick={{ fontSize: 10 }} />
                        <Tooltip
                          contentStyle={{ borderRadius: '12px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                        />
                        <Legend wrapperStyle={{ fontSize: '12px' }} />
                        <Line type="monotone" dataKey="temp" stroke="#16a34a" strokeWidth={2} dot={false} name="Temp (°C)" />
                        <Line type="monotone" dataKey="humidity" stroke="#2563eb" strokeWidth={2} dot={false} name="Humidity (%)" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Soil Moisture & Light chart */}
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                  <h3 className="text-sm font-semibold text-gray-700 mb-4">Soil Moisture & Light</h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#9ca3af" />
                        <YAxis stroke="#9ca3af" tick={{ fontSize: 10 }} />
                        <Tooltip
                          contentStyle={{ borderRadius: '12px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                        />
                        <Legend wrapperStyle={{ fontSize: '12px' }} />
                        <Line type="monotone" dataKey="soil" stroke="#ca8a04" strokeWidth={2} dot={false} name={blynkRaw ? 'Soil (raw)' : 'Soil (%)'} />
                        <Line type="monotone" dataKey="light" stroke="#9333ea" strokeWidth={2} dot={false} name="Light (lx)" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                  <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  Care Recommendations
                </h3>
                <div className="space-y-3">
                  {recommendations.map((rec, i) => (
                    <div
                      key={i}
                      className={`flex items-start gap-3 p-3 rounded-xl ${
                        rec.type === 'good' ? 'bg-green-50' : rec.type === 'warning' ? 'bg-yellow-50' : 'bg-red-50'
                      }`}
                    >
                      <span className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                        rec.type === 'good' ? 'bg-green-200 text-green-700' : rec.type === 'warning' ? 'bg-yellow-200 text-yellow-700' : 'bg-red-200 text-red-700'
                      }`}>
                        {rec.type === 'good' ? '✓' : rec.type === 'warning' ? '!' : '✕'}
                      </span>
                      <p className={`text-sm ${
                        rec.type === 'good' ? 'text-green-800' : rec.type === 'warning' ? 'text-yellow-800' : 'text-red-800'
                      }`}>
                        {rec.text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Sidebar - 1 column */}
            <div className="space-y-6">
              {/* Model Stats */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-gray-700 mb-4">AI Model Stats</h3>
                <div className="space-y-4">
                  <StatItem label="Model Accuracy" value="92.37%" />
                  <StatItem label="Supported Plants" value="6" />
                  <StatItem label="Disease Classes" value="29" />
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">AI Status</span>
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-50 px-2 py-1 rounded-full">
                      <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                      Online
                    </span>
                  </div>
                </div>
              </div>

              {/* Soil Status */}
              {soil && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Soil Status</h3>
                  <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium ${soil.color}`}>
                    <span>{soil.icon}</span>
                    <span>{soil.label}</span>
                  </div>
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Dry</span>
                      <span>Wet</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-orange-400 via-green-500 to-blue-500"
                        style={{ width: `${Math.min(100, soilBarWidth)}%` }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Quick actions */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Actions</h3>
                <div className="space-y-2">
                  <a href="/diagnose" className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors group">
                    <span className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600 group-hover:bg-purple-200 transition-colors">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </span>
                    <span className="text-sm text-gray-700">Diagnose Disease</span>
                  </a>
                  <a href="/chat" className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors group">
                    <span className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600 group-hover:bg-blue-200 transition-colors">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                    </span>
                    <span className="text-sm text-gray-700">Ask AI Assistant</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon,
  metric,
  rawValue,
  badge,
  blynkRaw = false,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  metric: string;
  rawValue: number;
  badge?: { label: string; color: string; icon: string } | null;
  blynkRaw?: boolean;
}) {
  const { status, delta } = getMetricStatus(metric, rawValue, blynkRaw);

  return (
    <div className={`rounded-2xl border p-4 transition-all hover:shadow-md ${statusColors[status]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className={`${statusTextColors[status]}`}>{icon}</span>
        <span className={`w-2 h-2 rounded-full ${statusDotColors[status]}`} />
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
      <p className={`text-xs font-medium mt-1 ${statusTextColors[status]}`}>{delta}</p>
      {badge && (
        <span className={`inline-block mt-2 text-xs px-2 py-0.5 rounded-full font-medium ${badge.color}`}>
          {badge.icon} {badge.label}
        </span>
      )}
    </div>
  );
}

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-sm font-semibold text-gray-900">{value}</span>
    </div>
  );
}
