from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.identifiability_panel import IdentifiabilityPanel


class MoralityIdentifiabilityPanel(IdentifiabilityPanel):
    """Morality twin of the pairwise identifiability panel: are two personas' morality runs distinguishable?"""

    traits = MORALITY_TRAITS
    table = 'morality'
    data_dir = "data/db/morality/individual"
    title = "道德基础可识别性分析：画像两两对比"
