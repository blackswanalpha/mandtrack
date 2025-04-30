document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle functionality
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');
    
    if (sidebarToggle && sidebar && mainContent) {
        // Check for saved sidebar state
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        
        // Set initial state
        if (sidebarCollapsed) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
        }
        
        // Toggle sidebar on button click
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
            
            // Save state to localStorage
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
        
        // Handle mobile sidebar
        const mobileToggle = document.getElementById('mobileSidebarToggle');
        if (mobileToggle) {
            mobileToggle.addEventListener('click', function() {
                sidebar.classList.toggle('show');
                if (sidebarBackdrop) {
                    sidebarBackdrop.classList.toggle('show');
                }
            });
        }
        
        // Close sidebar when clicking outside on mobile
        if (sidebarBackdrop) {
            sidebarBackdrop.addEventListener('click', function() {
                sidebar.classList.remove('show');
                sidebarBackdrop.classList.remove('show');
            });
        }
    }
    
    // Submenu toggle functionality
    const submenuToggles = document.querySelectorAll('.submenu-toggle');
    submenuToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            const submenuId = this.getAttribute('data-bs-target');
            const submenu = document.querySelector(submenuId);
            
            if (submenu) {
                // Toggle aria-expanded attribute
                const expanded = this.getAttribute('aria-expanded') === 'true';
                this.setAttribute('aria-expanded', !expanded);
                
                // Toggle submenu visibility
                const submenuCollapse = new bootstrap.Collapse(submenu, {
                    toggle: true
                });
            }
        });
    });
    
    // Add animation classes to sidebar elements
    function addAnimations() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach((item, index) => {
            item.classList.add('animate-fade-in');
            item.style.animationDelay = `${0.1 * (index + 1)}s`;
        });
        
        const sidebarUser = document.querySelector('.sidebar-user');
        if (sidebarUser) {
            sidebarUser.classList.add('animate-fade-in');
        }
        
        const sidebarSettings = document.querySelector('.sidebar-settings');
        if (sidebarSettings) {
            sidebarSettings.classList.add('animate-fade-in');
            sidebarSettings.style.animationDelay = '0.5s';
        }
        
        const sidebarFooter = document.querySelector('.sidebar-footer');
        if (sidebarFooter) {
            sidebarFooter.classList.add('animate-fade-in');
            sidebarFooter.style.animationDelay = '0.6s';
        }
    }
    
    // Call the animation function
    addAnimations();
    
    // Handle active menu items based on current URL
    function setActiveMenuItem() {
        const currentPath = window.location.pathname;
        
        const navLinks = document.querySelectorAll('.nav-link, .submenu-link');
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.includes(href) && href !== '#') {
                link.classList.add('active');
                
                // If it's a submenu item, expand the parent menu
                if (link.classList.contains('submenu-link')) {
                    const parentItem = link.closest('.submenu').previousElementSibling;
                    if (parentItem && parentItem.classList.contains('nav-link')) {
                        parentItem.classList.add('active');
                        parentItem.setAttribute('aria-expanded', 'true');
                        
                        // Show the submenu
                        const submenuId = parentItem.getAttribute('data-bs-target');
                        if (submenuId) {
                            const submenu = document.querySelector(submenuId);
                            if (submenu) {
                                submenu.classList.add('show');
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Call the function to set active menu item
    setActiveMenuItem();
});
