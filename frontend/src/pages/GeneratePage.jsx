import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGeneration } from '../context/GenerationContext';
import { fetchSupportedLanguages } from '../services/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import CustomSelect from '../components/common/CustomSelect';
import LengthDropdown from '../components/common/LengthDropdown';
import {
  Sparkles,
  Globe,
  Layers,
  ArrowRight,
  Check,
  FileText,
  Sliders,
  Cpu,
  BookOpen,
  MessageSquare,
  Briefcase,
  ShieldCheck,
  Search,
  CheckCircle2,
  X,
  Command,
} from 'lucide-react';

const SUGGESTION_TOPICS = [
  { label: 'Machine Learning 101', text: 'Machine Learning for Beginners' },
  { label: 'Python Fundamentals', text: 'Python Programming for Beginners' },
  { label: 'RAG Explained', text: 'Retrieval-Augmented Generation Explained' },
  { label: 'Deep RL Applications', text: 'Deep Reinforcement Learning Applications' },
  { label: 'Agentic AI 2026', text: 'Autonomous Agentic AI in 2026: Trends, Reasoning Paradigms, and Multi-Agent Orchestration' },
];

const AUDIENCES = [
  {
    id: 'Beginner',
    label: 'Beginner',
    desc: 'Clear intuition, analogies, foundational Python code',
    icon: BookOpen,
  },
  {
    id: 'Intermediate',
    label: 'Intermediate',
    desc: 'Practical design patterns, architecture & tradeoffs',
    icon: Cpu,
  },
  {
    id: 'Advanced',
    label: 'Advanced',
    desc: 'Algorithmic internals, mathematical depth & edge cases',
    icon: Layers,
  },
  {
    id: 'Executive',
    label: 'Executive',
    desc: 'High-level strategy, business impact & deployment ROI',
    icon: Briefcase,
  },
];

const TONES = [
  {
    id: 'Informative',
    label: 'Informative',
    desc: 'Balanced, clear, educational',
    icon: BookOpen,
  },
  {
    id: 'Technical',
    label: 'Technical',
    desc: 'Deep architecture & code specs',
    icon: Cpu,
  },
  {
    id: 'Casual',
    label: 'Casual',
    desc: 'Engaging, human & conversational',
    icon: MessageSquare,
  },
  {
    id: 'Executive',
    label: 'Executive',
    desc: 'High-level strategy & ROI impact',
    icon: Briefcase,
  },
];

