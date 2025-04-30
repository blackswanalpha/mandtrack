document.addEventListener('DOMContentLoaded', function() {
    // Theme switcher functionality
    const themeToggleBtn = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    
    // Check for saved theme preference or use the system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        htmlElement.classList.add('dark');
        updateThemeIcon(true);
    } else {
        htmlElement.classList.remove('dark');
        updateThemeIcon(false);
    }
    
    // Toggle theme when button is clicked
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const isDarkMode = htmlElement.classList.toggle('dark');
            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
            updateThemeIcon(isDarkMode);
            
            // Add animation effect
            themeToggleBtn.classList.add('animate-spin');
            setTimeout(() => {
                themeToggleBtn.classList.remove('animate-spin');
            }, 500);
        });
    }
    
    // Update icon based on current theme
    function updateThemeIcon(isDarkMode) {
        if (!themeToggleBtn) return;
        
        const sunIcon = themeToggleBtn.querySelector('.sun-icon');
        const moonIcon = themeToggleBtn.querySelector('.moon-icon');
        
        if (isDarkMode) {
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
        } else {
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
        }
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            const isDarkMode = e.matches;
            htmlElement.classList.toggle('dark', isDarkMode);
            updateThemeIcon(isDarkMode);
        }
    });
});
