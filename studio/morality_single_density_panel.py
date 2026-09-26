from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.single_density_panel import SingleDensityPanel


class MoralitySingleDensityPanel(SingleDensityPanel):
    """Morality twin of the manual multi-file Mahalanobis density panel."""

    traits = MORALITY_TRAITS
    table = 'morality'
    initialdir = 'data/db/morality'
    title = "道德基础马氏距离分析 (多文件)"
