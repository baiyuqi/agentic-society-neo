from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.multi_mahalanobis_panel import MultiMahalanobisPanel


class MoralityMultiMahalanobisPanel(MultiMahalanobisPanel):
    """Morality twin of the multi-source Mahalanobis panel: spread within each morality arm."""

    traits = MORALITY_TRAITS
    table = 'morality'
    data_dir = 'data/db/morality/individual'
