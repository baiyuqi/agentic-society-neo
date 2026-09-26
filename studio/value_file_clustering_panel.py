from asociety.value.value_analysis import VALUE_TRAITS
from studio.file_clustering_panel import FileClusteringPanel


class ValueFileClusteringPanel(FileClusteringPanel):
    """Value twin of the manual file-clustering panel: K-Means over the 14-d value vectors."""

    traits = VALUE_TRAITS
    table = 'value'
    initialdir = 'data/db/value'
