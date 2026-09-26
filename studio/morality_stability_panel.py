from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.stability_analysis_panel import StabilityAnalysisPanel


class MoralityStabilityPanel(StabilityAnalysisPanel):
    """Morality twin of the stability panel: same persona, two morality runs, Mahalanobis distance."""

    traits = MORALITY_TRAITS
    table = 'morality'
    data_dir = 'data/db/morality/individual'
    title = "道德基础稳定性分析 (马氏距离)"
