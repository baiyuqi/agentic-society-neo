from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.file_clustering_panel import FileClusteringPanel


class MoralityFileClusteringPanel(FileClusteringPanel):
    """Morality twin of the manual file-clustering panel: K-Means over the 7-d morality vectors."""

    traits = MORALITY_TRAITS
    table = 'morality'
    initialdir = 'data/db/morality'
