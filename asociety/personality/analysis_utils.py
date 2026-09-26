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

PERSONALITY_TRAITS = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']

def load_personality_data(db_path: str, table: str = 'personality',
                          columns: list = None) -> pd.DataFrame:
    """Loads a trait vector table from a single specified database.

    The defaults reproduce the personality tree exactly; the value tree passes
    table='value' plus its own column list.
    """
    if columns is None:
        columns = PERSONALITY_TRAITS
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")
    cols = ', '.join(f'"{c}"' for c in columns)
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(f'SELECT {cols} FROM "{table}"', conn)
    if df.empty:
        raise ValueError(f"The '{table}' table in {db_path} is empty.")
    # A persona whose answer set failed to parse is stored as an all-NaN row by the
    # value/morality extractors; drop it rather than let sklearn/numpy blow up downstream.
    return df.dropna()

def load_profiles_from_directory(directory: str, loader=load_personality_data, pattern: str = '*.db') -> tuple[list[pd.DataFrame], list[str]]:
    """
    Loads all trait profiles from .db files in a specified directory
    for multi-profile analysis. Pass a different `loader` for another instrument.
    `pattern` is a glob relative to `directory`, so a caller can pick one method
    across the nested individual layout (e.g. 'persona*/standard.db').
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"The provided path '{directory}' is not a valid directory.")

    db_files = sorted(glob.glob(os.path.join(directory, pattern)))

    if len(db_files) < 2:
        raise ValueError(f"Multi-profile analysis requires at least two .db files, but only {len(db_files)} found in '{directory}'.")

    profile_dataframes = [loader(p) for p in db_files]
    profile_names = [os.path.basename(p) for p in db_files]

    return profile_dataframes, profile_names

# --- Single-Profile Analysis ---

def calculate_single_profile_mahalanobis(db_path: str, return_df: bool = False,
                                         columns: list = None, table: str = 'personality'):
    """
    Calculates Mahalanobis distance for each point to the center of a single profile.
    Used for analyzing the internal distribution of a single dataset.

    Args:
        db_path (str): Path to the SQLite database file.
        return_df (bool): If True, returns the DataFrame along with the distances.
        columns (list): Trait columns to use; defaults to the Big Five.
        table (str): Trait table to read; defaults to the personality tree's.

    Returns:
        np.ndarray or tuple[np.ndarray, pd.DataFrame]:
        - If return_df is False (default), returns an array of Mahalanobis distances.
        - If return_df is True, returns a tuple containing the distances array and the DataFrame.
    """
    trait_columns = list(columns) if columns else PERSONALITY_TRAITS
    df = load_personality_data(db_path, table=table, columns=trait_columns)
    vectors = df.values

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

    # The value/morality trait sets include higher-order dimensions that are exact linear
    # combinations of the primary ones, so the covariance is rank-deficient. The pseudoinverse
    # gives the Mahalanobis distance in the subspace the data actually spans (equivalent to
    # dropping the redundant dimensions), instead of failing or fudging a ridge term.
    inv_cov_matrix = np.linalg.pinv(cov_matrix)

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
    # A persona whose answer set failed to parse is stored as an all-NaN row by the value/morality
    # extractors; drop it rather than let StandardScaler blow up on NaN.
    cleaned = [df.dropna().values for df in profile_dataframes]
    all_vectors = np.vstack(cleaned)
    true_labels = np.concatenate([[i] * len(v) for i, v in enumerate(cleaned)])

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

    # Higher-order value/morality dimensions are linear combinations of the primary ones,
    # making the pooled covariance singular; the pseudoinverse handles it (see above).
    inv_pooled_cov = np.linalg.pinv(pooled_cov)
    delta_mean = mean1 - mean2
    distance = np.sqrt(delta_mean.T @ inv_pooled_cov @ delta_mean)
    return distance
