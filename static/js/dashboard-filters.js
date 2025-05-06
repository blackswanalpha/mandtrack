/**
 * Dashboard Filters
 * Handles filtering functionality for the dashboard
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboardFilters();
});

function initializeDashboardFilters() {
    // Initialize date range picker
    initializeDateRangePicker();
    
    // Initialize filter form submission
    initializeFilterForm();
    
    // Initialize filter tag removal
    initializeFilterTagRemoval();
}

function initializeDateRangePicker() {
    const dateRangeInput = document.getElementById('date-range');
    if (!dateRangeInput) return;
    
    // Check if daterangepicker library is available
    if (typeof $ !== 'undefined' && $.fn.daterangepicker) {
        $(dateRangeInput).daterangepicker({
            startDate: moment().subtract(29, 'days'),
            endDate: moment(),
            ranges: {
                'Today': [moment(), moment()],
                'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                'This Month': [moment().startOf('month'), moment().endOf('month')],
                'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
            },
            alwaysShowCalendars: true,
            opens: 'left',
            autoApply: true,
            locale: {
                format: 'MMM D, YYYY'
            }
        }, function(start, end, label) {
            // Update the date range tag
            const dateRangeTag = document.getElementById('date-range-tag');
            if (dateRangeTag) {
                dateRangeTag.textContent = label || `${start.format('MMM D, YYYY')} - ${end.format('MMM D, YYYY')}`;
            }
            
            // Show the active filters container
            const activeFilters = document.getElementById('active-filters');
            if (activeFilters) {
                activeFilters.classList.remove('d-none');
            }
            
            // Trigger dashboard update
            updateDashboardData({
                start_date: start.format('YYYY-MM-DD'),
                end_date: end.format('YYYY-MM-DD')
            });
        });
        
        // Set initial value
        $(dateRangeInput).data('daterangepicker').setStartDate(moment().subtract(29, 'days'));
        $(dateRangeInput).data('daterangepicker').setEndDate(moment());
    } else {
        console.warn('DateRangePicker library not loaded. Date range filtering will not work.');
        dateRangeInput.type = 'date';
    }
}

function initializeFilterForm() {
    const filterForm = document.getElementById('dashboard-filter-form');
    if (!filterForm) return;
    
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(filterForm);
        const filters = {};
        
        for (const [key, value] of formData.entries()) {
            if (value) {
                filters[key] = value;
            }
        }
        
        // Update filter tags
        updateFilterTags(filters);
        
        // Update dashboard data
        updateDashboardData(filters);
    });
    
    // Handle organization filter change
    const organizationFilter = document.getElementById('organization-filter');
    if (organizationFilter) {
        organizationFilter.addEventListener('change', function() {
            const organizationTag = document.getElementById('organization-tag');
            const organizationName = document.getElementById('organization-name');
            
            if (this.value) {
                const selectedOption = this.options[this.selectedIndex];
                organizationName.textContent = selectedOption.text;
                organizationTag.classList.remove('d-none');
                
                // Show the active filters container
                const activeFilters = document.getElementById('active-filters');
                if (activeFilters) {
                    activeFilters.classList.remove('d-none');
                }
            } else {
                organizationTag.classList.add('d-none');
            }
        });
    }
    
    // Handle questionnaire type filter change
    const questionnaireTypeFilter = document.getElementById('questionnaire-type');
    if (questionnaireTypeFilter) {
        questionnaireTypeFilter.addEventListener('change', function() {
            const questionnaireTypeTag = document.getElementById('questionnaire-type-tag');
            const questionnaireTypeName = document.getElementById('questionnaire-type-name');
            
            if (this.value) {
                const selectedOption = this.options[this.selectedIndex];
                questionnaireTypeName.textContent = selectedOption.text;
                questionnaireTypeTag.classList.remove('d-none');
                
                // Show the active filters container
                const activeFilters = document.getElementById('active-filters');
                if (activeFilters) {
                    activeFilters.classList.remove('d-none');
                }
            } else {
                questionnaireTypeTag.classList.add('d-none');
            }
        });
    }
}

function initializeFilterTagRemoval() {
    // Handle filter tag removal
    const filterTagButtons = document.querySelectorAll('[data-filter]');
    filterTagButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterType = this.getAttribute('data-filter');
            const filterInput = document.querySelector(`[name="${filterType}"]`);
            
            if (filterInput) {
                filterInput.value = '';
                
                // Hide the tag
                const tag = this.closest('.badge');
                if (tag) {
                    tag.classList.add('d-none');
                }
                
                // Check if all tags are hidden
                const visibleTags = document.querySelectorAll('#active-filters .badge:not(.d-none)');
                if (visibleTags.length === 0) {
                    const activeFilters = document.getElementById('active-filters');
                    if (activeFilters) {
                        activeFilters.classList.add('d-none');
                    }
                }
                
                // Update dashboard data
                const formData = new FormData(document.getElementById('dashboard-filter-form'));
                const filters = {};
                
                for (const [key, value] of formData.entries()) {
                    if (value) {
                        filters[key] = value;
                    }
                }
                
                updateDashboardData(filters);
            }
        });
    });
    
    // Handle clear all filters
    const clearAllFiltersButton = document.getElementById('clear-all-filters');
    if (clearAllFiltersButton) {
        clearAllFiltersButton.addEventListener('click', function() {
            // Reset form
            const filterForm = document.getElementById('dashboard-filter-form');
            if (filterForm) {
                filterForm.reset();
                
                // Hide all tags
                const tags = document.querySelectorAll('#active-filters .badge');
                tags.forEach(tag => {
                    tag.classList.add('d-none');
                });
                
                // Hide the active filters container
                const activeFilters = document.getElementById('active-filters');
                if (activeFilters) {
                    activeFilters.classList.add('d-none');
                }
                
                // Reset date range picker if available
                if (typeof $ !== 'undefined' && $.fn.daterangepicker) {
                    const dateRangeInput = document.getElementById('date-range');
                    if (dateRangeInput) {
                        $(dateRangeInput).data('daterangepicker').setStartDate(moment().subtract(29, 'days'));
                        $(dateRangeInput).data('daterangepicker').setEndDate(moment());
                    }
                }
                
                // Update dashboard data with default filters
                updateDashboardData({});
            }
        });
    }
}

function updateFilterTags(filters) {
    // Show/hide the active filters container
    const activeFilters = document.getElementById('active-filters');
    if (activeFilters) {
        if (Object.keys(filters).length > 0) {
            activeFilters.classList.remove('d-none');
        } else {
            activeFilters.classList.add('d-none');
        }
    }
}

function updateDashboardData(filters) {
    // Show loading state
    showDashboardLoading(true);
    
    // Make AJAX request to get filtered data
    fetch('/dashboard/api/data/?' + new URLSearchParams(filters))
        .then(response => response.json())
        .then(data => {
            // Update charts with new data
            updateDashboardCharts(data);
            
            // Hide loading state
            showDashboardLoading(false);
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
            
            // Hide loading state
            showDashboardLoading(false);
            
            // Show error message
            showDashboardError('Failed to load dashboard data. Please try again.');
        });
}

function showDashboardLoading(isLoading) {
    const dashboardContent = document.getElementById('dashboard-content');
    const dashboardLoader = document.getElementById('dashboard-loader');
    
    if (dashboardContent && dashboardLoader) {
        if (isLoading) {
            dashboardContent.classList.add('opacity-50');
            dashboardLoader.classList.remove('d-none');
        } else {
            dashboardContent.classList.remove('opacity-50');
            dashboardLoader.classList.add('d-none');
        }
    }
}

function showDashboardError(message) {
    const dashboardAlert = document.getElementById('dashboard-alert');
    
    if (dashboardAlert) {
        dashboardAlert.textContent = message;
        dashboardAlert.classList.remove('d-none');
        
        // Hide after 5 seconds
        setTimeout(() => {
            dashboardAlert.classList.add('d-none');
        }, 5000);
    }
}

function updateDashboardCharts(data) {
    // Update response trend chart
    updateResponseTrendChart(data.trend_data);
    
    // Update risk distribution chart
    updateRiskDistributionChart(data.risk_data);
    
    // Update categories chart
    updateCategoriesChart(data.top_questionnaires_data);
    
    // Update device distribution chart
    updateDeviceDistributionChart(data.device_data);
    
    // Update demographics charts
    updateDemographicsCharts(data.gender_distribution, data.age_distribution);
    
    // Update stats cards
    updateStatsCards(data);
}

function updateResponseTrendChart(trendData) {
    const responseTrendChart = Chart.getChart('responseTrendChart');
    if (responseTrendChart) {
        responseTrendChart.data.labels = trendData.labels;
        responseTrendChart.data.datasets[0].data = trendData.data;
        responseTrendChart.update();
    }
    
    const responseOverviewChart = Chart.getChart('responseOverviewChart');
    if (responseOverviewChart) {
        responseOverviewChart.data.labels = trendData.labels.slice(-7);
        responseOverviewChart.data.datasets[0].data = trendData.data.slice(-7);
        responseOverviewChart.update();
    }
}

function updateRiskDistributionChart(riskData) {
    const riskDistributionChart = Chart.getChart('riskDistributionChart');
    if (riskDistributionChart) {
        riskDistributionChart.data.labels = riskData.labels;
        riskDistributionChart.data.datasets[0].data = riskData.data;
        riskDistributionChart.data.datasets[0].backgroundColor = riskData.colors;
        riskDistributionChart.update();
    }
}

function updateCategoriesChart(categoriesData) {
    const categoriesChart = Chart.getChart('categoriesChart');
    if (categoriesChart) {
        categoriesChart.data.labels = categoriesData.labels;
        categoriesChart.data.datasets[0].data = categoriesData.data;
        categoriesChart.data.datasets[0].backgroundColor = categoriesData.colors;
        categoriesChart.update();
    }
}

function updateDeviceDistributionChart(deviceData) {
    const deviceDistributionChart = Chart.getChart('deviceDistributionChart');
    if (deviceDistributionChart) {
        deviceDistributionChart.data.labels = deviceData.labels;
        deviceDistributionChart.data.datasets[0].data = deviceData.data;
        deviceDistributionChart.data.datasets[0].backgroundColor = deviceData.colors;
        deviceDistributionChart.update();
    }
}

function updateDemographicsCharts(genderData, ageData) {
    const genderChart = Chart.getChart('genderChart');
    if (genderChart) {
        genderChart.data.labels = genderData.labels;
        genderChart.data.datasets[0].data = genderData.data;
        genderChart.data.datasets[0].backgroundColor = genderData.colors;
        genderChart.update();
    }
    
    const ageChart = Chart.getChart('ageChart');
    if (ageChart) {
        ageChart.data.labels = ageData.labels;
        ageChart.data.datasets[0].data = ageData.data;
        ageChart.data.datasets[0].backgroundColor = ageData.colors;
        ageChart.update();
    }
}

function updateStatsCards(data) {
    // Update total questionnaires
    const totalQuestionnaires = document.getElementById('total-questionnaires');
    if (totalQuestionnaires && data.total_questionnaires !== undefined) {
        totalQuestionnaires.textContent = data.total_questionnaires;
    }
    
    // Update total responses
    const totalResponses = document.getElementById('total-responses');
    if (totalResponses && data.total_responses !== undefined) {
        totalResponses.textContent = data.total_responses;
    }
    
    // Update completion rate
    const completionRate = document.getElementById('completion-rate');
    if (completionRate && data.completion_rate !== undefined) {
        completionRate.textContent = data.completion_rate + '%';
    }
    
    // Update average score
    const avgScore = document.getElementById('avg-score');
    if (avgScore && data.avg_score !== undefined) {
        avgScore.textContent = data.avg_score;
    }
    
    // Update active questionnaires
    const activeQuestionnaires = document.getElementById('active-questionnaires');
    if (activeQuestionnaires && data.active_questionnaires !== undefined) {
        activeQuestionnaires.textContent = data.active_questionnaires;
    }
    
    // Update completion time data
    if (data.completion_time_data) {
        const avgCompletionTime = document.getElementById('avg-completion-time');
        if (avgCompletionTime) {
            avgCompletionTime.textContent = data.completion_time_data.average_display;
        }
        
        const minCompletionTime = document.getElementById('min-completion-time');
        if (minCompletionTime) {
            minCompletionTime.textContent = data.completion_time_data.min_display;
        }
        
        const maxCompletionTime = document.getElementById('max-completion-time');
        if (maxCompletionTime) {
            maxCompletionTime.textContent = data.completion_time_data.max_display;
        }
    }
}
