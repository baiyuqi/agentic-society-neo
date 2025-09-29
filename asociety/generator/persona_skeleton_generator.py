import pandas as pd
import numpy as np
from asociety.repository.persona_rep import save_skeleton_personas

class PersonaSkeletonGenerator:
    def __init__(self, df) -> None:
        self.df = df
        self.total = df["fnlwgt"].sum()
        df["probability"] = df["fnlwgt"].apply(lambda x: x/self.total)
        # It's good practice to ensure probabilities sum to 1
        # np.isclose is better for floating point comparisons
        assert np.isclose(df["probability"].sum(), 1.0)

    def sampling(self, n: int):
        """
        Samples n skeletons, saves them directly to the database,
        and returns the generated samples as a list of dictionaries.
        """
        if n <= 0:
            return []
            
        # Perform sampling
        sample_indices = np.random.choice(self.df.shape[0], n, p=self.df["probability"].values)
        samples_df = self.df.iloc[sample_indices]
        
        # Convert to list of dictionaries for saving
        samples_list = samples_df.to_dict('records')
        import uuid
        for item in samples_list:
            item['id'] = str(uuid.uuid4())
        # Save the newly generated skeletons to the database
        print(f"Saving {len(samples_list)} new skeletons to the database...")
        save_skeleton_personas(samples_list)
        print("Skeletons saved.")
        
        return samples_list
      
    def enum(self, column:str):
        values = self.df[column].unique()
        return values
        
    def margin(self, column:str):
        values = self.df.groupby(column, sort=False)["probability"].sum().reset_index(name='probability')
        return values

class PersonaSkeletonGeneratorFactory:
    @classmethod
    def create(cls, column: str = None, value: any = None) -> PersonaSkeletonGenerator:
        df = pd.read_csv('data/census.csv')
        if column is not None and value is not None:
            df = df[df[column].isin([value])]
        return PersonaSkeletonGenerator(df)





