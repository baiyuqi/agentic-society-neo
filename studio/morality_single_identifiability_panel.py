from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.single_identifiability_panel import SingleIdentifiabilityPanel


class MoralitySingleIdentifiabilityPanel(SingleIdentifiabilityPanel):
    """Morality twin of the pairwise identifiability panel: are two personas' morality runs distinguishable?"""

    traits = MORALITY_TRAITS
    table = 'morality'
    initialdir = 'data/db/morality/individual'
    title = "道德基础单一可辨识性分析：贫乏 vs 标准样本聚类对比"
