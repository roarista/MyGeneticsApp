@app.route('/workout/<analysis_id>')
def workout(analysis_id):
    """Display detailed workout plan based on analysis results and user's weak points"""
    try:
        # Start with detailed logging
        logger.info(f"Accessing workout page for analysis_id: {analysis_id}")
        
        # Check if analysis exists
        if analysis_id not in analysis_results:
            logger.warning(f"Analysis not found with ID: {analysis_id}")
            flash('Analysis not found', 'danger')
            return redirect(url_for('profile'))
        
        # Get the result
        result = analysis_results[analysis_id]
        logger.debug(f"Retrieved analysis result for ID: {analysis_id}")
        
        # Import the WorkoutPlanner
        from utils.workout_planner import WorkoutPlanner
        
        # Create user data dictionary for workout planner
        user_data = {
            'gender': result['user_info'].get('gender', 'male'),
            'height_cm': result['user_info'].get('height_cm', 175),
            'weight_kg': result['user_info'].get('weight_kg', 75),
            'experience': result['user_info'].get('experience', 'beginner'),
            'body_fat_percentage': result.get('body_fat_percentage', 20),
            'measurements': result.get('measurements', {}),
            'traits': result.get('traits', {})
        }
        
        # Generate personalized workout plan
        logger.debug(f"Generating personalized workout plan based on physique analysis")
        workout_planner = WorkoutPlanner()
        workout_data = workout_planner.generate_workout_plan(user_data)
        
        # Extract data from the workout plan
        workout_plan = workout_data['workout_plan']
        analysis = workout_data['analysis']
        training_tips = workout_data['training_tips']
        equipment = workout_data['equipment']
        progression_methods = workout_data['progression_methods']
        
        # Process traits to include their units for display
        formatted_traits = {}
        for trait_name, trait_data in result['traits'].items():
            try:
                # For traits that are dictionaries with value keys
                if isinstance(trait_data, dict) and 'value' in trait_data:
                    # Copy the trait data
                    formatted_trait = trait_data.copy()
                    # Format the value with units
                    formatted_trait['display_value'] = format_trait_value(trait_name, trait_data['value'])
                    formatted_trait['unit'] = get_unit(trait_name)
                    formatted_traits[trait_name] = formatted_trait
                else:
                    # For other types of traits
                    formatted_traits[trait_name] = trait_data
            except Exception as trait_error:
                logger.error(f"Error formatting trait {trait_name}: {str(trait_error)}")
                formatted_traits[trait_name] = trait_data
        
        # Get user genetic traits and experience
        logger.debug(f"Processing user genetic traits for workout planning")
        experience = user_data['experience']
        
        # Use weak points identified by the workout planner
        weak_points = analysis['focus_areas']
        
        # Create the basic measurements for the left panel
        basic_measurements = {}
        measurements = result.get('measurements', {})
        
        # Extract main measurements for display
        if measurements:
            basic_measurements = {
                'shoulder_width': measurements.get('shoulder_width_cm', 0),
                'chest_circumference': measurements.get('chest_circumference_cm', 0),
                'arm_circumference': measurements.get('arm_circumference_cm', 0),
                'waist_circumference': measurements.get('waist_circumference_cm', 0),
                'thigh_circumference': measurements.get('thigh_circumference_cm', 0),
                'calf_circumference': measurements.get('calf_circumference_cm', 0)
            }
        
        # Parse proportion measurements for display
        proportion_measurements = {}
        for key, value in measurements.items():
            if 'ratio' in key or 'proportion' in key:
                proportion_measurements[key] = value
        
        # Separate left and right side measurements for comparison
        circumference_measurements_left = {}
        circumference_measurements_right = {}
        
        for key, value in measurements.items():
            if 'left' in key and 'circumference' in key:
                # Clean up the key name for display
                display_key = key.replace('left_', '').replace('_cm', '').replace('_', ' ').title()
                circumference_measurements_left[display_key] = value
            elif 'right' in key and 'circumference' in key:
                # Clean up the key name for display
                display_key = key.replace('right_', '').replace('_cm', '').replace('_', ' ').title()
                circumference_measurements_right[display_key] = value
        
        # Template context with all required data
        context = {
            'analysis_id': analysis_id,
            'traits': formatted_traits,
            'weak_points': weak_points,
            'workout_plan': workout_plan,
            'training_tips': training_tips,
            'equipment': equipment,
            'progression_methods': progression_methods,
            'experience': experience,
            'split_type': 'Push/Pull/Legs',
            'basic_measurements': basic_measurements,  # Basic measurements for the template
            'estimated_measurements': measurements,  # All measurements
            'proportion_measurements': proportion_measurements,  # Proportion measurements for the template
            'circumference_measurements_left': circumference_measurements_left,  # Left side measurements
            'circumference_measurements_right': circumference_measurements_right  # Right side measurements
        }
        
        # Log the key parts of context for debugging
        logger.info(f"Rendering workout template for analysis_id: {analysis_id}")
        
        # Render the template with the context
        return render_template('tailwind_workout_direct.html', **context)
        
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error in workout endpoint for analysis_id {analysis_id}: {str(e)}")
        # Return a user-friendly error message
        flash('An error occurred while generating your workout plan. Please try again later.', 'danger')
        # Return a fallback error page or redirect
        return render_template('error.html', error_message="We couldn't generate your workout plan right now. Our team is looking into it."), 500