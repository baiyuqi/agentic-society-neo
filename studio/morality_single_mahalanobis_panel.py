from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.single_mahalanobis_panel import SingleMahalanobisPanel


class MoralitySingleMahalanobisPanel(SingleMahalanobisPanel):
    """Morality twin of the single-profile Mahalanobis panel: the spread of one morality DB."""

    traits = MORALITY_TRAITS
    table = 'morality'
    initialdir = 'data/db/morality'
