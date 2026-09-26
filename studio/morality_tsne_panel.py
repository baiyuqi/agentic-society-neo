from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.tsne_panel import TSNEPanel


class MoralityTSNEPanel(TSNEPanel):
    """Morality twin of the t-SNE panel: the 7-d moral-foundation space projected to 2-d."""

    traits = MORALITY_TRAITS
    table = 'morality'
    initialdir = 'data/db/morality'
