import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGeneration } from '../context/GenerationContext';
import { fetchSupportedLanguages } from '../services/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import { Sparkles, Globe, Layers, BookOpen, ArrowRight, Check } from 'lucide-react';

const PRESET_TOPICS = [
  'Autonomous Agentic AI in 2026: Trends and Paradigms',
  'Mastering Directed Acyclic Graphs (DAG) in LangGraph',
  'High-Performance Async REST APIs with FastAPI & PostgreSQL',
  'Vector Databases vs Relational DBs for Production RAG',
];

const TONES = [
  { id: 'Informative', label: 'Informative', desc: 'Balanced, educational, and accessible' },
  { id: 'Technical', label: 'Technical', desc: 'In-depth architecture, code, and CLI details' },
  { id: 'Casual', label: 'Casual', desc: 'Conversational, engaging, and lighthearted' },
  { id: 'Executive', label: 'Executive', desc: 'High-level business implications and strategy' },
];

export default function GeneratePage() {
  const navigate = useNavigate();
  const {
    topic,
    setTopic,
    tone,
    setTone,
    targetLanguage,
    setTargetLanguage,
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
        console.warn('Could not load language registry:', err);
        if (isMounted) {
          setLanguages([
            { code: 'en', name: 'English', native_name: 'English' },
            { code: 'es', name: 'Spanish', native_name: 'Español' },
            { code: 'fr', name: 'French', native_name: 'Français' },
            { code: 'de', name: 'German', native_name: 'Deutsch' },
            { code: 'hi', name: 'Hindi', native_name: 'हिन्दी' },
            { code: 'ja', name: 'Japanese', native_name: '日本語' },
          ]);
        }
      } finally {
        if (isMounted) setLoadingLanguages(false);
      }
    };
    loadLangs();
    return () => { isMounted = false; };
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!topic.trim() || isGenerating) return;

    startGeneration({ topic, tone, target_language: targetLanguage });
    navigate('/pipeline/live');
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>
                <Sparkles size={20} color="var(--accent-primary-text)" />
                <span>Configure Content Generation Agent</span>
              </CardTitle>
              <CardDescription>
                Define your target topic, tone, and localization options for the autonomous LangGraph pipeline.
              </CardDescription>
            </div>
          </CardHeader>

          <CardContent style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
            {/* Topic Input */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
                <label
                  htmlFor="blog-topic-input"
                  style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)' }}
                >
                  Blog Topic / Primary Subject <span style={{ color: 'var(--color-danger)' }}>*</span>
                </label>
                <span style={{ fontSize: 'var(--text-2xs)', color: topic.length > 280 ? 'var(--color-warning-text)' : 'var(--text-tertiary)' }}>
                  {topic.length} / 300 characters
                </span>
              </div>

              <textarea
                id="blog-topic-input"
                rows={3}
                maxLength={300}
                required
                disabled={isGenerating}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g., Deep dive into LangGraph DAG workflows, multi-agent self-correction loops, and FastAPI integration..."
                style={{
                  width: '100%',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  padding: 'var(--space-3) var(--space-4)',
                  fontSize: 'var(--text-sm)',
                  fontFamily: 'inherit',
                  lineHeight: 1.5,
                  resize: 'vertical',
                  transition: 'border-color var(--transition-fast)',
                }}
                onFocus={(e) => (e.target.style.borderColor = 'var(--accent-primary)')}
                onBlur={(e) => (e.target.style.borderColor = 'var(--border-default)')}
              />

              {/* Preset Topic Chips */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap', marginTop: 'var(--space-3)' }}>
                <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', fontWeight: 500 }}>
                  Suggestions:
                </span>
                {PRESET_TOPICS.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setTopic(preset)}
                    disabled={isGenerating}
                    style={{
                      background: 'var(--bg-surface-elevated)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '2px var(--space-2)',
                      fontSize: 'var(--text-2xs)',
                      color: 'var(--text-secondary)',
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'var(--accent-primary)';
                      e.currentTarget.style.color = 'var(--text-primary)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--border-subtle)';
                      e.currentTarget.style.color = 'var(--text-secondary)';
                    }}
                  >
                    {preset.slice(0, 36)}...
                  </button>
                ))}
              </div>
            </div>

            {/* Tone Selector */}
            <div>
              <label style={{ display: 'block', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
                Editorial Tone
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-3)' }}>
                {TONES.map((t) => {
                  const isSelected = tone === t.id;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setTone(t.id)}
                      disabled={isGenerating}
                      style={{
                        padding: 'var(--space-3) var(--space-4)',
                        borderRadius: 'var(--radius-md)',
                        border: `1px solid ${isSelected ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                        background: isSelected ? 'var(--accent-primary-subtle)' : 'var(--bg-surface-elevated)',
                        color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
                        textAlign: 'left',
                        cursor: 'pointer',
                        transition: 'all var(--transition-fast)',
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) e.currentTarget.style.borderColor = 'var(--border-default)';
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) e.currentTarget.style.borderColor = 'var(--border-subtle)';
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-1)' }}>
                        <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)', color: isSelected ? 'var(--accent-primary-text)' : 'var(--text-primary)' }}>
                          {t.label}
                        </span>
                        {isSelected && <Check size={14} color="var(--accent-primary-text)" />}
                      </div>
                      <p style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', margin: 0 }}>
                        {t.desc}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Target Language Dropdown */}
            <div>
              <label
                htmlFor="target-language-select"
                style={{ display: 'block', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}
              >
                Target Output Language
              </label>
              <div style={{ position: 'relative' }}>
                <select
                  id="target-language-select"
                  value={targetLanguage}
                  onChange={(e) => setTargetLanguage(e.target.value)}
                  disabled={isGenerating || loadingLanguages}
                  style={{
                    width: '100%',
                    background: 'var(--bg-input)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--text-primary)',
                    padding: 'var(--space-3) var(--space-4)',
                    paddingLeft: 'var(--space-10)',
                    fontSize: 'var(--text-sm)',
                    fontFamily: 'inherit',
                    outline: 'none',
                    cursor: 'pointer',
                  }}
                  onFocus={(e) => (e.target.style.borderColor = 'var(--accent-primary)')}
                  onBlur={(e) => (e.target.style.borderColor = 'var(--border-default)')}
                >
                  {languages.map((lang) => (
                    <option key={lang.code} value={lang.name} style={{ background: '#0b101c', color: '#fff' }}>
                      {lang.name} ({lang.native_name}) {lang.name === 'English' ? '— Direct Route' : '— Invokes Localization Agent'}
                    </option>
                  ))}
                </select>
                <Globe
                  size={16}
                  color="var(--accent-primary-text)"
                  style={{ position: 'absolute', left: 'var(--space-3)', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}
                />
              </div>
              <p style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', marginTop: 'var(--space-2)' }}>
                {targetLanguage.toLowerCase() === 'english'
                  ? 'English posts route directly from the Verifier Node to storage without extra translation latency.'
                  : `Selecting ${targetLanguage} dynamically routes execution through Node 5 (Localization Agent).`}
              </p>
            </div>
          </CardContent>

          <CardFooter>
            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={isGenerating || !topic.trim()}
              isLoading={isGenerating}
              rightIcon={ArrowRight}
            >
              Launch Autonomous Agent
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  );
}
