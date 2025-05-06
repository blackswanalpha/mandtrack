document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts for the admin dashboard
    initializeAdminDashboardCharts();
});

function initializeAdminDashboardCharts() {
    // Response Overview Chart (small chart in the header)
    initializeResponseOverviewChart();

    // Response Trend Chart (larger chart)
    initializeResponseTrendChart();

    // Risk Distribution Chart
    initializeRiskDistributionChart();

    // Categories Chart
    initializeCategoriesChart();

    // Device Distribution Chart
    initializeDeviceDistributionChart();

    // Demographics Charts (Gender and Age)
    initializeDemographicsCharts();

    // Category Comparison Radar Chart
    initializeCategoryComparisonChart();

    // Heatmap Chart for Response Times
    initializeResponseTimeHeatmap();
}

function initializeResponseOverviewChart() {
    const chartElement = document.getElementById('responseOverviewChart');
    if (!chartElement) return;

    // Get trend data from the data attribute if available
    let trendData;
    try {
        trendData = JSON.parse(document.getElementById('trend-data').textContent);
    } catch (e) {
        // Fallback to sample data if parsing fails
        trendData = {
            labels: ['May 1', 'May 2', 'May 3', 'May 4', 'May 5', 'May 6', 'May 7'],
            data: [5, 8, 12, 7, 10, 15, 9],
            colors: Array(7).fill('rgba(255, 255, 255, 0.7)')
        };
    }

    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: trendData.labels.slice(-7),
            datasets: [{
                label: 'Responses',
                data: trendData.data.slice(-7),
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                borderColor: 'rgba(255, 255, 255, 0.8)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(255, 255, 255, 1)',
                pointRadius: 3,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.7)'
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        font: {
                            size: 10
                        }
                    }
                },
                y: {
                    display: true,
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        font: {
                            size: 10
                        },
                        stepSize: 5
                    }
                }
            },
            elements: {
                line: {
                    tension: 0.4
                }
            }
        }
    });
}

