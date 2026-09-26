"""Moral Foundations Questionnaire, MFQ-30.

Items and their foundation keying live in data/MFQ/MFQ30.json; see data/MFQ/README.md for the
provenance and the scoring rule.
"""

import json
import os

ITEMS_PATH = 'data/MFQ/MFQ30.json'
ITEM_WORDING = 'en_neutral'

# Response scales, 0..5. The MFQ is administered in two blocks and the scale changes with the
# block, so unlike the PVQ the scale is a property of the item, not of the instrument.
RELEVANCE_SCALE = [
    (0, 'Not at all relevant'),
    (1, 'Not very relevant'),
    (2, 'Slightly relevant'),
    (3, 'Somewhat relevant'),
    (4, 'Very relevant'),
    (5, 'Extremely relevant'),
]

AGREEMENT_SCALE = [
    (0, 'Strongly disagree'),
    (1, 'Moderately disagree'),
    (2, 'Slightly disagree'),
    (3, 'Slightly agree'),
    (4, 'Moderately agree'),
    (5, 'Strongly agree'),
]

SCALES = {'relevance': RELEVANCE_SCALE, 'agreement': AGREEMENT_SCALE}

FOUNDATION_TO_COLUMN = {
    'Care/Harm': 'care',
    'Fairness/Cheating': 'fairness',
    'Loyalty/Betrayal': 'loyalty',
    'Authority/Subversion': 'authority',
    'Sanctity/Degradation': 'sanctity',
}

HIGHER_TO_COLUMN = {
    'Individualizing': 'individualizing',
    'Binding': 'binding',
}

HIGHER_MEMBERS = {
    'Individualizing': ['Care/Harm', 'Fairness/Cheating'],
    'Binding': ['Loyalty/Betrayal', 'Authority/Subversion', 'Sanctity/Degradation'],
}

# The MFQ-30 has no reverse-scored items. Kept so a future instrument can add them without
# reshaping compute().
REVERSE = {}

# How each block is put to the model. The relevance items are sentence fragments ("Whether or not
# someone was cruel.") and need the "how relevant is this consideration" framing; the agreement
# items are self-contained statements.
PART_FRAMING = {
    'relevance': 'When you decide whether something is right or wrong, to what extent is the '
                 'following consideration relevant to your judgment?',
    'agreement': 'Please read the following statement and indicate how much you agree with it.',
}

_items = None


def items():
    """{question_id: {'text': str, 'foundation': str, 'higher_order': str, 'part': str}}"""
    global _items
    if _items is None:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            *ITEMS_PATH.split('/'))
        with open(path, encoding='utf-8') as f:
            raw = json.load(f)
        _items = {
            int(qid): {
                'text': entry[ITEM_WORDING],
                'foundation': entry['meta_data']['foundation'],
                'higher_order': entry['meta_data']['higher_order'],
                'part': entry['meta_data']['part'],
            }
            for qid, entry in raw.items()
        }
    return _items


def question_ids():
    return sorted(items())


def items_of(foundation_name):
    return [qid for qid, it in items().items() if it['foundation'] == foundation_name]


def higher_order_members():
    """{higher_order_name: [foundation_name, ...]} derived from the item keying."""
    out = {}
    for it in items().values():
        out.setdefault(it['higher_order'], [])
        if it['foundation'] not in out[it['higher_order']]:
            out[it['higher_order']].append(it['foundation'])
    return out


def options_text(part):
    """The numbered option block for this block's items, embedded in the quiz sheet."""
    return ''.join(f'{num}: {label}\n' for num, label in SCALES[part])


def question_text(qid):
    """The item as it is put to the model: the block's framing plus the item wording."""
    it = items()[qid]
    return f"{PART_FRAMING[it['part']]}\n\"{it['text']}\""


def compute(answers):
    """Score one persona.

    answers: [{'id_question': int|str, 'id_select': int}] as returned by
    asociety.personality.answer_extractor.get_answers.

    Each item is scored 0-5 and each foundation score is the raw mean of its items -- the
    conventional MFQ-30 scoring, with no within-person centring. Contrast asociety.value.pvq,
    where every item is centred on the persona's own grand mean: here an all-5s response scores
    5.0 on every scale, not 0.0.
    """
    keyed = items()
    raw = {}
    for a in answers:
        try:
            qid = int(a['id_question'])
        except (KeyError, TypeError, ValueError):
            continue
        if qid not in keyed:
            continue
        raw[qid] = int(a['id_select'])

    if not raw:
        return {'foundations': {}, 'higher_order': {}, 'items': {}}

    scores = {qid: (5 - score if REVERSE.get(qid) else score) for qid, score in raw.items()}

    foundations = {}
    for name in FOUNDATION_TO_COLUMN:
        qids = [q for q in items_of(name) if q in scores]
        if qids:
            foundations[name] = sum(scores[q] for q in qids) / len(qids)

    higher = {}
    for name, members in higher_order_members().items():
        present = [foundations[m] for m in members if m in foundations]
        if present:
            higher[name] = sum(present) / len(present)

    return {
        'foundations': foundations,
        'higher_order': higher,
        'items': raw,
    }
