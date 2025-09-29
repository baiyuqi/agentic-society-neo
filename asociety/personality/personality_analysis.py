from asociety.repository.database import get_engine
import numpy as np

def data(ps):
        result = [[],[],[],[],[],[]]
        
        for i, r in enumerate(ps):
            for j in range(0, 6):
                result[j].append(r[j])
 
        return result

def compute(x_values, y_values):
    import numpy as np
    import pandas as pd

    # Create a DataFrame to easily handle data cleaning
    df = pd.DataFrame({
        'x': x_values,
        'y': y_values
    })

    # Convert columns to numeric, coercing errors to NaN
    df['x'] = pd.to_numeric(df['x'], errors='coerce')
    df['y'] = pd.to_numeric(df['y'], errors='coerce')

    # Drop rows with NaN values in either column
    df.dropna(inplace=True)

    # If no data is left after cleaning, return empty arrays
    if df.empty:
        return np.array([]), np.array([]), np.array([]), np.array([])

    x_scatter = df['x'].values
    y_scatter = df['y'].values

    # For a 3rd degree polynomial, we need at least 4 data points.
    if len(x_scatter) < 4:
        return x_scatter, y_scatter, np.array([]), np.array([])

    # Calculate the polynomial
    z = np.polyfit(x_scatter, y_scatter, 3)
    p = np.poly1d(z)

    # Create a smooth, sorted range of x-values for plotting the curve
    x_curve = np.linspace(x_scatter.min(), x_scatter.max(), 300)
    y_curve = p(x_curve)
    
    return x_scatter, y_scatter, x_curve, y_curve

def calculate_personality_stats(db_path=None):
    """
    计算五个性格维度的均值和方差
    返回: 包含均值和方差的字典
    """
    from sqlalchemy.orm import Session
    from sqlalchemy import text, create_engine
    
    engine = None
    if db_path:
        engine = create_engine(f'sqlite:///{db_path}')
    else:
        engine = get_engine()

    with Session(engine) as session:
        # 获取所有性别的数据
        ps = session.execute(text('select age,openness ,conscientiousness ,extraversion, agreeableness, neuroticism FROM persona_personality'))
        
        # 处理数据
        mdata = data(ps)
        
        # 性格维度名称
        personality_traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        
        # 计算统计量
        stats = {}
        for i, trait in enumerate(personality_traits):
            trait_data = np.array(mdata[i+1]) if len(mdata) > i + 1 else np.array([]) # i+1 因为mdata[0]是age
            
            if trait_data.size > 0:
                mean_val = np.mean(trait_data)
                var_val = np.var(trait_data)
                std_val = np.std(trait_data)
            else:
                mean_val = np.nan
                var_val = np.nan
                std_val = np.nan
            
            stats[trait] = {
                'mean': mean_val,
                'variance': var_val,
                'std': std_val,
                'data': trait_data.tolist()
            }
        
        return stats

def get_personas_ana(db_path=None, dimension='age', sex_filter='All'):
    from sqlalchemy.orm import Session
    from sqlalchemy import text, create_engine
    import pandas as pd

    engine = None
    if db_path:
        engine = create_engine(f'sqlite:///{db_path}')
    else:
        engine = get_engine()

    # Basic security check for dimension name
    if not dimension.isalnum() and '_' not in dimension:
        raise ValueError(f"Invalid dimension name: {dimension}")

    # Build the query
    base_query = f'SELECT {dimension}, openness, conscientiousness, extraversion, agreeableness, neuroticism FROM persona_personality'
    
    where_clauses = []
    if sex_filter != 'All':
        # Basic security check for sex_filter
        if sex_filter not in ['Male', 'Female']:
            raise ValueError(f"Invalid sex filter: {sex_filter}")
        where_clauses.append(f"sex = '{sex_filter}'")

    if where_clauses:
        base_query += ' WHERE ' + ' AND '.join(where_clauses)
        
    final_query = text(base_query + f' ORDER BY {dimension}')

    with Session(engine) as session:
        # Use pandas to easily handle the data
        df = pd.read_sql(final_query, session.bind)

    # Convert dataframe columns to a list of lists
    result_data = [df[col].tolist() for col in df.columns]
    
    return result_data

def project_personality_2d(method='pca'):
    """
    将五维personality向量降到二维，返回二维坐标和性别标签。
    method: 'pca' 或 'tsne'
    """
    import numpy as np
    import pandas as pd
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    from asociety.repository.database import get_engine

    with Session(get_engine()) as session:
        df = pd.read_sql(text('select openness, conscientiousness, extraversion, agreeableness, neuroticism, sex FROM persona_personality'), session.bind)
    X = df[['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']].values

    if method == 'pca':
        from sklearn.decomposition import PCA
        coords_2d = PCA(n_components=2).fit_transform(X)
    elif method == 'tsne':
        from sklearn.manifold import TSNE
        coords_2d = TSNE(n_components=2, random_state=42).fit_transform(X)
    else:
        raise ValueError('Unknown method')
    return coords_2d, df['sex'].values

def project_personality_1d():
    """
    将五维personality向量降到一维，返回一维坐标、性别标签和原始df。
    """
    import numpy as np
    import pandas as pd
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    from asociety.repository.database import get_engine

    with Session(get_engine()) as session:
        df = pd.read_sql(text('select * FROM persona_personality'), session.bind)
    X = df[['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']].values

    from sklearn.decomposition import PCA
    coords_1d = PCA(n_components=1).fit_transform(X).flatten()
    return coords_1d, df['sex'].values, df


      
   

