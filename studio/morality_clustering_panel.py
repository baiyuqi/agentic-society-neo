from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.clustering_panel import ClusteringPanel


class MoralityClusteringPanel(ClusteringPanel):
    """Morality twin of the clustering panel: K-Means over the 7-d moral-foundation vectors."""

    traits = MORALITY_TRAITS
    table = 'morality'
    initialdir = 'data/db/morality'
