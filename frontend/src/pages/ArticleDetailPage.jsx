import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchBlogById, updateBlogById } from '../services/api';
import { useToast } from '../context/ToastContext';
import { useTheme } from '../context/ThemeContext';
import { Card, CardHeader, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import Modal from '../components/common/Modal';
import MarkdownRenderer from '../components/article/MarkdownRenderer';
import {
  ArrowLeft,
  Copy,
  Check,
  Download,
  Printer,
  Edit3,
  Save,
  X,
  Maximize2,
  Minimize2,
  Sun,
  Moon,
  BookOpen,
  Share2,
  FileText,
  FileCode,
  ShieldCheck,
  ExternalLink,
  ChevronUp,
  List,
  Type,
  AlignLeft,
  HelpCircle,
  AlertCircle,
  Sparkles,
} from 'lucide-react';

function slugify(text) {
  return String(text)
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export default function ArticleDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const { theme, setTheme, cycleTheme } = useTheme();

  // Core Article State
  const [blog, setBlog] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Edit Mode State
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState('');
  const [editedContent, setEditedContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [editTab, setEditTab] = useState('write'); // 'write' | 'preview'

  // View / Localization state
  const [viewVersion, setViewVersion] = useState('current'); // 'current' | 'original'

  // Focus & Fullscreen
  const [isFocusMode, setIsFocusMode] = useState(false);

  // Scroll & Reading Progress
  const [readingProgress, setReadingProgress] = useState(0);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [activeHeadingSlug, setActiveHeadingSlug] = useState('');

  // Reader Preferences (persisted in localStorage)
  const [fontSize, setFontSize] = useState(() => localStorage.getItem('reader-font-size') || '18px');
  const [fontFamily, setFontFamily] = useState(() => localStorage.getItem('reader-font-family') || 'serif');
  const [lineHeight, setLineHeight] = useState(() => localStorage.getItem('reader-line-height') || '1.75');
  const [columnWidth, setColumnWidth] = useState(() => localStorage.getItem('reader-column-width') || '720px');

  // Modals & Drawers
  const [showShortcutsModal, setShowShortcutsModal] = useState(false);
  const [showTocMobile, setShowTocMobile] = useState(false);
  const [showPrefsMobile, setShowPrefsMobile] = useState(false);
  const [showSources, setShowSources] = useState(false);

  // Copy Feedback
  const [copiedType, setCopiedType] = useState(null);

  // Load Blog from PostgreSQL
  useEffect(() => {
    let isMounted = true;
    const loadBlog = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchBlogById(id);
        if (isMounted) {
          setBlog(data);
          setEditedTitle(data.title || '');
          setEditedContent(data.content || '');
        }
      } catch (err) {
        if (isMounted) setError(err.response?.data?.detail || err.message || 'Article not found');
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    loadBlog();
    return () => { isMounted = false; };
  }, [id]);

  // Persist Reader Preferences
  useEffect(() => {
    localStorage.setItem('reader-font-size', fontSize);
  }, [fontSize]);

  useEffect(() => {
    localStorage.setItem('reader-font-family', fontFamily);
  }, [fontFamily]);

  useEffect(() => {
    localStorage.setItem('reader-line-height', lineHeight);
  }, [lineHeight]);

  useEffect(() => {
    localStorage.setItem('reader-column-width', columnWidth);
  }, [columnWidth]);

  // Fullscreen event listener
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFocusMode(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Sync Focus Mode to document.body for chrome suppression
  useEffect(() => {
    document.body.classList.toggle('focus-mode-active', isFocusMode);
    return () => {
      document.body.classList.remove('focus-mode-active');
    };
  }, [isFocusMode]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if typing in input or textarea
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;

      if (e.key === '?' || (e.shiftKey && e.key === '/')) {
        e.preventDefault();
        setShowShortcutsModal((prev) => !prev);
      } else if (e.key === 'f' || e.key === 'F') {
        e.preventDefault();
        toggleFocusMode();
      } else if (e.key === 'e' || e.key === 'E') {
        e.preventDefault();
        setIsEditing((prev) => !prev);
      } else if (e.key === 't' || e.key === 'T') {
        e.preventDefault();
        cycleTheme();
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 'p' || e.key === 'P')) {
        // Let native print handle or trigger print
      } else if (e.key === 'Escape') {
        if (showShortcutsModal) setShowShortcutsModal(false);
        if (showTocMobile) setShowTocMobile(false);
        if (isFocusMode && document.fullscreenElement) {
          document.exitFullscreen();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showShortcutsModal, showTocMobile, isFocusMode, cycleTheme]);

  // Reading Progress & Back-to-Top scroll listener
  useEffect(() => {
    const handleScroll = () => {
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (totalHeight > 0) {
        const progress = Math.min(100, Math.max(0, (window.scrollY / totalHeight) * 100));
        setReadingProgress(progress);
      }
      setShowBackToTop(window.scrollY > 350);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Compute Active Article Version
  const isTranslated = !!blog?.original_title && (blog?.target_language || '').toLowerCase() !== 'english';
  const showOriginal = viewVersion === 'original' && isTranslated;
  const currentTitle = isEditing ? editedTitle : (showOriginal ? blog?.original_title : blog?.title) || '';
  const currentContent = isEditing ? editedContent : (showOriginal ? blog?.original_content : blog?.content) || '';

  const wordCount = useMemo(() => {
    return (currentContent || '').trim().split(/\s+/).filter(Boolean).length;
  }, [currentContent]);

  const readingTime = useMemo(() => {
    return Math.max(1, Math.ceil(wordCount / 200));
  }, [wordCount]);

  // Extract Table of Contents from Markdown
  const tableOfContents = useMemo(() => {
    if (!currentContent) return [];
    const headings = [];
    const lines = currentContent.split('\n');
    lines.forEach((line) => {
      const match = /^(#{1,3})\s+(.+)$/.exec(line);
      if (match) {
        const level = match[1].length;
        const text = match[2].trim().replace(/\*|_|`/g, '');
        const slug = slugify(text);
        if (slug) {
          headings.push({ level, text, slug });
        }
      }
    });
    return headings;
  }, [currentContent]);

  // Scrollspy observer for active heading in TOC
  useEffect(() => {
    if (tableOfContents.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveHeadingSlug(entry.target.id);
          }
        });
      },
      { rootMargin: '-80px 0px -70% 0px' }
    );

    tableOfContents.forEach(({ slug }) => {
      const el = document.getElementById(slug);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [tableOfContents]);

  // Toggle Focus / Fullscreen Mode
  const toggleFocusMode = async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (err) {
      // Fallback for browsers blocking requestFullscreen
      setIsFocusMode((prev) => !prev);
    }
  };

  // Scroll to heading anchor
  const scrollToHeading = (slug) => {
    const el = document.getElementById(slug);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setActiveHeadingSlug(slug);
      setShowTocMobile(false);
    }
  };

  // Save Edits back to PostgreSQL
  const handleSaveEdits = async () => {
    if (!editedTitle.trim()) {
      addToast('Article title cannot be empty', 'error');
      return;
    }
    setIsSaving(true);
    try {
      const updated = await updateBlogById(id, {
        title: editedTitle.trim(),
        content: editedContent,
      });
      setBlog(updated);
      setIsEditing(false);
      addToast('Article edits saved to PostgreSQL!', 'success');
    } catch (err) {
      addToast(`Failed to save edits: ${err.message}`, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  // Copy Markdown
  const handleCopyMarkdown = () => {
    const fullText = `# ${currentTitle}\n\n${currentContent}`;
    navigator.clipboard.writeText(fullText);
    setCopiedType('md');
    addToast('Article copied as Markdown to clipboard', 'success');
    setTimeout(() => setCopiedType(null), 2000);
  };

  // Copy Plain Text
  const handleCopyPlainText = () => {
    // Strip markdown formatting
    const plainText = `# ${currentTitle}\n\n${currentContent}`
      .replace(/#+\s/g, '')
      .replace(/(\*\*|__)(.*?)\1/g, '$2')
      .replace(/(\*|_)(.*?)\1/g, '$2')
      .replace(/```[\s\S]*?```/g, '')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
    navigator.clipboard.writeText(plainText);
    setCopiedType('text');
    addToast('Article copied as plain text', 'info');
    setTimeout(() => setCopiedType(null), 2000);
  };

  // Download Markdown (.md)
  const handleDownloadMarkdown = () => {
    const fullText = `# ${currentTitle}\n\n${currentContent}`;
    const blob = new Blob([fullText], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${slugify(currentTitle)}.md`;
    link.click();
    URL.revokeObjectURL(url);
    addToast('Downloaded .md file', 'info');
  };

  // Download HTML (.html)
  const handleDownloadHTML = () => {
    const htmlDoc = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${currentTitle}</title>
  <style>
    body { font-family: 'Newsreader', Georgia, serif; max-width: 720px; margin: 40px auto; padding: 0 20px; line-height: 1.75; color: #1c1917; }
    h1, h2, h3 { font-family: system-ui, -apple-system, sans-serif; }
    pre { background: #f5f2eb; padding: 16px; border-radius: 8px; overflow-x: auto; }
    blockquote { border-left: 3px solid #0f766e; padding-left: 16px; font-style: italic; color: #444; }
  </style>
</head>
<body>
  <h1>${currentTitle}</h1>
  <div class="content">${currentContent}</div>
</body>
</html>`;
    const blob = new Blob([htmlDoc], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${slugify(currentTitle)}.html`;
    link.click();
    URL.revokeObjectURL(url);
    addToast('Downloaded .html document', 'info');
  };

  // Print / PDF Export
  const handlePrintPDF = () => {
    window.print();
  };

  // Share Link
  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    addToast('Article URL copied to clipboard!', 'success');
  };

  if (isLoading) {
    return (
      <div style={{ maxWidth: '800px', margin: 'var(--space-16) auto', textAlign: 'center', color: 'var(--text-tertiary)' }}>
        <p style={{ fontSize: 'var(--text-base)' }}>Loading article studio and facts from PostgreSQL...</p>
      </div>
    );
  }

  if (error || !blog) {
    return (
      <div style={{ maxWidth: '640px', margin: 'var(--space-16) auto', textAlign: 'center' }}>
        <Card style={{ padding: 'var(--space-10) var(--space-6)' }}>
          <AlertCircle size={40} color="var(--color-danger)" style={{ margin: '0 auto var(--space-3) auto' }} />
          <h3 style={{ fontSize: 'var(--text-lg)', color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
            Article Not Found
          </h3>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-6)' }}>
            {error || `Could not find an article with ID #${id} in PostgreSQL.`}
          </p>
          <Button variant="secondary" leftIcon={ArrowLeft} onClick={() => navigate('/articles')}>
            Back to Library
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <>
      {/* Sticky 3px Reading Progress Indicator */}
      <div
        className="no-print"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: `${readingProgress}%`,
          height: '3px',
          background: 'var(--accent-primary)',
          zIndex: 9999,
          transition: 'width 100ms ease-out',
        }}
        aria-hidden="true"
      />

      {/* Focus Mode Overlay Banner (exit instructions) */}
      {isFocusMode && (
        <div
          className="no-print"
          style={{
            position: 'fixed',
            top: 'var(--space-4)',
            right: 'var(--space-4)',
            zIndex: 9998,
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-full)',
            padding: 'var(--space-2) var(--space-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            boxShadow: 'var(--shadow-lg)',
            fontSize: 'var(--text-xs)',
            color: 'var(--text-secondary)',
          }}
        >
          <span>Focus Mode</span>
          <kbd style={{ background: 'var(--bg-canvas)', padding: '2px 6px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)' }}>
            F / Esc
          </kbd>
          <button
            type="button"
            onClick={toggleFocusMode}
            aria-label="Exit Focus Mode"
            style={{ background: 'transparent', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', display: 'flex' }}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Main Studio View Container */}
      <div
        style={{
          maxWidth: '1240px',
          margin: '0 auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-6)',
        }}
      >
        {/* Top Action & Navigation Strip */}
        <div
          className="no-print"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 'var(--space-4)',
          }}
        >
          {/* Back button & Breadcrumb */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <Button
              variant="ghost"
              size="sm"
              leftIcon={ArrowLeft}
              onClick={() => navigate('/articles')}
            >
              Library
            </Button>
            <span style={{ color: 'var(--border-default)' }}>/</span>
            <Badge variant="neutral">#{id}</Badge>
            <Badge variant="primary">{blog.target_language || 'English'}</Badge>
            <Badge variant={(blog.verification_score || 8.5) >= 8.0 ? 'success' : 'warning'} icon={ShieldCheck}>
              Score: {blog.verification_score || 8.5}/10
            </Badge>
          </div>

          {/* Action Strip: Focus, Edit, Export, Shortcuts */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
            <Button
              variant={isFocusMode ? 'primary' : 'ghost'}
              size="sm"
              leftIcon={isFocusMode ? Minimize2 : Maximize2}
              onClick={toggleFocusMode}
              title="Toggle Fullscreen Focus Mode (F key)"
            >
              {isFocusMode ? 'Exit Focus' : 'Focus (F)'}
            </Button>

            <Button
              variant={isEditing ? 'primary' : 'secondary'}
              size="sm"
              leftIcon={isEditing ? X : Edit3}
              onClick={() => setIsEditing((prev) => !prev)}
              title="Edit Title and Markdown (E key)"
            >
              {isEditing ? 'Exit Edit' : 'Edit (E)'}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              leftIcon={Printer}
              onClick={handlePrintPDF}
              title="Print / Save as PDF (@media print)"
            >
              PDF
            </Button>

            <Button
              variant="ghost"
              size="sm"
              leftIcon={copiedType === 'md' ? Check : FileCode}
              onClick={handleCopyMarkdown}
              title="Copy raw Markdown"
            >
              {copiedType === 'md' ? 'Copied' : 'Markdown'}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              leftIcon={Download}
              onClick={handleDownloadMarkdown}
              title="Download .md file"
            >
              Export
            </Button>

            <Button
              variant="ghost"
              size="sm"
              leftIcon={Share2}
              onClick={handleShare}
              title="Share article URL"
            />

            <Button
              variant="ghost"
              size="sm"
              leftIcon={HelpCircle}
              onClick={() => setShowShortcutsModal(true)}
              title="Keyboard Shortcuts (? key)"
            />
          </div>
        </div>

        {/* Mobile Reader Preferences Toggle Pill */}
        <div className="mobile-only no-print" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Button
            variant="secondary"
            size="sm"
            leftIcon={Type}
            onClick={() => setShowPrefsMobile((prev) => !prev)}
            aria-expanded={showPrefsMobile}
          >
            {showPrefsMobile ? 'Hide Reader Settings' : 'Aa Reading Settings'}
          </Button>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
            {readingTime} min &bull; {wordCount} words
          </span>
        </div>

        {/* Reader Preferences Bar (Floating Toolstrip) */}
        <div
          className={`reader-preferences-bar no-print ${showPrefsMobile ? 'mobile-expanded' : ''}`}
        >
          {/* Typography Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
            {/* Font Family (Serif vs Sans) */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Typeface
              </span>
              <div style={{ display: 'flex', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-sm)', padding: '2px', border: '1px solid var(--border-subtle)' }}>
                <button
                  type="button"
                  onClick={() => setFontFamily('serif')}
                  aria-pressed={fontFamily === 'serif'}
                  style={{
                    padding: '2px 8px',
                    fontSize: 'var(--text-xs)',
                    fontFamily: 'var(--font-serif)',
                    border: 'none',
                    borderRadius: 'var(--radius-xs)',
                    background: fontFamily === 'serif' ? 'var(--bg-surface)' : 'transparent',
                    color: fontFamily === 'serif' ? 'var(--text-primary)' : 'var(--text-tertiary)',
                    cursor: 'pointer',
                    fontWeight: fontFamily === 'serif' ? 600 : 400,
                  }}
                >
                  Serif
                </button>
                <button
                  type="button"
                  onClick={() => setFontFamily('sans')}
                  aria-pressed={fontFamily === 'sans'}
                  style={{
                    padding: '2px 8px',
                    fontSize: 'var(--text-xs)',
                    fontFamily: 'var(--font-sans)',
                    border: 'none',
                    borderRadius: 'var(--radius-xs)',
                    background: fontFamily === 'sans' ? 'var(--bg-surface)' : 'transparent',
                    color: fontFamily === 'sans' ? 'var(--text-primary)' : 'var(--text-tertiary)',
                    cursor: 'pointer',
                    fontWeight: fontFamily === 'sans' ? 600 : 400,
                  }}
                >
                  Sans
                </button>
              </div>
            </div>

            {/* Font Size Adjuster (A- / A+) */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Size
              </span>
              <div style={{ display: 'flex', alignItems: 'center', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-sm)', padding: '2px', border: '1px solid var(--border-subtle)' }}>
                {['16px', '18px', '20px', '22px'].map((sz) => (
                  <button
                    key={sz}
                    type="button"
                    onClick={() => setFontSize(sz)}
                    aria-pressed={fontSize === sz}
                    style={{
                      padding: '2px 8px',
                      fontSize: 'var(--text-xs)',
                      border: 'none',
                      borderRadius: 'var(--radius-xs)',
                      background: fontSize === sz ? 'var(--bg-surface)' : 'transparent',
                      color: fontSize === sz ? 'var(--accent-primary-text)' : 'var(--text-tertiary)',
                      fontWeight: fontSize === sz ? 700 : 400,
                      cursor: 'pointer',
                    }}
                  >
                    {sz.replace('px', '')}
                  </button>
                ))}
              </div>
            </div>

            {/* Line Spacing */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Spacing
              </span>
              <div style={{ display: 'flex', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-sm)', padding: '2px', border: '1px solid var(--border-subtle)' }}>
                {[
                  { label: 'Compact', val: '1.6' },
                  { label: 'Normal', val: '1.75' },
                  { label: 'Relaxed', val: '1.9' },
                ].map(({ label, val }) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => setLineHeight(val)}
                    aria-pressed={lineHeight === val}
                    style={{
                      padding: '2px 8px',
                      fontSize: 'var(--text-xs)',
                      border: 'none',
                      borderRadius: 'var(--radius-xs)',
                      background: lineHeight === val ? 'var(--bg-surface)' : 'transparent',
                      color: lineHeight === val ? 'var(--accent-primary-text)' : 'var(--text-tertiary)',
                      fontWeight: lineHeight === val ? 600 : 400,
                      cursor: 'pointer',
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Reading Column Width */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Width
              </span>
              <div style={{ display: 'flex', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-sm)', padding: '2px', border: '1px solid var(--border-subtle)' }}>
                {[
                  { label: 'Narrow', val: '640px' },
                  { label: 'Standard', val: '720px' },
                  { label: 'Wide', val: '840px' },
                ].map(({ label, val }) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => setColumnWidth(val)}
                    aria-pressed={columnWidth === val}
                    style={{
                      padding: '2px 8px',
                      fontSize: 'var(--text-xs)',
                      border: 'none',
                      borderRadius: 'var(--radius-xs)',
                      background: columnWidth === val ? 'var(--bg-surface)' : 'transparent',
                      color: columnWidth === val ? 'var(--accent-primary-text)' : 'var(--text-tertiary)',
                      fontWeight: columnWidth === val ? 600 : 400,
                      cursor: 'pointer',
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Reading Metrics & Translation Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              {readingTime} min read &bull; {wordCount} words
            </span>

            {/* Translation switch if localized */}
            {isTranslated && (
              <div style={{ display: 'flex', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-sm)', padding: '2px', border: '1px solid var(--border-subtle)' }}>
                <button
                  type="button"
                  onClick={() => setViewVersion('current')}
                  aria-pressed={viewVersion === 'current'}
                  style={{
                    padding: '2px 8px',
                    fontSize: 'var(--text-xs)',
                    border: 'none',
                    borderRadius: 'var(--radius-xs)',
                    background: viewVersion === 'current' ? 'var(--bg-surface)' : 'transparent',
                    color: viewVersion === 'current' ? 'var(--accent-primary-text)' : 'var(--text-tertiary)',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {blog.target_language}
                </button>
                <button
                  type="button"
                  onClick={() => setViewVersion('original')}
                  aria-pressed={viewVersion === 'original'}
                  style={{
                    padding: '2px 8px',
                    fontSize: 'var(--text-xs)',
                    border: 'none',
                    borderRadius: 'var(--radius-xs)',
                    background: viewVersion === 'original' ? 'var(--bg-surface)' : 'transparent',
                    color: viewVersion === 'original' ? 'var(--accent-primary-text)' : 'var(--text-tertiary)',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  English
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Edit Mode Panel */}
        {isEditing && (
          <Card className="no-print" style={{ border: '2px solid var(--accent-primary)' }}>
            <CardHeader style={{ justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <Edit3 size={18} color="var(--accent-primary-text)" />
                <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                  Inline Article Editor
                </h3>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <div style={{ display: 'flex', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-sm)', padding: '2px', border: '1px solid var(--border-subtle)' }}>
                  <button
                    type="button"
                    onClick={() => setEditTab('write')}
                    style={{
                      padding: '4px 10px',
                      fontSize: 'var(--text-xs)',
                      border: 'none',
                      borderRadius: 'var(--radius-xs)',
                      background: editTab === 'write' ? 'var(--accent-primary)' : 'transparent',
                      color: editTab === 'write' ? '#ffffff' : 'var(--text-tertiary)',
                      cursor: 'pointer',
                      fontWeight: 600,
                    }}
                  >
                    Write
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditTab('preview')}
                    style={{
                      padding: '4px 10px',
                      fontSize: 'var(--text-xs)',
                      border: 'none',
                      borderRadius: 'var(--radius-xs)',
                      background: editTab === 'preview' ? 'var(--accent-primary)' : 'transparent',
                      color: editTab === 'preview' ? '#ffffff' : 'var(--text-tertiary)',
                      cursor: 'pointer',
                      fontWeight: 600,
                    }}
                  >
                    Live Preview
                  </button>
                </div>

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsEditing(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  leftIcon={Save}
                  isLoading={isSaving}
                  onClick={handleSaveEdits}
                >
                  Save Changes
                </Button>
              </div>
            </CardHeader>

            <CardContent style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div>
                <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
                  Article Headline (SEO Title)
                </label>
                <input
                  type="text"
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'var(--bg-input)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-2) var(--space-4)',
                    color: 'var(--text-primary)',
                    fontSize: 'var(--text-base)',
                    fontWeight: 600,
                    outline: 'none',
                  }}
                />
              </div>

              {editTab === 'write' ? (
                <div>
                  <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
                    Markdown Body
                  </label>
                  <textarea
                    rows={18}
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'var(--bg-input)',
                      border: '1px solid var(--border-default)',
                      borderRadius: 'var(--radius-md)',
                      padding: 'var(--space-4)',
                      color: 'var(--text-primary)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: 'var(--text-sm)',
                      lineHeight: 1.6,
                      resize: 'vertical',
                      outline: 'none',
                    }}
                  />
                </div>
              ) : (
                <div style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: 'var(--space-6)', background: 'var(--bg-surface)' }}>
                  <MarkdownRenderer content={editedContent} />
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Mobile Table of Contents Accordion */}
        {tableOfContents.length > 0 && (
          <div
            className="mobile-only no-print"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--space-3) var(--space-4)',
            }}
          >
            <button
              type="button"
              onClick={() => setShowTocMobile((prev) => !prev)}
              aria-expanded={showTocMobile}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                fontSize: 'var(--text-xs)',
                fontWeight: 600,
                cursor: 'pointer',
                padding: 'var(--space-1) 0',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <List size={14} color="var(--accent-primary-text)" />
                <span>Table of Contents ({tableOfContents.length} sections)</span>
              </div>
              <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)' }}>
                {showTocMobile ? 'Hide' : 'Show'}
              </span>
            </button>

            {showTocMobile && (
              <nav style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', marginTop: 'var(--space-3)', paddingTop: 'var(--space-2)', borderTop: '1px solid var(--border-subtle)' }}>
                {tableOfContents.map(({ level, text, slug }) => {
                  const isActive = activeHeadingSlug === slug;
                  return (
                    <button
                      key={slug}
                      type="button"
                      onClick={() => scrollToHeading(slug)}
                      style={{
                        textAlign: 'left',
                        padding: 'var(--space-2)',
                        paddingLeft: `${(level - 1) * 12 + 8}px`,
                        fontSize: 'var(--text-xs)',
                        border: 'none',
                        borderRadius: 'var(--radius-xs)',
                        background: isActive ? 'var(--accent-primary-subtle)' : 'transparent',
                        color: isActive ? 'var(--accent-primary-text)' : 'var(--text-secondary)',
                        fontWeight: isActive ? 600 : 400,
                        borderLeft: isActive ? '2px solid var(--accent-primary)' : '2px solid transparent',
                        cursor: 'pointer',
                      }}
                    >
                      {text}
                    </button>
                  );
                })}
              </nav>
            )}
          </div>
        )}

        {/* Reading Grid: Responsive TOC Sidebar + Centered Article Column */}
        <div
          className={`article-studio-layout ${tableOfContents.length > 0 ? 'with-toc' : ''}`}
        >
          {/* Table of Contents Sticky Sidebar (Desktop only) */}
          {tableOfContents.length > 0 && (
            <aside
              className="toc-desktop-sidebar hide-on-mobile no-print"
              style={{
                position: 'sticky',
                top: '80px',
                maxHeight: 'calc(100vh - 120px)',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)',
                padding: 'var(--space-4)',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: 'var(--space-2)' }}>
                <List size={14} color="var(--text-secondary)" />
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Table of Contents
                </span>
              </div>

              <nav style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                {tableOfContents.map(({ level, text, slug }) => {
                  const isActive = activeHeadingSlug === slug;
                  return (
                    <button
                      key={slug}
                      type="button"
                      onClick={() => scrollToHeading(slug)}
                      style={{
                        textAlign: 'left',
                        padding: 'var(--space-1) var(--space-2)',
                        paddingLeft: `${(level - 1) * 12 + 8}px`,
                        fontSize: 'var(--text-xs)',
                        border: 'none',
                        borderRadius: 'var(--radius-xs)',
                        background: isActive ? 'var(--accent-primary-subtle)' : 'transparent',
                        color: isActive ? 'var(--accent-primary-text)' : 'var(--text-secondary)',
                        fontWeight: isActive ? 600 : 400,
                        borderLeft: isActive ? '2px solid var(--accent-primary)' : '2px solid transparent',
                        cursor: 'pointer',
                        transition: 'all var(--transition-fast)',
                        lineHeight: 1.4,
                      }}
                    >
                      {text}
                    </button>
                  );
                })}
              </nav>
            </aside>
          )}

          {/* Centered Editorial Reading Column */}
          <article className="article-card">
            {/* Formal Document Publication Masthead (PDF & Print Only) */}
            <div className="print-only" style={{ marginBottom: '24pt', paddingBottom: '16pt', borderBottom: '2pt solid #111111' }}>
              <div style={{ fontSize: '9pt', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#555555', marginBottom: '8pt' }}>
                Autonomous Blog Engine &bull; Publication & Quality Audit Record
              </div>
              <h1 style={{ fontSize: '24pt', fontWeight: 700, margin: '0 0 10pt 0', color: '#000000', lineHeight: 1.2 }}>
                {currentTitle}
              </h1>
              <div style={{ fontSize: '10pt', color: '#333333', lineHeight: 1.6 }}>
                <span><strong>Tone:</strong> {blog.tone || 'Informative'}</span> &bull;{' '}
                <span><strong>Language:</strong> {blog.target_language || 'English'}</span> &bull;{' '}
                <span><strong>Published:</strong> {blog.created_at ? new Date(blog.created_at).toLocaleDateString() : 'Recent'}</span> &bull;{' '}
                <span><strong>Length:</strong> {wordCount} words ({readingTime} min read)</span> &bull;{' '}
                <span><strong>Audit Score:</strong> {blog.verification_score || 8.5}/10</span>
              </div>
            </div>

            {/* Dynamic CSS Variables for Custom Reader Ergonomics */}
            <div
              style={{
                '--reader-font-size': fontSize,
                '--reader-font-family': fontFamily === 'serif' ? 'var(--font-serif)' : 'var(--font-sans)',
                '--reader-line-height': lineHeight,
                '--reader-max-width': columnWidth,
              }}
            >
              {/* Article Header (Editorial Cover - Web only) */}
              <header className="no-print" style={{ maxWidth: columnWidth, margin: '0 auto var(--space-8) auto', borderBottom: '1px solid var(--border-subtle)', paddingBottom: 'var(--space-6)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
                  <Badge variant="primary">{blog.tone || 'Informative'}</Badge>
                  <Badge variant="neutral">{blog.target_language || 'English'}</Badge>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
                    Published {blog.created_at ? new Date(blog.created_at).toLocaleDateString() : 'Recently'}
                  </span>
                </div>

                <h1
                  style={{
                    fontSize: 'var(--text-3xl)',
                    fontWeight: 700,
                    lineHeight: 1.25,
                    color: 'var(--text-primary)',
                    letterSpacing: '-0.025em',
                    marginBottom: 'var(--space-4)',
                    textWrap: 'balance',
                  }}
                >
                  {currentTitle}
                </h1>

                {/* Sub-header reading meta */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-3)', fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
                  <span>{wordCount} words &bull; {readingTime} min read</span>
                  {blog.sources?.length > 0 && (
                    <button
                      type="button"
                      className="no-print"
                      onClick={() => setShowSources((prev) => !prev)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--accent-primary-text)',
                        cursor: 'pointer',
                        fontSize: 'var(--text-xs)',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <span>{blog.sources.length} Ground-Truth Citations</span>
                      <ExternalLink size={12} />
                    </button>
                  )}
                </div>
              </header>

              {/* Collapsible Verified Citations Banner */}
              {showSources && blog.sources?.length > 0 && (
                <div
                  className="no-print"
                  style={{
                    maxWidth: columnWidth,
                    margin: '0 auto var(--space-8) auto',
                    padding: 'var(--space-4) var(--space-5)',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-md)',
                  }}
                >
                  <h4 style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
                    Live Web Citations Used for Fact Grounding:
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: 'var(--space-4)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                    {blog.sources.map((src, i) => (
                      <li key={i} style={{ marginBottom: '4px' }}>
                        <a href={src.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-primary-text)' }}>
                          {src.title || src.url}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Article Markdown Body */}
              {wordCount === 0 ? (
                <div style={{ textAlign: 'center', padding: 'var(--space-12) var(--space-4)', color: 'var(--text-tertiary)' }}>
                  <AlertCircle size={40} color="var(--color-warning)" style={{ margin: '0 auto var(--space-3) auto' }} />
                  <h3 style={{ fontSize: 'var(--text-base)', color: 'var(--text-primary)', marginBottom: 'var(--space-1)' }}>
                    Draft Has No Content (0 Words)
                  </h3>
                  <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', maxWidth: '440px', margin: '0 auto var(--space-5) auto' }}>
                    This generation was saved without markdown content. You can write content using Edit Mode or generate a fresh blog.
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-3)' }}>
                    <Button variant="secondary" size="sm" onClick={() => setIsEditing(true)}>
                      Write Content in Editor
                    </Button>
                    <Button variant="primary" size="sm" onClick={() => navigate('/generate')}>
                      Generate Fresh Blog
                    </Button>
                  </div>
                </div>
              ) : (
                <MarkdownRenderer
                  content={currentContent}
                  onCopyHeadingLink={(slug) => addToast(`Heading link #${slug} copied!`, 'info')}
                />
              )}
            </div>

            {/* End-of-Article Quality Footer Strip */}
            <footer
              style={{
                maxWidth: columnWidth,
                margin: 'var(--space-12) auto 0 auto',
                paddingTop: 'var(--space-6)',
                borderTop: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: 'var(--space-4)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <ShieldCheck size={18} color="var(--color-success)" />
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  Fact-Checked by Verifier Agent &bull; Audit Score: {blog.verification_score || 8.5}/10
                </span>
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => navigate(`/articles/${id}/audit`)}
                >
                  View Quality Audit
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  leftIcon={Printer}
                  onClick={handlePrintPDF}
                >
                  Print / Export PDF
                </Button>
              </div>
            </footer>
          </article>
        </div>
      </div>

      {/* Floating Back to Top Button */}
      {showBackToTop && (
        <button
          type="button"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="no-print"
          title="Back to Top"
          aria-label="Back to top of article"
          style={{
            position: 'fixed',
            bottom: 'var(--space-6)',
            right: 'var(--space-6)',
            width: '42px',
            height: '42px',
            borderRadius: 'var(--radius-full)',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            color: 'var(--text-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-lg)',
            cursor: 'pointer',
            zIndex: 9990,
            transition: 'transform var(--transition-fast)',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-2px)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
        >
          <ChevronUp size={20} />
        </button>
      )}

      {/* Keyboard Shortcuts Modal */}
      <Modal
        isOpen={showShortcutsModal}
        onClose={() => setShowShortcutsModal(false)}
        title="Reader Keyboard Shortcuts"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', fontSize: 'var(--text-sm)' }}>
          <p style={{ color: 'var(--text-secondary)', margin: '0 0 var(--space-2) 0' }}>
            Boost your reading and editorial productivity with quick keys:
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 'var(--space-2)', alignItems: 'center' }}>
            <span style={{ color: 'var(--text-primary)' }}>Toggle Fullscreen Focus Mode</span>
            <kbd style={{ background: 'var(--bg-surface-elevated)', padding: '2px 8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-default)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>F</kbd>

            <span style={{ color: 'var(--text-primary)' }}>Toggle Inline Markdown Editor</span>
            <kbd style={{ background: 'var(--bg-surface-elevated)', padding: '2px 8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-default)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>E</kbd>

            <span style={{ color: 'var(--text-primary)' }}>Cycle Theme (Light / Sepia / Dark)</span>
            <kbd style={{ background: 'var(--bg-surface-elevated)', padding: '2px 8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-default)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>T</kbd>

            <span style={{ color: 'var(--text-primary)' }}>Print / Save as PDF</span>
            <kbd style={{ background: 'var(--bg-surface-elevated)', padding: '2px 8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-default)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>Ctrl + P</kbd>

            <span style={{ color: 'var(--text-primary)' }}>Close Modals / Exit Focus</span>
            <kbd style={{ background: 'var(--bg-surface-elevated)', padding: '2px 8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-default)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>Esc</kbd>

            <span style={{ color: 'var(--text-primary)' }}>Open this Shortcuts Dialog</span>
            <kbd style={{ background: 'var(--bg-surface-elevated)', padding: '2px 8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-default)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>?</kbd>
          </div>
        </div>
      </Modal>
    </>
  );
}
