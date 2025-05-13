// Replace the existing body type spectrum chart with this updated implementation
// First instance
document.addEventListener('DOMContentLoaded', function() {
    // Body Type Spectrum Chart setup
    const bodyTypeCtx = document.getElementById('bodyTypeSpectrum').getContext('2d');
    
    // Create a horizontal bar chart that serves as the spectrum
    const bodyTypeSpectrum = new Chart(bodyTypeCtx, {
        type: 'bar',
        data: {
            labels: ['Body Type Spectrum'],
            datasets: [
                // Background gradient
                {
                    data: [100],
                    backgroundColor: createSpectrumGradient(),
                    barPercentage: 0.4, // Thinner bar
                    categoryPercentage: 0.5, // Reduced height
                    borderRadius: 8,    // More rounded corners
                    borderWidth: 1,
                    borderColor: 'rgba(255, 255, 255, 0.3)' // Subtle white border
                },
                // Placeholder for user's position indicator
                {
                    data: [0], // Will be handled by plugin
                    backgroundColor: 'rgba(0, 0, 0, 0)',
                    barPercentage: 0,
                    categoryPercentage: 0
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        display: false
                    },
                    ticks: {
                        display: false
                    },
                    border: {
                        display: false
                    }
                },
                markerAxis: {
                    type: 'linear',
                    position: 'top',
                    min: 0,
                    max: 100,
                    offset: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        display: false
                    },
                    border: {
                        display: false
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        display: false
                    },
                    border: {
                        display: false
                    }
                }
            },
            // Disable all animations
            animation: false
        },
        plugins: [{
            id: 'bodyTypeLabels',
            afterDraw: function(chart) {
                const ctx = chart.ctx;
                const width = chart.width;
                const height = chart.height * 0.8; // Adjust for space
                
                ctx.save();
                
                // Draw subtle tick marks on the spectrum
                ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
                for (let i = 0; i <= 10; i++) {
                    const tickX = width * (i / 10);
                    const tickHeight = (i % 5 === 0) ? 10 : 5; // Taller ticks at major points
                    // Move ticks below the bar
                    ctx.fillRect(tickX, height * 0.6 - tickHeight/2, 1, tickHeight);
                }
                
                // Add the type labels
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                
                // Ectomorph label (left)
                ctx.fillStyle = '#3b82f6'; // Blue
                ctx.font = 'bold 14px Arial';
                // Move labels further below the bar
                ctx.fillText('Ectomorph', width * 0.15, height * 0.85);
                
                // Mesomorph label (center)
                ctx.fillStyle = '#10b981'; // Green
                ctx.font = 'bold 14px Arial';
                // Move labels further below the bar
                ctx.fillText('Mesomorph', width * 0.5, height * 0.85);
                
                // Endomorph label (right)
                ctx.fillStyle = '#f59e0b'; // Amber
                ctx.font = 'bold 14px Arial';
                // Move labels further below the bar
                ctx.fillText('Endomorph', width * 0.85, height * 0.85);
                
                // Draw user's body type position marker
                if (body_type) {
                    // Calculate position based on body_type percentage
                    const xPos = width * (position / 100);
                    const yPos = height * 0.25; // Move up above the bar
                    
                    // Draw marker dot (smaller size to avoid overlap)
                    ctx.beginPath();
                    ctx.arc(xPos, yPos, 7, 0, Math.PI * 2);
                    ctx.fillStyle = '#ffffff';
                    ctx.fill();
                    
                    // Draw outer ring
                    ctx.beginPath();
                    ctx.arc(xPos, yPos, 7, 0, Math.PI * 2);
                    ctx.lineWidth = 2;
                    ctx.strokeStyle = '#2563eb'; // Blue border
                    ctx.stroke();
                    
                    // Draw body type text label
                    ctx.textAlign = 'center';
                    ctx.fillStyle = '#ffffff';
                    ctx.font = 'bold 12px Arial';
                    ctx.fillText(body_type.charAt(0).toUpperCase() + body_type.slice(1), xPos, height * 0.95);
                }
                
                ctx.restore();
            }
        }]
    });
    
    // Create a gradient for the spectrum
    function createSpectrumGradient() {
        const gradient = bodyTypeCtx.createLinearGradient(0, 0, bodyTypeCtx.canvas.width, 0);
        gradient.addColorStop(0, '#3b82f6');    // Ectomorph (blue)
        gradient.addColorStop(0.5, '#10b981');  // Mesomorph (green)
        gradient.addColorStop(1, '#f59e0b');    // Endomorph (amber)
        return gradient;
    }
});
