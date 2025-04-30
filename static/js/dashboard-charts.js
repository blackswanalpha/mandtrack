document.addEventListener('DOMContentLoaded', function() {
    // Check if chart element exists
    const chartElement = document.getElementById('mentalHealthChart');
    if (!chartElement) return;
    
    // Chart configuration
    const ctx = chartElement.getContext('2d');
    
    // Initial data for weekly view
    const weeklyData = {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [
            {
                label: 'Anxiety',
                data: [65, 59, 80, 81, 56, 55, 40],
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2
            },
            {
                label: 'Depression',
                data: [42, 49, 40, 39, 36, 30, 32],
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                borderColor: 'rgba(139, 92, 246, 1)',
                borderWidth: 2
            },
            {
                label: 'Stress',
                data: [53, 48, 60, 55, 40, 45, 39],
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                borderColor: 'rgba(239, 68, 68, 1)',
                borderWidth: 2
            }
        ]
    };
    
    // Monthly data
    const monthlyData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [
            {
                label: 'Anxiety',
                data: [65, 70, 62, 75, 68, 60, 55, 50, 55, 60, 70, 75],
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2
            },
            {
                label: 'Depression',
                data: [55, 60, 58, 62, 55, 50, 48, 45, 50, 55, 60, 65],
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                borderColor: 'rgba(139, 92, 246, 1)',
                borderWidth: 2
            },
            {
                label: 'Stress',
                data: [60, 65, 59, 68, 60, 55, 50, 47, 52, 58, 65, 70],
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                borderColor: 'rgba(239, 68, 68, 1)',
                borderWidth: 2
            }
        ]
    };
    
    // Create initial chart with bar type
    let chartType = 'bar';
    let timeRange = 'weekly';
    let currentData = weeklyData;
    
    let chart = new Chart(ctx, {
        type: chartType,
        data: currentData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
    
    // Handle chart type change
    const chartTypeSelect = document.querySelector('#chart-type-select');
    if (chartTypeSelect) {
        chartTypeSelect.addEventListener('change', function(e) {
            chartType = e.target.value;
            updateChart();
        });
    }
    
    // Handle time range change
    const timeRangeSelect = document.querySelector('#time-range-select');
    if (timeRangeSelect) {
        timeRangeSelect.addEventListener('change', function(e) {
            timeRange = e.target.value;
            currentData = timeRange === 'weekly' ? weeklyData : monthlyData;
            updateChart();
        });
    }
    
    // Function to update chart
    function updateChart() {
        chart.destroy();
        chart = new Chart(ctx, {
            type: chartType,
            data: currentData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
});
