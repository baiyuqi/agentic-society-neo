from flask import Flask, render_template, jsonify, request
import sqlite3
import json
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add parent directory to Python path for module imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

app = Flask(__name__, static_folder='static', template_folder='templates')

# Default database path - relative to backup directory
DEFAULT_DB_PATH = "agentic_society.db"

# Backup directory path
BACKUP_DIR = Path("d:/agentic-society-neo/data/db/backup")

def resolve_db_path(relative_path):
    """Resolve relative path to full database path"""
    if not relative_path:
        return BACKUP_DIR / DEFAULT_DB_PATH

    # If it's already an absolute path, return as is
    if Path(relative_path).is_absolute():
        return Path(relative_path)

    # Otherwise, resolve relative to backup directory
    return BACKUP_DIR / relative_path

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/databases')
def get_databases():
    """Get hierarchical tree structure of available database files"""
    def build_tree_structure():
        """Build hierarchical tree structure from file system"""
        tree = []

        if not BACKUP_DIR.exists():
            return tree

        # Create a dictionary to store directory nodes
        dir_nodes = {}

        # First pass: collect all directories and files
        for file in BACKUP_DIR.rglob("*"):
            relative_path = file.relative_to(BACKUP_DIR)
            parts = relative_path.parts

            # Skip if it's the backup directory itself
            if len(parts) == 0:
                continue

            current_path = ""
            current_level = tree

            # Build the directory structure
            for i, part in enumerate(parts):
                current_path = str(Path(current_path) / part) if current_path else part

                # Check if this is a file (last part and ends with .db)
                is_file = i == len(parts) - 1 and part.endswith('.db')

                # Find or create the node
                node = None
                for item in current_level:
                    if item['name'] == part:
                        node = item
                        break

                if not node:
                    node = {
                        'name': part,
                        'path': current_path,
                        'type': 'file' if is_file else 'directory',
                        'expanded': False,
                        'children': [] if not is_file else None,
                        'size': file.stat().st_size if is_file else 0
                    }
                    current_level.append(node)

                # If this is a directory, move to its children for next level
                if not is_file:
                    current_level = node['children']

        return tree

    def sort_tree(tree):
        """Sort tree structure: directories first, then files"""
        for node in tree:
            if node['type'] == 'directory' and node['children']:
                sort_tree(node['children'])

        # Sort current level: directories first, then files
        tree.sort(key=lambda x: (0 if x['type'] == 'directory' else 1, x['name']))
        return tree

    try:
        tree = build_tree_structure()
        sorted_tree = sort_tree(tree)
        return jsonify(sorted_tree)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personas')
def get_personas():
    """Get personas from database"""
    relative_path = request.args.get('db', DEFAULT_DB_PATH)
    db_path = resolve_db_path(relative_path)

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get personas with their personality traits including full JSON
        cursor.execute("""
            SELECT id, age, sex, occupation,
                   openness, conscientiousness, extraversion,
                   agreeableness, neuroticism, personality_json
            FROM persona_personality
            LIMIT 100
        """)

        personas = []
        for row in cursor.fetchall():
            personas.append({
                'id': row[0],
                'age': row[1],
                'gender': row[2],
                'occupation': row[3],
                'openness': row[4],
                'conscientiousness': row[5],
                'extraversion': row[6],
                'agreeableness': row[7],
                'neuroticism': row[8],
                'personality_json': row[9]
            })

        conn.close()
        return jsonify(personas)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personality/stats')