function initializeResponseTrendChart() {
    const chartElement = document.getElementById('responseTrendChart');
    if (!chartElement) return;

    // Get trend data from the data attribute if available
    let trendData;
    try {
        trendData = JSON.parse(document.getElementById('trend-data').textContent);
    } catch (e) {
        // Fallback to sample data if parsing fails
        trendData = {
            labels: Array.from({length: 30}, (_, i) => `May ${i+1}`),
            data: Array.from({length: 30}, () => Math.floor(Math.random() * 20) + 5),
            colors: Array(30).fill('rgba(54, 162, 235, 0.7)')
        };
    }

    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: trendData.labels,
            datasets: [{
                label: 'Responses',
                data: trendData.data,
                backgroundColor: trendData.colors,
                borderColor: trendData.colors.map(color => color.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

function initializeRiskDistributionChart() {
    const chartElement = document.getElementById('riskDistributionChart');
    if (!chartElement) return;

    // Get risk data from the data attribute if available
    let riskData;
    try {
        riskData = JSON.parse(document.getElementById('risk-data').textContent);
    } catch (e) {
        // Fallback to sample data if parsing fails
        riskData = {
            labels: ['Low', 'Medium', 'High', 'Critical'],
            data: [45, 30, 15, 10],
            colors: [
                'rgba(75, 192, 192, 0.7)',
                'rgba(255, 206, 86, 0.7)',
                'rgba(255, 159, 64, 0.7)',
                'rgba(255, 99, 132, 0.7)'
            ]
        };
    }

    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: riskData.labels,
            datasets: [{
                data: riskData.data,
                backgroundColor: riskData.colors,
                borderColor: riskData.colors.map(color => color.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '65%'
        }
    });
}

function initializeCategoriesChart() {
    const chartElement = document.getElementById('categoriesChart');
    if (!chartElement) return;

    // Get top questionnaires data from the data attribute if available
    let categoriesData;
    try {
        categoriesData = JSON.parse(document.getElementById('top-questionnaires-data').textContent);
    } catch (e) {
        // Fallback to sample data if parsing fails
        categoriesData = {
            labels: ['Mental Health', 'Physical Health', 'Customer Satisfaction', 'Employee Feedback', 'Product Feedback'],
            data: [35, 25, 20, 15, 5],
            colors: [
                'rgba(54, 162, 235, 0.7)',
                'rgba(255, 99, 132, 0.7)',
                'rgba(255, 206, 86, 0.7)',
                'rgba(75, 192, 192, 0.7)',
                'rgba(153, 102, 255, 0.7)'
            ]
        };
    }

    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: categoriesData.labels,
            datasets: [{
                data: categoriesData.data,
                backgroundColor: categoriesData.colors,
                borderColor: categoriesData.colors.map(color => color.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 10
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${percentage}%`;
                        }
                    }
                }
            }
        }
    });
}

function initializeDeviceDistributionChart() {
    const chartElement = document.getElementById('deviceDistributionChart');
    if (!chartElement) return;

    // Get device data from the data attribute if available
    let deviceData;
    try {
        deviceData = JSON.parse(document.getElementById('device-data').textContent);
    } catch (e) {
        // Fallback to sample data if parsing fails
        deviceData = {
            labels: ['Desktop', 'Mobile', 'Tablet'],
            data: [40, 45, 15],
            colors: [
                'rgba(54, 162, 235, 0.7)',
                'rgba(255, 99, 132, 0.7)',
                'rgba(255, 206, 86, 0.7)'
            ]
        };
    }

    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: deviceData.labels,
            datasets: [{
                label: 'Responses',
                data: deviceData.data,
                backgroundColor: deviceData.colors,
                borderColor: deviceData.colors.map(color => color.replace('0.7', '1')),
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        precision: 0
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function initializeDemographicsCharts() {
    // Gender Chart
    const genderChartElement = document.getElementById('genderChart');
    if (genderChartElement) {
        // Get gender data from the data attribute if available
        let genderData;
        try {
            genderData = JSON.parse(document.getElementById('gender-distribution').textContent);
        } catch (e) {
            // Fallback to sample data if parsing fails
            genderData = {
                labels: ['Male', 'Female', 'Non-binary', 'Prefer Not To Say'],
                data: [40, 45, 10, 5],
                colors: [
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)'
                ]
            };
        }

        const genderCtx = genderChartElement.getContext('2d');
        new Chart(genderCtx, {
            type: 'doughnut',
            data: {
                labels: genderData.labels,
                datasets: [{
                    data: genderData.data,
                    backgroundColor: genderData.colors,
                    borderColor: genderData.colors.map(color => color.replace('0.7', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 10
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }

    // Age Chart
    const ageChartElement = document.getElementById('ageChart');
    if (ageChartElement) {
        // Get age data from the data attribute if available
        let ageData;
        try {
            ageData = JSON.parse(document.getElementById('age-distribution').textContent);
        } catch (e) {
            // Fallback to sample data if parsing fails
            ageData = {
                labels: ['Under 18', '18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
                data: [5, 15, 25, 20, 15, 12, 8],
                colors: Array(7).fill('rgba(54, 162, 235, 0.7)')
            };
        }

        const ageCtx = ageChartElement.getContext('2d');
        new Chart(ageCtx, {
            type: 'bar',
            data: {
                labels: ageData.labels,
                datasets: [{
                    label: 'Age Distribution',
                    data: ageData.data,
                    backgroundColor: ageData.colors,
                    borderColor: ageData.colors.map(color => color.replace('0.7', '1')),
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${value} respondents (${percentage}%)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }

    // Toggle between gender and age charts
    const genderTabBtn = document.getElementById('genderTabBtn');
    const ageTabBtn = document.getElementById('ageTabBtn');

    if (genderTabBtn && ageTabBtn) {
        genderTabBtn.addEventListener('click', function() {
            document.getElementById('genderChart').style.display = 'block';
            document.getElementById('ageChart').style.display = 'none';
            genderTabBtn.classList.add('active');
            ageTabBtn.classList.remove('active');
        });

        ageTabBtn.addEventListener('click', function() {
            document.getElementById('genderChart').style.display = 'none';
            document.getElementById('ageChart').style.display = 'block';
            ageTabBtn.classList.add('active');
            genderTabBtn.classList.remove('active');
        });
    }
}

function initializeCategoryComparisonChart() {
    const chartElement = document.getElementById('categoryComparisonChart');
    if (!chartElement) return;

    // Get category comparison data from the data attribute if available
    let categoryData;
    try {
        categoryData = JSON.parse(document.getElementById('category-comparison-data').textContent);
    } catch (e) {
        // Fallback to sample data if parsing fails
        categoryData = {
            labels: ['Mental Health', 'Physical Health', 'Customer Satisfaction', 'Employee Feedback', 'Product Feedback'],
            datasets: [
                {
                    label: 'Response Count',
                    data: [65, 59, 90, 81, 56],
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
                },
                {
                    label: 'Completion Rate (%)',
                    data: [85, 70, 95, 80, 65],
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    pointBackgroundColor: 'rgba(255, 99, 132, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(255, 99, 132, 1)'
                },
                {
                    label: 'Average Score',
                    data: [75, 60, 85, 70, 55],
                    backgroundColor: 'rgba(255, 206, 86, 0.2)',
                    borderColor: 'rgba(255, 206, 86, 1)',
                    pointBackgroundColor: 'rgba(255, 206, 86, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(255, 206, 86, 1)'
                }
            ]
        };
    }

    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'radar',
        data: categoryData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            elements: {
                line: {
                    borderWidth: 3
                }
            },
            scales: {
                r: {
                    angleLines: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    suggestedMin: 0,
                    suggestedMax: 100,
                    ticks: {
                        backdropColor: 'rgba(255, 255, 255, 0.8)',
                        color: '#666'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.raw || 0;
                            return `${label}: ${value}`;
                        }
                    }
                }
            }
        }
    });
}

function initializeResponseTimeHeatmap() {
    const chartElement = document.getElementById('responseTimeHeatmap');
    if (!chartElement) return;

    // Get heatmap data from the data attribute if available
    let heatmapData;
    try {
        heatmapData = JSON.parse(document.getElementById('response-time-heatmap-data').textContent);
    } catch (e) {
        // Fallback to sample data if parsing fails
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const hours = Array.from({length: 24}, (_, i) => `${i}:00`);

        // Generate random data
        const data = [];
        for (let i = 0; i < days.length; i++) {
            for (let j = 0; j < hours.length; j++) {
                data.push({
                    x: hours[j],
                    y: days[i],
                    v: Math.floor(Math.random() * 50)
                });
            }
        }

        heatmapData = {
            days: days,
            hours: hours,
            data: data
        };
    }

    // Prepare data for Chart.js
    const datasets = [];
    for (let i = 0; i < heatmapData.days.length; i++) {
        const dayData = heatmapData.data.filter(d => d.y === heatmapData.days[i]);
        datasets.push({
            label: heatmapData.days[i],
            data: dayData.map(d => ({x: d.x, y: d.v})),
            backgroundColor: getHeatmapColor(dayData.map(d => d.v)),
            borderColor: 'rgba(0, 0, 0, 0.1)',
            borderWidth: 1
        });
    }

    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: heatmapData.hours,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Hours'
                    }
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Days'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.raw || 0;
                            return `${label} at ${context.label}: ${value} responses`;
                        }
                    }
                }
            }
        }
    });
}

function getHeatmapColor(values) {
    // Calculate color based on value
    return values.map(value => {
        const intensity = Math.min(value / 50, 1); // Normalize to 0-1

        // Generate color from blue (cold) to red (hot)
        if (intensity < 0.25) {
            // Blue to cyan
            return `rgba(0, ${Math.floor(255 * (intensity * 4))}, 255, 0.7)`;
        } else if (intensity < 0.5) {
            // Cyan to green
            return `rgba(0, 255, ${Math.floor(255 * (1 - (intensity - 0.25) * 4))}, 0.7)`;
        } else if (intensity < 0.75) {
            // Green to yellow
            return `rgba(${Math.floor(255 * ((intensity - 0.5) * 4))}, 255, 0, 0.7)`;
        } else {
            // Yellow to red
            return `rgba(255, ${Math.floor(255 * (1 - (intensity - 0.75) * 4))}, 0, 0.7)`;
        }
    });
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

    // Update category comparison chart if available
    if (data.category_comparison_data) {
        updateCategoryComparisonChart(data.category_comparison_data);
    }

    // Update response time heatmap if available
    if (data.response_time_heatmap_data) {
        updateResponseTimeHeatmap(data.response_time_heatmap_data);
    }

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

function updateCategoryComparisonChart(categoryData) {
    const categoryComparisonChart = Chart.getChart('categoryComparisonChart');
    if (categoryComparisonChart) {
        categoryComparisonChart.data.labels = categoryData.labels;

        // Update datasets
        for (let i = 0; i < categoryData.datasets.length; i++) {
            if (i < categoryComparisonChart.data.datasets.length) {
                categoryComparisonChart.data.datasets[i].data = categoryData.datasets[i].data;
            }
        }

        categoryComparisonChart.update();
    }
}

function updateResponseTimeHeatmap(heatmapData) {
    const responseTimeHeatmap = Chart.getChart('responseTimeHeatmap');
    if (responseTimeHeatmap) {
        // Prepare data for Chart.js
        const datasets = [];
        for (let i = 0; i < heatmapData.days.length; i++) {
            const dayData = heatmapData.data.filter(d => d.y === heatmapData.days[i]);
            datasets.push({
                label: heatmapData.days[i],
                data: dayData.map(d => ({x: d.x, y: d.v})),
                backgroundColor: getHeatmapColor(dayData.map(d => d.v)),
                borderColor: 'rgba(0, 0, 0, 0.1)',
                borderWidth: 1
            });
        }

        responseTimeHeatmap.data.labels = heatmapData.hours;
        responseTimeHeatmap.data.datasets = datasets;
        responseTimeHeatmap.update();
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

    // Update cache timestamp if available
    const cacheTimestamp = document.getElementById('cache-timestamp');
    if (cacheTimestamp && data.cache_timestamp) {
        const date = new Date(data.cache_timestamp);
        cacheTimestamp.textContent = date.toLocaleString();
    }
}
