/**
 * Toast Notification System
 *
 * A lightweight, customizable toast notification system for MindTrack
 */

class ToastNotification {
  constructor(options = {}) {
    this.container = null;
    this.defaultOptions = {
      duration: 5000, // 5 seconds
      position: 'top-right', // top-right, top-left, bottom-right, bottom-left, top-center, bottom-center
      theme: 'light', // light, dark, colored
      animation: null, // slide-right, slide-left, slide-up, slide-down, fade, bounce
      dismissible: true,
      sound: false, // true, false, or URL to sound file
      maxToasts: 5, // Maximum number of toasts to show at once
      stackingBehavior: 'stack', // stack or replace
    };
    this.options = { ...this.defaultOptions, ...options };
    this.toasts = [];
    this.soundEffects = {
      success: '/static/sounds/success.mp3',
      error: '/static/sounds/error.mp3',
      warning: '/static/sounds/warning.mp3',
      info: '/static/sounds/info.mp3',
    };
    this.initialize();
  }

  /**
   * Initialize the toast container
   */
  initialize() {
    // Create container if it doesn't exist
    if (!document.querySelector('.toast-container')) {
      this.container = document.createElement('div');
      this.container.className = `toast-container ${this.options.position}`;

      // Add theme class if specified
      if (this.options.theme) {
        this.container.classList.add(`toast-theme-${this.options.theme}`);
      }

      // Add animation class if specified
      if (this.options.animation) {
        this.container.classList.add(`toast-animation-${this.options.animation}`);
      }

      document.body.appendChild(this.container);
    } else {
      this.container = document.querySelector('.toast-container');

      // Update container classes
      this.container.className = 'toast-container';
      this.container.classList.add(this.options.position);

      if (this.options.theme) {
        this.container.classList.add(`toast-theme-${this.options.theme}`);
      }

      if (this.options.animation) {
        this.container.classList.add(`toast-animation-${this.options.animation}`);
      }
    }
  }

  /**
   * Update toast options
   *
   * @param {Object} options - New options
   */
  updateOptions(options) {
    this.options = { ...this.options, ...options };
    this.initialize(); // Reinitialize with new options
  }

  /**
   * Play a sound effect
   *
   * @param {string} type - Toast type
   */
  playSound(type) {
    if (!this.options.sound) return;

    let soundUrl = '';

    if (typeof this.options.sound === 'string') {
      // Custom sound URL
      soundUrl = this.options.sound;
    } else if (this.options.sound === true) {
      // Default sound based on type
      soundUrl = this.soundEffects[type] || this.soundEffects.info;
    }

    if (soundUrl) {
      const audio = new Audio(soundUrl);
      audio.volume = 0.5;
      audio.play().catch(e => console.warn('Could not play toast sound:', e));
    }
  }

