import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os
import glob
from sklearn.preprocessing import StandardScaler
from sklearn.manifold import TSNE

def load_personality_data(db_path: str) -> pd.DataFrame:
    """Loads personality data from the specified database."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT openness, conscientiousness, extraversion, agreeableness, neuroticism FROM personality", conn)
    if df.empty:
        raise ValueError(f"The 'personality' table in {db_path} is empty.")
    return df

def visualize_with_tsne(db_paths: list[str]):
    """
    Visualizes personality profile separability using t-SNE.

    This script loads data from multiple personality profiles, standardizes it,
    and then uses t-SNE to reduce the dimensionality to 2D for visualization.
    t-SNE is excellent at revealing the underlying structure and natural clustering
    of data.

    Each point on the plot represents a single personality test result, and its
    color indicates its original source profile. If profiles are highly distinct,
    points of the same color should form tight, separate clusters.
    """
    # 1. Load and combine data
    all_profiles_df = [load_personality_data(db_path) for db_path in db_paths]
    all_vectors = np.vstack([df.values for df in all_profiles_df])
    
    # Create labels to identify the source of each data point
    true_labels = np.concatenate([[i] * len(df) for i, df in enumerate(all_profiles_df)])
    
    num_profiles = len(db_paths)

    # 2. Standardize the data
    scaler = StandardScaler()
    scaled_vectors = scaler.fit_transform(all_vectors)

    # 3. Perform t-SNE dimensionality reduction
    print(f"Performing t-SNE on {len(all_vectors)} data points...")
    tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(all_vectors) - 1))
    tsne_results = tsne.fit_transform(scaled_vectors)

    # 4. Create a DataFrame for plotting
    profile_names = [os.path.basename(p) for p in db_paths]
    plot_df = pd.DataFrame({
        't-SNE-1': tsne_results[:, 0],
        't-SNE-2': tsne_results[:, 1],
        'Profile': [profile_names[label] for label in true_labels]
    })

    # 5. Generate the visualization
    print("Generating visualization...")
    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        data=plot_df,
        x='t-SNE-1',
        y='t-SNE-2',
        hue='Profile',
        s=80,
        alpha=0.7,
        palette='tab10'
    )

    plt.title('t-SNE Visualization of Personality Profiles')
    plt.xlabel('t-SNE Dimension 1')
    plt.ylabel('t-SNE Dimension 2')
    plt.legend(title='Source Profile')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    print("Plot displayed. Check for distinct color clusters.")
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Visualize personality profile separability using t-SNE.'
    )
    parser.add_argument(
        '--directory', 
        '-d',
        type=str, 
        required=True,
        help='Path to the directory containing the personality database (.db) files.'
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: The provided path '{args.directory}' is not a valid directory.")
        exit(1)

    db_files = sorted(glob.glob(os.path.join(args.directory, '*.db')))
    
    if len(db_files) < 2:
        print(f"Error: Visualization requires at least two .db files, but only {len(db_files)} found in '{args.directory}'.")
        exit(1)
        
    print(f"Found {len(db_files)} database files for visualization.")
    visualize_with_tsne(db_files)
