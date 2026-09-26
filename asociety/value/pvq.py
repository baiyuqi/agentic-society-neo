"""Schwartz Portrait Values Questionnaire, ESS PVQ-21 short form.

Items and their value keying live in data/PVQ/PVQ21.json; see data/PVQ/README.md for the
provenance and the scoring rule.
"""

import json
import os

ITEMS_PATH = 'data/PVQ/PVQ21.json'
ITEM_WORDING = 'en_neutral'

# Response scale, 1..6.
SCALE = [
    (1, 'Not like me at all'),
    (2, 'Not like me'),
    (3, 'A little like me'),
    (4, 'Somewhat like me'),
    (5, 'Like me'),
    (6, 'Very much like me'),
]

VALUE_TO_COLUMN = {
    'Self-Direction': 'self_direction',
    'Power': 'power',
    'Universalism': 'universalism',
    'Achievement': 'achievement',
    'Security': 'security',
    'Stimulation': 'stimulation',
    'Conformity': 'conformity',
    'Tradition': 'tradition',
    'Hedonism': 'hedonism',
    'Benevolence': 'benevolence',
}

HIGHER_TO_COLUMN = {
    'Openness to change': 'openness_to_change',
    'Self-Enhancement': 'self_enhancement',
    'Self-Transcendence': 'self_transcendence',
    'Conservation': 'conservation',
}

# The PVQ-21 has no reverse-scored items. Kept so a future instrument can add them without
# reshaping compute().
REVERSE = {}

_items = None


def items():
    """{question_id: {'text': str, 'value': str, 'higher_order_value': str}}"""
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
                'value': entry['meta_data']['value'],
                'higher_order_value': entry['meta_data']['higher_order_value'],
            }
            for qid, entry in raw.items()
        }
    return _items


def question_ids():
    return sorted(items())


def items_of(value_name):
    return [qid for qid, it in items().items() if it['value'] == value_name]


def higher_order_members():
    """{higher_order_name: [value_name, ...]} derived from the item keying."""
    out = {}
    for it in items().values():
        out.setdefault(it['higher_order_value'], [])
        if it['value'] not in out[it['higher_order_value']]:
            out[it['higher_order_value']].append(it['value'])
    return out


def options_text():
    """The numbered option block embedded in each quiz sheet."""
    return ''.join(f'{num}: {label}\n' for num, label in SCALE)


def compute(answers):
    """Score one persona.

    answers: [{'id_question': int|str, 'id_select': int}] as returned by
    asociety.personality.answer_extractor.get_answers.

    Each item is scored 1-6, the mean over the 21 items is subtracted from every item, and each
    value score is the mean of its centred items: the ESS PVQ scoring rule, so the scores are
    directly comparable with the ESS human baseline.
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
        return {'values': {}, 'higher_order': {}, 'items': {}, 'grand_mean': None}

    grand_mean = sum(raw.values()) / len(raw)
    centred = {
        qid: (1 + 6 - score if REVERSE.get(qid) else score) - grand_mean
        for qid, score in raw.items()
    }

    values = {}
    for name in VALUE_TO_COLUMN:
        qids = [q for q in items_of(name) if q in centred]
        if qids:
            values[name] = sum(centred[q] for q in qids) / len(qids)

    higher = {}
    for name, members in higher_order_members().items():
        present = [values[m] for m in members if m in values]
        if present:
            higher[name] = sum(present) / len(present)

    return {
        'values': values,
        'higher_order': higher,
        'items': raw,
        'grand_mean': grand_mean,
    }
