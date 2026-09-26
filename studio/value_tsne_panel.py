from asociety.value.value_analysis import VALUE_TRAITS
from studio.tsne_panel import TSNEPanel


class ValueTSNEPanel(TSNEPanel):
    """Value twin of the t-SNE panel: the 14-d value space projected to 2-d."""

    traits = VALUE_TRAITS
    table = 'value'
    initialdir = 'data/db/value'
