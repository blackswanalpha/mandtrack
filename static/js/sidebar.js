/**
 * Sidebar Animation and Interaction Enhancements
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar animations
    initSidebarAnimations();
    
    // Initialize sidebar toggle for mobile
    initSidebarToggle();
    
    // Initialize dropdown animations
    initDropdownAnimations();
});

/**
 * Initialize sidebar animations
 */
function initSidebarAnimations() {
    // Add staggered animation to sidebar items
    const sidebarItems = document.querySelectorAll('.sidebar .nav-item');
    sidebarItems.forEach((item, index) => {
        // Add animation delay based on index
        item.style.animationDelay = `${0.1 * (index + 1)}s`;
        
        // Add hover effect to nav links
        const navLink = item.querySelector('.nav-link');
        if (navLink) {
            navLink.addEventListener('mouseenter', function() {
                this.classList.add('hover-active');
            });
            
            navLink.addEventListener('mouseleave', function() {
                this.classList.remove('hover-active');
            });
        }
    });
    
    // Add ripple effect to nav links
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

/**
 * Initialize sidebar toggle for mobile
 */
function initSidebarToggle() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const sidebarBackdrop = document.createElement('div');
    sidebarBackdrop.classList.add('sidebar-backdrop');
    document.body.appendChild(sidebarBackdrop);
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            sidebarBackdrop.classList.toggle('show');
            document.body.classList.toggle('sidebar-open');
        });
        
        sidebarBackdrop.addEventListener('click', function() {
            sidebar.classList.remove('show');
            sidebarBackdrop.classList.remove('show');
            document.body.classList.remove('sidebar-open');
        });
    }
    
    // Close sidebar on window resize if in mobile view
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 768 && sidebar.classList.contains('show')) {
            sidebar.classList.remove('show');
            sidebarBackdrop.classList.remove('show');
            document.body.classList.remove('sidebar-open');
        }
    });
}

/**
 * Initialize dropdown animations
 */
function initDropdownAnimations() {
    const dropdownToggles = document.querySelectorAll('.sidebar .nav-link[data-bs-toggle="collapse"]');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            const chevron = this.querySelector('.fa-chevron-down');
            
            if (chevron) {
                if (isExpanded) {
                    chevron.style.transform = 'rotate(180deg)';
                } else {
                    chevron.style.transform = 'rotate(0deg)';
                }
            }
        });
        
        // Initialize chevron rotation based on initial state
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        const chevron = toggle.querySelector('.fa-chevron-down');
        
        if (chevron && isExpanded) {
            chevron.style.transform = 'rotate(180deg)';
        }
    });
    
    // Add animation to submenu items
    const subMenuItems = document.querySelectorAll('.sidebar .collapse .nav-item');
    subMenuItems.forEach((item, index) => {
        item.style.transitionDelay = `${0.05 * (index + 1)}s`;
    });
}

/**
 * Add active class to current page in sidebar
 */
function highlightCurrentPage() {
    const currentPath = window.location.pathname;
    
    // Find all links in the sidebar
    const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
    
    sidebarLinks.forEach(link => {
        const href = link.getAttribute('href');
        
        // Skip dropdown toggles
        if (link.hasAttribute('data-bs-toggle')) return;
        
        // Check if the link href matches the current path
        if (href && currentPath.includes(href) && href !== '/') {
            // Add active class to the link
            link.classList.add('active');
            
            // If the link is in a dropdown, expand the dropdown
            const dropdown = link.closest('.collapse');
            if (dropdown) {
                const dropdownToggle = document.querySelector(`[data-bs-toggle="collapse"][href="#${dropdown.id}"]`);
                if (dropdownToggle) {
                    dropdownToggle.classList.add('active');
                    dropdownToggle.setAttribute('aria-expanded', 'true');
                    dropdown.classList.add('show');
                    
                    // Rotate chevron
                    const chevron = dropdownToggle.querySelector('.fa-chevron-down');
                    if (chevron) {
                        chevron.style.transform = 'rotate(180deg)';
                    }
                }
            }
        }
    });
}

// Call highlightCurrentPage when the page loads
document.addEventListener('DOMContentLoaded', highlightCurrentPage);
