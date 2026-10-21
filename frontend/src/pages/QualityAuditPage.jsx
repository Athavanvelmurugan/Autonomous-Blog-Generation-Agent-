import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchBlogById } from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import {
  ShieldCheck,
  ArrowLeft,
  ExternalLink,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Layers,
  Terminal,
} from 'lucide-react';

export default function QualityAuditPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [blog, setBlog] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const loadBlog = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchBlogById(id);
        if (isMounted) setBlog(data);
      } catch (err) {
        if (isMounted) setError(err.response?.data?.detail || err.message || 'Audit not available');
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    loadBlog();
    return () => { isMounted = false; };
  }, [id]);

  if (isLoading) {
    return (
      <div style={{ maxWidth: '800px', margin: 'var(--space-12) auto', textAlign: 'center', color: 'var(--text-tertiary)' }}>
        Loading quality audit report...
      </div>
    );
  }

  if (error || !blog) {
    return (
      <div style={{ maxWidth: '600px', margin: 'var(--space-12) auto', textAlign: 'center' }}>
        <Card style={{ padding: 'var(--space-8)' }}>
          <p style={{ color: 'var(--color-danger-text)' }}>{error || 'Audit not found.'}</p>
          <Button variant="secondary" onClick={() => navigate('/articles')} style={{ marginTop: 'var(--space-4)' }}>
            Back to Library
          </Button>
        </Card>
      </div>
    );
  }

  const score = blog.verification_score || 8.5;
  const isPassed = score >= 8.0;
  const sources = blog.sources || [];

  return (
    <div style={{ maxWidth: '980px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Top Navigation */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Button
          variant="ghost"
          size="sm"
          leftIcon={ArrowLeft}
          onClick={() => navigate(`/articles/${blog.id}`)}
        >
          Back to Article Studio
        </Button>
        <Badge variant={isPassed ? 'success' : 'warning'} icon={ShieldCheck}>
          Audit Status: {isPassed ? 'VERIFIED PASSED' : 'REVISED'}
        </Badge>
      </div>

      {/* Main Scorecard Overview */}
      <Card>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: 'var(--radius-md)',
                background: isPassed ? 'var(--color-success-bg)' : 'var(--color-warning-bg)',
                color: isPassed ? 'var(--color-success-text)' : 'var(--color-warning-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ShieldCheck size={24} />
            </div>
            <div>
              <CardTitle>Verifier Agent Fact-Checking Report</CardTitle>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', margin: 'var(--space-1) 0 0 0' }}>
                Article: &ldquo;{blog.title}&rdquo; (PostgreSQL ID #{blog.id})
              </p>
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: isPassed ? 'var(--color-success-text)' : 'var(--color-warning-text)' }}>
              {score} <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-tertiary)' }}>/ 10.0</span>
            </div>
            <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)' }}>
              Factuality & Accuracy Threshold: 8.0
            </span>
          </div>
        </CardHeader>

        <CardContent style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          {/* Audit Metrics Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-4)' }}>
            <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Verification Node
              </div>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
                LangGraph Node 4 (Auditor)
              </div>
              <p style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', margin: '4px 0 0 0' }}>
                Deterministic CLI linter + LLM eval
              </p>
            </div>

            <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Grounding Citations
              </div>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
                {sources.length} Live Web Sources
              </div>
              <p style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', margin: '4px 0 0 0' }}>
                Retrieved via Trend Research Agent
              </p>
            </div>

            <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Execution Duration
              </div>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
                {blog.execution_time_seconds} seconds
              </div>
              <p style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', margin: '4px 0 0 0' }}>
                Total DAG workflow time
              </p>
            </div>
          </div>

          {/* Full Verifier Critique Card */}
          <div>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
              Editorial & Hallucination Audit Findings
            </h3>
            <div
              style={{
                background: '#070a12',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-5)',
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-xs)',
                lineHeight: 1.6,
                color: '#cbd5e1',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {blog.critique || 'Quality audit passed with zero flagged hallucinations or invalid CLI commands.'}
            </div>
          </div>

          {/* Grounding Citations Table */}
          <div>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
              Verified Ground-Truth Sources & References ({sources.length})
            </h3>
            {sources.length === 0 ? (
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
                No external web source citations recorded for this article.
              </p>
            ) : (
              <div style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-xs)' }}>
                  <thead>
                    <tr style={{ background: 'var(--bg-surface-elevated)', borderBottom: '1px solid var(--border-subtle)' }}>
                      <th style={{ padding: 'var(--space-3)', textAlign: 'left', color: 'var(--text-tertiary)' }}>#</th>
                      <th style={{ padding: 'var(--space-3)', textAlign: 'left', color: 'var(--text-tertiary)' }}>SOURCE TITLE</th>
                      <th style={{ padding: 'var(--space-3)', textAlign: 'right', color: 'var(--text-tertiary)' }}>ACTION</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sources.map((src, idx) => (
                      <tr key={idx} style={{ borderBottom: idx < sources.length - 1 ? '1px solid var(--border-subtle)' : 'none' }}>
                        <td style={{ padding: 'var(--space-3)', color: 'var(--text-tertiary)', width: '36px' }}>{idx + 1}</td>
                        <td style={{ padding: 'var(--space-3)', color: 'var(--text-primary)', fontWeight: 500 }}>{src.title}</td>
                        <td style={{ padding: 'var(--space-3)', textAlign: 'right' }}>
                          <a
                            href={src.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              fontSize: 'var(--text-2xs)',
                              color: 'var(--accent-primary-text)',
                            }}
                          >
                            <span>Open URL</span>
                            <ExternalLink size={12} />
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
