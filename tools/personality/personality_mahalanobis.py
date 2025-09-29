# asociety/personality/personality_mahalanobis.py

import matplotlib.pyplot as plt
import argparse

# Import from the new, correctly named, shared library
from .analysis_utils import calculate_single_profile_mahalanobis

def main():
    """
    Command-line tool to analyze and visualize the Mahalanobis distance
    distribution for a single personality profile.
    """
    parser = argparse.ArgumentParser(description='Analyze personality data distribution using Mahalanobis distance.')
    parser.add_argument('--db-path', type=str, required=True, help='Path to the single SQLite database file.')
    
    args = parser.parse_args()
    
    try:
        print(f"Analyzing file: {args.db_path}")
        # 1. Calculate distances using the core library function
        distances = calculate_single_profile_mahalanobis(args.db_path)
        
        print("--- Analysis using Mahalanobis Distance ---")
        print("This distance measures how many standard deviations away a point is from the mean, accounting for inter-trait correlations.")
        
        # 2. Plot the distribution
        plt.figure(figsize=(10, 6))
        plt.hist(distances, bins='auto', density=True, alpha=0.7, color='purple', edgecolor='black')
        
        plt.title('Probability Distribution of Mahalanobis Distances')
        plt.xlabel('Mahalanobis Distance')
        plt.ylabel('Probability Density')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        
        print("\nAnalysis complete. Displaying plot...")
        plt.show()

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main()
