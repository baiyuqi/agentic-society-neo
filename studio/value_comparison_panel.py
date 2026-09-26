from asociety.value.value_analysis import VALUE_TRAITS
from studio.comparison_panel import ComparisonPanel


class ValueComparisonPanel(ComparisonPanel):
    """Value twin of the pairwise comparison panel: Mahalanobis distance between value DBs."""

    traits = VALUE_TRAITS
    table = 'value'
    initialdir = 'data/db/value'
