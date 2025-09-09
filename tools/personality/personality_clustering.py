# asociety/personality/personality_clustering.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse

# Import from the new, correctly named, shared library
from .analysis_utils import (
    load_profiles_from_directory,
    get_combined_and_scaled_data,
    run_kmeans_analysis,
    run_pca
)

def main():
    """
    Main function to run the personality clustering analysis from the command line.
    """
    parser = argparse.ArgumentParser(
        description='Test personality profile identifiability using K-Means clustering and PCA visualization.'
    )
    parser.add_argument(
        '--directory', 
        '-d',
        type=str, 
        required=True,
        help='Path to the directory containing the personality database (.db) files.'
    )
    args = parser.parse_args()

    try:
        # 1. Load data using the core analysis library
        profile_dataframes, profile_names = load_profiles_from_directory(args.directory)
        
        # 2. Get combined, labeled, and scaled data
        scaled_vectors, true_labels = get_combined_and_scaled_data(profile_dataframes)
        
        # 3. Run K-Means analysis
        num_profiles = len(profile_dataframes)
        predicted_labels, ari_score = run_kmeans_analysis(scaled_vectors, true_labels, num_profiles)
        
        print("\n--- Clustering Evaluation ---")
        print(f"Adjusted Rand Index (ARI): {ari_score:.4f}")
        print(" (Score Interpretation: 1.0 = Perfect Match, 0.0 = Random Guessing)")

        # 4. Run PCA for visualization
        print("\nGenerating visualization...")
        principal_components, explained_variance = run_pca(scaled_vectors)

        # 5. Create a DataFrame for plotting
        plot_df = pd.DataFrame({
            'PC1': principal_components[:, 0],
            'PC2': principal_components[:, 1],
            'True Profile': [f'Profile {profile_names[label]}' for label in true_labels],
            'Predicted Cluster': [f'Cluster {label + 1}' for label in predicted_labels]
        })

        # 6. Plot the results
        plt.figure(figsize=(12, 8))
        sns.scatterplot(
            data=plot_df,
            x='PC1',
            y='PC2',
            hue='Predicted Cluster',
            style='True Profile',
            s=100,
            alpha=0.7,
            palette='tab10'
        )
        plt.title('K-Means Clustering Results vs. True Profile Labels (PCA)')
        plt.xlabel(f'Principal Component 1 ({explained_variance[0]:.1%} variance)')
        plt.ylabel(f'Principal Component 2 ({explained_variance[1]:.1%} variance)')
        plt.legend(title='Legend')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        
        print("Plot displayed. Check if colors and shapes align.")
        plt.show()

    except (ValueError, FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main()
