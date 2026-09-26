from asociety.value.value_analysis import VALUE_TRAITS
from studio.single_density_panel import SingleDensityPanel


class ValueSingleDensityPanel(SingleDensityPanel):
    """Value twin of the manual multi-file Mahalanobis density panel."""

    traits = VALUE_TRAITS
    table = 'value'
    initialdir = 'data/db/value'
    title = "价值观马氏距离分析 (多文件)"
