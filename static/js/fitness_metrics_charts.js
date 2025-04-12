// Advanced Fitness Metrics Charts
// This script implements the Recovery Capacity and Body Composition Estimation charts
// with dynamic calculations based on user's physical metrics

// Do not initialize charts on DOM load, let metrics_data_bridge.js initialize them after metrics are loaded
// This ensures data values are properly set before charts are rendered

// Function to initialize all charts - called by metrics_data_bridge.js
function initAllFitnessCharts() {
    console.log('Initializing fitness charts...');
    
    // Initialize recovery capacity chart with calculated values
    initRecoveryCapacityChart();
    
    // Initialize body composition estimation chart
    initBodyCompositionChart();
}

function initRecoveryCapacityChart() {
    const ctx = document.getElementById('recoveryCapacityChart').getContext('2d');
    if (!ctx) return; // Skip if canvas not found
    
    // Calculate recovery capacity based on available metrics
    const recoveryScore = calculateRecoveryCapacity();
    const remainingScore = 10 - recoveryScore;
    
    // Get recovery rating text based on score
    const ratingText = getRecoveryRating(recoveryScore);
    const ratingColor = getRecoveryRatingColor(recoveryScore);
    
    // Create a recovery capacity gauge chart
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [recoveryScore, remainingScore],
                backgroundColor: [
                    ratingColor,  // Dynamic color based on score
                    'rgba(31, 41, 55, 0.2)'  // Dark background
                ],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        },
        plugins: [{
            id: 'recoveryText',
            afterDraw: function(chart) {
                const width = chart.width;
                const height = chart.height;
                const ctx = chart.ctx;
                
                ctx.restore();
                
                // Font settings for score
                const fontSize = (height / 10).toFixed(2);
                ctx.font = fontSize + "px Arial";
                ctx.textBaseline = "middle";
                ctx.fillStyle = "#fff";
                
                // Display score
                const scoreText = recoveryScore.toFixed(1);
                const textX = width / 2;
                const textY = height - (height / 3);
                
                ctx.textAlign = "center";
                ctx.fillText(scoreText + "/10", textX, textY);
                
                // Add rating text
                ctx.font = (fontSize * 0.6) + "px Arial";
                ctx.fillStyle = ratingColor;
                ctx.fillText(ratingText, textX, textY + fontSize * 1.2);
                
                ctx.save();
            }
        }]
    });
}

function initBodyCompositionChart() {
    const ctx = document.getElementById('bodyCompositionChart');
    if (!ctx) {
        console.error('Body composition chart canvas not found!');
        return; 
    }
    
    // Force clear any existing charts to prevent conflicts
    if (window.bodyCompChart) {
        window.bodyCompChart.destroy();
    }
    
    const context2d = ctx.getContext('2d');
    if (!context2d) {
        console.error('Could not get 2D context for body composition chart');
        return;
    }
    
    // Get body composition percentages - ensure they're proper numbers, not strings
    let fatPercentage = parseFloat(bodyFatPercentage) || 20;
    
    // Always calculate lean mass directly from body fat to ensure they sum to 100%
    // This overrides any existing leanMassPercentage value for mathematical consistency
    let leanMassPercentage = 100 - fatPercentage;
    
    // Light logging to track chart initialization
    console.log('Body composition values:');
    console.log('- Body Fat %:', fatPercentage.toFixed(1));
    console.log('- Lean Mass %:', leanMassPercentage.toFixed(1));
    
    // Mark container as having data
    const container = ctx.closest('.chart-container');
    if (container) {
        container.classList.add('has-data');
    }
    
    // Create body composition donut chart with guaranteed numeric values
    window.bodyCompChart = new Chart(context2d, {
        type: 'doughnut',
        data: {
            labels: ['Body Fat', 'Lean Mass'],
            datasets: [{
                data: [fatPercentage, leanMassPercentage],
                backgroundColor: [
                    '#ef4444', // red for fat
                    '#10b981'  // green for lean mass
                ],
                borderWidth: 1,
                borderColor: '#1f2937'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#fff',
                        padding: 10,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            return `${context.label}: ${value.toFixed(1)}%`;
                        }
                    }
                }
            }
        },
        plugins: [{
            id: 'bodyCompositionText',
            afterDraw: function(chart) {
                const width = chart.width;
                const height = chart.height;
                const ctx = chart.ctx;
                
                ctx.restore();
                ctx.textBaseline = "middle";
                
                // Draw fat mass in center
                const fontSize = (height / 10).toFixed(2);
                ctx.font = "bold " + fontSize + "px Arial";
                ctx.fillStyle = '#ef4444';
                ctx.textAlign = "center";
                
                // Fat percentage in center - ensure number formatting
                const fatText = `${fatPercentage.toFixed(1)}%`;
                ctx.fillText(fatText, width / 2, height / 2 - fontSize / 2);
                
                // Smaller "Body Fat" text
                ctx.font = (fontSize * 0.5) + "px Arial";
                ctx.fillStyle = '#fff';
                ctx.fillText("Body Fat", width / 2, height / 2 + fontSize);
                
                // Get category based on gender and body fat percentage
                let category = "";
                let categoryColor = "";
                
                if (gender && gender.toLowerCase() === 'male') {
                    if (fatPercentage < 6) {
                        category = "Essential Fat";
                        categoryColor = "#f59e0b"; // amber - too low can be unhealthy
                    } else if (fatPercentage < 14) {
                        category = "Athletic";
                        categoryColor = "#10b981"; // green
                    } else if (fatPercentage < 18) {
                        category = "Fitness";
                        categoryColor = "#3b82f6"; // blue
                    } else if (fatPercentage < 25) {
                        category = "Average";
                        categoryColor = "#f59e0b"; // amber
                    } else {
                        category = "Excess";
                        categoryColor = "#ef4444"; // red
                    }
                } else {
                    // Female or undefined - use female ranges
                    if (fatPercentage < 14) {
                        category = "Essential Fat";
                        categoryColor = "#f59e0b"; // amber - too low can be unhealthy
                    } else if (fatPercentage < 21) {
                        category = "Athletic";
                        categoryColor = "#10b981"; // green
                    } else if (fatPercentage < 25) {
                        category = "Fitness";
                        categoryColor = "#3b82f6"; // blue
                    } else if (fatPercentage < 32) {
                        category = "Average";
                        categoryColor = "#f59e0b"; // amber
                    } else {
                        category = "Excess";
                        categoryColor = "#ef4444"; // red
                    }
                }
                
                // Add category text
                ctx.font = (fontSize * 0.6) + "px Arial";
                ctx.fillStyle = categoryColor;
                ctx.fillText(category, width / 2, height / 2 + fontSize * 2);
                
                ctx.save();
            }
        }]
    });
    
    // Log success
    console.log('Body composition chart successfully initialized');
}

