"""Instrument surface shared by the Schwartz PVQ-21 curve panels.

BaseCurvePanel indexes its mdata positionally, and `get_values_ana` returns
[age, <10 primary values>, <4 higher-order values>] in VALUE_TRAITS order, so the
higher-order values sit at mdata[11:15]. Those four fit the inherited 2x3 grid and
leave one cell for the legend.
"""

from asociety.value.value_analysis import get_values_ana
from studio.base_curve_panel import BaseCurvePanel


class ValueCurvePanelBase(BaseCurvePanel):
    # Mirrors HIGHER_ORDER_VALUES, i.e. the order of mdata[11:15].
    trait_order = ['Openness to change', 'Self-Enhancement', 'Self-Transcendence', 'Conservation']
    data_index_map = [11, 12, 13, 14]
    table_columns = ('model', 'OTC', 'SE', 'ST', 'CON', 'euclidean')
    table_headings = {
        'model': 'Model', 'OTC': 'Openness to change', 'SE': 'Self-Enhancement',
        'ST': 'Self-Transcendence', 'CON': 'Conservation', 'euclidean': 'Euclidean Dist.',
    }
    human_db_path = 'data/db/value/human.db'
    grid_shape = (2, 3)

    def load_mdata(self, db_path):
        return get_values_ana(db_path=db_path, dimension='age')
