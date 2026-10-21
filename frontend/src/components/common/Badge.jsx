import React from 'react';

export default function Badge({
  children,
  variant = 'neutral', // 'neutral' | 'success' | 'warning' | 'danger' | 'info' | 'primary'
  size = 'sm', // 'sm' | 'md'
  icon: Icon,
  style = {},
  ...props
}) {
  const sizeStyles = {
    sm: {
      fontSize: 'var(--text-2xs)',
      padding: '2px var(--space-2)',
      borderRadius: 'var(--radius-sm)',
      gap: 'var(--space-1)',
    },
    md: {
      fontSize: 'var(--text-xs)',
      padding: 'var(--space-1) var(--space-3)',
      borderRadius: 'var(--radius-md)',
      gap: 'var(--space-1)',
    },
  }[size] || {};

  const variantStyles = {
    neutral: {
      background: 'var(--bg-surface-elevated)',
      border: '1px solid var(--border-default)',
      color: 'var(--text-secondary)',
    },
    primary: {
      background: 'var(--accent-primary-subtle)',
      border: '1px solid var(--accent-primary-border)',
      color: 'var(--accent-primary-text)',
    },
    success: {
      background: 'var(--color-success-bg)',
      border: '1px solid var(--color-success-border)',
      color: 'var(--color-success-text)',
    },
    warning: {
      background: 'var(--color-warning-bg)',
      border: '1px solid var(--color-warning-border)',
      color: 'var(--color-warning-text)',
    },
    danger: {
      background: 'var(--color-danger-bg)',
      border: '1px solid var(--color-danger-border)',
      color: 'var(--color-danger-text)',
    },
    info: {
      background: 'var(--color-info-bg)',
      border: '1px solid var(--color-info-border)',
      color: 'var(--color-info-text)',
    },
  }[variant] || {};

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        fontWeight: 600,
        lineHeight: 1.2,
        letterSpacing: '0.01em',
        userSelect: 'none',
        ...sizeStyles,
        ...variantStyles,
        ...style,
      }}
      {...props}
    >
      {Icon && <Icon size={size === 'sm' ? 11 : 13} />}
      <span>{children}</span>
    </span>
  );
}
