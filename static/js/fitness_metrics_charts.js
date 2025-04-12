// Advanced Fitness Metrics Charts
// This script implements the Recovery Capacity and Training Volume Tolerance charts
// with dynamic calculations based on user's physical metrics

document.addEventListener('DOMContentLoaded', function() {
    // Initialize recovery capacity chart with calculated values
    initRecoveryCapacityChart();
    
    // Initialize training volume tolerance chart
    initTrainingVolumeChart();
});

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

function initTrainingVolumeChart() {
    const ctx = document.getElementById('trainingVolumeChart').getContext('2d');
    if (!ctx) return; // Skip if canvas not found
    
    // Calculate training volume response values based on metrics
    const volumeResponse = calculateTrainingVolumeResponse();
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Low', 'Moderate', 'High', 'Very High'],
            datasets: [{
                label: 'Response',
                data: volumeResponse,
                backgroundColor: [
                    'rgba(59, 130, 246, 0.7)',  // blue
                    'rgba(16, 185, 129, 0.7)',  // green
                    'rgba(245, 158, 11, 0.7)',  // amber
                    'rgba(239, 68, 68, 0.7)'    // red
                ],
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: {
                        color: '#fff',
                        font: { size: 10 }
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 10,
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: {
                        color: '#fff',
                        stepSize: 2
                    }
                }
            }
        }
    });
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
        let baseRecovery = metabolicEfficiency / 10;
        
        // Adjust for body type
        let bodyTypeMultiplier = 1.0;
        if (bodyType === 'ectomorph') {
            bodyTypeMultiplier = 1.2; // Better recovery for ectomorphs
        } else if (bodyType === 'endomorph') {
            bodyTypeMultiplier = 0.9; // Slower recovery for endomorphs
        } else if (bodyType === 'mesomorph') {
            bodyTypeMultiplier = 1.1; // Good recovery for mesomorphs
        }
        
        // Adjust for muscle building potential
        let mbpFactor = muscleBuilding / 10;
        
        // Calculate final score (0-10 scale)
        recoveryScore = baseRecovery * bodyTypeMultiplier * (1 + mbpFactor * 0.2);
        
        // Ensure the score is within bounds
        recoveryScore = Math.max(1, Math.min(9.5, recoveryScore));
    }
    
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