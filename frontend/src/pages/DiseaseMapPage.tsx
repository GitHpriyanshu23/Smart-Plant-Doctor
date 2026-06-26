import { useMutation, useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { api } from '../lib/api';

interface MapPoint {
  geohash: string;
  region: string | null;
  disease: string;
  count: number;
}

function geohashToLatLng(gh: string): [number, number] {
  if (gh === 'unknown' || !gh) return [20, 78];
  const base32 = '0123456789bcdefghjkmnpqrstuvwxyz';
  let latMin = -90, latMax = 90, lngMin = -180, lngMax = 180;
  let even = true;
  for (const c of gh) {
    const idx = base32.indexOf(c);
    if (idx < 0) continue;
    for (let i = 4; i >= 0; i--) {
      const bit = (idx >> i) & 1;
      if (even) {
        const mid = (lngMin + lngMax) / 2;
        if (bit) lngMin = mid; else lngMax = mid;
      } else {
        const mid = (latMin + latMax) / 2;
        if (bit) latMin = mid; else latMax = mid;
      }
      even = !even;
    }
  }
  return [(latMin + latMax) / 2, (lngMin + lngMax) / 2];
}

export default function DiseaseMapPage() {
  const { data: points = [] } = useQuery({
    queryKey: ['disease-map'],
    queryFn: () => api<MapPoint[]>('/api/v1/disease-map'),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold text-leaf-800 mb-2">Disease Map</h1>
      <p className="text-sm text-gray-600 mb-4">Anonymized, opt-in reports from the community.</p>

      <div className="bg-white rounded-xl shadow overflow-hidden h-96 mb-4">
        <MapContainer center={[20, 78]} zoom={4} style={{ height: '100%', width: '100%' }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {points.map((p, i) => {
            const [lat, lng] = geohashToLatLng(p.geohash);
            return (
              <CircleMarker key={i} center={[lat, lng]} radius={6 + p.count * 2} pathOptions={{ color: '#16a34a' }}>
                <Popup>
                  <strong>{p.disease}</strong>
                  <br />
                  Reports: {p.count}
                  {p.region && <><br />Region: {p.region}</>}
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>

      <ul className="text-sm space-y-1">
        {points.map((p, i) => (
          <li key={i}>{p.disease}: {p.count} report(s)</li>
        ))}
      </ul>
    </div>
  );
}
