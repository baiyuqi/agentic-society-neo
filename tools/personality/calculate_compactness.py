import argparse
import sqlite3
import pandas as pd
import numpy as np
from scipy.stats import chi2

def remove_outliers_mahalanobis(df: pd.DataFrame, threshold_p: float = 0.001) -> pd.DataFrame:
    """
    Removes outliers from a DataFrame using Mahalanobis distance.

    Args:
        df: DataFrame containing the multivariate data.
        threshold_p: The p-value to use as a cutoff. Points with a p-value
                     less than this will be considered outliers.

    Returns:
        DataFrame with outliers removed.
    """
    data = df.values
    cov_matrix = np.cov(data, rowvar=False)
    inv_cov_matrix = np.linalg.inv(cov_matrix)
    mean = np.mean(data, axis=0)
    
    # Calculate squared Mahalanobis distance for each observation
    mahalanobis_sq = np.array([
        (row - mean).T @ inv_cov_matrix @ (row - mean) for row in data
    ])
    
    # The squared Mahalanobis distance follows a chi-squared distribution
    # with degrees of freedom equal to the number of variables (5 in our case).
    # We find the critical value for our desired p-value.
    critical_value = chi2.ppf(1 - threshold_p, df=data.shape[1])
    
    # Find the indices of non-outliers
    non_outlier_indices = np.where(mahalanobis_sq < critical_value)[0]
    
    num_outliers = len(df) - len(non_outlier_indices)
    if num_outliers > 0:
        print(f"Removed {num_outliers} outliers using Mahalanobis distance (p < {threshold_p}).")
        
    return df.iloc[non_outlier_indices]

def calculate_compactness(db_path: str, remove_outliers: bool, outlier_threshold: float):
    """
    Calculates the compactness of personality data from a database.

    Compactness is defined as the trace of the covariance matrix of the
    Big Five personality traits (total variance).

    Args:
        db_path: Path to the SQLite database file.
        remove_outliers: Whether to remove outliers before calculation.
        outlier_threshold: The p-value threshold for outlier removal.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)

        # Define the Big Five columns
        big_five_columns = [
            "neuroticism",
            "extraversion",
            "openness",
            "agreeableness",
            "conscientiousness"
        ]
        
        columns_str = ", ".join(big_five_columns)
        
        # Construct the query to select the Big Five traits, filtering out nulls
        query = f"SELECT {columns_str} FROM personality WHERE " + \
                " AND ".join([f"{col} IS NOT NULL" for col in big_five_columns])

        # Read data into a pandas DataFrame
        df = pd.read_sql_query(query, conn)

        # Close the connection
        conn.close()

        if len(df) < 2:
            print("Error: Not enough data to calculate compactness (less than 2 valid records found).")
            return
            
        print(f"Found {len(df)} valid personality records.")

        # Optionally remove outliers
        if remove_outliers:
            df = remove_outliers_mahalanobis(df, threshold_p=outlier_threshold)

        if len(df) < 2:
            print("Error: Not enough data remaining after outlier removal.")
            return

        # Convert DataFrame to a NumPy array
        data_array = df.values

        # Calculate the covariance matrix
        # rowvar=False means each column is a variable, each row is an observation
        cov_matrix = np.cov(data_array, rowvar=False)

        # Calculate the trace of the covariance matrix (total variance)
        trace = np.trace(cov_matrix)

        print(f"Database: {db_path}")
        print(f"Using {len(df)} records for calculation.")
        print(f"Personality Compactness (Total Variance / Trace of Covariance Matrix): {trace:.4f}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except pd.io.sql.DatabaseError as e:
        print(f"Data query error: {e}. Check if the 'personality' table and columns exist.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculate the compactness (total variance) of Big Five personality data in a database."
    )
    parser.add_argument(
        "db_path",
        type=str,
        help="Path to the SQLite database file containing the 'personality' table."
    )
    parser.add_argument(
        "--remove-outliers",
        action="store_true",
        help="Enable outlier removal using Mahalanobis distance before calculation."
    )
    parser.add_argument(
        "--outlier-threshold",
        type=float,
        default=0.001,
        help="The p-value for the chi-squared test to identify outliers (default: 0.001)."
    )
    args = parser.parse_args()
    
    calculate_compactness(args.db_path, args.remove_outliers, args.outlier_threshold)
