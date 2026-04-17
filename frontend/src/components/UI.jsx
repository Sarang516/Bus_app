import React from 'react';

// Spinner component - shows loading indicator
export const Spinner = ({ size = 'medium' }) => {
  const sizeClass = {
    small: 'spinner-small',
    medium: 'spinner-medium',
    large: 'spinner-large',
  }[size] || 'spinner-medium';

  return <div className={`spinner ${sizeClass}`} />;
};

// Alert component - shows error/success/info messages
export const Alert = ({ type = 'info', title, message, onClose, children }) => {
  const alertClass = `alert alert-${type}`;
  const body = message || children;

  return (
    <div className={alertClass} role="alert">
      <div className="alert-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span>{title && <strong>{title} </strong>}{body}</span>
        {onClose && (
          <button className="alert-close" onClick={onClose}>
            ×
          </button>
        )}
      </div>
    </div>
  );
};

// Button component
export const Button = ({
  children,
  onClick,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  type = 'button',
  className = '',
}) => {
  const btnClass = `btn btn-${variant} btn-${size} ${className}`;
  return (
    <button
      type={type}
      className={btnClass}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

// Card component - container with styling
export const Card = ({
  children,
  title,
  subtitle,
  footer,
  className = '',
}) => {
  return (
    <div className={`card ${className}`}>
      {(title || subtitle) && (
        <div className="card-header">
          {title && <h3 className="card-title">{title}</h3>}
          {subtitle && <p className="card-subtitle">{subtitle}</p>}
        </div>
      )}
      <div className="card-body">{children}</div>
      {footer && <div className="card-footer">{footer}</div>}
    </div>
  );
};

// Badge component - small label/tag
export const Badge = ({ children, variant = 'default', className = '' }) => {
  const badgeClass = `badge badge-${variant} ${className}`;
  return <span className={badgeClass}>{children}</span>;
};

// StatusBadge component - semantic status indicator
export const StatusBadge = ({ status, label }) => {
  const statusMap = {
    '0001': { label: 'Draft', variant: 'secondary' },
    '0002': { label: 'Submitted', variant: 'info' },
    '0003': { label: 'Approved', variant: 'success' },
    '0004': { label: 'Rejected', variant: 'danger' },
    '0005': { label: 'Vehicle Allotted', variant: 'primary' },
    '0006': { label: 'Withdrawn', variant: 'warning' },
  };

  const config = statusMap[status] || { label: label || status, variant: 'default' };

  return <Badge variant={config.variant}>{config.label}</Badge>;
};

// Modal component - dialog/popup
export const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'medium',
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className={`modal modal-${size}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 className="modal-title">{title}</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
};

// ConfirmModal component - confirmation dialog
export const ConfirmModal = ({
  isOpen,
  onConfirm,
  onCancel,
  title = 'Confirm',
  message = 'Are you sure?',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isDangerous = false,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onCancel} title={title}>
      <p>{message}</p>
      <div className="modal-footer">
        <Button onClick={onCancel} variant="secondary">
          {cancelText}
        </Button>
        <Button
          onClick={onConfirm}
          variant={isDangerous ? 'danger' : 'primary'}
        >
          {confirmText}
        </Button>
      </div>
    </Modal>
  );
};

// FormGroup component - label + input wrapper
export const FormGroup = ({
  label,
  error,
  required = false,
  children,
  className = '',
}) => {
  return (
    <div className={`form-group ${error ? 'has-error' : ''} ${className}`}>
      {label && (
        <label className="form-label">
          {label}
          {required && <span className="text-danger">*</span>}
        </label>
      )}
      {children}
      {error && <span className="form-error">{error}</span>}
    </div>
  );
};

// Input component
export const Input = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  error,
  required = false,
  disabled = false,
  name,
  className = '',
}) => {
  const inputClass = `form-input ${error ? 'is-invalid' : ''} ${className}`;
  return (
    <input
      type={type}
      name={name}
      className={inputClass}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      required={required}
      disabled={disabled}
    />
  );
};

// Select component
export const Select = ({
  options = [],
  value,
  onChange,
  placeholder = 'Select...',
  error,
  disabled = false,
  className = '',
}) => {
  return (
    <select
      className={`form-select ${error ? 'is-invalid' : ''} ${className}`}
      value={value}
      onChange={onChange}
      disabled={disabled}
    >
      <option value="">{placeholder}</option>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
};

// Table component
export const Table = ({
  columns,
  rows,
  isLoading = false,
  onRowClick,
  className = '',
}) => {
  if (isLoading) {
    return (
      <div className="table-loading">
        <Spinner />
      </div>
    );
  }

  if (!rows || rows.length === 0) {
    return <EmptyState message="No data available" />;
  }

  return (
    <table className={`table ${className}`}>
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={col.key} className={col.className}>
              {col.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, idx) => (
          <tr
            key={idx}
            onClick={() => onRowClick && onRowClick(row)}
            className={onRowClick ? 'cursor-pointer' : ''}
          >
            {columns.map((col) => (
              <td key={col.key} className={col.className}>
                {col.render ? col.render(row[col.key], row) : row[col.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

// EmptyState component - shown when no data
export const EmptyState = ({
  icon = '📭',
  title = 'No Data',
  message = 'Nothing to show here',
  action,
  className = '',
}) => {
  return (
    <div className={`empty-state ${className}`}>
      <div className="empty-state-icon">{icon}</div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-message">{message}</p>
      {action && <div className="empty-state-action">{action}</div>}
    </div>
  );
};

// TextArea component
export const TextArea = ({
  placeholder,
  value,
  onChange,
  rows = 4,
  error,
  disabled = false,
  className = '',
}) => {
  return (
    <textarea
      className={`form-textarea ${error ? 'is-invalid' : ''} ${className}`}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      rows={rows}
      disabled={disabled}
    />
  );
};

// Loading overlay
export const LoadingOverlay = ({ isVisible = false }) => {
  if (!isVisible) return null;
  return (
    <div className="loading-overlay">
      <Spinner />
    </div>
  );
};
