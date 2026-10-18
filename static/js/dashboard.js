/**
 * LibraVerse - Administrative Dashboard & Analytics Visualization Engine
 * Powered by Chart.js with Cyberpunk Dark Purple and Cyan Theme Styling
 */

document.addEventListener('DOMContentLoaded', () => {
    if (typeof Chart === 'undefined') return;

    // Apply global Chart.js aesthetic defaults
    Chart.defaults.color = '#94A3B8';
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.font.size = 12;

    const commonTooltipOptions = {
        backgroundColor: 'rgba(14, 14, 32, 0.94)',
        titleColor: '#22D3EE',
        titleFont: { weight: 'bold', size: 13 },
        bodyColor: '#F8FAFC',
        bodyFont: { size: 12 },
        borderColor: 'rgba(34, 211, 238, 0.4)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        boxPadding: 6
    };

    // 1. Categories Donut Chart
    const catCanvas = document.getElementById('categoryDistributionChart');
    if (catCanvas && window.categoryChartData) {
        new Chart(catCanvas, {
            type: 'doughnut',
            data: {
                labels: window.categoryChartData.labels,
                datasets: [{
                    data: window.categoryChartData.counts,
                    backgroundColor: [
                        '#8B5CF6', '#22D3EE', '#EC4899', '#3B82F6',
                        '#10B981', '#F59E0B', '#6366F1', '#14B8A6'
                    ],
                    borderColor: '#0e0e1e',
                    borderWidth: 2,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 12, padding: 15, color: '#CBD5E1' }
                    },
                    tooltip: commonTooltipOptions
                },
                cutout: '68%'
            }
        });
    }

    // 2. Available vs Issued Copies (Bar Chart)
    const copiesCanvas = document.getElementById('copiesComparisonChart');
    if (copiesCanvas && window.copiesChartData) {
        new Chart(copiesCanvas, {
            type: 'bar',
            data: {
                labels: window.copiesChartData.labels,
                datasets: [
                    {
                        label: 'Available Copies',
                        data: window.copiesChartData.available,
                        backgroundColor: 'rgba(34, 211, 238, 0.75)',
                        borderColor: '#22D3EE',
                        borderWidth: 1,
                        borderRadius: 6
                    },
                    {
                        label: 'Issued Copies',
                        data: window.copiesChartData.issued,
                        backgroundColor: 'rgba(139, 92, 246, 0.75)',
                        borderColor: '#8B5CF6',
                        borderWidth: 1,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top', labels: { color: '#CBD5E1' } },
                    tooltip: commonTooltipOptions
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(139, 92, 246, 0.08)' },
                        ticks: { color: '#94A3B8' }
                    },
                    y: {
                        grid: { color: 'rgba(139, 92, 246, 0.08)' },
                        ticks: { color: '#94A3B8', stepSize: 1 },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 3. Most Frequently Borrowed Books (Horizontal Bar Chart)
    const popularCanvas = document.getElementById('popularBooksChart');
    if (popularCanvas && window.popularBooksChartData) {
        new Chart(popularCanvas, {
            type: 'bar',
            data: {
                labels: window.popularBooksChartData.labels,
                datasets: [{
                    label: 'Times Borrowed',
                    data: window.popularBooksChartData.counts,
                    backgroundColor: 'rgba(167, 139, 250, 0.8)',
                    borderColor: '#A78BFA',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: commonTooltipOptions
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(139, 92, 246, 0.08)' },
                        ticks: { color: '#94A3B8', stepSize: 1 },
                        beginAtZero: true
                    },
                    y: {
                        grid: { display: false },
                        ticks: {
                            color: '#CBD5E1',
                            callback: function(value) {
                                const label = this.getLabelForValue(value);
                                return label.length > 20 ? label.substr(0, 18) + '...' : label;
                            }
                        }
                    }
                }
            }
        });
    }

    // 4. Monthly Borrowing Trends (Area Line Chart)
    const trendsCanvas = document.getElementById('monthlyTrendsChart');
    if (trendsCanvas && window.monthlyTrendsChartData) {
        const ctx = trendsCanvas.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(34, 211, 238, 0.35)');
        gradient.addColorStop(1, 'rgba(34, 211, 238, 0.0)');

        new Chart(trendsCanvas, {
            type: 'line',
            data: {
                labels: window.monthlyTrendsChartData.labels,
                datasets: [{
                    label: 'Borrowings Recorded',
                    data: window.monthlyTrendsChartData.counts,
                    borderColor: '#22D3EE',
                    borderWidth: 3,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#8B5CF6',
                    pointBorderColor: '#22D3EE',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: commonTooltipOptions
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(139, 92, 246, 0.08)' },
                        ticks: { color: '#94A3B8' }
                    },
                    y: {
                        grid: { color: 'rgba(139, 92, 246, 0.08)' },
                        ticks: { color: '#94A3B8', stepSize: 1 },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 5. Loan Duration Distribution (Analytics Page)
    const durationCanvas = document.getElementById('durationDistributionChart');
    if (durationCanvas && window.durationDistributionData) {
        new Chart(durationCanvas, {
            type: 'bar',
            data: {
                labels: window.durationDistributionData.labels,
                datasets: [{
                    label: 'Returned Loans',
                    data: window.durationDistributionData.counts,
                    backgroundColor: 'rgba(236, 72, 153, 0.75)',
                    borderColor: '#EC4899',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: commonTooltipOptions
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(139, 92, 246, 0.08)' },
                        ticks: { color: '#94A3B8' }
                    },
                    y: {
                        grid: { color: 'rgba(139, 92, 246, 0.08)' },
                        ticks: { color: '#94A3B8', stepSize: 1 },
                        beginAtZero: true
                    }
                }
            }
        });
    }
});
