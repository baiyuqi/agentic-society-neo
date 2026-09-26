from asociety.value.value_analysis import VALUE_TRAITS
from studio.identifiability_panel import IdentifiabilityPanel


class ValueIdentifiabilityPanel(IdentifiabilityPanel):
    """Value twin of the identifiability panel: are the value profiles distinguishable?

    Compares the standard group against the poor group, exactly as the personality panel does;
    both directories are the value tree's mirrored copies of the same personas.
    """

    traits = VALUE_TRAITS
    table = 'value'
    dir_samples = "data/db/value/individual"
    dir_poor = "data/db/value/individual"
    label_samples = "标准样本 (Samples 300)"
    label_poor = "贫乏样本 (Poor 300)"
    title = "价值观可识别性分析：比较标准样本与贫乏样本"
