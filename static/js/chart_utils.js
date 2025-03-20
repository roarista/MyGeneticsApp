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
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Your Genetic Traits',
                data: chartData.values,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                pointBackgroundColor: chartData.colors,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 100,
                    ticks: {
                        stepSize: 25
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
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
