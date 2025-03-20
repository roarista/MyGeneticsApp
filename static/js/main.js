// File upload preview functionality
document.addEventListener('DOMContentLoaded', function() {
    // Check if file input exists
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            // Get the file
            const file = e.target.files[0];
            
            // Check if it's an image
            if (file && file.type.match('image.*')) {
                // Image file validation - Check size
                if (file.size > 5 * 1024 * 1024) { // 5MB limit
                    alert('File size exceeds 5MB. Please choose a smaller image.');
                    fileInput.value = ''; // Clear the file input
                    return;
                }
                
                // Successful selection
                const uploadBtn = document.getElementById('analyze-btn');
                if (uploadBtn) {
                    uploadBtn.textContent = 'Analyze My Genetics';
                    uploadBtn.disabled = false;
                }
            }
        });
    }
    
    // Enable tooltips if any exist
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Enable popovers if any exist
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    if (popoverTriggerList.length > 0) {
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
});

// Form validation enhancement
const validateForm = () => {
    const form = document.getElementById('upload-form');
    if (!form) return true;
    
    const file = document.getElementById('file');
    if (file && (!file.files || file.files.length === 0)) {
        alert('Please select an image to analyze');
        return false;
    }
    
    return true;
};

// Add form validation to the upload form if it exists
const uploadForm = document.getElementById('upload-form');
if (uploadForm) {
    uploadForm.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return false;
        }
        
        // Show loading state
        const button = document.getElementById('analyze-btn');
        if (button) {
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Analyzing...';
            button.disabled = true;
        }
        
        return true;
    });
}
