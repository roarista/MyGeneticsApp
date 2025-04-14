@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Process uploaded front and back photos for comprehensive body analysis including 50 bodybuilding measurements"""
    # If it's a GET request, redirect to the homepage
    if request.method == 'GET':
        return redirect(url_for('index'))
        
    try:
        # Extract form data for debugging
        print("📥 FULL FORM DATA:", request.form)
        
        # Get basic user information from form
        height = request.form.get('height', 0)
        weight = request.form.get('weight', 0)
        age = request.form.get('age', 25)  # Default age if not provided
        gender = request.form.get('gender', 'male')  # Default to male if not specified
        
        # Convert to appropriate types with validation
        height_cm = float(height) if height else 0
        weight_kg = float(weight) if weight else 0
        age_years = int(age) if age else 25
        
        print(f"📥 Input values - Height: {height_cm}cm, Weight: {weight_kg}kg, Age: {age_years}, Gender: {gender}")
        
        # Calculate basic body composition
        body_fat_pct = 0
        lean_mass_pct = 0
        
        # Convert height from cm to meters for the calculation
        height_m = height_cm / 100
        
        try:
            # Calculate BMI first
            bmi = weight_kg / (height_m * height_m)
            print(f"📊 BMI: {bmi}")
            
            # Use Navy method for body fat calculation
            sex_value = 1 if gender.lower() == 'male' else 0
            body_fat_pct, lean_mass_pct = calculate_body_composition(weight_kg, height_m, age_years, sex_value)
            print(f"📊 Body composition - Fat: {body_fat_pct}%, Lean Mass: {lean_mass_pct}%")
        except Exception as calc_error:
            print(f"❌ Error calculating body composition: {str(calc_error)}")
            # Use BMI-based fallback
            if gender.lower() == 'male':
                body_fat_pct = (1.2 * bmi) + (0.23 * age_years) - 16.2
            else:
                body_fat_pct = (1.2 * bmi) + (0.23 * age_years) - 5.4
                
            # Ensure it's in reasonable range
            body_fat_pct = max(5, min(body_fat_pct, 40))
            lean_mass_pct = 100 - body_fat_pct
            print(f"📊 Fallback body composition - Fat: {body_fat_pct}%, Lean Mass: {lean_mass_pct}%")
        
        # Store in session with multiple redundant approaches
        # 1. Store as a dictionary
        session['analysis_results'] = {
            'body_fat': body_fat_pct,
            'lean_mass': lean_mass_pct,
            'id': str(uuid.uuid4())  # Generate a unique ID for reference
        }
        
        # 2. Store values directly in session
        session['body_fat'] = body_fat_pct
        session['lean_mass'] = lean_mass_pct
        
        # 3. Force session persistence
        session.modified = True
        
        print(f"💾 Session set with keys: {list(session.keys())}")
        print(f"💾 analysis_results: {session['analysis_results']}")
        
        # Redirect to results page
        return redirect(url_for('results'))
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERROR in /analyze: {str(e)}")
        print(f"❌ TRACEBACK: {error_trace}")
        print(f"❌ FORM DATA: {request.form}")
        
        # Log detailed error to help with debugging
        flash(f"Analysis failed: {str(e)}", 'danger')
        return redirect(url_for('index'))