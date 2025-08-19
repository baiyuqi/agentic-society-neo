# asociety/personality/analysis_utils.py
"""
A central library for personality data analysis functions,
used by both command-line tools and the GUI studio.
"""

import sqlite3
import pandas as pd
import numpy as np
import glob
import os
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.decomposition import PCA

# --- Data Loading ---

def load_personality_data(db_path: str) -> pd.DataFrame:
    """Loads personality data from a single specified database."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT openness, conscientiousness, extraversion, agreeableness, neuroticism FROM personality", conn)
    if df.empty:
        raise ValueError(f"The 'personality' table in {db_path} is empty.")
    return df

def load_profiles_from_directory(directory: str) -> tuple[list[pd.DataFrame], list[str]]:
    """
    Loads all personality profiles from .db files in a specified directory
    for multi-profile analysis.
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"The provided path '{directory}' is not a valid directory.")

    db_files = sorted(glob.glob(os.path.join(directory, '*.db')))
    
    if len(db_files) < 2:
        raise ValueError(f"Multi-profile analysis requires at least two .db files, but only {len(db_files)} found in '{directory}'.")
        
    profile_dataframes = [load_personality_data(p) for p in db_files]
    profile_names = [os.path.basename(p) for p in db_files]
    
    return profile_dataframes, profile_names

# --- Single-Profile Analysis ---

def calculate_single_profile_mahalanobis(db_path: str, return_df: bool = False):
    """
    Calculates Mahalanobis distance for each point to the center of a single profile.
    Used for analyzing the internal distribution of a single dataset.
    
    Args:
        db_path (str): Path to the SQLite database file.
        return_df (bool): If True, returns the DataFrame along with the distances.

    Returns:
        np.ndarray or tuple[np.ndarray, pd.DataFrame]: 
        - If return_df is False (default), returns an array of Mahalanobis distances.
        - If return_df is True, returns a tuple containing the distances array and the DataFrame.
    """
    df = load_personality_data(db_path)
    trait_columns = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
    vectors = df[trait_columns].values

    # --- Defensive check for sufficient data ---
    n_samples, n_features = vectors.shape
    if n_samples <= n_features:
        raise ValueError(
            f"Not enough data points ({n_samples}) to compute a non-singular covariance matrix "
            f"for {n_features} features. The number of samples must be greater than the number of features."
        )
    # --- End of defensive check ---

    mean_vector = np.mean(vectors, axis=0)
    cov_matrix = np.cov(vectors, rowvar=False)
    
    try:
        inv_cov_matrix = np.linalg.inv(cov_matrix)
    except np.linalg.LinAlgError:
        # Add a small regularization term (ridge) to the diagonal
        # This can help with matrices that are almost singular
        regularization = 1e-6
        cov_matrix += np.eye(cov_matrix.shape[0]) * regularization
        try:
            inv_cov_matrix = np.linalg.inv(cov_matrix)
        except np.linalg.LinAlgError:
            raise ValueError("Covariance matrix is singular and cannot be inverted, even with regularization.")

    delta = vectors - mean_vector
    mahalanobis_sq_dist = np.sum((delta @ inv_cov_matrix) * delta, axis=1)
    distances = np.sqrt(mahalanobis_sq_dist)
    
    if return_df:
        return distances, df
    else:
        return distances

# --- Multi-Profile (Identifiability) Analysis ---

def get_combined_and_scaled_data(profile_dataframes: list[pd.DataFrame]) -> tuple[np.ndarray, np.ndarray]:
    """
    Combines, labels, and scales data from multiple profile DataFrames.
    """
    all_vectors = np.vstack([df.values for df in profile_dataframes])
    true_labels = np.concatenate([[i] * len(df) for i, df in enumerate(profile_dataframes)])
    
    scaler = StandardScaler()
    scaled_vectors = scaler.fit_transform(all_vectors)
    
    return scaled_vectors, true_labels

def run_kmeans_analysis(scaled_vectors: np.ndarray, true_labels: np.ndarray, n_clusters: int, return_model: bool = False):
    """
    Performs K-Means clustering and evaluates it using the Adjusted Rand Index.

    Args:
        scaled_vectors (np.ndarray): The input data, scaled.
        true_labels (np.ndarray): The ground truth labels for the data.
        n_clusters (int): The number of clusters to form.
        return_model (bool): If True, returns the fitted KMeans model object as well.

    Returns:
        tuple: By default, returns (predicted_labels, ari_score).
               If return_model is True, returns (kmeans_model, predicted_labels, ari_score).
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    predicted_labels = kmeans.fit_predict(scaled_vectors)
    ari_score = adjusted_rand_score(true_labels, predicted_labels)
    
    if return_model:
        return kmeans, predicted_labels, ari_score
    else:
        return predicted_labels, ari_score

def run_pca(scaled_vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Performs PCA to reduce data to 2 dimensions.
    """
    pca = PCA(n_components=2)
    principal_components = pca.fit_transform(scaled_vectors)
    return principal_components, pca.explained_variance_ratio_

def run_tsne(scaled_vectors: np.ndarray) -> np.ndarray:
    """
    Performs t-SNE to reduce data to 2 dimensions.
    """
    from sklearn.manifold import TSNE
    tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(scaled_vectors) - 1))
    tsne_results = tsne.fit_transform(scaled_vectors)
    return tsne_results

# --- Two-Profile Comparison Analysis ---

def calculate_mahalanobis_distance(profile1_df: pd.DataFrame, profile2_df: pd.DataFrame) -> float:
    """
    Calculates the Mahalanobis distance between the means of two profiles.
    """
    # --- Defensive check for sufficient data ---
    if profile1_df.empty or profile2_df.empty:
        raise ValueError("One or both of the provided profiles are empty.")
    
    n1, p1 = profile1_df.shape
    n2, p2 = profile2_df.shape

    if n1 <= p1 or n2 <= p2:
        raise ValueError(
            f"Not enough data to compute a non-singular covariance matrix. "
            f"Profile 1 has {n1} samples for {p1} variables. "
            f"Profile 2 has {n2} samples for {p2} variables. "
            "The number of samples must be greater than the number of variables."
        )
    # --- End of defensive check ---

    mean1 = np.mean(profile1_df.values, axis=0)
    mean2 = np.mean(profile2_df.values, axis=0)
    
    cov1 = np.cov(profile1_df.values, rowvar=False)
    cov2 = np.cov(profile2_df.values, rowvar=False)
    
    # Pooled covariance matrix
    pooled_cov = ((n1 - 1) * cov1 + (n2 - 1) * cov2) / (n1 + n2 - 2)
    
    inv_pooled_cov = np.linalg.inv(pooled_cov)
    delta_mean = mean1 - mean2
    distance = np.sqrt(delta_mean.T @ inv_pooled_cov @ delta_mean)
    return distance
