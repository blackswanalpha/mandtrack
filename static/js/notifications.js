document.addEventListener('DOMContentLoaded', function() {
    const notificationButton = document.getElementById('notification-button');
    const notificationBadge = document.getElementById('notification-badge');
    const notificationList = document.getElementById('notification-list');
    const notificationDropdown = document.getElementById('notification-dropdown');
    const markAllReadButton = document.getElementById('mark-all-read');
    
    if (!notificationButton || !notificationList) return;
    
    // Load notifications
    function loadNotifications() {
        fetch('/dashboard/notifications/')
            .then(response => response.json())
            .then(data => {
                // Update notification badge
                if (data.unread_count > 0) {
                    notificationBadge.classList.remove('hidden');
                } else {
                    notificationBadge.classList.add('hidden');
                }
                
                // Clear previous notifications
                notificationList.innerHTML = '';
                
                // If no notifications
                if (data.notifications.length === 0) {
                    notificationList.innerHTML = `
                        <div class="px-4 py-3 text-sm text-gray-500 text-center">
                            No notifications
                        </div>
                    `;
                    return;
                }
                
                // Add notifications
                data.notifications.forEach(notification => {
                    const notificationItem = document.createElement('a');
                    notificationItem.href = notification.url;
                    notificationItem.className = 'block px-4 py-3 hover:bg-gray-50 transition-colors border-b border-gray-100';
                    
                    // Set background color for unread notifications
                    if (!notification.is_read) {
                        notificationItem.classList.add('bg-blue-50');
                    }
                    
                    // Set icon based on notification type
                    let iconClass = 'info';
                    let iconColor = 'blue';
                    
                    switch (notification.type) {
                        case 'success':
                            iconClass = 'check-circle';
                            iconColor = 'green';
                            break;
                        case 'warning':
                            iconClass = 'exclamation-triangle';
                            iconColor = 'yellow';
                            break;
                        case 'error':
                            iconClass = 'exclamation-circle';
                            iconColor = 'red';
                            break;
                    }
                    
                    notificationItem.innerHTML = `
                        <div class="flex items-start">
                            <div class="flex-shrink-0 bg-${iconColor}-100 rounded-full p-1">
                                <i class="fas fa-${iconClass} text-${iconColor}-600 text-sm"></i>
                            </div>
                            <div class="ml-3 w-0 flex-1">
                                <p class="text-sm font-medium text-gray-900">${notification.title}</p>
                                <p class="text-xs text-gray-500">${notification.message}</p>
                                <p class="text-xs text-gray-400 mt-1">${notification.created_at}</p>
                            </div>
                        </div>
                    `;
                    
                    // Mark as read when clicked
                    notificationItem.addEventListener('click', function(e) {
                        if (!notification.is_read) {
                            fetch(`/dashboard/notifications/mark-read/${notification.id}/`)
                                .then(response => response.json())
                                .then(data => {
                                    if (data.success) {
                                        notification.is_read = true;
                                        notificationItem.classList.remove('bg-blue-50');
                                        loadNotifications(); // Reload to update badge
                                    }
                                });
                        }
                    });
                    
                    notificationList.appendChild(notificationItem);
                });
            })
            .catch(error => {
                console.error('Error fetching notifications:', error);
                notificationList.innerHTML = `
                    <div class="px-4 py-3 text-sm text-red-500">
                        Error loading notifications
                    </div>
                `;
            });
    }
    
    // Load notifications on page load
    loadNotifications();
    
    // Reload notifications every 60 seconds
    setInterval(loadNotifications, 60000);
    
    // Mark all as read
    if (markAllReadButton) {
        markAllReadButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            fetch('/dashboard/notifications/mark-all-read/')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadNotifications();
                    }
                });
        });
    }
});