  /**
   * Show a toast notification
   *
   * @param {Object} options - Toast options
   * @param {string} options.type - Toast type (success, error, warning, info)
   * @param {string} options.title - Toast title
   * @param {string} options.message - Toast message
   * @param {number} options.duration - Duration in milliseconds
   * @param {boolean} options.dismissible - Whether the toast can be dismissed
   * @param {string} options.position - Position of the toast
   * @param {string} options.theme - Theme of the toast
   * @param {string} options.animation - Animation of the toast
   * @param {boolean|string} options.sound - Whether to play a sound
   */
  show(options) {
    const {
      type = 'info',
      title = '',
      message = '',
      duration = this.options.duration,
      dismissible = this.options.dismissible,
      position = this.options.position,
      theme = this.options.theme,
      animation = this.options.animation,
      sound = this.options.sound,
    } = options;

    // Check if we need to update container position or theme
    if (position !== this.options.position || theme !== this.options.theme || animation !== this.options.animation) {
      this.updateOptions({ position, theme, animation });
    }

    // Handle stacking behavior
    if (this.options.stackingBehavior === 'replace' && this.toasts.length >= this.options.maxToasts) {
      // Remove the oldest toast
      this.dismiss(this.toasts[0]);
    } else if (this.toasts.length >= this.options.maxToasts) {
      // Remove the oldest toast when we reach the maximum
      this.dismiss(this.toasts[0]);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    // Set icon based on type
    let iconClass = '';
    switch (type) {
      case 'success':
        iconClass = 'fa-check-circle';
        break;
      case 'error':
        iconClass = 'fa-exclamation-circle';
        break;
      case 'warning':
        iconClass = 'fa-exclamation-triangle';
        break;
      case 'info':
      default:
        iconClass = 'fa-info-circle';
        break;
    }

    // Create toast content
    toast.innerHTML = `
      <div class="toast-icon">
        <i class="fas ${iconClass}"></i>
      </div>
      <div class="toast-content">
        ${title ? `<div class="toast-title">${title}</div>` : ''}
        <div class="toast-message">${message}</div>
      </div>
      ${dismissible ? `
        <div class="toast-close" aria-label="Close">
          <i class="fas fa-times"></i>
        </div>
      ` : ''}
      <div class="toast-progress" style="animation-duration: ${duration}ms;"></div>
    `;

    // Add to container
    this.container.appendChild(toast);

    // Add to toasts array
    this.toasts.push(toast);

    // Play sound if enabled
    if (sound) {
      this.playSound(type);
    }

    // Show toast with animation
    setTimeout(() => {
      toast.classList.add('show');
    }, 10);

    // Set up close button
    if (dismissible) {
      const closeButton = toast.querySelector('.toast-close');
      closeButton.addEventListener('click', () => {
        this.dismiss(toast);
      });
    }

    // Auto dismiss after duration
    if (duration > 0) {
      setTimeout(() => {
        this.dismiss(toast);
      }, duration);
    }

    return toast;
  }

  /**
   * Dismiss a toast notification
   *
   * @param {HTMLElement} toast - Toast element to dismiss
   */
  dismiss(toast) {
    toast.classList.remove('show');

    // Remove from toasts array
    const index = this.toasts.indexOf(toast);
    if (index > -1) {
      this.toasts.splice(index, 1);
    }

    // Remove from DOM after animation
    setTimeout(() => {
      if (toast.parentNode === this.container) {
        this.container.removeChild(toast);
      }
    }, 300);
  }

  /**
   * Show a success toast
   *
   * @param {string} message - Toast message
   * @param {string} title - Toast title
   * @param {Object} options - Additional options
   */
  success(message, title = 'Success', options = {}) {
    return this.show({
      type: 'success',
      title,
      message,
      ...options
    });
  }

  /**
   * Show an error toast
   *
   * @param {string} message - Toast message
   * @param {string} title - Toast title
   * @param {Object} options - Additional options
   */
  error(message, title = 'Error', options = {}) {
    return this.show({
      type: 'error',
      title,
      message,
      ...options
    });
  }

  /**
   * Show a warning toast
   *
   * @param {string} message - Toast message
   * @param {string} title - Toast title
   * @param {Object} options - Additional options
   */
  warning(message, title = 'Warning', options = {}) {
    return this.show({
      type: 'warning',
      title,
      message,
      ...options
    });
  }

  /**
   * Show an info toast
   *
   * @param {string} message - Toast message
   * @param {string} title - Toast title
   * @param {Object} options - Additional options
   */
  info(message, title = 'Information', options = {}) {
    return this.show({
      type: 'info',
      title,
      message,
      ...options
    });
  }

  /**
   * Clear all toasts
   */
  clearAll() {
    // Create a copy of the toasts array to avoid modification during iteration
    const toastsCopy = [...this.toasts];
    toastsCopy.forEach(toast => {
      this.dismiss(toast);
    });
  }
}

// Create global toast instance
const toast = new ToastNotification();

// Handle Django messages
document.addEventListener('DOMContentLoaded', function() {
  // Check for Django messages
  const djangoMessages = document.querySelectorAll('.django-message');

  djangoMessages.forEach(message => {
    const type = message.dataset.type || 'info';
    const text = message.textContent.trim();

    // Map Django message tags to toast types
    const typeMap = {
      'debug': 'info',
      'info': 'info',
      'success': 'success',
      'warning': 'warning',
      'error': 'error'
    };

    // Show toast
    toast.show({
      type: typeMap[type] || 'info',
      message: text
    });

    // Remove the original message
    message.remove();
  });
});
