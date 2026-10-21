import React, { useState, useEffect } from 'react';
import { checkHealth, fetchSupportedLanguages } from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import {
  Settings,
  Database,
  Cpu,
  Globe,
  Activity,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Server,
} from 'lucide-react';

export default function SettingsPage() {
  const [health, setHealth] = useState(null);
  const [languages, setLanguages] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [healthData, langData] = await Promise.all([
        checkHealth(),
        fetchSupportedLanguages(),
      ]);
      setHealth(healthData);
      setLanguages(langData || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div style={{ maxWidth: '980px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Top Header Card */}
      <Card>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <Settings size={20} color="var(--accent-primary-text)" />
            <CardTitle>System Diagnostics & Environment Configuration</CardTitle>
          </div>
          <Button
            variant="secondary"
            size="sm"
            leftIcon={RefreshCw}
            isLoading={isLoading}
            onClick={loadData}
          >
            Refresh Diagnostics
          </Button>
        </CardHeader>

        <CardContent style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          {error && (
            <div
              style={{
                padding: 'var(--space-3) var(--space-4)',
                background: 'var(--color-danger-bg)',
                border: '1px solid var(--color-danger-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-danger-text)',
                fontSize: 'var(--text-xs)',
              }}
            >
              Error contacting backend: {error}
            </div>
          )}

          {/* Engine Parameters Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)' }}>
            {/* FastAPI Engine */}
            <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                <Server size={16} color="var(--accent-primary-text)" />
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>FastAPI Engine</span>
              </div>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                {health?.service || 'Autonomous Blog Engine'}
              </div>
              <div style={{ marginTop: 'var(--space-2)' }}>
                <Badge variant={health?.status === 'healthy' ? 'success' : 'danger'}>
                  {health?.status === 'healthy' ? 'Online & Healthy' : 'Offline'}
                </Badge>
              </div>
            </div>

            {/* LLM Model */}
            <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                <Cpu size={16} color="var(--color-warning-text)" />
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>LLM Provider & Model</span>
              </div>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                {health?.model_name || 'Groq / Llama 3.3 70B'}
              </div>
              <div style={{ marginTop: 'var(--space-2)' }}>
                <Badge variant="neutral">Provider: {health?.model_provider || 'groq'}</Badge>
              </div>
            </div>

            {/* PostgreSQL */}
            <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                <Database size={16} color="var(--color-info-text)" />
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>Database Persistence</span>
              </div>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                {health?.database || 'blog_db'}
              </div>
              <div style={{ marginTop: 'var(--space-2)' }}>
                <Badge variant="info">SQLAlchemy Async (asyncpg)</Badge>
              </div>
            </div>

            {/* LangSmith Tracing */}
            <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                <Activity size={16} color="var(--color-success-text)" />
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>LangSmith Tracing</span>
              </div>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)' }}>
                {health?.langsmith_tracing ? 'Enabled' : 'Disabled'}
              </div>
              <div style={{ marginTop: 'var(--space-2)' }}>
                <Badge variant={health?.langsmith_tracing ? 'success' : 'neutral'}>
                  {health?.langsmith_tracing ? 'Live Observability' : 'Offline Trace'}
                </Badge>
              </div>
            </div>
          </div>

          {/* Active Features Strip */}
          <div>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
              Active Agent Features in DAG
            </h3>
            <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
              {(health?.features || ['trend_research_agent', 'fact_verifier_agent', 'self_correction_loop']).map((f) => (
                <Badge key={f} variant="primary" icon={CheckCircle2}>
                  {f.replace(/_/g, ' ')}
                </Badge>
              ))}
            </div>
          </div>

          {/* Supported Languages Registry */}
          <div>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
              Localization & Language Registry ({languages.length} Supported)
            </h3>
            <div style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-xs)', textAlign: 'left' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-surface-elevated)', borderBottom: '1px solid var(--border-subtle)' }}>
                    <th style={{ padding: 'var(--space-3)', color: 'var(--text-tertiary)' }}>ISO CODE</th>
                    <th style={{ padding: 'var(--space-3)', color: 'var(--text-tertiary)' }}>LANGUAGE NAME</th>
                    <th style={{ padding: 'var(--space-3)', color: 'var(--text-tertiary)' }}>NATIVE NAME</th>
                    <th style={{ padding: 'var(--space-3)', color: 'var(--text-tertiary)', textAlign: 'right' }}>ROUTER ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {languages.map((l, idx) => (
                    <tr key={l.code} style={{ borderBottom: idx < languages.length - 1 ? '1px solid var(--border-subtle)' : 'none' }}>
                      <td style={{ padding: 'var(--space-3)', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>{l.code}</td>
                      <td style={{ padding: 'var(--space-3)', color: 'var(--text-primary)', fontWeight: 500 }}>{l.name}</td>
                      <td style={{ padding: 'var(--space-3)', color: 'var(--text-secondary)' }}>{l.native_name}</td>
                      <td style={{ padding: 'var(--space-3)', textAlign: 'right' }}>
                        <Badge variant={l.code === 'en' ? 'neutral' : 'info'}>
                          {l.code === 'en' ? 'Direct Route' : 'Invokes Translator'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
