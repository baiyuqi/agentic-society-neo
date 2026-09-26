from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.comparison_panel import ComparisonPanel


class MoralityComparisonPanel(ComparisonPanel):
    """Morality twin of the pairwise comparison panel: Mahalanobis distance between morality DBs."""

    traits = MORALITY_TRAITS
    table = 'morality'
    initialdir = 'data/db/morality'
