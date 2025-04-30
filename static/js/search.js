document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('navbar-search');
    const searchResults = document.getElementById('search-results');
    const searchDropdown = document.getElementById('search-dropdown');
    
    if (!searchInput || !searchResults) return;
    
    let searchTimeout;
    
    // Handle search input
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        // Clear previous timeout
        clearTimeout(searchTimeout);
        
        // Hide results if query is too short
        if (query.length < 2) {
            searchDropdown.classList.add('hidden');
            return;
        }
        
        // Set a timeout to avoid making too many requests
        searchTimeout = setTimeout(function() {
            // Make AJAX request
            fetch(`/dashboard/search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    // Clear previous results
                    searchResults.innerHTML = '';
                    
                    // Show dropdown
                    searchDropdown.classList.remove('hidden');
                    
                    // If no results
                    if (data.results.length === 0) {
                        searchResults.innerHTML = `
                            <div class="px-4 py-3 text-sm text-gray-500">
                                No results found for "${query}"
                            </div>
                        `;
                        return;
                    }
                    
                    // Group results by type
                    const groupedResults = {};
                    data.results.forEach(result => {
                        if (!groupedResults[result.type]) {
                            groupedResults[result.type] = [];
                        }
                        groupedResults[result.type].push(result);
                    });
                    
                    // Display results by group
                    for (const [type, results] of Object.entries(groupedResults)) {
                        // Add group header
                        const header = document.createElement('div');
                        header.className = 'px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50';
                        header.textContent = type.charAt(0).toUpperCase() + type.slice(1) + 's';
                        searchResults.appendChild(header);
                        
                        // Add results
                        results.forEach(result => {
                            const resultItem = document.createElement('a');
                            resultItem.href = result.url;
                            resultItem.className = 'block px-4 py-3 hover:bg-gray-50 transition-colors';
                            
                            resultItem.innerHTML = `
                                <div class="flex items-start">
                                    <div class="flex-shrink-0 bg-gray-100 rounded-full p-1">
                                        <i class="fas fa-${result.icon} text-gray-600 text-sm"></i>
                                    </div>
                                    <div class="ml-3 w-0 flex-1">
                                        <p class="text-sm font-medium text-gray-900">${result.title}</p>
                                        <p class="text-xs text-gray-500">${result.description}</p>
                                    </div>
                                </div>
                            `;
                            
                            searchResults.appendChild(resultItem);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error fetching search results:', error);
                    searchResults.innerHTML = `
                        <div class="px-4 py-3 text-sm text-red-500">
                            Error fetching results. Please try again.
                        </div>
                    `;
                });
        }, 300);
    });
    
    // Close search results when clicking outside
    document.addEventListener('click', function(event) {
        if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
            searchDropdown.classList.add('hidden');
        }
    });
    
    // Close search results when pressing Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            searchDropdown.classList.add('hidden');
        }
    });
});
