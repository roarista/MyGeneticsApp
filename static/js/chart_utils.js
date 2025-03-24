/**
 * Utility functions for managing charts in the fitness genetics analysis app
 */

// Format data for radar chart
function formatTraitDataForRadar(traits) {
    // Default colors for different ratings
    const colorMap = {
        'excellent': 'rgba(40, 167, 69, 0.7)',  // green
        'good': 'rgba(23, 162, 184, 0.7)',      // blue
        'average': 'rgba(255, 193, 7, 0.7)',    // yellow
        'below_average': 'rgba(220, 53, 69, 0.7)',  // red
        'informational': 'rgba(108, 117, 125, 0.7)'  // gray for purely informational metrics
    };
    
    // Format labels, values and colors
    const chartData = {
        labels: [],
        values: [],
        colors: []
    };
    
    // Define which traits to include in the chart
    // We'll prioritize certain traits and exclude purely informational ones
    const priorityTraits = [
        // Primary body structure traits
        'shoulder_width', 'shoulder_hip_ratio', 'arm_length', 
        'leg_length', 'arm_torso_ratio', 'torso_length', 'waist_hip_ratio',
        // Body composition traits (if available)
        'bmi', 'body_fat_percentage', 'muscle_potential', 'ffmi',
        // Athletic potential traits
        'arm_span_height_ratio'
    ];
    
    // Process traits in the priority order
    for (const trait of priorityTraits) {
        if (!traits[trait] || typeof traits[trait] !== 'object') {
            continue;
        }
        
        const data = traits[trait];
        
        // Skip purely informational traits with no rating scale
        if (data.rating === 'informational') {
            continue;
        }
        
        // Format trait name for display
        let displayName;
        if (trait === 'bmi') {
            displayName = 'BMI';
        } else if (trait === 'body_fat_percentage') {
            displayName = 'Body Fat %';
        } else {
            displayName = trait.split('_')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
        }
        
        chartData.labels.push(displayName);
        
        // Determine numerical value based on rating
        if (data.rating) {
            const numericValue = {
                'excellent': 90,
                'good': 75,
                'average': 50,
                'below_average': 25
            }[data.rating] || 50;
            
            chartData.values.push(numericValue);
            chartData.colors.push(colorMap[data.rating] || 'rgba(108, 117, 125, 0.7)');
        } else {
            // For direct numerical values
            chartData.values.push(data.value || 50);
            chartData.colors.push('rgba(23, 162, 184, 0.7)');
        }
    }
    
    return chartData;
}

// Create and render a radar chart
function createTraitsRadarChart(canvasId, traitsData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const chartData = formatTraitDataForRadar(traitsData);
    
    // Limit the number of traits to display to prevent overlapping
    // If there are more than 8 traits, only show the most important ones
    if (chartData.labels.length > 8) {
        const essentialTraits = [
            'Shoulder Width', 'Shoulder Hip Ratio', 'Arm Length', 
            'Leg Length', 'Muscle Potential', 'Body Fat %', 
            'Torso Length', 'Arm Torso Ratio'
        ];
        
        // Filter the chartData to only include essential traits
        const filteredIndices = [];
        chartData.labels.forEach((label, index) => {
            if (essentialTraits.includes(label)) {
                filteredIndices.push(index);
            }
        });
        
        if (filteredIndices.length > 0) {
            chartData.labels = filteredIndices.map(i => chartData.labels[i]);
            chartData.values = filteredIndices.map(i => chartData.values[i]);
            chartData.colors = filteredIndices.map(i => chartData.colors[i]);
        }
    }
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Your Genetic Traits',
                data: chartData.values,
                backgroundColor: 'rgba(66, 133, 244, 0.2)',
                borderColor: 'rgba(66, 133, 244, 1)',
                borderWidth: 2,
                pointBackgroundColor: chartData.colors,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(66, 133, 244, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    suggestedMin: 0,
                    suggestedMax: 100,
                    ticks: {
                        stepSize: 25,
                        color: '#666',
                        backdropColor: 'transparent'
                    },
                    pointLabels: {
                        color: '#333',
                        font: {
                            size: 12,
                            family: "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
                            weight: 'bold'
                        },
                        padding: 15 // Add more padding to prevent overlap
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        font: {
                            family: "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
                            size: 14
                        },
                        color: '#333'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    titleColor: '#333',
                    bodyColor: '#333',
                    borderColor: 'rgba(0, 0, 0, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 6,
                    boxPadding: 6,
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            let rating = 'Average';
                            
                            if (value >= 85) rating = 'Excellent';
                            else if (value >= 70) rating = 'Good';
                            else if (value >= 40) rating = 'Average';
                            else rating = 'Below Average';
                            
                            return `Rating: ${rating} (${value}/100)`;
                        }
                    }
                }
            }
        }
    });
}
