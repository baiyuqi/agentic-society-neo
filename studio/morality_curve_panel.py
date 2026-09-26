"""Instrument surface shared by the MFQ-30 curve panels.

BaseCurvePanel indexes its mdata positionally, and `get_morality_ana` returns
[age, <5 foundations>, <2 higher-order>] in MORALITY_TRAITS order, so the higher-order
scores sit at mdata[6:8]. The seven traits fill a 3x3 grid and leave two cells for the legend.
"""

from asociety.morality.morality_analysis import get_morality_ana
from studio.base_curve_panel import BaseCurvePanel


class MoralityCurvePanelBase(BaseCurvePanel):
    # Mirrors MORALITY_TRAITS, i.e. the order of mdata[1:8].
    trait_order = ['care', 'fairness', 'loyalty', 'authority', 'sanctity',
                   'individualizing', 'binding']
    data_index_map = [1, 2, 3, 4, 5, 6, 7]
    table_columns = ('model', 'CAR', 'FAI', 'LOY', 'AUT', 'SAN', 'IND', 'BIN', 'euclidean')
    table_headings = {
        'model': 'Model', 'CAR': 'Care', 'FAI': 'Fairness', 'LOY': 'Loyalty',
        'AUT': 'Authority', 'SAN': 'Sanctity', 'IND': 'Individualizing', 'BIN': 'Binding',
        'euclidean': 'Euclidean Dist.',
    }
    # The human reference is the "D and Moral Foundations" deposit (OSF 37eht), built by
    # tools/importers/import_mfq_human.py; see data/MFQ/human/README.md.
    human_db_path = 'data/db/morality/human.db'
    grid_shape = (3, 3)

    def load_mdata(self, db_path):
        return get_morality_ana(db_path=db_path, dimension='age')
