from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.group_identifiability_panel import GroupIdentifiabilityPanel


class MoralityGroupIdentifiabilityPanel(GroupIdentifiabilityPanel):
    """Morality twin of the poor-vs-standard group clustering panel."""

    traits = MORALITY_TRAITS
    table = 'morality'
    data_dir = 'data/db/morality/individual'
    title = "道德基础群体可识别性分析：贫乏 vs 标准样本聚类"
