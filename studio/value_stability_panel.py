from asociety.value.value_analysis import VALUE_TRAITS
from studio.stability_analysis_panel import StabilityAnalysisPanel


class ValueStabilityPanel(StabilityAnalysisPanel):
    """Value twin of the stability panel: same persona, two value runs, Mahalanobis distance."""

    traits = VALUE_TRAITS
    table = 'value'
    data_dir = 'data/db/value/individual'
    title = "价值观稳定性分析 (马氏距离)"
