import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../lib/api';

interface RegisterResponse {
  device_id: number;
  setup_token: string;
  qr_payload: string;
  claim_url: string;
}

export default function DeviceOnboardPage() {
  const [reg, setReg] = useState<RegisterResponse | null>(null);

  const register = useMutation({
    mutationFn: () =>
      api<RegisterResponse>('/api/v1/devices/register?name=ESP32', { method: 'POST' }),
    onSuccess: setReg,
  });

  return (
    <div>
      <h1 className="text-2xl font-bold text-leaf-800 mb-6">Device Onboarding</h1>

      <div className="bg-white rounded-xl shadow p-6 max-w-lg">
        <p className="text-sm text-gray-600 mb-4">
          Register a new ESP32 sensor hub. Flash the updated firmware, then use the setup token below
          during the device claim step.
        </p>
        <button
          onClick={() => register.mutate()}
          disabled={register.isPending}
          className="bg-leaf-700 text-white px-4 py-2 rounded"
        >
          Register new device
        </button>

        {reg && (
          <div className="mt-6 space-y-3 text-sm">
            <p><strong>Device ID:</strong> {reg.device_id}</p>
            <p><strong>Setup token:</strong></p>
            <code className="block bg-gray-100 p-2 rounded break-all">{reg.setup_token}</code>
            <p><strong>Claim URL:</strong> {reg.claim_url}</p>
            <p><strong>QR payload:</strong></p>
            <code className="block bg-gray-100 p-2 rounded break-all text-xs">{reg.qr_payload}</code>
            <p className="text-gray-500 mt-2">
              ESP32 will POST to <code>/api/v1/devices/claim</code> with this token, then store the
              returned device token in NVS.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
