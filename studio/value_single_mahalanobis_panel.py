from asociety.value.value_analysis import VALUE_TRAITS
from studio.single_mahalanobis_panel import SingleMahalanobisPanel


class ValueSingleMahalanobisPanel(SingleMahalanobisPanel):
    """Value twin of the single-profile Mahalanobis panel: the spread of one value DB."""

    traits = VALUE_TRAITS
    table = 'value'
    initialdir = 'data/db/value'