def get_personality_stats():
    """Get detailed personality statistics"""
    relative_path = request.args.get('db', DEFAULT_DB_PATH)
    db_path = resolve_db_path(relative_path)

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Calculate average personality traits
        cursor.execute("""
            SELECT
                AVG(openness) as avg_openness,
                AVG(conscientiousness) as avg_conscientiousness,
                AVG(extraversion) as avg_extraversion,
                AVG(agreeableness) as avg_agreeableness,
                AVG(neuroticism) as avg_neuroticism,
                COUNT(*) as total_personas
            FROM persona_personality
        """)

        stats = cursor.fetchone()

        # Calculate variance and standard deviation for each trait
        cursor.execute("""
            SELECT
                VAR(openness) as var_openness,
                VAR(conscientiousness) as var_conscientiousness,
                VAR(extraversion) as var_extraversion,
                VAR(agreeableness) as var_agreeableness,
                VAR(neuroticism) as var_neuroticism
            FROM persona_personality
        """)

        variances = cursor.fetchone()

        result = {
            'avg_openness': stats[0],
            'avg_conscientiousness': stats[1],
            'avg_extraversion': stats[2],
            'avg_agreeableness': stats[3],
            'avg_neuroticism': stats[4],
            'total_personas': stats[5],
            'var_openness': variances[0],
            'var_conscientiousness': variances[1],
            'var_extraversion': variances[2],
            'var_agreeableness': variances[3],
            'var_neuroticism': variances[4],
            'std_openness': variances[0] ** 0.5 if variances[0] else 0,
            'std_conscientiousness': variances[1] ** 0.5 if variances[1] else 0,
            'std_extraversion': variances[2] ** 0.5 if variances[2] else 0,
            'std_agreeableness': variances[3] ** 0.5 if variances[3] else 0,
            'std_neuroticism': variances[4] ** 0.5 if variances[4] else 0
        }

        conn.close()
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/mahalanobis', methods=['POST'])
def mahalanobis_analysis():
    """Perform Mahalanobis distance analysis for a single profile"""
    try:
        data = request.get_json()
        relative_path = data.get('db_path')

        if not relative_path:
            return jsonify({'error': 'Database path is required'}), 400

        # Resolve database path
        db_path = resolve_db_path(relative_path)
        if not db_path.exists():
            return jsonify({'error': f'Database not found: {relative_path}'}), 404

        # Import and use the Mahalanobis analysis function
        from asociety.personality.analysis_utils import calculate_single_profile_mahalanobis

        distances, data_df = calculate_single_profile_mahalanobis(str(db_path), return_df=True)

        # Calculate statistical metrics
        cv, kurtosis = calculate_statistical_metrics(distances)

        # Create histogram data
        hist_data = create_histogram_data(distances)

        return jsonify({
            'distances': distances.tolist(),
            'statistics': {
                'variation_coefficient': cv,
                'kurtosis': kurtosis,
                'mean': float(np.mean(distances)),
                'std': float(np.std(distances)),
                'min': float(np.min(distances)),
                'max': float(np.max(distances)),
                'count': len(distances)
            },
            'histogram': hist_data,
            'profile_name': relative_path.replace('.db', '')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_statistical_metrics(distances):
    """Calculate variation coefficient and kurtosis"""
    if len(distances) < 2:
        return 0.0, 0.0

    mean = np.mean(distances)
    std = np.std(distances)

    # Variation coefficient (avoid division by zero)
    cv = std / mean if mean != 0 else 0.0

    # Kurtosis (using Fisher's definition, normal distribution = 0)
    if len(distances) >= 4 and std > 0:
        kurtosis = np.mean(((distances - mean) / std) ** 4) - 3
    else:
        kurtosis = 0.0

    return float(cv), float(kurtosis)

def create_histogram_data(distances):
    """Create histogram data for frontend display"""
    if len(distances) == 0:
        return {'bins': [], 'counts': [], 'probabilities': []}

    # Use numpy histogram with auto bins
    counts, bin_edges = np.histogram(distances, bins='auto', density=False)

    # Calculate probabilities
    total = len(distances)
    probabilities = (counts / total).tolist()

    # Create bin ranges
    bin_ranges = []
    for i in range(len(bin_edges) - 1):
        bin_ranges.append(f"{bin_edges[i]:.4f} - {bin_edges[i+1]:.4f}")

    return {
        'bins': bin_ranges,
        'counts': counts.tolist(),
        'probabilities': probabilities,
        'bin_edges': bin_edges.tolist()
    }

@app.route('/api/analysis/clustering', methods=['POST'])
def clustering_analysis():
    """Perform clustering analysis on multiple database files"""
    try:
        data = request.get_json()
        directory_path = data.get('directory_path')

        if not directory_path:
            return jsonify({'error': 'Directory path is required'}), 400

        # Resolve directory path - support both relative and absolute paths
        if Path(directory_path).is_absolute():
            dir_path = Path(directory_path)
        else:
            dir_path = BACKUP_DIR / directory_path

        if not dir_path.exists() or not dir_path.is_dir():
            return jsonify({'error': f'Directory not found: {directory_path}'}), 404

        # Import clustering analysis functions
        from asociety.personality.analysis_utils import (
            load_profiles_from_directory,
            get_combined_and_scaled_data,
            run_kmeans_analysis,
            run_pca
        )

        # Load data from directory
        profile_dataframes, profile_names = load_profiles_from_directory(str(dir_path))

        # Get combined and scaled data
        scaled_vectors, true_labels = get_combined_and_scaled_data(profile_dataframes)

        # Run K-Means analysis
        num_profiles = len(profile_dataframes)
        kmeans, predicted_labels, ari_score = run_kmeans_analysis(
            scaled_vectors, true_labels, num_profiles, return_model=True
        )

        # Run PCA for visualization
        principal_components, explained_variance = run_pca(scaled_vectors)

        # Calculate centroid distances
        from scipy.spatial.distance import pdist, squareform
        centroids = kmeans.cluster_centers_
        centroid_distances_condensed = pdist(centroids, 'euclidean')
        centroid_distance_matrix = squareform(centroid_distances_condensed)

        avg_dist = np.mean(centroid_distances_condensed) if centroid_distances_condensed.size > 0 else 0
        min_dist = np.min(centroid_distances_condensed) if centroid_distances_condensed.size > 0 else 0
        max_dist = np.max(centroid_distances_condensed) if centroid_distances_condensed.size > 0 else 0

        return jsonify({
            'profile_names': profile_names,
            'ari_score': ari_score,
            'principal_components': principal_components.tolist(),
            'explained_variance': explained_variance.tolist(),
            'true_labels': true_labels.tolist(),
            'predicted_labels': predicted_labels.tolist(),
            'centroid_distance_matrix': centroid_distance_matrix.tolist(),
            'average_centroid_distance': avg_dist,
            'min_centroid_distance': min_dist,
            'max_centroid_distance': max_dist,
            'num_samples': len(scaled_vectors)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/multi_mahalanobis', methods=['POST'])
def multi_mahalanobis_analysis():
    """Perform multi-source Mahalanobis distance convergence analysis"""
    try:
        # Define data source templates (matching studio implementation)
        # 使用预设的persona编号，不需要用户选择
        data_source_templates = [
            {
                'name': 'poor300',
                'template': 'poor300/deepseek-chat-single-poor-{}-300.db',
                'color': 'red',
                'label': 'Poor Quality'
            },
            {
                'name': 'samples300',
                'template': 'samples300/deepseek-chat-single-{}-300.db',
                'color': 'blue',
                'label': 'Standard Sample'
            },
            {
                'name': 'narrative300',
                'template': 'samples-narrative300/deepseek-chat-single-{}-300-narra.db',
                'color': 'green',
                'label': 'Narrative'
            }
        ]

        # Update paths for both personas (使用预设的persona编号)
        def update_data_sources_paths(persona_number):
            updated_sources = []
            for template in data_source_templates:
                updated_source = template.copy()
                # 直接使用BACKUP_DIR下的相对路径
                updated_source['path'] = str(BACKUP_DIR / template['template'].format(persona_number))
                updated_sources.append(updated_source)
            return updated_sources

        # 使用预设的persona编号（如studio中的"1"和"2"）
        data_sources_persona1 = update_data_sources_paths("1")
        data_sources_persona2 = update_data_sources_paths("2")

        # Calculate results for both personas
        results_persona1 = _calculate_persona_results_multi(data_sources_persona1)
        results_persona2 = _calculate_persona_results_multi(data_sources_persona2)

        return jsonify({
            'persona1': results_persona1,
            'persona2': results_persona2,
            'persona1_name': 'Persona 1',
            'persona2_name': 'Persona 2'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _calculate_persona_results_multi(data_sources):
    """Calculate Mahalanobis distance results for a persona using multiple data sources"""
    results = {}

    # First load all data to calculate common statistics
    all_data = []
    all_labels = []

    for source in data_sources:
        if not os.path.exists(source['path']):
            raise FileNotFoundError(f"数据库文件不存在: {source['path']}")

        # Load personality data
        from asociety.personality.analysis_utils import load_personality_data
        df = load_personality_data(source['path'])
        trait_columns = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        vectors = df[trait_columns].values

        all_data.append(vectors)
        all_labels.extend([source['label']] * len(vectors))

    # Combine all data and calculate common statistics
    combined_data = np.vstack(all_data)
    global_mean = np.mean(combined_data, axis=0)
    global_cov = np.cov(combined_data, rowvar=False)

    # Add regularization to ensure invertibility
    regularization = 1e-6
    global_cov += np.eye(global_cov.shape[0]) * regularization
    global_inv_cov = np.linalg.inv(global_cov)

    # Calculate Mahalanobis distances using common reference
    for source, data in zip(data_sources, all_data):
        # Calculate Mahalanobis distances relative to global distribution
        delta = data - global_mean
        mahalanobis_sq_dist = np.sum((delta @ global_inv_cov) * delta, axis=1)
        distances = np.sqrt(mahalanobis_sq_dist)

        # Remove outliers using IQR method
        distances_clean = _remove_outliers_iqr_multi(distances)

        # Calculate statistical metrics
        cv, kurtosis = _calculate_statistical_metrics_multi(distances_clean)

        results[source['name']] = {
            'distances': distances.tolist(),
            'distances_clean': distances_clean.tolist(),
            'cv': cv,
            'kurtosis': kurtosis,
            'color': source['color'],
            'label': source['label'],
            'sample_count': len(distances_clean)
        }

    return results

def _remove_outliers_iqr_multi(data):
    """Remove outliers using Interquartile Range method."""
    if len(data) < 4:
        return data

    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    return data[(data >= lower_bound) & (data <= upper_bound)]

def _calculate_statistical_metrics_multi(data):
    """Calculate variation coefficient and kurtosis."""
    if len(data) < 2:
        return 0.0, 0.0

    mean = np.mean(data)
    std = np.std(data)

    # Variation coefficient
    cv = std / mean if mean != 0 else 0.0

    # Kurtosis (Fisher's definition)
    if len(data) >= 4 and std > 0:
        kurtosis = np.mean(((data - mean) / std) ** 4) - 3
    else:
        kurtosis = 0.0

    return cv, kurtosis

@app.route('/api/analysis/personality-curve', methods=['POST'])
def personality_curve_analysis():
    """Perform personality curve analysis with human baseline comparison"""
    try:
        data = request.get_json()
        relative_path = data.get('db_path')
        gender = data.get('gender', '')

        if not relative_path:
            return jsonify({'error': 'Database path is required'}), 400

        # Resolve model database path
        db_path = resolve_db_path(relative_path)
        if not db_path.exists():
            return jsonify({'error': f'Database not found: {relative_path}'}), 404

        # Get model data
        model_data = get_personality_data(str(db_path), gender)

        # Get human baseline data
        human_db_path = BACKUP_DIR / "human.db"
        if not human_db_path.exists():
            return jsonify({'error': f'Human baseline database not found at {human_db_path}'}), 404

        human_data = get_personality_data(str(human_db_path), '')

        # If using the same database for model and human, use different data
        if db_path.name == human_db_path.name:
            # For testing/demo purposes, create slightly different model data
            model_data = human_data.copy() if human_data else None
            if model_data:
                # Add small variations to model data for visualization
                for i in range(1, len(model_data)):
                    model_data[i] = [x + np.random.normal(0, 2) for x in model_data[i]]
        else:
            model_data = get_personality_data(str(db_path), gender)

        # Compute curves for both datasets - match desktop mapping
        curves = {}
        trait_names = ['神经质', '外向性', '开放性', '宜人性', '尽责性']
        trait_order = ['neuroticism', 'extraversion', 'openness', 'agreeableness', 'conscientiousness']
        # Desktop uses this mapping: [5, 3, 1, 4, 2] for O,C,E,A,N -> N,E,O,A,C
        data_index_map = [5, 3, 1, 4, 2]  # neuroticism, extraversion, openness, agreeableness, conscientiousness

        for i, trait in enumerate(trait_order):
            curves[trait_names[i]] = {
                'ages': [],
                'human': [],
                'model': []
            }

            data_idx = data_index_map[i]  # Get the correct data index from desktop mapping

            # Human baseline curve
            if human_data and len(human_data) > data_idx:
                human_ages = human_data[0]
                human_scores = human_data[data_idx]
                human_x, human_y = compute_smooth_curve(human_ages, human_scores)
                curves[trait_names[i]]['ages'] = human_x.tolist()
                curves[trait_names[i]]['human'] = human_y.tolist()

            # Model curve
            if model_data and len(model_data) > data_idx:
                model_ages = model_data[0]
                model_scores = model_data[data_idx]
                model_x, model_y = compute_smooth_curve(model_ages, model_scores)
                curves[trait_names[i]]['model'] = model_y.tolist()

        # Calculate distances
        distances = calculate_distances(curves, relative_path.replace('.db', ''))

        return jsonify({
            'curves': curves,
            'distances': distances,
            'model_name': relative_path.replace('.db', '')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_personality_data(db_path, gender_filter=''):
    """Get personality data from database with optional gender filter - matches desktop version"""
    try:
        # Import the same function used in desktop version
        from asociety.personality.personality_analysis import get_personas_ana

        # Map gender filter to match desktop format
        sex_filter = 'All'
        if gender_filter and gender_filter.lower() in ['male', 'female']:
            sex_filter = gender_filter.capitalize()

        # Use the same function as desktop version
        result = get_personas_ana(db_path=db_path, dimension='age', sex_filter=sex_filter)

        print(f"Retrieved data from {db_path}: {[len(arr) for arr in result] if result else 'None'}")
        if result and len(result) > 0:
            print(f"Sample age range: {min(result[0]) if result[0] else 'N/A'} - {max(result[0]) if result[0] else 'N/A'}")

        return result

    except Exception as e:
        print(f"Error getting personality data: {e}")
        return None

def compute_smooth_curve(x_values, y_values):
    """Compute smooth curve using polynomial fitting - matches desktop version"""
    # Use the same compute function as desktop version
    from asociety.personality.personality_analysis import compute

    x_scatter, y_scatter, x_curve, y_curve = compute(x_values, y_values)

    print(f"Curve computation - scatter: {len(x_scatter)}, curve: {len(x_curve)}")

    return x_curve, y_curve

def calculate_distances(curves, model_name):
    """Calculate Euclidean distances between human baseline and model"""
    ages_to_check = np.array([20, 30, 40, 50, 60, 70])
    trait_names = ['神经质', '外向性', '开放性', '宜人性', '尽责性']

    distances = {
        'model_name': model_name,
        'neuroticism': 0,
        'extraversion': 0,
        'openness': 0,
        'agreeableness': 0,
        'conscientiousness': 0,
        'euclidean': 0
    }

    trait_distances = []

    for trait_name in trait_names:
        curve_data = curves.get(trait_name, {})
        human_curve = curve_data.get('human', [])
        model_curve = curve_data.get('model', [])
        ages = curve_data.get('ages', [])

        if human_curve and model_curve and ages:
            # Interpolate at specific ages
            human_scores = np.interp(ages_to_check, ages, human_curve)
            model_scores = np.interp(ages_to_check, ages, model_curve)

            # Calculate average absolute distance
            avg_dist = np.mean(np.abs(human_scores - model_scores))
            trait_distances.append(avg_dist)

            # Store individual trait distance
            trait_key = {
                '神经质': 'neuroticism',
                '外向性': 'extraversion',
                '开放性': 'openness',
                '宜人性': 'agreeableness',
                '尽责性': 'conscientiousness'
            }[trait_name]
            distances[trait_key] = float(avg_dist)
        else:
            trait_distances.append(np.nan)

    # Calculate Euclidean distance (only if all traits have valid distances)
    if not np.isnan(trait_distances).any():
        distances['euclidean'] = float(np.linalg.norm(trait_distances))

    return distances

def generate_plot_images(curves, model_name):
    """Placeholder function - plotting is now handled by frontend Chart.js"""
    return {}

# Serve static pages
@app.route('/pages/<path:page_path>')
def serve_page(page_path):
    """Serve static pages for iframe content"""
    return app.send_static_file(f'pages/{page_path}')

if __name__ == '__main__':
    # 生产环境配置
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)