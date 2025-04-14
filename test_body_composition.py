#!/usr/bin/env python3
import sys
from utils.body_analysis import calculate_body_composition

def test_body_fat_calculation():
    # Test parameters for different scenarios
    test_scenarios = [
        # Male cases (weight_kg, height_m, age, sex=1)
        (70, 1.75, 30, 1),  # Fit male
        (90, 1.75, 30, 1),  # Overweight male
        (65, 1.85, 30, 1),  # Lean tall male
        (85, 1.65, 45, 1),  # Older, overweight, shorter male
        
        # Female cases (weight_kg, height_m, age, sex=0)
        (60, 1.65, 30, 0),  # Fit female
        (75, 1.65, 30, 0),  # Overweight female
        (55, 1.75, 30, 0),  # Lean tall female
        (68, 1.58, 45, 0),  # Older, overweight, shorter female
    ]
    
    print("\n=== Body Fat Percentage Calculation Tests ===")
    print("Weight | Height | Age | Sex | Body Fat % | Lean Mass %")
    print("-" * 60)
    
    for weight_kg, height_m, age, sex in test_scenarios:
        body_fat, lean_mass = calculate_body_composition(weight_kg, height_m, age, sex)
        gender = "Male" if sex == 1 else "Female"
        print(f"{weight_kg:6.1f} | {height_m:6.2f} | {age:3d} | {gender:6} | {body_fat:9.1f}% | {lean_mass:10.1f}%")

if __name__ == "__main__":
    test_body_fat_calculation()