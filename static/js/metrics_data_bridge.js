// Metrics Data Bridge
// This file connects Flask server-side data to client-side JavaScript charts

// These variables will be populated by the Jinja2 template with real data from the server
let bodyType = 'balanced';
let bodyTypePosition = 50;
let metabolicEfficiency = 5.0;
let muscleBuilding = 5.0;
let recoveryCapacity = 5.0;
let shoulderToWaistRatio = 1.6;
let bodyFatPercentage = 15.0;

// Function to initialize all metrics from server data
function initMetricsFromServer(data) {
    if (!data) return;
    
    // Update global variables with real data
    if (data.bodyType) bodyType = data.bodyType;
    if (data.bodyTypePosition) bodyTypePosition = data.bodyTypePosition;
    if (data.metabolicEfficiency) metabolicEfficiency = data.metabolicEfficiency;
    if (data.muscleBuilding) muscleBuilding = data.muscleBuilding;
    if (data.recoveryCapacity) recoveryCapacity = data.recoveryCapacity;
    if (data.shoulderToWaistRatio) shoulderToWaistRatio = data.shoulderToWaistRatio;
    if (data.bodyFatPercentage) bodyFatPercentage = data.bodyFatPercentage;
    
    console.log('Metrics initialized with real data:', data);
}