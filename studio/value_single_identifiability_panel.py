from asociety.value.value_analysis import VALUE_TRAITS
from studio.single_identifiability_panel import SingleIdentifiabilityPanel


class ValueSingleIdentifiabilityPanel(SingleIdentifiabilityPanel):
    """Value twin of the pairwise identifiability panel: are two personas' value runs distinguishable?"""

    traits = VALUE_TRAITS
    table = 'value'
    initialdir = 'data/db/value/individual'
    title = "价值观单一可辨识性分析：贫乏 vs 标准样本聚类对比"
