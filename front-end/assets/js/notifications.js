// Notification system
const Notifications = {
    // Container for notifications
    container: null,

    // Initialize notification system
    init() {
        this.createContainer();
        this.initializeWebSocket();
    },

    // Create notification container
    createContainer() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(this.container);
        }
    },

    // Show notification
    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            padding: 15px 20px;
            border-radius: 4px;
            margin-bottom: 10px;
            min-width: 300px;
            max-width: 500px;
            animation: slideIn 0.3s ease-out;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        `;

        // Set background color based on type
        switch (type) {
            case 'success':
                notification.style.backgroundColor = '#4caf50';
                notification.style.color = 'white';
                break;
            case 'error':
                notification.style.backgroundColor = '#f44336';
                notification.style.color = 'white';
                break;
            case 'warning':
                notification.style.backgroundColor = '#ff9800';
                notification.style.color = 'white';
                break;
            default:
                notification.style.backgroundColor = '#2196f3';
                notification.style.color = 'white';
        }

        // Create message container
        const messageDiv = document.createElement('div');
        messageDiv.textContent = message;
        notification.appendChild(messageDiv);

        // Create close button
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '&times;';
        closeButton.style.cssText = `
            background: none;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            padding: 0 5px;
            margin-left: 10px;
        `;
        closeButton.onclick = () => this.remove(notification);
        notification.appendChild(closeButton);

        // Add to container
        this.container.appendChild(notification);

        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => this.remove(notification), duration);
        }

        return notification;
    },

    // Remove notification
    remove(notification) {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (notification.parentElement === this.container) {
                this.container.removeChild(notification);
            }
        }, 300);
    },

    // Success notification
    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    },

    // Error notification
    error(message, duration = 7000) {
        return this.show(message, 'error', duration);
    },

    // Warning notification
    warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    },

    // Info notification
    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    },

    // Initialize WebSocket for real-time notifications
    initializeWebSocket() {
        const token = localStorage.getItem('token');
        if (!token) return;

        const ws = new WebSocket(`ws://${window.location.host}/ws/notifications`);
        
        ws.onopen = () => {
            // Send authentication
            ws.send(JSON.stringify({ type: 'auth', token }));
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'appointment_reminder':
                    this.show(data.message, 'info', 0);
                    break;
                case 'appointment_update':
                    this.show(data.message, 'info');
                    break;
                case 'medical_record_update':
                    this.show(data.message, 'info');
                    break;
                case 'test_results_ready':
                    this.show(data.message, 'success', 0);
                    break;
                case 'prescription_update':
                    this.show(data.message, 'info');
                    break;
            }
        };

        ws.onclose = () => {
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.initializeWebSocket(), 5000);
        };
    }
};

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .notification {
        position: relative;
        overflow: hidden;
    }

    .notification::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: rgba(255,255,255,0.3);
        animation: progress linear;
    }

    @keyframes progress {
        from { width: 100%; }
        to { width: 0%; }
    }
`;
document.head.appendChild(style);

// Initialize notifications when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    Notifications.init();
});

// Export for use in other files
window.Notifications = Notifications;