export default function GeneratePage() {
  const navigate = useNavigate();
  const textareaRef = useRef(null);

  const {
    topic,
    setTopic,
    tone,
    setTone,
    targetAudience,
    setTargetAudience,
    targetLanguage,
    setTargetLanguage,
    wordCount,
    setWordCount,
    isGenerating,
    startGeneration,
  } = useGeneration();

  const [languages, setLanguages] = useState([]);
  const [loadingLanguages, setLoadingLanguages] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const loadLangs = async () => {
      try {
        const data = await fetchSupportedLanguages();
        if (isMounted) setLanguages(data);
      } catch (err) {
        console.warn('Could not load language registry, using fallback list:', err);
        if (isMounted) {
          setLanguages([
            { code: 'en', name: 'English', native_name: 'English' },
            { code: 'es', name: 'Spanish', native_name: 'Español' },
            { code: 'fr', name: 'French', native_name: 'Français' },
            { code: 'de', name: 'German', native_name: 'Deutsch' },
            { code: 'hi', name: 'Hindi', native_name: 'हिन्दी' },
            { code: 'ja', name: 'Japanese', native_name: '日本語' },
            { code: 'zh', name: 'Chinese', native_name: '中文' },
            { code: 'ar', name: 'Arabic', native_name: 'العربية' },
          ]);
        }
      } finally {
        if (isMounted) setLoadingLanguages(false);
      }
    };
    loadLangs();
    return () => {
      isMounted = false;
    };
  }, []);

  const languageOptions = languages.map((lang) => {
    const isDirect = lang.name.toLowerCase() === 'english';
    return {
      value: lang.name,
      label: lang.name,
      sublabel: lang.native_name !== lang.name ? lang.native_name : undefined,
      badge: isDirect ? 'Direct' : 'Localization',
    };
  });

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!topic.trim() || isGenerating) return;

    startGeneration({
      topic,
      tone,
      target_audience: targetAudience || 'Beginner',
      target_language: targetLanguage,
      word_count: Number(wordCount) || 1500,
    });
    navigate('/pipeline/live');
  };

  // Keyboard shortcut: Cmd/Ctrl + Enter to trigger generation
  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const estReadTime = Math.max(1, Math.ceil((Number(wordCount) || 800) / 200));

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', paddingBottom: 'var(--space-8)' }}>
      {/* Studio Header */}
      <div style={{ marginBottom: 'var(--space-6)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
        <div>
          <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <Sparkles size={22} color="var(--accent-primary-text)" />
            <span>Autonomous Blog Studio</span>
          </h1>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', margin: 'var(--space-1) 0 0 0' }}>
            Configure your research directive, depth, and autonomous multi-agent pipeline parameters.
          </p>
        </div>

        {/* Live Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              background: 'var(--accent-primary-subtle)',
              border: '1px solid var(--accent-primary-border)',
              color: 'var(--accent-primary-text)',
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
            }}
          >
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-primary)' }} />
            LangGraph Multi-Agent Engine
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Dual-Column Studio Grid Layout */}
        <div className="studio-grid-layout">
          {/* ========================================================= */}
          {/* LEFT COLUMN: CREATIVE CANVAS & PROMPT DIRECTIVE */}
          {/* ========================================================= */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
            {/* Prompt Editor Box */}
            <div className="studio-prompt-card" style={{ padding: 'var(--space-5)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
                <label
                  htmlFor="blog-topic-input"
                  style={{
                    fontSize: 'var(--text-sm)',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                  }}
                >
                  <span>Blog Topic or Research Subject</span>
                  <span style={{ color: 'var(--color-danger)' }}>*</span>
                </label>

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  {topic.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setTopic('')}
                      disabled={isGenerating}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-tertiary)',
                        cursor: 'pointer',
                        padding: '2px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '2px',
                        fontSize: 'var(--text-2xs)',
                      }}
                      title="Clear topic"
                    >
                      <X size={12} />
                      <span>Clear</span>
                    </button>
                  )}
                  <span
                    style={{
                      fontSize: 'var(--text-2xs)',
                      fontWeight: 500,
                      color: topic.length > 280 ? 'var(--color-warning-text)' : 'var(--text-tertiary)',
                      background: 'var(--bg-surface-elevated)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    {topic.length} / 300
                  </span>
                </div>
              </div>

              {/* Textarea */}
              <div style={{ position: 'relative' }}>
                <textarea
                  id="blog-topic-input"
                  ref={textareaRef}
                  rows={4}
                  maxLength={300}
                  required
                  disabled={isGenerating}
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="e.g. Write a comprehensive guide on building scalable agentic DAG workflows in LangGraph with deterministic verification..."
                  style={{
                    width: '100%',
                    background: 'var(--bg-input)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-primary)',
                    padding: 'var(--space-4)',
                    fontSize: 'var(--text-sm)',
                    fontFamily: 'inherit',
                    lineHeight: 1.6,
                    resize: 'vertical',
                    outline: 'none',
                    minHeight: '120px',
                    transition: 'border-color var(--transition-fast)',
                  }}
                />
              </div>

              {/* Prompt Suggestions Toolbar */}
              <div style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-3)', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
                  <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Quick Directive Inspiration
                  </span>
                  <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-muted)' }}>
                    Click to load prompt
                  </span>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                  {SUGGESTION_TOPICS.map((sugg, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setTopic(sugg.text)}
                      disabled={isGenerating}
                      style={{
                        background: 'var(--bg-surface-elevated)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '4px 10px',
                        fontSize: 'var(--text-xs)',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                        transition: 'all var(--transition-fast)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = 'var(--accent-primary)';
                        e.currentTarget.style.color = 'var(--text-primary)';
                        e.currentTarget.style.background = 'var(--bg-surface-hover)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = 'var(--border-subtle)';
                        e.currentTarget.style.color = 'var(--text-secondary)';
                        e.currentTarget.style.background = 'var(--bg-surface-elevated)';
                      }}
                    >
                      <Sparkles size={11} color="var(--accent-primary-text)" />
                      <span>{sugg.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Pipeline Architecture Blueprint Preview */}
            <div
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: 'var(--space-4) var(--space-5)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <Layers size={15} color="var(--accent-primary-text)" />
                  <span>Execution Blueprint & Quality Guardrails</span>
                </span>
                <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--accent-primary-text)', fontWeight: 500 }}>
                  Deterministic Verification
                </span>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                  gap: 'var(--space-2)',
                  fontSize: 'var(--text-2xs)',
                }}
              >
                <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ color: 'var(--text-tertiary)', marginBottom: '2px' }}>Step 1-2</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Multi-Search DAG</div>
                  <div style={{ color: 'var(--text-muted)' }}>Tavily & Wikipedia</div>
                </div>

                <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ color: 'var(--text-tertiary)', marginBottom: '2px' }}>Step 3-4</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Fact Extraction</div>
                  <div style={{ color: 'var(--text-muted)' }}>Topical grounding</div>
                </div>

                <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ color: 'var(--text-tertiary)', marginBottom: '2px' }}>Step 5-6</div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Prose Generator</div>
                  <div style={{ color: 'var(--text-muted)' }}>Target: {Number(wordCount) || 800}w</div>
                </div>

                <div style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ color: 'var(--text-tertiary)', marginBottom: '2px' }}>Step 7</div>
                  <div style={{ fontWeight: 600, color: 'var(--color-success-text)' }}>Audit & Store</div>
                  <div style={{ color: 'var(--text-muted)' }}>PostgreSQL persistence</div>
                </div>
              </div>
            </div>
          </div>

          {/* ========================================================= */}
          {/* RIGHT COLUMN: PRECISION ENGINE CONTROLS */}
          {/* ========================================================= */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
            {/* Engine Parameters Card */}
            <div
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: 'var(--space-5)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-5)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <div>
                <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <Sliders size={16} color="var(--accent-primary-text)" />
                  <span>Engine Parameters</span>
                </h3>
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', margin: 'var(--space-1) 0 0 0' }}>
                  Fine-tune output length, voice, and localization.
                </p>
              </div>

              {/* 1. Target Audience Selector */}
              <div>
                <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
                  Target Audience
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-2)' }}>
                  {AUDIENCES.map((a) => {
                    const isSelected = (targetAudience || 'Beginner') === a.id;
                    const IconComp = a.icon;
                    return (
                      <button
                        key={a.id}
                        type="button"
                        onClick={() => setTargetAudience(a.id)}
                        disabled={isGenerating}
                        style={{
                          padding: 'var(--space-2) var(--space-3)',
                          borderRadius: 'var(--radius-md)',
                          border: `1px solid ${isSelected ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                          background: isSelected ? 'var(--accent-primary-subtle)' : 'var(--bg-surface-elevated)',
                          textAlign: 'left',
                          cursor: 'pointer',
                          transition: 'all var(--transition-fast)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '2px',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: isSelected ? 'var(--accent-primary-text)' : 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '5px' }}>
                            <IconComp size={13} />
                            {a.label}
                          </span>
                          {isSelected && <Check size={12} color="var(--accent-primary-text)" />}
                        </div>
                        <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', lineHeight: 1.2 }}>
                          {a.desc}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 2. Word Count Dropdown Selector */}
              <div>
                <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
                  Article Length & Target Word Count
                </label>
                <LengthDropdown
                  value={wordCount}
                  onChange={setWordCount}
                  disabled={isGenerating}
                />
              </div>

              {/* 3. Editorial Tone Selector */}
              <div>
                <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
                  Editorial Tone & Voice
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-2)' }}>
                  {TONES.map((t) => {
                    const isSelected = tone === t.id;
                    const IconComp = t.icon;
                    return (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => setTone(t.id)}
                        disabled={isGenerating}
                        style={{
                          padding: 'var(--space-2) var(--space-3)',
                          borderRadius: 'var(--radius-md)',
                          border: `1px solid ${isSelected ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                          background: isSelected ? 'var(--accent-primary-subtle)' : 'var(--bg-surface-elevated)',
                          textAlign: 'left',
                          cursor: 'pointer',
                          transition: 'all var(--transition-fast)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '2px',
                        }}
                        onMouseEnter={(e) => {
                          if (!isSelected) e.currentTarget.style.borderColor = 'var(--border-default)';
                        }}
                        onMouseLeave={(e) => {
                          if (!isSelected) e.currentTarget.style.borderColor = 'var(--border-subtle)';
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: isSelected ? 'var(--accent-primary-text)' : 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '5px' }}>
                            <IconComp size={13} />
                            {t.label}
                          </span>
                          {isSelected && <Check size={12} color="var(--accent-primary-text)" />}
                        </div>
                        <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', lineHeight: 1.2 }}>
                          {t.desc}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 3. Output Language Custom Dropdown */}
              <div>
                <label style={{ display: 'block', fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
                  Target Output Language
                </label>
                <CustomSelect
                  value={targetLanguage}
                  onChange={setTargetLanguage}
                  options={languageOptions}
                  leftIcon={Globe}
                  disabled={isGenerating || loadingLanguages}
                  searchable={true}
                />
                <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', margin: 'var(--space-1) 0 0 0' }}>
                  {targetLanguage.toLowerCase() === 'english'
                    ? 'English drafts route directly to persistence without translation latency.'
                    : `Triggers Node 5 (Localization Agent) for ${targetLanguage}.`}
                </p>
              </div>
            </div>

            {/* Launch Action Card */}
            <div
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: 'var(--space-5)',
                boxShadow: 'var(--shadow-sm)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-4)',
              }}
            >
              {/* Summary pills */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                <span
                  style={{
                    fontSize: '11px',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                    fontWeight: 500,
                  }}
                >
                  📄 {Number(wordCount).toLocaleString()}w (~{estReadTime}m)
                </span>
                <span
                  style={{
                    fontSize: '11px',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                    fontWeight: 500,
                  }}
                >
                  🎭 {tone}
                </span>
                <span
                  style={{
                    fontSize: '11px',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                    fontWeight: 500,
                  }}
                >
                  🌐 {targetLanguage}
                </span>
              </div>

              {/* Primary Launch Button */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                disabled={isGenerating || !topic.trim()}
                isLoading={isGenerating}
                rightIcon={ArrowRight}
                style={{ width: '100%', height: '48px', fontSize: 'var(--text-sm)', fontWeight: 600 }}
              >
                Launch Autonomous Agent
              </Button>

              {/* Keyboard Shortcut Note */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', fontSize: '11px', color: 'var(--text-tertiary)' }}>
                <span>Tip: Press</span>
                <kbd
                  style={{
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '1px 5px',
                    fontSize: '10px',
                    fontFamily: 'inherit',
                    color: 'var(--text-secondary)',
                  }}
                >
                  Ctrl
                </kbd>
                <span>+</span>
                <kbd
                  style={{
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '1px 5px',
                    fontSize: '10px',
                    fontFamily: 'inherit',
                    color: 'var(--text-secondary)',
                  }}
                >
                  Enter
                </kbd>
                <span>to launch</span>
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
