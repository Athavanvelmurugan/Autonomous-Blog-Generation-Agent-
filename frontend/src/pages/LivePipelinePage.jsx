import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useGeneration } from '../context/GenerationContext';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import {
  Activity,
  CheckCircle2,
  Circle,
  Loader2,
  ShieldCheck,
  Globe,
  Terminal,
  ExternalLink,
  Sparkles,
  ArrowRight,
  AlertCircle,
  Clock,
  Download,
  FileText,
} from 'lucide-react';

export default function LivePipelinePage() {
  const navigate = useNavigate();
  const {
    isGenerating,
    currentStep,
    stepsCompleted = [],
    targetLanguage,
    liveTelemetry,
    revisionCount = 0,
    activeResult,
    executionLogs = [],
    generationError,
    topic,
  } = useGeneration();

  const needsTranslation = targetLanguage && targetLanguage.toLowerCase() !== 'english';

  const stages = [
    {
      id: 'plan_queries',
      title: 'Plan Queries',
      desc: 'Temporal keyword & query planning',
    },
    {
      id: 'collect',
      title: 'Multi-Source Collect',
      desc: 'Parallel Search, RSS & HN ingestion',
    },
    {
      id: 'clean_dedupe',
      title: 'Clean & Dedupe',
      desc: 'URL normalization & min-sources gate',
    },
    {
      id: 'extract_facts',
      title: 'Fact Extraction',
      desc: 'Atomic facts with verified evidence',
    },
    {
      id: 'title_generator',
      title: 'Title Generator',
      desc: 'Fact-grounded headline creation',
    },
    {
      id: 'content_planner',
      title: 'Content Blueprint',
      desc: 'Pedagogical curriculum & code planning',
    },
    {
      id: 'content_generator',
      title: revisionCount > 0 ? `Writer (Revision #${revisionCount})` : 'Educational Writer',
      desc: revisionCount > 0 ? 'Refining draft against verifier audit' : 'Drafting full guide with code, tables & FAQs',
    },
    {
      id: 'verifier_agent',
      title: 'Fact Verifier',
      desc: 'Deterministic checks & semantic audit',
    },
    ...(needsTranslation
      ? [
          {
            id: 'translator',
            title: 'Localization Node',
            desc: `Translates to ${targetLanguage}`,
          },
        ]
      : []),
    {
      id: 'storage',
      title: 'PostgreSQL Storage',
      desc: 'Saved in blog_db with citations',
    },
  ];

  // Empty state: no generation running and no previous result
  if (!isGenerating && !activeResult && executionLogs.length === 0 && !generationError) {
    return (
      <div style={{ maxWidth: '800px', margin: 'var(--space-10) auto', textAlign: 'center' }}>
        <Card style={{ padding: 'var(--space-12) var(--space-6)' }}>
          <Activity size={48} color="var(--border-default)" style={{ margin: '0 auto var(--space-4) auto' }} />
          <h3 style={{ fontSize: 'var(--text-xl)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
            No Active Agent Pipeline Run
          </h3>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', maxWidth: '440px', margin: '0 auto var(--space-6) auto' }}>
            Configure your blog topic and desired output settings to launch the autonomous multi-agent execution pipeline.
          </p>
          <Button variant="primary" leftIcon={Sparkles} onClick={() => navigate('/generate')}>
            Go to Generator
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', maxWidth: '1280px', margin: '0 auto' }}>
      {/* Top Status & Summary Bar */}
      <Card>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <Activity size={20} color="var(--accent-primary-text)" />
            <div>
              <CardTitle>Autonomous Multi-Agent DAG Execution</CardTitle>
              {topic && (
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', margin: 'var(--space-1) 0 0 0' }}>
                  Target Topic: &ldquo;{topic}&rdquo;
                </p>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            {revisionCount > 0 && (
              <Badge variant="warning">
                Self-Correction Loop #{revisionCount}
              </Badge>
            )}

            {isGenerating ? (
              <Badge variant="warning" icon={Loader2}>
                Agents Executing
              </Badge>
            ) : activeResult ? (
              <Badge variant="success" icon={CheckCircle2}>
                Execution Completed
              </Badge>
            ) : null}

            {activeResult && (
              <Button
                variant="primary"
                size="sm"
                rightIcon={ArrowRight}
                onClick={() => navigate(`/articles/${activeResult.id}`)}
              >
                View Full Article Studio
              </Button>
            )}
          </div>
        </CardHeader>

        {/* Live Telemetry Banner */}
        {isGenerating && liveTelemetry && (
          <div
            style={{
              padding: 'var(--space-3) var(--space-6)',
              background: 'var(--accent-primary-subtle)',
              borderBottom: '1px solid var(--accent-primary-border)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
              fontSize: 'var(--text-xs)',
              color: 'var(--accent-primary-text)',
            }}
          >
            <span
              className="animate-pulse-live"
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'var(--accent-primary)',
              }}
            />
            <span>
              <strong>Live Telemetry:</strong> {liveTelemetry}
            </span>
          </div>
        )}

        {/* Error Notification */}
        {generationError && (
          <div
            style={{
              padding: 'var(--space-3) var(--space-6)',
              background: 'var(--color-danger-bg)',
              borderBottom: '1px solid var(--color-danger-border)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
              fontSize: 'var(--text-xs)',
              color: 'var(--color-danger-text)',
            }}
          >
            <AlertCircle size={16} />
            <span>
              <strong>Execution Error:</strong> {generationError}
            </span>
          </div>
        )}

        {/* Stage Timeline Grid */}
        <CardContent>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: `repeat(auto-fit, minmax(180px, 1fr))`,
              gap: 'var(--space-3)',
            }}
          >
            {stages.map((stage, idx) => {
              const isDone =
                stepsCompleted.includes(stage.id) ||
                (stage.id === 'storage' && !isGenerating && activeResult);
              const isCurrent = isGenerating && currentStep === stage.id;

              let cardBg = 'var(--bg-surface-elevated)';
              let borderCol = 'var(--border-subtle)';
              if (isCurrent) {
                cardBg = 'var(--accent-primary-subtle)';
                borderCol = 'var(--accent-primary)';
              } else if (isDone) {
                borderCol = 'var(--color-success-border)';
              }

              return (
                <div
                  key={stage.id}
                  style={{
                    background: cardBg,
                    border: `1px solid ${borderCol}`,
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-3)',
                    transition: 'all var(--transition-fast)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                      {isDone ? (
                        <CheckCircle2 size={16} color="var(--color-success)" />
                      ) : isCurrent ? (
                        <Loader2 size={16} color="var(--accent-primary)" style={{ animation: 'spin 1s linear infinite' }} />
                      ) : (
                        <Circle size={16} color="var(--text-muted)" />
                      )}
                      <span
                        style={{
                          fontSize: 'var(--text-2xs)',
                          fontWeight: 600,
                          color: isCurrent ? 'var(--accent-primary-text)' : isDone ? 'var(--text-primary)' : 'var(--text-tertiary)',
                        }}
                      >
                        Step {idx + 1}
                      </span>
                    </div>

                    <h4
                      style={{
                        fontSize: 'var(--text-xs)',
                        fontWeight: 600,
                        color: isCurrent ? 'var(--accent-primary-text)' : isDone ? 'var(--text-primary)' : 'var(--text-secondary)',
                        margin: '0 0 var(--space-1) 0',
                      }}
                    >
                      {stage.title}
                    </h4>
                    <p style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', margin: 0, lineHeight: 1.3 }}>
                      {stage.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Two-Column Telemetry & Output Preview */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)', alignItems: 'start' }}>
        {/* Terminal Execution Logs */}
        <Card>
          <CardHeader>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <Terminal size={16} color="var(--text-secondary)" />
              <CardTitle style={{ fontSize: 'var(--text-sm)' }}>Pipeline Event Logs</CardTitle>
            </div>
            <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)' }}>
              {executionLogs.length} events logged
            </span>
          </CardHeader>
          <CardContent style={{ padding: 0 }}>
            <div
              style={{
                height: '380px',
                overflowY: 'auto',
                padding: 'var(--space-4)',
                background: '#070a12',
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-xs)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)',
              }}
            >
              {executionLogs.map((log) => (
                <div key={log.id} style={{ display: 'flex', gap: 'var(--space-3)', lineHeight: 1.5 }}>
                  <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>[{log.timestamp}]</span>
                  <span
                    style={{
                      color:
                        log.node === 'verifier_agent'
                          ? 'var(--color-warning-text)'
                          : log.node === 'storage'
                          ? 'var(--color-success-text)'
                          : 'var(--accent-primary-text)',
                      fontWeight: 600,
                      flexShrink: 0,
                    }}
                  >
                    {log.node}:
                  </span>
                  <span style={{ color: 'var(--text-secondary)', wordBreak: 'break-word' }}>{log.message}</span>
                </div>
              ))}
              {isGenerating && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--text-tertiary)' }}>
                  <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
                  <span>Awaiting next DAG state update...</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Live Output Preview / Result Snapshot */}
        <Card>
          <CardHeader>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <ShieldCheck size={16} color="var(--color-success)" />
              <CardTitle style={{ fontSize: 'var(--text-sm)' }}>Live Generation Artifacts</CardTitle>
            </div>
            {activeResult?.verification_score && (
              <Badge variant={activeResult.verification_score >= 8.0 ? 'success' : 'warning'}>
                Score: {activeResult.verification_score}/10
              </Badge>
            )}
          </CardHeader>
          <CardContent style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {activeResult ? (
              <>
                <div>
                  <label style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                    Final SEO Headline
                  </label>
                  <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--text-primary)', marginTop: 'var(--space-1)' }}>
                    {activeResult.title}
                  </h3>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-3)' }}>
                  <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)' }}>Word Count</div>
                      {activeResult.target_word_count && (
                        <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--accent-primary-text)', background: 'var(--accent-primary-subtle)', padding: '1px 5px', borderRadius: '4px' }}>
                          Target: {activeResult.target_word_count}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 'var(--text-lg)', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                      {activeResult.word_count || (activeResult.content || '').trim().split(/\s+/).filter(Boolean).length}
                      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', fontWeight: 400, marginLeft: '4px' }}>words</span>
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)' }}>Execution Time</div>
                    <div style={{ fontSize: 'var(--text-lg)', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {activeResult.execution_time_seconds}s
                    </div>
                  </div>

                  <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)' }}>Citations Found</div>
                    <div style={{ fontSize: 'var(--text-lg)', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {activeResult.sources?.length || 0}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 'var(--space-2)', marginTop: 'var(--space-3)' }}>
                  <Button
                    variant="primary"
                    onClick={() => navigate(`/articles/${activeResult.id}`)}
                  >
                    Open Studio
                  </Button>
                  <Button
                    variant="secondary"
                    leftIcon={Download}
                    onClick={() => window.open(`/api/blogs/${activeResult.id}/pdf`, '_blank')}
                  >
                    Download PDF
                  </Button>
                  <Button
                    variant="secondary"
                    leftIcon={FileText}
                    onClick={() => window.open(`/api/blogs/${activeResult.id}/html?download=true`, '_blank')}
                  >
                    Download HTML
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => navigate(`/articles/${activeResult.id}/audit`)}
                  >
                    View Audit
                  </Button>
                </div>
              </>
            ) : isGenerating ? (
              <div style={{ textAlign: 'center', padding: 'var(--space-10) var(--space-4)', color: 'var(--text-tertiary)' }}>
                <Loader2 size={32} color="var(--accent-primary)" style={{ animation: 'spin 1.5s linear infinite', margin: '0 auto var(--space-3) auto' }} />
                <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
                  The agent graph is currently running nodes in sequence.
                </p>
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', marginTop: 'var(--space-1)' }}>
                  Draft previews and verification audits will appear here once the writer finishes drafting.
                </p>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 'var(--space-8) var(--space-4)', color: 'var(--text-tertiary)' }}>
                <p style={{ fontSize: 'var(--text-sm)' }}>No artifacts generated yet.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
