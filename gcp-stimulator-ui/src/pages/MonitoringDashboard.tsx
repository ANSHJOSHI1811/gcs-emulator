import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, TrendingUp, TrendingDown, RefreshCw, Settings } from 'lucide-react';

export const MonitoringDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [autoscalers, setAutoscalers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const API_BASE = 'http://localhost:8080';

  const fetchMetrics = async () => {
    try {
      // Fetch metrics from monitoring service
      const response = await fetch(`${API_BASE}/v3/projects/test-project-123/timeSeries?filter=metric.type="compute.googleapis.com/instance/cpu/utilization"`);
      if (response.ok) {
        const data = await response.json();
        setMetrics(data.timeSeries || []);
      }
    } catch (err) {
      console.error('Error fetching metrics:', err);
    }
  };

  const fetchAlerts = async () => {
    try {
      // Fetch alert policies
      const response = await fetch(`${API_BASE}/v3/projects/test-project-123/alertPolicies`);
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alertPolicies || []);
      }
    } catch (err) {
      console.error('Error fetching alerts:', err);
    }
  };

  const fetchAutoscalers = async () => {
    try {
      // Fetch autoscaling policies
      const response = await fetch(`${API_BASE}/compute/v1/projects/test-project-123/zones/us-central1-a/autoscalers`);
      if (response.ok) {
        const data = await response.json();
        setAutoscalers(data.items || []);
      }
    } catch (err) {
      console.error('Error fetching autoscalers:', err);
    }
  };

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([fetchMetrics(), fetchAlerts(), fetchAutoscalers()]);
    } catch (err) {
      setError('Failed to fetch monitoring data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchAllData, 10000); // Refresh every 10 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getMetricValue = (points: any[]) => {
    if (!points || points.length === 0) return 'N/A';
    const lastPoint = points[points.length - 1];
    const value = lastPoint.value?.doubleValue || lastPoint.value?.int64Value || 0;
    return typeof value === 'number' ? value.toFixed(2) : value;
  };

  const getAlertState = (state: string) => {
    const stateColors: Record<string, string> = {
      'OK': 'bg-green-100 text-green-800',
      'ALARM': 'bg-red-100 text-red-800',
      'INSUFFICIENT_DATA': 'bg-yellow-100 text-yellow-800',
    };
    return stateColors[state] || 'bg-gray-100 text-gray-800';
  };

  const getScalingStatus = (policy: any) => {
    const isSameSize = policy.currentSize === policy.targetSize;
    if (isSameSize) {
      return <span className="text-green-600 font-medium">✓ Stable</span>;
    }
    if (policy.currentSize < policy.targetSize) {
      return <span className="text-blue-600 font-medium flex items-center gap-1"><TrendingUp size={16} /> Scaling Up</span>;
    }
    return <span className="text-orange-600 font-medium flex items-center gap-1"><TrendingDown size={16} /> Scaling Down</span>;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Activity className="w-8 h-8 text-cyan-400" />
            <h1 className="text-3xl font-bold text-white">Monitoring Dashboard</h1>
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-gray-300 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="w-4 h-4"
              />
              Auto Refresh
            </label>
            <button
              onClick={fetchAllData}
              className="p-2 hover:bg-slate-700 rounded-lg text-gray-300 hover:text-white transition"
              title="Refresh"
            >
              <RefreshCw size={20} className={autoRefresh ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg text-red-200">
            {error}
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-cyan-400 border-r-2 border-cyan-400"></div>
          </div>
        )}

        {!loading && (
          <>
            {/* Metrics Section */}
            <section className="mb-8">
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Activity size={20} className="text-cyan-400" />
                Time Series Metrics
              </h2>
              {metrics.length === 0 ? (
                <div className="p-6 bg-slate-800/50 border border-slate-700 rounded-lg text-gray-400 text-center">
                  No metrics data available
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {metrics.map((metric, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-cyan-500 transition"
                    >
                      <div className="text-sm text-gray-400 mb-2">
                        {metric.metric?.type?.split('/').pop()}
                      </div>
                      <div className="text-2xl font-bold text-cyan-400">
                        {getMetricValue(metric.points)}%
                      </div>
                      <div className="text-xs text-gray-500 mt-2">
                        {metric.resource?.labels?.instance_id || 'Unknown'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Alerts Section */}
            <section className="mb-8">
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <AlertTriangle size={20} className="text-yellow-400" />
                Alert Policies ({alerts.length})
              </h2>
              {alerts.length === 0 ? (
                <div className="p-6 bg-slate-800/50 border border-slate-700 rounded-lg text-gray-400 text-center">
                  No alert policies configured
                </div>
              ) : (
                <div className="space-y-3">
                  {alerts.map((alert, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-cyan-500 transition"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="font-semibold text-white">{alert.displayName}</div>
                          <div className="text-sm text-gray-400 mt-1">
                            {alert.conditions?.length || 0} condition(s) • 
                            {alert.notificationChannels?.length || 0} channel(s)
                          </div>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold ${getAlertState(
                            alert.state || 'OK'
                          )}`}
                        >
                          {alert.state || 'OK'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Auto-Scaling Section */}
            <section>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Settings size={20} className="text-green-400" />
                Auto-Scaling Policies ({autoscalers.length})
              </h2>
              {autoscalers.length === 0 ? (
                <div className="p-6 bg-slate-800/50 border border-slate-700 rounded-lg text-gray-400 text-center">
                  No autoscaling policies configured
                </div>
              ) : (
                <div className="space-y-3">
                  {autoscalers.map((autoscaler, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-cyan-500 transition"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="font-semibold text-white">{autoscaler.name?.split('/').pop()}</div>
                          <div className="text-sm text-gray-400 mt-2 space-y-1">
                            <div>Target: {autoscaler.target?.split('/').pop()}</div>
                            <div>
                              Size: {autoscaler.currentSize} / {autoscaler.minReplicas}-{autoscaler.maxReplicas}
                            </div>
                            <div>Last Action: {autoscaler.lastAction || 'None'}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          {getScalingStatus(autoscaler)}
                          <div className="text-xs text-gray-500 mt-2">
                            {autoscaler.enabled ? 'Enabled' : 'Disabled'}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
};

export default MonitoringDashboard;
