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

    // Initialize visualization
    initMeasurementPoints();
    initMeasurementLines();
    
    // Add hover effects for measurement table rows
    initTableRowHighlighting();
});

/**
 * Initialize measurement points on the body model
 */
function initMeasurementPoints() {
    const modelVisualization = document.querySelector('.model-visualization');
    if (!modelVisualization) return;
    
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

    // Add points to visualization
    measurementPoints.forEach(point => {
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
 * Initialize measurement lines between points
 */
function initMeasurementLines() {
    const modelVisualization = document.querySelector('.model-visualization');
    if (!modelVisualization) return;
    
    // Define lines between points
    const measurementLines = [
        { from: 'shoulder_left', to: 'shoulder_right', measurement: 'shoulder_width' },
        { from: 'shoulder_right', to: 'arm_right', measurement: 'arm_length' },
        { from: 'shoulder_left', to: 'arm_left', measurement: 'arm_length' },
        { from: 'neck', to: 'waist', measurement: 'torso_length' }
    ];
    
    // Delayed initialization to ensure points are rendered
    setTimeout(() => {
        measurementLines.forEach(line => {
            const fromPoint = document.getElementById(`point-${line.from}`);
            const toPoint = document.getElementById(`point-${line.to}`);
            
            if (fromPoint && toPoint) {
                drawLine(fromPoint, toPoint, line.measurement);
            }
        });
    }, 100);
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