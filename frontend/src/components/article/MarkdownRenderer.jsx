import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Check, Copy, Link as LinkIcon } from 'lucide-react';

function slugify(text) {
  return String(text)
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function CodeBlock({ className, children, ...props }) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  const codeContent = String(children).replace(/\n$/, '');

  const handleCopy = () => {
    navigator.clipboard.writeText(codeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      style={{
        position: 'relative',
        margin: 'var(--space-6) 0',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--code-border)',
        background: 'var(--code-bg)',
        overflow: 'hidden',
      }}
    >
      {/* Code Header Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: 'var(--space-2) var(--space-4)',
          background: 'rgba(0, 0, 0, 0.04)',
          borderBottom: '1px solid var(--code-border)',
          fontSize: 'var(--text-2xs)',
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-tertiary)',
        }}
      >
        <span>{language ? language.toUpperCase() : 'CODE'}</span>
        <button
          type="button"
          onClick={handleCopy}
          aria-label="Copy code to clipboard"
          style={{
            background: 'transparent',
            border: 'none',
            color: copied ? 'var(--color-success)' : 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-1)',
            fontSize: 'var(--text-2xs)',
            padding: '2px var(--space-2)',
            borderRadius: 'var(--radius-xs)',
            transition: 'color var(--transition-fast)',
          }}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>

      {/* Code Body */}
      <pre style={{ margin: 0, padding: 'var(--space-4)', overflowX: 'auto', background: 'transparent' }}>
        <code className={className} style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', color: 'var(--text-primary)' }} {...props}>
          {children}
        </code>
      </pre>
    </div>
  );
}

function HeadingWithAnchor({ level: Level, children, onCopyHeadingLink, ...props }) {
  const [hovered, setHovered] = useState(false);
  const text = Array.isArray(children)
    ? children.map((c) => (typeof c === 'string' ? c : c?.props?.children || '')).join('')
    : String(children || '');
  const slug = slugify(text);

  const handleCopy = (e) => {
    e.preventDefault();
    const url = `${window.location.origin}${window.location.pathname}#${slug}`;
    navigator.clipboard.writeText(url);
    if (onCopyHeadingLink) onCopyHeadingLink(slug);
  };

  return (
    <Level
      id={slug}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{ position: 'relative', scrollMarginTop: '80px' }}
      {...props}
    >
      {children}
      {slug && (
        <a
          href={`#${slug}`}
          onClick={handleCopy}
          aria-label={`Copy link to ${text}`}
          title="Copy link to heading"
          className="no-print"
          style={{
            marginLeft: 'var(--space-2)',
            opacity: hovered ? 0.7 : 0,
            transition: 'opacity var(--transition-fast)',
            display: 'inline-flex',
            alignItems: 'center',
            verticalAlign: 'middle',
            color: 'var(--accent-primary)',
          }}
        >
          <LinkIcon size={16} />
        </a>
      )}
    </Level>
  );
}

export default function MarkdownRenderer({ content, className = '', onCopyHeadingLink }) {
  if (!content) return null;

  return (
    <div className={`article-reading-container ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1(props) {
            return <HeadingWithAnchor level="h1" onCopyHeadingLink={onCopyHeadingLink} {...props} />;
          },
          h2(props) {
            return <HeadingWithAnchor level="h2" onCopyHeadingLink={onCopyHeadingLink} {...props} />;
          },
          h3(props) {
            return <HeadingWithAnchor level="h3" onCopyHeadingLink={onCopyHeadingLink} {...props} />;
          },
          h4(props) {
            return <HeadingWithAnchor level="h4" onCopyHeadingLink={onCopyHeadingLink} {...props} />;
          },
          code({ node, inline, className, children, ...props }) {
            return !inline ? (
              <CodeBlock className={className} {...props}>
                {children}
              </CodeBlock>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          a({ node, href, children, ...props }) {
            return (
              <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                {children}
              </a>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
