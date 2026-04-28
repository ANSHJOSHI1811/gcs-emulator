import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, Copy, ExternalLink, Loader2, RefreshCw, Save, Trash2 } from 'lucide-react';
import { deleteRunService, getRunService, RunService, updateRunTraffic } from '../api/run';

const DEFAULT_REGION = 'us-central1';

interface TrafficDraftRow {
  revision: string;
  percent: number;
}

function extractRevisionName(input: string): string {
  if (!input) return '';
  const parts = input.split('/').filter(Boolean);
  return parts[parts.length - 1] || input;
}

export default function CloudRunServiceDetailPage() {
  const { serviceName } = useParams<{ serviceName: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const location = searchParams.get('location') || DEFAULT_REGION;

  const [service, setService] = useState<RunService | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingTraffic, setSavingTraffic] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [draftTraffic, setDraftTraffic] = useState<TrafficDraftRow[]>([]);

  const loadService = useCallback(async () => {
    if (!serviceName) return;
    try {
      setLoading(true);
      const data = await getRunService(location, serviceName);
      setService(data);

      const fromServiceTraffic = (data.traffic || []).map((t) => ({
        revision: extractRevisionName(t.revision || ''),
        percent: Number(t.percent || 0),
      }));

      if (fromServiceTraffic.length > 0) {
        setDraftTraffic(fromServiceTraffic);
      } else {
        setDraftTraffic(
          data.revisions.map((r, idx) => ({
            revision: extractRevisionName(r.name),
            percent: idx === 0 ? 100 : 0,
          }))
        );
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to load service details');
      setService(null);
    } finally {
      setLoading(false);
    }
  }, [location, serviceName]);

  useEffect(() => {
    loadService();
  }, [loadService]);

  const totalPercent = useMemo(
    () => draftTraffic.reduce((sum, row) => sum + Number(row.percent || 0), 0),
    [draftTraffic]
  );

  const hasNonZero = useMemo(() => draftTraffic.some((row) => row.percent > 0), [draftTraffic]);

  const trafficErrors = useMemo(() => {
    const errors: string[] = [];
    if (!draftTraffic.length) errors.push('At least one revision is required for traffic routing.');
    if (!hasNonZero) errors.push('At least one revision must have non-zero traffic.');
    if (totalPercent !== 100) errors.push('Traffic percentages must total exactly 100.');
    for (const row of draftTraffic) {
      if (!Number.isInteger(row.percent) || row.percent < 0 || row.percent > 100) {
        errors.push(`Revision ${row.revision}: percent must be an integer between 0 and 100.`);
      }
    }
    return errors;
  }, [draftTraffic, hasNonZero, totalPercent]);

  const canSaveTraffic = trafficErrors.length === 0 && !savingTraffic;

  const setRevisionPercent = (revision: string, percent: number) => {
    setDraftTraffic((prev) =>
      prev.map((row) =>
        row.revision === revision
          ? { ...row, percent: Number.isFinite(percent) ? percent : 0 }
          : row
      )
    );
  };

  const copyToClipboard = async (value: string, label: string) => {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      toast.success(`${label} copied`);
    } catch {
      toast.error('Clipboard copy failed');
    }
  };

  const handleSaveTraffic = async () => {
    if (!service || !serviceName) return;
    if (trafficErrors.length > 0) {
      toast.error(trafficErrors[0]);
      return;
    }

    setSavingTraffic(true);
    try {
      await updateRunTraffic(
        location,
        serviceName,
        draftTraffic.map((row) => ({ revision: row.revision, percent: row.percent }))
      );
      toast.success('Traffic split updated');
      await loadService();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to save traffic split');
    } finally {
      setSavingTraffic(false);
    }
  };

  const handleDeleteService = async () => {
    if (!serviceName) return;
    if (!confirm(`Delete Cloud Run service "${serviceName}"?`)) return;
    setDeleting(true);
    try {
      await deleteRunService(location, serviceName);
      toast.success(`Service "${serviceName}" deleted`);
      navigate('/services/cloud-run');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Delete failed');
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!service) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-3 bg-gray-50">
        <p className="text-gray-600">Service not found.</p>
        <button
          onClick={() => navigate('/services/cloud-run')}
          className="text-sm text-blue-600 hover:underline"
        >
          Back to Cloud Run
        </button>
      </div>
    );
  }

  const revisionMap = new Map(service.revisions.map((r) => [extractRevisionName(r.name), r]));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/services/cloud-run')}
              className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <p className="text-xs text-gray-500">Cloud Run • {location}</p>
              <h1 className="text-xl font-semibold text-gray-900">{service.serviceId}</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadService}
              className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            <button
              onClick={handleDeleteService}
              disabled={deleting}
              className="inline-flex items-center gap-2 rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50"
            >
              {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              Delete
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 py-6 space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Service URLs</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3 rounded-md border border-gray-200 p-3">
              <div className="min-w-0">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Simulated URL</p>
                <p className="text-sm text-blue-700 break-all">{service.simulatedUrl || '—'}</p>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => copyToClipboard(service.simulatedUrl, 'Simulated URL')}
                  disabled={!service.simulatedUrl}
                  className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600 disabled:opacity-40"
                >
                  <Copy className="h-4 w-4" />
                </button>
                {service.simulatedUrl && (
                  <a
                    href={service.simulatedUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>
            </div>
            <div className="flex items-center justify-between gap-3 rounded-md border border-gray-200 p-3">
              <div className="min-w-0">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Local URL</p>
                <p className="text-sm text-blue-700 break-all">{service.activeLocalUrl || '—'}</p>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => copyToClipboard(service.activeLocalUrl, 'Local URL')}
                  disabled={!service.activeLocalUrl}
                  className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600 disabled:opacity-40"
                >
                  <Copy className="h-4 w-4" />
                </button>
                {service.activeLocalUrl && (
                  <a
                    href={service.activeLocalUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-blue-600"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-900">Revisions</h2>
            <span className="text-xs text-gray-500">Latest: {service.latestReadyRevision || '—'}</span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-left">
                <th className="px-4 py-2.5 font-medium text-gray-600">Revision</th>
                <th className="px-4 py-2.5 font-medium text-gray-600">Image</th>
                <th className="px-4 py-2.5 font-medium text-gray-600">Port</th>
                <th className="px-4 py-2.5 font-medium text-gray-600">Created</th>
                <th className="px-4 py-2.5 font-medium text-gray-600">Traffic %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {draftTraffic.map((row) => {
                const rev = revisionMap.get(row.revision);
                return (
                  <tr key={row.revision} className="hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-medium text-gray-900">{row.revision}</td>
                    <td className="px-4 py-2.5 text-gray-600 break-all">{rev?.image || '—'}</td>
                    <td className="px-4 py-2.5 text-gray-600">{rev?.containerPort ?? '—'}</td>
                    <td className="px-4 py-2.5 text-gray-600">
                      {rev?.createTime ? new Date(rev.createTime).toLocaleString() : '—'}
                    </td>
                    <td className="px-4 py-2.5">
                      <input
                        type="number"
                        min={0}
                        max={100}
                        step={1}
                        value={row.percent}
                        onChange={(e) => setRevisionPercent(row.revision, parseInt(e.target.value, 10) || 0)}
                        className="w-24 rounded-md border border-gray-300 px-2 py-1 text-sm"
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${totalPercent === 100 ? 'text-green-700' : 'text-red-700'}`}>
                Total: {totalPercent}%
              </p>
              {trafficErrors.length > 0 && (
                <ul className="text-xs text-red-600 mt-1">
                  {trafficErrors.map((err) => (
                    <li key={err}>{err}</li>
                  ))}
                </ul>
              )}
            </div>
            <button
              onClick={handleSaveTraffic}
              disabled={!canSaveTraffic}
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {savingTraffic ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Save Traffic
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
