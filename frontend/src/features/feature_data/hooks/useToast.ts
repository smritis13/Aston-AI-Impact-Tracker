import { useCallback } from 'react';
import '../styles/toast.css';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastOptions {
  title?: string;
  message: string;
  type?: ToastType;
  position?: 'top-left' | 'top-center' | 'top-right' | 'middle-left' | 'middle-center' | 'middle-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
  duration?: number;
}

export const useToast = () => {
  const showToast = useCallback((options: ToastOptions) => {
    const {
      title = 'Notification',
      message,
      type = 'info',
      position = 'bottom-right',
      duration = 3000
    } = options;

    // Create toast container if it doesn't exist
    let container = document.querySelector(`.toast-container.position-fixed.${position}`);
    if (!container) {
      container = document.createElement('div');
      container.className = `toast-container position-fixed ${position} p-3`;
      document.body.appendChild(container);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast colored-toast bg-${type}-transparent text-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    // Create toast header
    const header = document.createElement('div');
    header.className = `toast-header bg-${type} text-fixed-white`;

    const titleElement = document.createElement('strong');
    titleElement.className = 'me-auto';
    titleElement.textContent = title;

    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn-close';
    closeButton.setAttribute('data-bs-dismiss', 'toast');
    closeButton.setAttribute('aria-label', 'Close');

    header.appendChild(titleElement);
    header.appendChild(closeButton);

    // Create toast body
    const body = document.createElement('div');
    body.className = 'toast-body';
    body.textContent = message;

    // Assemble toast
    toast.appendChild(header);
    toast.appendChild(body);
    container.appendChild(toast);

    // Initialize Bootstrap toast
    const bsToast = new (window as any).bootstrap.Toast(toast, {
      autohide: true,
      delay: duration
    });

    // Show toast
    bsToast.show();

    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
      toast.remove();
    });
  }, []);

  return { showToast };
}; 