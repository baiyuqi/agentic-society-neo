from asociety.value.value_analysis import VALUE_TRAITS
from studio.identifiability_panel import IdentifiabilityPanel


class ValueIdentifiabilityPanel(IdentifiabilityPanel):
    """Value twin of the pairwise identifiability panel: are two personas' value runs distinguishable?"""

    traits = VALUE_TRAITS
    table = 'value'
    data_dir = "data/db/value/individual"
    title = "价值观可识别性分析：画像两两对比"
