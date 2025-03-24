/**
 * 3D Scan Visualization and Interaction
 * 
 * This script manages the visualization of 3D scan data points,
 * measurement display, and interactive elements on the human body model.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the 3D scan results page
    if (!document.querySelector('.model-visualization')) {
        return;
    }

    // Initialize the model with front view
    initModelView('front');
    
    // Add hover effects for measurement table rows
    initTableRowHighlighting();
    
    // Initialize view toggles
    initViewToggle();
    
    // Initialize zoom controls
    initZoomControls();
});

/**
 * Initialize the view toggle buttons
 */
function initViewToggle() {
    const viewToggleButtons = document.querySelectorAll('.view-toggle-btn');
    
    viewToggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            viewToggleButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get view type
            const viewType = this.getAttribute('data-view');
            
            // Update model view
            initModelView(viewType);
        });
    });
}

/**
 * Initialize zoom controls for the model visualization
 */
function initZoomControls() {
    const zoomInBtn = document.getElementById('zoom-in-btn');
    const zoomOutBtn = document.getElementById('zoom-out-btn');
    const resetViewBtn = document.getElementById('reset-view-btn');
    const modelVisualization = document.querySelector('.model-visualization');
    
    let scale = 1;
    const maxScale = 1.5;
    const minScale = 0.8;
    
    if (zoomInBtn) {
        zoomInBtn.addEventListener('click', function() {
            if (scale < maxScale) {
                scale += 0.1;
                updateScale();
            }
        });
    }
    
    if (zoomOutBtn) {
        zoomOutBtn.addEventListener('click', function() {
            if (scale > minScale) {
                scale -= 0.1;
                updateScale();
            }
        });
    }
    
    if (resetViewBtn) {
        resetViewBtn.addEventListener('click', function() {
            scale = 1;
            updateScale();
            
            // Reset any active points
            document.querySelectorAll('.measurement-point.active').forEach(point => {
                point.classList.remove('active');
            });
            
            // Reset any highlighted table rows
            resetHighlights();
        });
    }
    
    function updateScale() {
        if (modelVisualization) {
            modelVisualization.style.transform = `scale(${scale})`;
        }
    }
}

/**
 * Initialize the model view based on view type (front, side, measurements)
 */
function initModelView(viewType) {
    const modelVisualization = document.querySelector('.model-visualization');
    if (!modelVisualization) return;
    
    // Clear previous content
    modelVisualization.innerHTML = '';
    
    // Set background image based on view type
    if (viewType === 'front') {
        modelVisualization.style.backgroundImage = "url('/static/images/body-model-outline.svg')";
        initFrontViewMeasurements();
    } else if (viewType === 'side') {
        modelVisualization.style.backgroundImage = "url('/static/images/body-model-side.svg')";
        initSideViewMeasurements();
    } else if (viewType === 'measurements') {
        modelVisualization.style.backgroundImage = 'none';
        initMeasurementsView();
    }
}

/**
 * Initialize front view measurement points
 */
function initFrontViewMeasurements() {
    // Define measurement points with positions (percentage based positions)
    const measurementPoints = [
        { id: 'neck', label: 'Neck', x: 50, y: 15, measurement: 'neck_circumference' },
        { id: 'chest', label: 'Chest', x: 50, y: 25, measurement: 'chest_circumference' },
        { id: 'shoulder_right', label: 'Shoulder', x: 70, y: 20, measurement: 'shoulder_width' },
        { id: 'shoulder_left', label: 'Shoulder', x: 30, y: 20, measurement: 'shoulder_width' },
        { id: 'arm_right', label: 'Arm', x: 75, y: 35, measurement: 'arm_circumference' },
        { id: 'arm_left', label: 'Arm', x: 25, y: 35, measurement: 'arm_circumference' },
        { id: 'waist', label: 'Waist', x: 50, y: 40, measurement: 'waist_circumference' },
        { id: 'hip', label: 'Hip', x: 50, y: 50, measurement: 'hip_circumference' },
        { id: 'thigh_right', label: 'Thigh', x: 60, y: 60, measurement: 'thigh_circumference' },
        { id: 'thigh_left', label: 'Thigh', x: 40, y: 60, measurement: 'thigh_circumference' },
        { id: 'calf_right', label: 'Calf', x: 60, y: 75, measurement: 'calf_circumference' },
        { id: 'calf_left', label: 'Calf', x: 40, y: 75, measurement: 'calf_circumference' },
        { id: 'wrist_right', label: 'Wrist', x: 80, y: 45, measurement: 'wrist_circumference' },
        { id: 'wrist_left', label: 'Wrist', x: 20, y: 45, measurement: 'wrist_circumference' }
    ];
    
    addMeasurementPoints(measurementPoints);
    
    // Define lines between points
    const measurementLines = [
        { from: 'shoulder_left', to: 'shoulder_right', measurement: 'shoulder_width' },
        { from: 'shoulder_right', to: 'arm_right', measurement: 'arm_length' },
        { from: 'shoulder_left', to: 'arm_left', measurement: 'arm_length' },
        { from: 'neck', to: 'waist', measurement: 'torso_length' }
    ];
    
    // Delayed initialization to ensure points are rendered
    setTimeout(() => {
        addMeasurementLines(measurementLines);
    }, 100);
}

