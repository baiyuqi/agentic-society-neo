#!/usr/bin/env python3
"""
Test script for personality curve API endpoint
"""
import requests
import json

# Test the personality curve API
def test_personality_curve():
    url = "http://localhost:5000/api/analysis/personality-curve"

    # Test data - use human database for both model and baseline to test variation generation
    test_data = {
        "db_path": "../data/db/backup/human.db",  # Using human.db for both model and baseline
        "gender": ""
    }

    try:
        response = requests.post(url, json=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            print("\nAPI Response Structure:")
            print(f"Model Name: {data.get('model_name')}")
            print(f"Curves Keys: {list(data.get('curves', {}).keys())}")
            print(f"Distances: {data.get('distances')}")

            # Check curve data
            for trait, curve_data in data.get('curves', {}).items():
                print(f"\n{trait}:")
                print(f"  Ages length: {len(curve_data.get('ages', []))}")
                print(f"  Human length: {len(curve_data.get('human', []))}")
                print(f"  Model length: {len(curve_data.get('model', []))}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decode failed: {e}")

if __name__ == "__main__":
    test_personality_curve()