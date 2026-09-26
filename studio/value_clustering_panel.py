from asociety.value.value_analysis import VALUE_TRAITS
from studio.clustering_panel import ClusteringPanel


class ValueClusteringPanel(ClusteringPanel):
    """Value twin of the clustering panel: K-Means over the 14-d value vectors."""

    traits = VALUE_TRAITS
    table = 'value'
    initialdir = 'data/db/value'