/**
 * Initialize side view measurement points
 */
function initSideViewMeasurements() {
    // Define measurement points with positions (percentage based positions)
    const measurementPoints = [
        { id: 'neck_side', label: 'Neck', x: 50, y: 15, measurement: 'neck_circumference' },
        { id: 'chest_side', label: 'Chest', x: 50, y: 25, measurement: 'chest_circumference' },
        { id: 'shoulder_side', label: 'Shoulder', x: 65, y: 17, measurement: 'shoulder_width' },
        { id: 'arm_side', label: 'Arm', x: 70, y: 35, measurement: 'arm_circumference' },
        { id: 'waist_side', label: 'Waist', x: 50, y: 40, measurement: 'waist_circumference' },
        { id: 'hip_side', label: 'Hip', x: 50, y: 50, measurement: 'hip_circumference' },
        { id: 'thigh_side', label: 'Thigh', x: 50, y: 60, measurement: 'thigh_circumference' },
        { id: 'calf_side', label: 'Calf', x: 50, y: 75, measurement: 'calf_circumference' }
    ];
    
    addMeasurementPoints(measurementPoints);
    
    // Define lines between points for side view
    const measurementLines = [
        { from: 'neck_side', to: 'waist_side', measurement: 'torso_length' },
        { from: 'shoulder_side', to: 'arm_side', measurement: 'arm_length' },
        { from: 'hip_side', to: 'thigh_side', measurement: 'leg_length' }
    ];
    
    // Delayed initialization to ensure points are rendered
    setTimeout(() => {
        addMeasurementLines(measurementLines);
    }, 100);
}

/**
 * Initialize measurements view with body composition visualization
 */
function initMeasurementsView() {
    const modelVisualization = document.querySelector('.model-visualization');
    if (!modelVisualization) return;
    
    // Create container for composition visualization
    const compositionContainer = document.createElement('div');
    compositionContainer.className = 'composition-visualization';
    compositionContainer.style.textAlign = 'center';
    compositionContainer.style.padding = '2rem';
    
    // Create heading
    const heading = document.createElement('h4');
    heading.className = 'mb-4';
    heading.innerHTML = '<i class="fas fa-chart-pie me-2"></i>Body Composition Overview';
    compositionContainer.appendChild(heading);
    
    // Create composition chart container
    const chartContainer = document.createElement('div');
    chartContainer.style.height = '300px';
    chartContainer.style.maxWidth = '500px';
    chartContainer.style.margin = '0 auto';
    
    // Add canvas for chart
    const canvas = document.createElement('canvas');
    canvas.id = 'compositionChart';
    chartContainer.appendChild(canvas);
    compositionContainer.appendChild(chartContainer);
    
    // Create legend
    const legend = document.createElement('div');
    legend.className = 'composition-legend d-flex justify-content-center mt-4 flex-wrap';
    legend.innerHTML = `
        <div class="px-3 py-2 me-3 mb-2" style="background-color: rgba(41, 182, 246, 0.2); border-radius: 5px;">
            <i class="fas fa-water me-2"></i>Lean Mass
        </div>
        <div class="px-3 py-2 me-3 mb-2" style="background-color: rgba(255, 193, 7, 0.2); border-radius: 5px;">
            <i class="fas fa-fire me-2"></i>Fat Mass
        </div>
        <div class="px-3 py-2 mb-2" style="background-color: rgba(76, 175, 80, 0.2); border-radius: 5px;">
            <i class="fas fa-bone me-2"></i>Bone Mass
        </div>
    `;
    compositionContainer.appendChild(legend);
    
    // Add measurement info
    const info = document.createElement('div');
    info.className = 'mt-4 text-center';
    info.innerHTML = `
        <p class="text-muted mb-2">
            <i class="fas fa-info-circle me-2"></i>Click on chart segments for detailed information
        </p>
        <p class="small text-muted">
            Body composition analysis is based on 3D volumetric calculations and correlations with Navy Method formulas.
        </p>
    `;
    compositionContainer.appendChild(info);
    
    modelVisualization.appendChild(compositionContainer);
    
    // Create composition chart
    setTimeout(() => {
        createCompositionChart();
    }, 100);
}

