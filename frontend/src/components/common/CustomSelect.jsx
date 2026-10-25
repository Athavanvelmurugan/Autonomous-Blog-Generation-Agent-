import React, { useState, useRef, useEffect, useId } from 'react';
import { ChevronDown, Check, Search } from 'lucide-react';

export default function CustomSelect({
  value,
  onChange,
  options = [],
  placeholder = 'Select option...',
  disabled = false,
  leftIcon: LeftIcon,
  searchable = false,
  style = {},
  className = '',
  menuWidth = '100%',
  align = 'left', // 'left' | 'right'
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const containerRef = useRef(null);
  const searchInputRef = useRef(null);
  const selectId = useId();

  // Find currently selected option object
  const selectedOption = options.find((opt) => opt.value === value) || null;

  // Filter options if searchable
  const filteredOptions = searchable && searchQuery.trim()
    ? options.filter((opt) =>
        opt.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (opt.sublabel && opt.sublabel.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : options;

  // Click outside listener
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  // Focus search input when menu opens
  useEffect(() => {
    if (isOpen && searchable && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen, searchable]);

  const handleSelect = (optVal) => {
    if (disabled) return;
    onChange(optVal);
    setIsOpen(false);
    setSearchQuery('');
  };

  return (
    <div
      ref={containerRef}
      className={`custom-select-container ${className}`}
      style={{ position: 'relative', width: '100%', ...style }}
    >
      {/* Trigger Button */}
      <button
        id={selectId}
        type="button"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        onClick={() => !disabled && setIsOpen((prev) => !prev)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--bg-input)',
          border: `1px solid ${isOpen ? 'var(--accent-primary)' : 'var(--border-default)'}`,
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-2) var(--space-3)',
          minHeight: '42px',
          color: 'var(--text-primary)',
          fontSize: 'var(--text-sm)',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.6 : 1,
          transition: 'border-color var(--transition-fast), box-shadow var(--transition-fast)',
          boxShadow: isOpen ? '0 0 0 2px var(--accent-primary-subtle)' : 'none',
          outline: 'none',
          gap: 'var(--space-2)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', minWidth: 0, flex: 1, textAlign: 'left' }}>
          {LeftIcon && (
            <LeftIcon
              size={16}
              style={{
                color: isOpen ? 'var(--accent-primary-text)' : 'var(--text-secondary)',
                flexShrink: 0,
                transition: 'color var(--transition-fast)',
              }}
            />
          )}
          {selectedOption ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', minWidth: 0 }}>
              {selectedOption.icon && <span style={{ flexShrink: 0 }}>{selectedOption.icon}</span>}
              <span style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {selectedOption.label}
              </span>
              {selectedOption.badge && (
                <span
                  style={{
                    fontSize: 'var(--text-2xs)',
                    padding: '1px 6px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--accent-primary-subtle)',
                    color: 'var(--accent-primary-text)',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {selectedOption.badge}
                </span>
              )}
            </div>
          ) : (
            <span style={{ color: 'var(--text-tertiary)' }}>{placeholder}</span>
          )}
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

      {/* Floating Dropdown Popover */}
      {isOpen && (
        <div
          role="listbox"
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            [align === 'right' ? 'right' : 'left']: 0,
            width: menuWidth,
            minWidth: '220px',
            maxWidth: '100vw',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-dropdown)',
            zIndex: 100,
            overflow: 'hidden',
            animation: 'fadeIn var(--transition-fast) ease-out forwards',
          }}
        >
          {/* Search Header if enabled */}
          {searchable && (
            <div
              style={{
                padding: 'var(--space-2) var(--space-3)',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-2)',
                background: 'var(--bg-surface-elevated)',
              }}
            >
              <Search size={14} color="var(--text-tertiary)" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search languages..."
                style={{
                  width: '100%',
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-primary)',
                  padding: '2px 0',
                }}
              />
            </div>
          )}

          {/* Options List */}
          <div style={{ maxHeight: '240px', overflowY: 'auto', padding: '4px' }}>
            {filteredOptions.length === 0 ? (
              <div
                style={{
                  padding: 'var(--space-3)',
                  textAlign: 'center',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-tertiary)',
                }}
              >
                No matching options found
              </div>
            ) : (
              filteredOptions.map((opt) => {
                const isSelected = opt.value === value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    disabled={opt.disabled}
                    onClick={() => handleSelect(opt.value)}
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: 'var(--space-2) var(--space-3)',
                      borderRadius: 'var(--radius-md)',
                      border: 'none',
                      background: isSelected ? 'var(--accent-primary-subtle)' : 'transparent',
                      color: isSelected ? 'var(--accent-primary-text)' : 'var(--text-primary)',
                      fontSize: 'var(--text-sm)',
                      cursor: opt.disabled ? 'not-allowed' : 'pointer',
                      textAlign: 'left',
                      transition: 'background var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected && !opt.disabled) {
                        e.currentTarget.style.background = 'var(--bg-surface-hover)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected && !opt.disabled) {
                        e.currentTarget.style.background = 'transparent';
                      }
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', minWidth: 0 }}>
                      {opt.icon && <span style={{ flexShrink: 0 }}>{opt.icon}</span>}
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: isSelected ? 600 : 400, display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {opt.label}
                          </span>
                          {opt.badge && (
                            <span
                              style={{
                                fontSize: 'var(--text-2xs)',
                                padding: '1px 6px',
                                borderRadius: 'var(--radius-sm)',
                                background: isSelected ? 'var(--accent-primary)' : 'var(--bg-surface-elevated)',
                                color: isSelected ? '#ffffff' : 'var(--text-tertiary)',
                                fontWeight: 500,
                              }}
                            >
                              {opt.badge}
                            </span>
                          )}
                        </div>
                        {opt.sublabel && (
                          <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', marginTop: '2px' }}>
                            {opt.sublabel}
                          </div>
                        )}
                      </div>
                    </div>

                    {isSelected && (
                      <Check size={14} color="var(--accent-primary-text)" style={{ flexShrink: 0, marginLeft: 'var(--space-2)' }} />
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
