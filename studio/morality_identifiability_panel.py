from asociety.morality.morality_analysis import MORALITY_TRAITS
from studio.identifiability_panel import IdentifiabilityPanel


class MoralityIdentifiabilityPanel(IdentifiabilityPanel):
    """Morality twin of the identifiability panel: are the moral-foundation profiles distinguishable?

    Compares the standard group against the poor group, exactly as the personality panel does;
    both directories are the morality tree's mirrored copies of the same personas.
    """

    traits = MORALITY_TRAITS
    table = 'morality'
    dir_samples = "data/db/morality/individual"
    dir_poor = "data/db/morality/individual"
    label_samples = "标准样本 (Samples 300)"
    label_poor = "贫乏样本 (Poor 300)"
    title = "道德基础可识别性分析：比较标准样本与贫乏样本"