/**
 * Create body composition chart
 */
function createCompositionChart() {
    const ctx = document.getElementById('compositionChart');
    if (!ctx) return;
    
    // Get composition data from the page if available
    let leanMass = 80;
    let fatMass = 15;
    let boneMass = 5;
    
    // Look for the actual values in the page
    const leanMassElement = document.querySelector('div.stat-value:not(.text-primary):not(.text-success):not(.text-info):not(.text-warning):not(.text-danger)');
    if (leanMassElement && leanMassElement.textContent.includes('%')) {
        const match = leanMassElement.textContent.match(/(\d+\.?\d*)%/);
        if (match && match[1]) {
            leanMass = parseFloat(match[1]);
        }
    }
    
    const fatMassElement = document.querySelector('div.stat-value:not(.text-primary):not(.text-success):not(.text-info):not(.text-warning):not(.text-danger)');
    if (fatMassElement && fatMassElement.textContent.includes('%')) {
        const match = fatMassElement.textContent.match(/(\d+\.?\d*)%/);
        if (match && match[1]) {
            fatMass = parseFloat(match[1]);
            leanMass = 100 - fatMass - boneMass;
        }
    }
    
    // Create chart using Chart.js if available
    if (typeof Chart !== 'undefined') {
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Lean Mass', 'Fat Mass', 'Bone Mass'],
                datasets: [{
                    label: 'Body Composition',
                    data: [leanMass, fatMass, boneMass],
                    backgroundColor: [
                        'rgba(41, 182, 246, 0.7)',
                        'rgba(255, 193, 7, 0.7)',
                        'rgba(76, 175, 80, 0.7)'
                    ],
                    borderColor: [
                        'rgba(41, 182, 246, 1)',
                        'rgba(255, 193, 7, 1)',
                        'rgba(76, 175, 80, 1)'
                    ],
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
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.raw}%`;
                            }
                        }
                    }
                }
            }
        });
    } else {
        // Fallback if Chart.js is not available
        ctx.parentNode.innerHTML = `
            <div style="text-align: center; padding: 50px 0;">
                <p><i class="fas fa-chart-pie" style="font-size: 3rem; opacity: 0.3;"></i></p>
                <p class="mt-3">Composition breakdown:</p>
                <p>Lean Mass: ${leanMass}% | Fat Mass: ${fatMass}% | Bone Mass: ${boneMass}%</p>
            </div>
        `;
    }
}

/**
 * Add measurement points to the visualization
 */
function addMeasurementPoints(points) {
    const modelVisualization = document.querySelector('.model-visualization');
    if (!modelVisualization) return;
    
    points.forEach(point => {
        // Get measurement value if available in the document
        let measurementValue = '';
        const measurementRow = document.querySelector(`tr[data-measurement="${point.measurement}"]`);
        if (measurementRow) {
            const valueCell = measurementRow.querySelector('td:nth-child(2)');
            if (valueCell) {
                measurementValue = valueCell.textContent.trim();
            }
        }
        
        // Create point element
        const pointElement = document.createElement('div');
        pointElement.className = 'measurement-point';
        pointElement.id = `point-${point.id}`;
        pointElement.setAttribute('data-label', `${point.label}: ${measurementValue}`);
        pointElement.setAttribute('data-measurement', point.measurement);
        pointElement.style.left = `${point.x}%`;
        pointElement.style.top = `${point.y}%`;

        // Add click handler
        pointElement.addEventListener('click', function() {
            // Highlight corresponding row in the measurements table
            highlightTableRow(this.getAttribute('data-measurement'));
            
            // Highlight the point
            document.querySelectorAll('.measurement-point').forEach(p => {
                p.classList.remove('active');
            });
            this.classList.add('active');
        });
        
        modelVisualization.appendChild(pointElement);
    });
}

/**
 * Add measurement lines between points
 */
function addMeasurementLines(lines) {
    lines.forEach(line => {
        const fromPoint = document.getElementById(`point-${line.from}`);
        const toPoint = document.getElementById(`point-${line.to}`);
        
        if (fromPoint && toPoint) {
            drawLine(fromPoint, toPoint, line.measurement);
        }
    });
}

/**
 * Draw a line between two measurement points
 */
function drawLine(fromPoint, toPoint, measurement) {
    const modelVisualization = document.querySelector('.model-visualization');
    if (!modelVisualization) return;
    
    // Get positions
    const fromRect = fromPoint.getBoundingClientRect();
    const toRect = toPoint.getBoundingClientRect();
    const containerRect = modelVisualization.getBoundingClientRect();
    
    // Calculate relative positions
    const fromX = fromRect.left + fromRect.width/2 - containerRect.left;
    const fromY = fromRect.top + fromRect.height/2 - containerRect.top;
    const toX = toRect.left + toRect.width/2 - containerRect.left;
    const toY = toRect.top + toRect.height/2 - containerRect.top;
    
    // Calculate line length and angle
    const length = Math.sqrt(Math.pow(toX - fromX, 2) + Math.pow(toY - fromY, 2));
    const angle = Math.atan2(toY - fromY, toX - fromX) * 180 / Math.PI;
    
    // Create line element
    const lineElement = document.createElement('div');
    lineElement.className = 'measurement-line';
    lineElement.setAttribute('data-measurement', measurement);
    
    // Position and rotate line
    lineElement.style.width = `${length}px`;
    lineElement.style.left = `${fromX}px`;
    lineElement.style.top = `${fromY}px`;
    lineElement.style.transform = `rotate(${angle}deg)`;
    
    modelVisualization.appendChild(lineElement);
}

/**
 * Initialize hover effects for measurement table rows
 */
function initTableRowHighlighting() {
    // Add data-measurement attributes to table rows if not already present
    document.querySelectorAll('.table tbody tr').forEach(row => {
        const measurementName = row.querySelector('td:first-child').textContent.trim().toLowerCase().replace(/ /g, '_');
        row.setAttribute('data-measurement', measurementName);
        
        // Add hover effect
        row.addEventListener('mouseenter', function() {
            const measurement = this.getAttribute('data-measurement');
            highlightMeasurementPoint(measurement);
        });
        
        row.addEventListener('mouseleave', function() {
            resetHighlights();
        });
    });
}

/**
 * Highlight a specific table row
 */
function highlightTableRow(measurement) {
    resetHighlights();
    
    const row = document.querySelector(`tr[data-measurement="${measurement}"]`);
    if (row) {
        row.classList.add('highlight');
        // Scroll to the row if needed
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/**
 * Highlight specific measurement points and lines
 */
function highlightMeasurementPoint(measurement) {
    // Highlight all points associated with this measurement
    document.querySelectorAll(`.measurement-point[data-measurement="${measurement}"]`).forEach(point => {
        point.classList.add('highlight');
    });
    
    // Highlight all lines associated with this measurement
    document.querySelectorAll(`.measurement-line[data-measurement="${measurement}"]`).forEach(line => {
        line.classList.add('highlight');
    });
}

/**
 * Reset all highlights
 */
function resetHighlights() {
    document.querySelectorAll('.measurement-point.highlight, .measurement-line.highlight, tr.highlight').forEach(element => {
        element.classList.remove('highlight');
    });
}