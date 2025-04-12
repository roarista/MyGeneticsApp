// Advanced Fitness Metrics Charts
// This script implements the Recovery Capacity and Fitness Age Estimation charts
// with dynamic calculations based on user's physical metrics

document.addEventListener('DOMContentLoaded', function() {
    // Initialize recovery capacity chart with calculated values
    initRecoveryCapacityChart();
    
    // Initialize fitness age estimation chart
    initFitnessAgeChart();
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

function initFitnessAgeChart() {
    const ctx = document.getElementById('fitnessAgeChart').getContext('2d');
    if (!ctx) return; // Skip if canvas not found
    
    // Get user data from the page if available (these variables might be defined in the template)
    let chronologicalAge = typeof userAge !== 'undefined' ? userAge : 30; // Default if not available
    const bodyFatPercentage = typeof bodyFatPercent !== 'undefined' ? bodyFatPercent : 20;
    const gender = typeof userGender !== 'undefined' ? userGender : 'male';
    const heightCm = typeof userHeight !== 'undefined' ? userHeight : 175;
    const weightKg = typeof userWeight !== 'undefined' ? userWeight : 75;
    const activityLevel = typeof userActivity !== 'undefined' ? userActivity : 'moderate';

    // Fallback: Try to extract age from the DOM if JS variables aren't available
    if (typeof userAge === 'undefined') {
        const ageElements = document.querySelectorAll('.user-age, .age-value, [data-age]');
        if (ageElements.length > 0) {
            const ageText = ageElements[0].textContent || ageElements[0].dataset.age;
            if (ageText) {
                const ageMatch = ageText.match(/\d+/);
                if (ageMatch) {
                    chronologicalAge = parseInt(ageMatch[0], 10);
                }
            }
        }
    }

    // Calculate fitness age using available metrics
    const fitnessAge = calculateFitnessAge(chronologicalAge, bodyFatPercentage, gender, heightCm, weightKg, activityLevel);
    
    // Determine if fitness age is better or worse than chronological age
    const ageDifference = chronologicalAge - fitnessAge;
    
    // Choose colors based on whether fitness age is better or worse than chronological
    let chronologicalColor = 'rgba(103, 120, 136, 0.8)'; // Neutral gray
    let fitnessColor = ageDifference >= 0 ? 'rgba(16, 185, 129, 0.8)' : 'rgba(239, 68, 68, 0.8)'; // Green if younger, red if older
    
    // Create bar chart comparing chronological age vs fitness age
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Chronological Age', 'Fitness Age'],
            datasets: [{
                data: [chronologicalAge, fitnessAge],
                backgroundColor: [chronologicalColor, fitnessColor],
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Age: ${Math.round(context.raw)} years`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#fff' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#fff' },
                    suggestedMin: Math.min(fitnessAge, chronologicalAge) * 0.8,
                    suggestedMax: Math.max(fitnessAge, chronologicalAge) * 1.2
                }
            }
        },
        plugins: [{
            id: 'fitnessAgeText',
            afterDraw: function(chart) {
                const ctx = chart.ctx;
                const width = chart.width;
                const height = chart.height;
                
                // Add a semi-transparent overlay with age difference
                ctx.save();
                
                // Add semi-transparent background
                ctx.fillStyle = 'rgba(17, 24, 39, 0.7)';
                ctx.fillRect(width * 0.6, height * 0.05, width * 0.35, height * 0.25);
                ctx.strokeStyle = ageDifference >= 0 ? '#10b981' : '#ef4444'; // Green if younger, red if older
                ctx.lineWidth = 2;
                ctx.strokeRect(width * 0.6, height * 0.05, width * 0.35, height * 0.25);
                
                // Add age difference text
                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 16px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                
                // Show age difference with sign (+ means younger fitness age, - means older)
                const differenceText = Math.abs(ageDifference) < 1 ? 
                    'Age Aligned' : 
                    `${ageDifference >= 0 ? '+' : ''}${Math.round(ageDifference)} years`;
                ctx.fillText(differenceText, width * 0.78, height * 0.15);
                
                // Add status text
                ctx.font = '12px Arial';
                ctx.fillStyle = ageDifference >= 5 ? '#10b981' : // Much younger
                               ageDifference >= 0 ? '#3b82f6' : // Slightly younger
                               ageDifference >= -5 ? '#f59e0b' : // Slightly older
                               '#ef4444'; // Much older
                               
                const statusText = getAgeComparisonStatus(ageDifference);
                ctx.fillText(statusText, width * 0.78, height * 0.23);
                
                ctx.restore();
            }
        }]
    });
}

// Calculate estimated fitness age based on available metrics
function calculateFitnessAge(chronologicalAge, bodyFatPercentage, gender, height, weight, activityLevel) {
    // Default to chronological age if insufficient data
    if (!bodyFatPercentage || !gender) {
        return chronologicalAge;
    }
    
    // Activity level multipliers
    const activityMultipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9
    };
    
    // Get activity multiplier (default to moderate if not specified)
    const activityMultiplier = activityMultipliers[activityLevel] || activityMultipliers.moderate;
    
    // Calculate BMI
    const heightM = height / 100;
    const bmi = weight / (heightM * heightM);
    
    // Estimate VO2 max using a simplified formula based on body fat and age
    // This is a simplification of the Jackson formula
    let estimatedVo2Max;
    
    if (gender.toLowerCase() === 'male') {
        // For males
        estimatedVo2Max = 56.2 - (0.413 * chronologicalAge) - (0.4 * bodyFatPercentage);
    } else {
        // For females
        estimatedVo2Max = 44.3 - (0.413 * chronologicalAge) - (0.4 * bodyFatPercentage);
    }
    
    // Apply activity level adjustment to VO2 max
    estimatedVo2Max *= (0.8 + (activityMultiplier / 5));
    
    // Calculate fitness age using the simplified formula:
    // Fitness Age = Real Age - (VO2 max adjustment)
    // This approximates the Norwegian formula from NTNU research
    let fitnessAge = 60 - ((estimatedVo2Max - 20) * 0.5);
    
    // Apply a BMI correction
    // Higher BMI tends to correlate with higher fitness age
    if (bmi > 25) {
        fitnessAge += (bmi - 25) * 0.5;
    } else if (bmi < 18.5) {
        fitnessAge += (18.5 - bmi) * 0.3; // Being underweight can also negatively impact fitness age
    }
    
    // Ensure fitness age doesn't go below 15 or above 100
    fitnessAge = Math.max(15, Math.min(100, fitnessAge));
    
    return fitnessAge;
}

// Get status text based on the age difference
function getAgeComparisonStatus(ageDifference) {
    if (ageDifference >= 10) return "Exceptional";
    if (ageDifference >= 5) return "Excellent";
    if (ageDifference >= 2) return "Good";
    if (ageDifference >= -2) return "Average";
    if (ageDifference >= -5) return "Below Average";
    if (ageDifference >= -10) return "Poor";
    return "Concerning";
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
    
    console.log('Calculated recovery capacity:', recoveryScore, 
                'Using metrics - metabolicEfficiency:', metabolicEfficiency, 
                'bodyType:', bodyType, 
                'muscleBuilding:', muscleBuilding);
    
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