// Calculate recovery capacity based on available metrics
function calculateRecoveryCapacity() {
    // Default to a moderate value if metrics are unavailable
    let recoveryScore = 5.0;
    
    // If we have the necessary metrics, calculate a more precise score
    if (typeof metabolicEfficiency !== 'undefined' && 
        typeof bodyType !== 'undefined' && 
        typeof muscleBuilding !== 'undefined') {
        
        // Base recovery on metabolic efficiency (0-10 scale)
        let baseRecovery = metabolicEfficiency;
        
        // Adjust for body type
        let bodyTypeMultiplier = 1.0;
        if (bodyType === 'ectomorph') {
            bodyTypeMultiplier = 1.2; // Better recovery for ectomorphs
        } else if (bodyType === 'endomorph') {
            bodyTypeMultiplier = 0.9; // Slower recovery for endomorphs
        } else if (bodyType === 'mesomorph') {
            bodyTypeMultiplier = 1.1; // Good recovery for mesomorphs
        } else if (bodyType === 'ecto-mesomorph') {
            bodyTypeMultiplier = 1.15; // Mix of ecto and meso
        } else if (bodyType === 'endo-mesomorph') {
            bodyTypeMultiplier = 1.0; // Mix of endo and meso
        }
        
        // Adjust for muscle building potential
        let mbpFactor = muscleBuilding;
        
        // Calculate final score (0-10 scale)
        recoveryScore = (baseRecovery * 0.6) + 
                        (bodyTypeMultiplier * 2) + 
                        (mbpFactor * 0.2);
        
        // Ensure the score is within bounds
        recoveryScore = Math.max(1, Math.min(9.5, recoveryScore));
    } else if (recoveryCapacity) {
        // Use pre-calculated recovery capacity from server if available
        recoveryScore = recoveryCapacity;
    }
    
    // Recovery capacity calculation complete
    console.log('Recovery capacity score:', recoveryScore.toFixed(1));
    
    return recoveryScore;
}

// Get text rating based on recovery score
function getRecoveryRating(score) {
    if (score >= 8.5) return "Excellent";
    if (score >= 7.0) return "Above Average";
    if (score >= 5.0) return "Average";
    if (score >= 3.5) return "Below Average";
    return "Poor";
}

// Get color for recovery rating
function getRecoveryRatingColor(score) {
    if (score >= 8.5) return '#10b981'; // green
    if (score >= 7.0) return '#3b82f6'; // blue
    if (score >= 5.0) return '#f59e0b'; // amber
    if (score >= 3.5) return '#f97316'; // orange
    return '#ef4444'; // red
}

// Calculate training volume response based on metrics
function calculateTrainingVolumeResponse() {
    // Default response pattern if metrics unavailable
    let response = [4, 7, 5, 2];
    
    // If we have recovery capacity and body type, calculate a more specific response
    if (typeof recoveryCapacity !== 'undefined' && typeof bodyType !== 'undefined') {
        // Ectomorph - better with moderate volume
        if (bodyType === 'ectomorph') {
            response = [5, 8, 4, 1];
        } 
        // Mesomorph - responds well to high volume
        else if (bodyType === 'mesomorph') {
            response = [3, 6, 8, 5];
        }
        // Endomorph - best with lower to moderate volume
        else if (bodyType === 'endomorph') {
            response = [7, 6, 3, 1];
        }
        // Mixed types
        else if (bodyType === 'ecto-mesomorph') {
            response = [4, 7, 6, 3];
        }
        else if (bodyType === 'endo-mesomorph') {
            response = [5, 7, 5, 2];
        }
        
        // Adjust for recovery capacity
        if (recoveryCapacity >= 8) {
            // Better recovery = better response to higher volume
            response[2] += 1; // High
            response[3] += 1; // Very High
        } else if (recoveryCapacity <= 4) {
            // Poor recovery = better response to lower volume
            response[0] += 1; // Low
            response[1] += 1; // Moderate
            response[2] -= 1; // High
            response[3] -= 1; // Very High
        }
    }
    
    return response;
}