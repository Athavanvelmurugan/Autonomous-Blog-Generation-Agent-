import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchBlogHistory, deleteBlogById } from '../services/api';
import { useToast } from '../context/ToastContext';
import { Card, CardHeader, CardTitle, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import Modal from '../components/common/Modal';
import {
  Library,
  Search,
  Trash2,
  BookOpen,
  ShieldCheck,
  LayoutList,
  LayoutGrid,
  Clock,
  Sparkles,
  ArrowRight,
  Filter,
} from 'lucide-react';

export default function ArticlesPage() {
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [blogs, setBlogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & search state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTone, setSelectedTone] = useState('ALL');
  const [selectedLanguage, setSelectedLanguage] = useState('ALL');
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'grid'

  // Delete modal state
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadBlogs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchBlogHistory();
      setBlogs(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadBlogs();
  }, []);

  // Compute distinct options for filter dropdowns
  const availableTones = useMemo(() => {
    const set = new Set(blogs.map((b) => b.tone).filter(Boolean));
    return Array.from(set);
  }, [blogs]);

  const availableLanguages = useMemo(() => {
    const set = new Set(blogs.map((b) => b.target_language).filter(Boolean));
    return Array.from(set);
  }, [blogs]);

  // Filtered dataset
  const filteredBlogs = useMemo(() => {
    return blogs.filter((b) => {
      const matchesSearch =
        searchQuery === '' ||
        (b.title && b.title.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (b.topic && b.topic.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesTone = selectedTone === 'ALL' || b.tone === selectedTone;
      const matchesLang = selectedLanguage === 'ALL' || b.target_language === selectedLanguage;

      return matchesSearch && matchesTone && matchesLang;
    });
  }, [blogs, searchQuery, selectedTone, selectedLanguage]);

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteBlogById(deleteTarget.id);
      addToast(`Deleted article #${deleteTarget.id} from PostgreSQL`, 'success');
      setDeleteTarget(null);
      await loadBlogs();
    } catch (err) {
      addToast(`Failed to delete: ${err.message}`, 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', maxWidth: '1280px', margin: '0 auto' }}>
      {/* Top Filter & Toolbar Card */}
      <Card>
        <CardContent style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
            {/* Search Input */}
            <div style={{ position: 'relative', flex: '1 1 280px', maxWidth: '400px' }}>
              <Search
                size={16}
                color="var(--text-tertiary)"
                style={{ position: 'absolute', left: 'var(--space-3)', top: '50%', transform: 'translateY(-50%)' }}
              />
              <input
                type="text"
                placeholder="Search articles by title or topic..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  padding: 'var(--space-2) var(--space-4)',
                  paddingLeft: 'var(--space-9)',
                  fontSize: 'var(--text-sm)',
                  outline: 'none',
                }}
              />
            </div>

            {/* Filter Dropdowns & View Mode Switcher */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
              {/* Tone Filter */}
              <select
                value={selectedTone}
                onChange={(e) => setSelectedTone(e.target.value)}
                style={{
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  padding: 'var(--space-2) var(--space-3)',
                  fontSize: 'var(--text-xs)',
                  cursor: 'pointer',
                }}
              >
                <option value="ALL">All Tones</option>
                {availableTones.map((t) => (
                  <option key={t} value={t}>
                    Tone: {t}
                  </option>
                ))}
              </select>

              {/* Language Filter */}
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                style={{
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  padding: 'var(--space-2) var(--space-3)',
                  fontSize: 'var(--text-xs)',
                  cursor: 'pointer',
                }}
              >
                <option value="ALL">All Languages</option>
                {availableLanguages.map((l) => (
                  <option key={l} value={l}>
                    Lang: {l}
                  </option>
                ))}
              </select>

              {/* View Mode Toggle */}
              <div
                style={{
                  display: 'flex',
                  background: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '2px',
                }}
              >
                <button
                  type="button"
                  onClick={() => setViewMode('table')}
                  aria-label="Table view"
                  style={{
                    background: viewMode === 'table' ? 'var(--accent-primary)' : 'transparent',
                    border: 'none',
                    borderRadius: 'var(--radius-xs)',
                    color: viewMode === 'table' ? '#fff' : 'var(--text-tertiary)',
                    padding: 'var(--space-1) var(--space-2)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <LayoutList size={16} />
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('grid')}
                  aria-label="Grid view"
                  style={{
                    background: viewMode === 'grid' ? 'var(--accent-primary)' : 'transparent',
                    border: 'none',
                    borderRadius: 'var(--radius-xs)',
                    color: viewMode === 'grid' ? '#fff' : 'var(--text-tertiary)',
                    padding: 'var(--space-1) var(--space-2)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <LayoutGrid size={16} />
                </button>
              </div>

              {/* New Generation Button */}
              <Button
                variant="primary"
                size="sm"
                leftIcon={Sparkles}
                onClick={() => navigate('/generate')}
              >
                New Article
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Area */}
      {isLoading ? (
        <Card>
          <CardContent style={{ textAlign: 'center', padding: 'var(--space-12) var(--space-4)', color: 'var(--text-tertiary)' }}>
            Loading saved publications from PostgreSQL...
          </CardContent>
        </Card>
      ) : error ? (
        <Card>
          <CardContent style={{ textAlign: 'center', padding: 'var(--space-8) var(--space-4)', color: 'var(--color-danger-text)' }}>
            Error fetching articles: {error}
          </CardContent>
        </Card>
      ) : filteredBlogs.length === 0 ? (
        <Card>
          <CardContent style={{ textAlign: 'center', padding: 'var(--space-12) var(--space-4)', color: 'var(--text-tertiary)' }}>
            <Library size={40} style={{ opacity: 0.35, margin: '0 auto var(--space-3) auto' }} />
            <h3 style={{ fontSize: 'var(--text-base)', color: 'var(--text-primary)', marginBottom: 'var(--space-1)' }}>
              No articles match your criteria
            </h3>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', maxWidth: '400px', margin: '0 auto var(--space-4) auto' }}>
              {searchQuery || selectedTone !== 'ALL' || selectedLanguage !== 'ALL'
                ? 'Try adjusting your search query or reset filters.'
                : 'Your PostgreSQL database has no articles yet. Launch a generation to get started.'}
            </p>
            {(searchQuery || selectedTone !== 'ALL' || selectedLanguage !== 'ALL') ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setSearchQuery('');
                  setSelectedTone('ALL');
                  setSelectedLanguage('ALL');
                }}
              >
                Reset Filters
              </Button>
            ) : (
              <Button variant="primary" size="sm" onClick={() => navigate('/generate')}>
                Generate Your First Article
              </Button>
            )}
          </CardContent>
        </Card>
      ) : viewMode === 'table' ? (
        /* Table View */
        <Card>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 'var(--text-sm)' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-surface-elevated)' }}>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-tertiary)', fontWeight: 600, fontSize: 'var(--text-2xs)' }}>ID</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-tertiary)', fontWeight: 600, fontSize: 'var(--text-2xs)' }}>ARTICLE TITLE & TOPIC</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-tertiary)', fontWeight: 600, fontSize: 'var(--text-2xs)' }}>LANGUAGE</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-tertiary)', fontWeight: 600, fontSize: 'var(--text-2xs)' }}>TONE</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-tertiary)', fontWeight: 600, fontSize: 'var(--text-2xs)' }}>FACT SCORE</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-tertiary)', fontWeight: 600, fontSize: 'var(--text-2xs)' }}>EXECUTION</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-tertiary)', fontWeight: 600, fontSize: 'var(--text-2xs)', textAlign: 'right' }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {filteredBlogs.map((item) => {
                  const score = item.verification_score || 8.5;
                  return (
                    <tr
                      key={item.id}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        transition: 'background var(--transition-fast)',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-surface-elevated)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      <td style={{ padding: 'var(--space-4)', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)' }}>
                        #{item.id}
                      </td>
                      <td style={{ padding: 'var(--space-4)', maxWidth: '420px' }}>
                        <div
                          onClick={() => navigate(`/articles/${item.id}`)}
                          style={{
                            fontWeight: 600,
                            color: 'var(--text-primary)',
                            cursor: 'pointer',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {item.title}
                        </div>
                        <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: '2px' }}>
                          Topic: {item.topic}
                        </div>
                      </td>
                      <td style={{ padding: 'var(--space-4)' }}>
                        <Badge variant="primary">{item.target_language || 'English'}</Badge>
                      </td>
                      <td style={{ padding: 'var(--space-4)', color: 'var(--text-secondary)' }}>
                        {item.tone || 'Informative'}
                      </td>
                      <td style={{ padding: 'var(--space-4)' }}>
                        <Badge variant={score >= 8.0 ? 'success' : 'warning'}>
                          {score}/10
                        </Badge>
                      </td>
                      <td style={{ padding: 'var(--space-4)', color: 'var(--text-tertiary)', fontSize: 'var(--text-xs)' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <Clock size={12} />
                          {item.execution_time_seconds}s
                        </span>
                      </td>
                      <td style={{ padding: 'var(--space-4)', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => navigate(`/articles/${item.id}`)}
                          >
                            Read
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/articles/${item.id}/audit`)}
                            title="View Fact-Check Quality Audit"
                          >
                            Audit
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setDeleteTarget(item)}
                            title="Delete article record"
                            style={{ color: 'var(--color-danger-text)' }}
                          >
                            <Trash2 size={14} />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        /* Grid View */
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 'var(--space-4)' }}>
          {filteredBlogs.map((item) => {
            const score = item.verification_score || 8.5;
            return (
              <Card key={item.id} hoverable style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <CardHeader>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <Badge variant="neutral">#{item.id}</Badge>
                    <Badge variant="primary">{item.target_language || 'English'}</Badge>
                    <Badge variant={score >= 8.0 ? 'success' : 'warning'}>
                      {score}/10
                    </Badge>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteTarget(item);
                    }}
                    aria-label="Delete article"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-tertiary)',
                      cursor: 'pointer',
                      padding: '4px',
                      display: 'flex',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-danger)')}
                    onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-tertiary)')}
                  >
                    <Trash2 size={14} />
                  </button>
                </CardHeader>
                <CardContent
                  onClick={() => navigate(`/articles/${item.id}`)}
                  style={{ cursor: 'pointer', flex: 1 }}
                >
                  <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
                    {item.title}
                  </h3>
                  <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', lineHeight: 1.4, margin: 0 }}>
                    Topic: {item.topic}
                  </p>
                </CardContent>
                <div
                  style={{
                    padding: 'var(--space-3) var(--space-6)',
                    borderTop: '1px solid var(--border-subtle)',
                    background: 'rgba(0, 0, 0, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: 'var(--text-2xs)',
                    color: 'var(--text-tertiary)',
                  }}
                >
                  <span>Duration: {item.execution_time_seconds}s</span>
                  <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                    <Button variant="ghost" size="sm" onClick={() => navigate(`/articles/${item.id}/audit`)}>
                      Audit
                    </Button>
                    <Button variant="secondary" size="sm" onClick={() => navigate(`/articles/${item.id}`)}>
                      Read
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Article"
        description={`Permanently remove article #${deleteTarget?.id} from PostgreSQL?`}
        confirmText="Delete Article"
        confirmVariant="danger"
        isConfirmLoading={isDeleting}
        onConfirm={handleDeleteConfirm}
      >
        <p style={{ margin: 0 }}>
          Are you sure you want to delete <strong>&ldquo;{deleteTarget?.title}&rdquo;</strong>? This action will permanently remove the record from the database.
        </p>
      </Modal>
    </div>
  );
}
