import React from 'react';
import { Loader2 } from 'lucide-react';

export default function Button({
  children,
  variant = 'primary', // 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size = 'md', // 'sm' | 'md' | 'lg'
  isLoading = false,
  disabled = false,
  leftIcon: LeftIcon,
  rightIcon: RightIcon,
  type = 'button',
  onClick,
  style = {},
  className = '',
  ...props
}) {
  // Size-specific styles
  const sizeStyles = {
    sm: {
      padding: 'var(--space-1) var(--space-3)',
      fontSize: 'var(--text-xs)',
      height: '30px',
      gap: 'var(--space-1)',
    },
    md: {
      padding: 'var(--space-2) var(--space-4)',
      fontSize: 'var(--text-sm)',
      height: '38px',
      gap: 'var(--space-2)',
    },
    lg: {
      padding: 'var(--space-3) var(--space-6)',
      fontSize: 'var(--text-base)',
      height: '46px',
      gap: 'var(--space-3)',
    },
  }[size] || {};

  // Variant styles
  const variantStyles = {
    primary: {
      background: 'var(--accent-primary)',
      color: '#ffffff',
      border: '1px solid transparent',
      boxShadow: 'var(--shadow-sm)',
    },
    secondary: {
      background: 'var(--bg-surface-elevated)',
      color: 'var(--text-primary)',
      border: '1px solid var(--border-default)',
    },
    outline: {
      background: 'transparent',
      color: 'var(--text-primary)',
      border: '1px solid var(--border-default)',
    },
    ghost: {
      background: 'transparent',
      color: 'var(--text-secondary)',
      border: '1px solid transparent',
    },
    danger: {
      background: 'var(--color-danger)',
      color: '#ffffff',
      border: '1px solid transparent',
    },
  }[variant] || {};

  const isDisabled = disabled || isLoading;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 500,
        borderRadius: 'var(--radius-md)',
        cursor: isDisabled ? 'not-allowed' : 'pointer',
        opacity: isDisabled ? 0.6 : 1,
        transition: 'all var(--transition-fast)',
        userSelect: 'none',
        whiteSpace: 'nowrap',
        ...sizeStyles,
        ...variantStyles,
        ...style,
      }}
      onMouseEnter={(e) => {
        if (isDisabled) return;
        if (variant === 'primary') e.currentTarget.style.background = 'var(--accent-primary-hover)';
        if (variant === 'secondary') e.currentTarget.style.background = 'var(--bg-surface-hover)';
        if (variant === 'outline') {
          e.currentTarget.style.background = 'var(--bg-surface-hover)';
          e.currentTarget.style.borderColor = 'var(--border-hover)';
        }
        if (variant === 'ghost') {
          e.currentTarget.style.background = 'var(--bg-surface-hover)';
          e.currentTarget.style.color = 'var(--text-primary)';
        }
        if (variant === 'danger') e.currentTarget.style.filter = 'brightness(0.9)';
      }}
      onMouseLeave={(e) => {
        if (isDisabled) return;
        if (variant === 'primary') e.currentTarget.style.background = 'var(--accent-primary)';
        if (variant === 'secondary') e.currentTarget.style.background = 'var(--bg-surface-elevated)';
        if (variant === 'outline') {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.borderColor = 'var(--border-default)';
        }
        if (variant === 'ghost') {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.color = 'var(--text-secondary)';
        }
        if (variant === 'danger') e.currentTarget.style.filter = 'none';
      }}
      {...props}
    >
      {isLoading ? (
        <Loader2 size={size === 'sm' ? 14 : 16} style={{ animation: 'spin 1s linear infinite' }} />
      ) : (
        LeftIcon && <LeftIcon size={size === 'sm' ? 14 : 16} />
      )}
      <span>{children}</span>
      {!isLoading && RightIcon && <RightIcon size={size === 'sm' ? 14 : 16} />}
    </button>
  );
}
