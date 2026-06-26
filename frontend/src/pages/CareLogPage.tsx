import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { api } from '../lib/api';

const EVENT_TYPES = ['water', 'fertilize', 'prune', 'repot', 'note'];

interface CareEvent {
  id: number;
  event_type: string;
  notes: string | null;
  created_at: string;
}

export default function CareLogPage() {
  const { plantId } = useParams<{ plantId: string }>();
  const id = Number(plantId);
  const qc = useQueryClient();

  const { data: events = [] } = useQuery({
    queryKey: ['care', id],
    queryFn: () => api<CareEvent[]>(`/api/v1/plants/${id}/care-events`),
    enabled: !!id,
  });

  const add = useMutation({
    mutationFn: (body: { event_type: string; notes?: string }) =>
      api(`/api/v1/plants/${id}/care-events`, {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['care', id] }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold text-leaf-800 mb-6">Care Log</h1>

      <div className="flex flex-wrap gap-2 mb-6">
        {EVENT_TYPES.map((t) => (
          <button
            key={t}
            onClick={() => add.mutate({ event_type: t })}
            className="bg-leaf-700 text-white px-3 py-1 rounded text-sm capitalize"
          >
            Log {t}
          </button>
        ))}
      </div>

      <ul className="space-y-3">
        {events.map((e) => (
          <li key={e.id} className="bg-white rounded-lg shadow p-4 flex justify-between">
            <span className="capitalize font-medium">{e.event_type}</span>
            <span className="text-gray-500 text-sm">{new Date(e.created_at).toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
