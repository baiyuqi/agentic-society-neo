from asociety.value.value_analysis import VALUE_TRAITS
from studio.multi_mahalanobis_panel import MultiMahalanobisPanel


class ValueMultiMahalanobisPanel(MultiMahalanobisPanel):
    """Value twin of the multi-source Mahalanobis panel: spread within each value arm."""

    traits = VALUE_TRAITS
    table = 'value'
    data_dir = 'data/db/value/individual'
