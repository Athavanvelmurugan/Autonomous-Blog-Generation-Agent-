import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchBlogHistory, checkHealth } from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import {
  Sparkles,
  BookOpen,
  ShieldCheck,
  Cpu,
  Clock,
  ArrowRight,
  Activity,
  FileText,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [blogs, setBlogs] = useState([]);
  const [health, setHealth] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const loadDashboard = async () => {
      try {
        const [blogData, healthData] = await Promise.all([
          fetchBlogHistory(),
          checkHealth(),
        ]);
        if (isMounted) {
          setBlogs(blogData || []);
          setHealth(healthData || null);
        }
      } catch (err) {
        if (isMounted) setError(err.message);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    loadDashboard();
    return () => { isMounted = false; };
  }, []);

  // Compute stats
  const totalArticles = blogs.length;
  const avgScore =
    totalArticles > 0
      ? (blogs.reduce((acc, b) => acc + (b.verification_score || 8.5), 0) / totalArticles).toFixed(1)
      : '—';
  const recentBlogs = blogs.slice(0, 4);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', maxWidth: '1280px', margin: '0 auto' }}>
      {/* Top Banner / Hero Metric Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-4)' }}>
        {/* Metric 1 */}
        <Card>
          <CardContent style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--accent-primary-subtle)',
                color: 'var(--accent-primary-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <BookOpen size={22} />
            </div>
            <div>
              <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Saved Articles
              </div>
              <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
                {isLoading ? '...' : totalArticles}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Metric 2 */}
        <Card>
          <CardContent style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--color-success-bg)',
                color: 'var(--color-success-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ShieldCheck size={22} />
            </div>
            <div>
              <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Avg Fact-Check Score
              </div>
              <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
                {isLoading ? '...' : `${avgScore} / 10`}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Metric 3 */}
        <Card>
          <CardContent style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface-elevated)',
                color: 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Cpu size={22} />
            </div>
            <div>
              <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Active LLM Architecture
              </div>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                {health?.model_name ? health.model_name.split('/').pop() : 'Groq / Llama 3.3'}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Metric 4 */}
        <Card>
          <CardContent style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-md)',
                background: health?.status === 'healthy' ? 'var(--color-success-bg)' : 'var(--color-danger-bg)',
                color: health?.status === 'healthy' ? 'var(--color-success-text)' : 'var(--color-danger-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {health?.status === 'healthy' ? <CheckCircle2 size={22} /> : <AlertCircle size={22} />}
            </div>
            <div>
              <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Engine Status
              </div>
              <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                {health?.status === 'healthy' ? 'FastAPI & DB Connected' : 'Checking connection...'}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Launch & Recent Articles 2-Column Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: 'var(--space-6)', alignItems: 'start' }}>
        {/* Quick Launch Card */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Sparkles size={18} color="var(--accent-primary-text)" />
              <span>Launch Content Agent</span>
            </CardTitle>
          </CardHeader>
          <CardContent style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', margin: 0 }}>
              Generate comprehensive, research-backed, and fact-verified articles autonomously using a LangGraph multi-agent DAG.
            </p>
            <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
              &bull; Web Trend Retrieval (DuckDuckGo / Tavily)<br />
              &bull; SEO Headline Generation<br />
              &bull; Markdown Article Drafting<br />
              &bull; Automated Hallucination & Fact Audit<br />
              &bull; Multi-Language Localization
            </div>
            <Button
              variant="primary"
              rightIcon={ArrowRight}
              onClick={() => navigate('/generate')}
              style={{ marginTop: 'var(--space-2)' }}
            >
              Start New Generation
            </Button>
          </CardContent>
        </Card>

        {/* Recent Publications Table / Cards */}
        <Card>
          <CardHeader>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <FileText size={18} color="var(--accent-primary-text)" />
              <CardTitle>Recent Published Articles</CardTitle>
            </div>
            {totalArticles > 0 && (
              <Button variant="ghost" size="sm" onClick={() => navigate('/articles')}>
                View all ({totalArticles})
              </Button>
            )}
          </CardHeader>
          <CardContent style={{ padding: 0 }}>
            {isLoading ? (
              <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                Loading recent publications...
              </div>
            ) : error ? (
              <div style={{ padding: 'var(--space-6)', color: 'var(--color-danger-text)' }}>
                Could not load articles: {error}
              </div>
            ) : recentBlogs.length === 0 ? (
              <div style={{ padding: 'var(--space-10) var(--space-4)', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                <FileText size={32} style={{ margin: '0 auto var(--space-2) auto', opacity: 0.4 }} />
                <p style={{ fontSize: 'var(--text-sm)', margin: 0 }}>No articles in PostgreSQL yet.</p>
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', marginTop: 'var(--space-1)' }}>
                  Launch your first autonomous generation to build your library.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {recentBlogs.map((blog, idx) => (
                  <div
                    key={blog.id}
                    onClick={() => navigate(`/articles/${blog.id}`)}
                    style={{
                      padding: 'var(--space-4) var(--space-6)',
                      borderBottom: idx < recentBlogs.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: 'var(--space-4)',
                      cursor: 'pointer',
                      transition: 'background var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-surface-elevated)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-1)' }}>
                        <Badge variant="neutral">#{blog.id}</Badge>
                        <Badge variant="primary">{blog.target_language || 'English'}</Badge>
                        <Badge variant={(blog.verification_score || 8.5) >= 8.0 ? 'success' : 'warning'}>
                          Fact Check: {blog.verification_score || 8.5}/10
                        </Badge>
                      </div>
                      <h4
                        style={{
                          fontSize: 'var(--text-sm)',
                          fontWeight: 600,
                          color: 'var(--text-primary)',
                          margin: 0,
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {blog.title}
                      </h4>
                      <p style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', margin: 'var(--space-1) 0 0 0' }}>
                        Topic: {blog.topic} &bull; Execution: {blog.execution_time_seconds}s
                      </p>
                    </div>

                    <ArrowRight size={16} color="var(--text-tertiary)" style={{ flexShrink: 0 }} />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
