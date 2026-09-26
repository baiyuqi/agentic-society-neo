from asociety.value.value_analysis import VALUE_TRAITS
from studio.group_identifiability_panel import GroupIdentifiabilityPanel


class ValueGroupIdentifiabilityPanel(GroupIdentifiabilityPanel):
    """Value twin of the poor-vs-standard group clustering panel."""

    traits = VALUE_TRAITS
    table = 'value'
    data_dir = 'data/db/value/individual'
    title = "价值观群体可识别性分析：贫乏 vs 标准样本聚类"
