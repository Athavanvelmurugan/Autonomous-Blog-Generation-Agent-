import React, { useState, useRef, useEffect } from 'react';
import { FileText, ChevronDown, Check, Sliders, Minus, Plus, Sparkles } from 'lucide-react';

const PRESETS = [
  { id: 600, label: 'Short Overview', words: 600, estRead: '3-4 min read', desc: 'Concise summary with core definitions and takeaways' },
  { id: 1200, label: 'Standard Guide', words: 1200, estRead: '6-7 min read', desc: 'Balanced educational article with fundamentals & illustrations' },
  { id: 1600, label: 'Detailed Educational Article', words: 1600, estRead: '8-10 min read', desc: 'Comprehensive tutorial with code breakdown, comparison tables & FAQs', popular: true },
  { id: 2400, label: 'Comprehensive Masterclass', words: 2400, estRead: '12-15 min read', desc: 'Authoritative deep-dive with end-to-end architecture & edge cases' },
];

const QUICK_CHIPS = [600, 1000, 1200, 1600, 2000, 2400];

export default function LengthDropdown({
  value,
  onChange,
  disabled = false,
  className = '',
  style = {},
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [showCustomBox, setShowCustomBox] = useState(false);
  const containerRef = useRef(null);
  const customInputRef = useRef(null);

  const numericValue = Number(value) || 1600;
  const isMatchingPreset = PRESETS.some((p) => p.words === numericValue);
  const activePreset = PRESETS.find((p) => p.words === numericValue);

  // If initial value is custom, expand custom controls inside the popover
  useEffect(() => {
    if (!isMatchingPreset) {
      setShowCustomBox(true);
    }
  }, [isMatchingPreset]);

  // Click outside and escape handler
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleSelectPreset = (words) => {
    onChange(words);
    setShowCustomBox(false);
    setIsOpen(false);
  };

  const handleStep = (delta) => {
    const nextVal = Math.max(300, Math.min(4000, numericValue + delta));
    onChange(nextVal);
  };

  const estMins = Math.max(1, Math.ceil(numericValue / 200));

  return (
    <div
      ref={containerRef}
      className={`length-dropdown-container ${className}`}
      style={{ position: 'relative', width: '100%', ...style }}
    >
      {/* Trigger Button */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => !disabled && setIsOpen((prev) => !prev)}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--bg-input)',
          border: `1px solid ${isOpen ? 'var(--accent-primary)' : 'var(--border-default)'}`,
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-2) var(--space-3)',
          minHeight: '44px',
          color: 'var(--text-primary)',
          fontSize: 'var(--text-sm)',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.6 : 1,
          transition: 'all var(--transition-fast)',
          boxShadow: isOpen ? '0 0 0 2px var(--accent-primary-subtle)' : 'none',
          gap: 'var(--space-2)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', minWidth: 0 }}>
          <FileText size={16} color="var(--accent-primary-text)" style={{ flexShrink: 0 }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', minWidth: 0, flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 600 }}>
              {activePreset ? activePreset.label : `Custom (${numericValue.toLocaleString()} words)`}
            </span>
            <span
              style={{
                fontSize: 'var(--text-2xs)',
                padding: '1px 6px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--accent-primary-subtle)',
                color: 'var(--accent-primary-text)',
                fontWeight: 600,
                border: '1px solid var(--accent-primary-border)',
              }}
            >
              ~{numericValue.toLocaleString()} words • {estMins} min read
            </span>
          </div>
        </div>

        <ChevronDown
          size={16}
          style={{
            color: 'var(--text-tertiary)',
            flexShrink: 0,
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform var(--transition-fast)',
          }}
        />
      </button>

      {/* Popover Floating Menu */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            left: 0,
            right: 0,
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-dropdown)',
            zIndex: 110,
            overflow: 'hidden',
            animation: 'fadeIn var(--transition-fast) ease-out forwards',
            minWidth: '310px',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: 'var(--space-2) var(--space-4)',
              background: 'var(--bg-surface-elevated)',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{ fontSize: 'var(--text-2xs)', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Target Article Length
            </span>
            <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--accent-primary-text)', fontWeight: 500 }}>
              {numericValue.toLocaleString()} words
            </span>
          </div>

          {/* Preset List */}
          <div style={{ padding: 'var(--space-2)' }}>
            {PRESETS.map((p) => {
              const isSelected = numericValue === p.words;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleSelectPreset(p.words)}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    padding: 'var(--space-2) var(--space-3)',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${isSelected ? 'var(--accent-primary)' : 'transparent'}`,
                    background: isSelected ? 'var(--accent-primary-subtle)' : 'transparent',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all var(--transition-fast)',
                    marginBottom: '2px',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'var(--bg-surface-hover)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <div style={{ minWidth: 0, paddingRight: 'var(--space-2)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: '2px' }}>
                      <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: isSelected ? 'var(--accent-primary-text)' : 'var(--text-primary)' }}>
                        {p.label}
                      </span>
                      <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', fontWeight: 500 }}>
                        ({p.words}w • {p.estRead})
                      </span>
                      {p.popular && (
                        <span
                          style={{
                            fontSize: '9px',
                            padding: '1px 5px',
                            borderRadius: 'var(--radius-full)',
                            background: 'var(--accent-primary-border)',
                            color: 'var(--accent-primary-text)',
                            fontWeight: 700,
                            textTransform: 'uppercase',
                          }}
                        >
                          Default
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', lineHeight: 1.3 }}>
                      {p.desc}
                    </div>
                  </div>

                  {isSelected && (
                    <Check size={16} color="var(--accent-primary-text)" style={{ flexShrink: 0, marginTop: '2px' }} />
                  )}
                </button>
              );
            })}
          </div>

          {/* Divider */}
          <div style={{ borderTop: '1px solid var(--border-subtle)' }} />

          {/* Custom Word Count Section */}
          <div style={{ padding: 'var(--space-3)', background: 'var(--bg-surface-elevated)' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: showCustomBox ? 'var(--space-3)' : 0,
              }}
            >
              <button
                type="button"
                onClick={() => setShowCustomBox((prev) => !prev)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  padding: 0,
                  fontSize: 'var(--text-xs)',
                  fontWeight: 600,
                  color: !isMatchingPreset || showCustomBox ? 'var(--accent-primary-text)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-1)',
                }}
              >
                <Sliders size={13} />
                <span>Custom Word Count & Stepper</span>
              </button>

              <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)' }}>
                Range: 300 - 4,000w
              </span>
            </div>

            {showCustomBox && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', paddingTop: 'var(--space-1)' }}>
                {/* Stepper + Direct Input */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
                    <button
                      type="button"
                      onClick={() => handleStep(-50)}
                      disabled={numericValue <= 300}
                      title="Decrease 50 words"
                      style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-default)',
                        background: 'var(--bg-input)',
                        color: 'var(--text-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: numericValue <= 300 ? 'not-allowed' : 'pointer',
                        opacity: numericValue <= 300 ? 0.4 : 1,
                      }}
                    >
                      <Minus size={13} />
                    </button>

                    <input
                      ref={customInputRef}
                      type="number"
                      min={300}
                      max={4000}
                      step={25}
                      value={value || ''}
                      onChange={(e) => {
                        const val = e.target.value;
                        if (val === '') {
                          onChange('');
                        } else {
                          const parsed = parseInt(val, 10);
                          if (!isNaN(parsed)) onChange(Math.max(100, Math.min(5000, parsed)));
                        }
                      }}
                      onBlur={() => {
                        const n = Number(value);
                        if (!n || n < 300) onChange(300);
                        else if (n > 4000) onChange(4000);
                      }}
                      style={{
                        width: '84px',
                        height: '28px',
                        textAlign: 'center',
                        background: 'var(--bg-input)',
                        border: '1px solid var(--border-default)',
                        borderRadius: 'var(--radius-sm)',
                        color: 'var(--text-primary)',
                        fontSize: 'var(--text-xs)',
                        fontWeight: 600,
                        outline: 'none',
                      }}
                    />

                    <button
                      type="button"
                      onClick={() => handleStep(50)}
                      disabled={numericValue >= 4000}
                      title="Increase 50 words"
                      style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-default)',
                        background: 'var(--bg-input)',
                        color: 'var(--text-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: numericValue >= 4000 ? 'not-allowed' : 'pointer',
                        opacity: numericValue >= 4000 ? 0.4 : 1,
                      }}
                    >
                      <Plus size={13} />
                    </button>
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginLeft: '4px' }}>
                      words
                    </span>
                  </div>

                  <span
                    style={{
                      fontSize: 'var(--text-2xs)',
                      color: 'var(--text-tertiary)',
                      background: 'var(--bg-surface)',
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-xs)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    ~{estMins} min read
                  </span>
                </div>

                {/* Range Slider */}
                <input
                  type="range"
                  min={300}
                  max={4000}
                  step={25}
                  value={numericValue}
                  onChange={(e) => onChange(Number(e.target.value))}
                  style={{
                    width: '100%',
                    accentColor: 'var(--accent-primary)',
                    cursor: 'pointer',
                  }}
                />

                {/* Quick Chips */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', marginRight: '2px' }}>
                    Jump to:
                  </span>
                  {QUICK_CHIPS.map((chip) => (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => onChange(chip)}
                      style={{
                        background: numericValue === chip ? 'var(--accent-primary)' : 'var(--bg-input)',
                        color: numericValue === chip ? '#ffffff' : 'var(--text-secondary)',
                        border: `1px solid ${numericValue === chip ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                        borderRadius: 'var(--radius-xs)',
                        padding: '1px 6px',
                        fontSize: '10px',
                        fontWeight: numericValue === chip ? 600 : 400,
                        cursor: 'pointer',
                        transition: 'all var(--transition-fast)',
                      }}
                    >
                      {chip}w
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
