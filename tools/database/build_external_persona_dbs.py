"""Build two external-persona pipeline DBs (ThinkPersona + real-persona-chat) and distribute them.

The two external datasets are persona *profiles* (人物画像), not human baselines: their full
natural-language content -- introduction + knowledge-graph triples + interview Q&A (ThinkPersona),
and persona sentences + conversation transcript (real-persona-chat) -- becomes `persona.persona_desc`.
Only the measurement scale's items/scores are excluded, which these datasets do not contain.

Each dataset yields 620 personas, traceable through `persona.sourcePersonaId`
(`{id}@thinkpersona` / `{dialogue_id}-{speaker}@real-persona-chat`). Each source is then copied into
all three trees (`personality/`, `value/`, `morality/`), injected with its `meta` and the
instrument's question items, so a run starts ready:

    request_method = 'sheet' everywhere (question-by-question is legacy). IPIP-NEO-120 splits into
    6 sheets of 20; PVQ-21 and MFQ-30 go out as a single whole sheet (整卷).

Usage:
    python tools/database/build_external_persona_dbs.py extract   # extract + translate -> 2 JSON files
    python tools/database/build_external_persona_dbs.py build     # build 6 DBs from the JSON files
    python tools/database/build_external_persona_dbs.py verify    # assert the 6 DBs are runnable
    python tools/database/build_external_persona_dbs.py all       # extract + build + verify
"""

import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

DB_ROOT = os.path.join(ROOT, 'data', 'db')
DATASETS = ('thinkpersona', 'real-persona-chat')
TREES = ('personality', 'value', 'morality')
N_PERSONAS = 620

THINKPERSONA_PATH = os.path.join(ROOT, 'data', 'thinkpersona', 'ThinkPersonaDataset.json')
RPC_PARQUET_PATH = os.path.join(
    ROOT, 'data', 'real-persona-chat', 'data', 'train-00000-of-00001.parquet')
THINKPERSONA_OUT = os.path.join(ROOT, 'data', 'thinkpersona', 'personas_620.json')
RPC_OUT = os.path.join(ROOT, 'data', 'real-persona-chat', 'personas_620.json')

# --- IPIP-NEO-120 items (the personality tree's question set) -------------------------------

def ipip_questions():
    with open(os.path.join(ROOT, 'data', 'IPIP-NEO', '120', 'questions.json'), encoding='utf-8') as f:
        raw = json.load(f)
    options = ''.join(f"{e['id']}: {e['text']}\n" for e in raw['select'])
    qs = raw['questions']
    return [(int(q['id']), q['text'], options) for q in qs]


# --- provenance + attribute extraction -------------------------------------------------------

_AGE_EN = re.compile(
    r'(?:\bage\s*)?(\d{1,3})\s*(?:years?\s*old|years?\s*of\s*age|[- ]years?\s*old|yo)\b'
    r'|\bage\s*(\d{1,3})\b'
    r'|(\d{1,3})\s*[- ]year[- ]old\b'
    r'|\bborn\s+in\s+(\d{4})\b')
_AGE_JA = re.compile(r'(\d{1,3})\s*[歳才]')

_MALE_EN = re.compile(r'\b(he|him|his|man|men|male|father|son|brother|uncle|husband|boy|gentleman)\b', re.I)
_FEMALE_EN = re.compile(r'\b(she|her|hers|woman|women|female|mother|daughter|sister|aunt|wife|girl|lady)\b', re.I)
_MALE_JA = re.compile(r'(夫|父|息子|男|彼|僕|俺|兄|弟|旦那|お父さん)')
_FEMALE_JA = re.compile(r'(妻|母|娘|女|彼女|姉|妹|奥さん|お母さん)')

_DEFAULT_AGE = 40


def extract_age(*texts):
    for text in texts:
        if not text:
            continue
        for m in _AGE_EN.finditer(text):
            year = m.group(4)
            if year:
                age = 2026 - int(year)
                if 0 < age < 130:
                    return age
            age = next((int(g) for g in m.groups()[:3] if g), None)
            if age and 10 <= age < 120:
                return age
        m = _AGE_JA.search(text)
        if m:
            age = int(m.group(1))
            if 10 <= age < 120:
                return age
    return _DEFAULT_AGE


def extract_sex(*texts):
    male = female = 0
    for text in texts:
        if not text:
            continue
        male += len(_MALE_EN.findall(text)) + len(_MALE_JA.findall(text))
        female += len(_FEMALE_EN.findall(text)) + len(_FEMALE_JA.findall(text))
    if male > female:
        return 'Male'
    if female > male:
        return 'Female'
    return None


def _occupation_from_triples(triples):
    """The 'Occupation' node's hasValue tails (the person's occupation(s))."""
    values = [t['tail'] for t in triples
              if t.get('relation') == 'hasValue' and t.get('head') == 'Occupation']
    return ', '.join(values) if values else None


# --- ThinkPersona ----------------------------------------------------------------------------

def build_thinkpersona_personas(n=N_PERSONAS):
    with open(THINKPERSONA_PATH, encoding='utf-8') as f:
        data = json.load(f)
    out = []
    for i, rec in enumerate(data[:n]):
        intro = rec.get('introduction') or ''
        facts = []
        for t in rec.get('triple', []):
            head, rel, tail = t.get('head'), t.get('relation'), t.get('tail')
            if head and tail:
                facts.append(f"- {head} {rel} {tail}")
        qa = []
        for item in rec.get('qra', []):
            q, a = item.get('q'), item.get('a')
            if q and a:
                qa.append(f"Q: {q}\nA: {a}")
        parts = [intro.strip()]
        if facts:
            parts.append('\nFacts:\n' + '\n'.join(facts))
        if qa:
            parts.append('\nInterview:\n' + '\n\n'.join(qa))
        persona_desc = '\n'.join(p for p in parts if p).strip()

        out.append({
            'id': i + 1,
            'sourcePersonaId': f"{rec.get('id')}@thinkpersona",
            'age': extract_age(intro),
            'sex': extract_sex(intro),
            'occupation': _occupation_from_triples(rec.get('triple', [])),
            'persona_desc': persona_desc,
        })
    return out


# --- real-persona-chat (Japanese -> English) --------------------------------------------------

def get_translate_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model='deepseek-chat',
        openai_api_base=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
        api_key=os.getenv('DEEPSEEK_API_KEY'))


_TRANSLATE_SYSTEM = (
    "You translate Japanese persona data into natural, fluent English. "
    "Preserve the first-person voice, all factual details, and the emotional tone. "
    "Do not add, omit, or interpret information beyond what is written."
)


def translate_interlocutor(llm, persona_sentences, turns):
    block = "Persona sentences:\n" + "\n".join(
        f"{i + 1}. {s}" for i, s in enumerate(persona_sentences)) + "\n\n"
    block += "Conversation turns (in order):\n" + "\n".join(
        f"{spk}: {txt}" for spk, txt in turns)
    prompt = (
        "Translate the following Japanese persona data into English. Return ONLY a JSON object "
        "with two keys:\n"
        '  "persona_en": a list of the translated persona sentences (same order),\n'
        '  "turns_en": a list of { "speaker": "<speaker>", "text": "<translated>" } objects for '
        "the conversation turns (same order).\n\n"
        + block)
    resp = llm.invoke(prompt)
    text = resp.content if hasattr(resp, 'content') else str(resp)
    return _parse_json(text)


def _parse_json(text):
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def _translate_one(item):
    dialogue_id, speaker_id, role, sentences, turns = item
    try:
        translated = translate_interlocutor(_SHARED_LLM, sentences, turns)
    except Exception as e:
        print(f'  [warn] translate failed for {dialogue_id}-{speaker_id}: {e}')
        translated = {'persona_en': sentences,
                      'turns_en': [{'speaker': spk, 'text': txt} for spk, txt in turns]}
    return dialogue_id, speaker_id, sentences, turns, translated


def _rpc_work_items(df, n):
    items = []
    for row_idx in range(n // 2):
        r = df.iloc[row_idx]
        dialogue_id = str(r['dialogue_id'])
        conversations = list(r['conversations'])
        turns = [(str(c['from']), str(c['value'])) for c in conversations]
        for interlocutor in list(r['interlocutors']):
            speaker_id = str(interlocutor['id'])
            role = str(interlocutor['role'])
            sentences = [str(s) for s in interlocutor['persona']]
            items.append((dialogue_id, speaker_id, role, sentences, turns))
    return items


def build_rpc_personas(n=N_PERSONAS, workers=15):
    import pandas as pd
    from concurrent.futures import ThreadPoolExecutor, as_completed
    global _SHARED_LLM
    _SHARED_LLM = get_translate_llm()

    df = pd.read_parquet(RPC_PARQUET_PATH)
    items = _rpc_work_items(df, n)
    personas = [None] * len(items)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_translate_one, item): idx for idx, item in enumerate(items)}
        done = 0
        for fut in as_completed(futures):
            idx = futures[fut]
            dialogue_id, speaker_id, sentences, turns, translated = fut.result()
            persona_en = translated.get('persona_en') or sentences
            turns_en = translated.get('turns_en') or [
                {'speaker': spk, 'text': txt} for spk, txt in turns]

            block = "Persona profile:\n" + "\n".join(f"- {s}" for s in persona_en)
            if turns_en:
                block += "\n\nConversation transcript:\n" + "\n".join(
                    f"{t.get('speaker')}: {t.get('text')}" for t in turns_en)

            ja_text = ' '.join(sentences)
            personas[idx] = {
                'id': idx + 1,
                'sourcePersonaId': f"{dialogue_id}-{speaker_id}@real-persona-chat",
                'age': extract_age(ja_text),
                'sex': extract_sex(ja_text),
                'occupation': None,
                'persona_desc': block.strip(),
            }
            done += 1
            if done % 100 == 0:
                print(f'    translated {done}/{len(items)}')

    return personas


# --- DB build --------------------------------------------------------------------------------

# The age-bucket CASE shared by all three persona_* views.
AGE_CASE = """CASE
   WHEN persona.age BETWEEN 16 AND 20 THEN '16_19'
  WHEN persona.age BETWEEN 20 AND 30 THEN '20_29'
  WHEN persona.age BETWEEN 30 AND 40 THEN '30_39'
  WHEN persona.age BETWEEN 40 AND 50 THEN '40_49'
  WHEN persona.age BETWEEN 50 AND 60 THEN '50_59'
  WHEN persona.age BETWEEN 60 AND 70 THEN '60_69'
  WHEN persona.age BETWEEN 70 AND 80 THEN '70_79'
  WHEN persona.age BETWEEN 80 AND 90 THEN '80_89'
  WHEN persona.age BETWEEN 90 AND 100 THEN '90_99'
  WHEN persona.age BETWEEN 100 AND 110 THEN '100_109'
END"""

META = {
    'personality': {'llm': 'deepseek', 'request_method': 'sheet', 'question_prompt': 'sheet_prompt',
                    'persona_prompt': 'from_skeleton', 'model': 'IPIP-NEO'},
    'value': {'llm': 'deepseek', 'request_method': 'sheet', 'question_prompt': 'sheet_prompt',
              'persona_prompt': 'from_skeleton', 'model': 'deepseek'},
    'morality': {'llm': 'deepseek', 'request_method': 'sheet', 'question_prompt': 'sheet_prompt',
                 'persona_prompt': 'from_skeleton', 'model': 'deepseek'},
}

RESULTS_TABLE = {'personality': 'personality', 'value': 'value', 'morality': 'morality'}
RESULTS_VIEW = {'personality': 'persona_personality', 'value': 'persona_value',
                'morality': 'persona_morality'}

QUIZ_SHEET_DDL = """CREATE TABLE quiz_sheet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sheet TEXT
            )"""


def _persona_ddl_path(tree):
    return os.path.join(DB_ROOT, tree, 'population')


def db_path(tree, dataset):
    return os.path.join(_persona_ddl_path(tree), f'{dataset}.db')


def _normalize_quiz_sheet(con):
    ddl = con.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='quiz_sheet'").fetchone()
    if ddl and 'AUTOINCREMENT' in ddl[0]:
        return
    con.execute('DROP TABLE IF EXISTS quiz_sheet')
    con.execute(QUIZ_SHEET_DDL)


def _insert_personas(path, personas):
    con = sqlite3.connect(path)
    try:
        con.executemany(
            'INSERT INTO persona (id, age, sourcePersonaId, sex, occupation, persona_desc) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            [(p['id'], p['age'], p['sourcePersonaId'], p['sex'], p['occupation'],
              p['persona_desc']) for p in personas])
        con.commit()
    finally:
        con.close()


def _load_questions(tree):
    from asociety.repository.database import set_currentdb
    if tree == 'personality':
        from asociety.repository.experiment_rep import Question
        from sqlalchemy.orm import Session
        from asociety.repository.database import get_engine
        with Session(get_engine()) as session:
            for qid, text, options in ipip_questions():
                session.add(Question(id=qid, question=text, options=options))
            session.commit()
        print('    loaded 120 IPIP items')
    elif tree == 'value':
        from tools.importers.import_pvq_set import import_pvq_set
        import_pvq_set()
    elif tree == 'morality':
        from tools.importers.import_mfq_set import import_mfq_set
        import_mfq_set()


def _create_view(tree):
    from asociety.repository.database import get_engine
    from sqlalchemy import text
    view = RESULTS_VIEW[tree]
    table = RESULTS_TABLE[tree]
    ddl = (f'CREATE VIEW "{view}" AS select\n {AGE_CASE} AS age_range,\n'
           f'persona.*, {table}.* from persona, {table} '
           f'where persona.id = {table}.persona_id')
    with get_engine().begin() as conn:
        conn.execute(text(f'DROP VIEW IF EXISTS "{view}"'))
        conn.execute(text(ddl))


def _set_meta(tree):
    from asociety.repository.meta_rep import set_meta
    set_meta(META[tree])


def _prepare_sheets(rel):
    """Materialize the quiz_sheet rows at build time so a run starts sheet-ready.

    The sheet content is a pure function of the question table + the instrument's sheet_size, so
    a run-ready DB carries it rather than leaving the pipeline to compute it. load_from_db derives
    the instrument from the question count already loaded by _load_questions.
    """
    from asociety import config
    from asociety.personality.quiz_service import create_sheets
    config.load_from_db(rel)
    create_sheets()


def build_one(tree, dataset, personas):
    from asociety.repository.database import set_currentdb, create_tables
    path = db_path(tree, dataset)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    rel = os.path.relpath(path, ROOT).replace('\\', '/')
    set_currentdb(rel)
    create_tables()

    con = sqlite3.connect(path)
    try:
        _normalize_quiz_sheet(con)
        con.commit()
    finally:
        con.close()

    _insert_personas(path, personas)
    _load_questions(tree)
    _set_meta(tree)
    _prepare_sheets(rel)
    _create_view(tree)
    print(f'  built {rel}: {len(personas)} personas')


def build():
    with open(THINKPERSONA_OUT, encoding='utf-8') as f:
        tp = json.load(f)
    with open(RPC_OUT, encoding='utf-8') as f:
        rpc = json.load(f)
    sources = {'thinkpersona': tp, 'real-persona-chat': rpc}
    for dataset in DATASETS:
        for tree in TREES:
            build_one(tree, dataset, sources[dataset])


def verify():
    from asociety.repository.database import set_currentdb
    failures = []
    for dataset in DATASETS:
        for tree in TREES:
            path = db_path(tree, dataset)
            rel = os.path.relpath(path, ROOT).replace('\\', '/')
            if not os.path.exists(path):
                failures.append(f'{rel}: missing')
                continue
            con = sqlite3.connect(path)
            try:
                n_persona = con.execute('SELECT COUNT(*) FROM persona').fetchone()[0]
                n_q = con.execute('SELECT COUNT(*) FROM question').fetchone()[0]
                n_sheets = con.execute('SELECT COUNT(*) FROM quiz_sheet').fetchone()[0]
                meta = dict(con.execute('SELECT key, value FROM meta').fetchall())
                results = RESULTS_TABLE[tree]
                view = RESULTS_VIEW[tree]
                has_results = con.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (results,)).fetchone()
                has_view = con.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='view' AND name=?", (view,)).fetchone()
                src = con.execute('SELECT sourcePersonaId FROM persona LIMIT 1').fetchone()[0]
                has_src_col = 'sourcePersonaId' in {
                    r[1] for r in con.execute('PRAGMA table_info(persona)')}
            finally:
                con.close()

            expected_q = {'personality': 120, 'value': 21, 'morality': 30}[tree]
            expected_sheets = {'personality': 6, 'value': 1, 'morality': 1}[tree]
            if n_persona != N_PERSONAS:
                failures.append(f'{rel}: {n_persona} personas (expected {N_PERSONAS})')
            if n_q != expected_q:
                failures.append(f'{rel}: {n_q} questions (expected {expected_q})')
            if n_sheets != expected_sheets:
                failures.append(f'{rel}: {n_sheets} quiz_sheets (expected {expected_sheets})')
            if meta.get('request_method') != 'sheet':
                failures.append(f'{rel}: request_method={meta.get("request_method")} (expected sheet)')
            if not has_src_col:
                failures.append(f'{rel}: persona lacks sourcePersonaId')
            if src is None or '@' not in src:
                failures.append(f'{rel}: sourcePersonaId not set ({src!r})')
            if not has_results or not has_view:
                failures.append(f'{rel}: missing {results} table or {view} view')
            print(f'  {rel}: {n_persona} personas, {n_q} questions, {n_sheets} sheets, meta={meta["request_method"]}')

    if failures:
        print('\nFAILURES:')
        for f in failures:
            print('  ' + f)
        sys.exit(1)
    print(f'\nOK: {len(DATASETS) * len(TREES)} external-persona DBs ready')


def main():
    actions = sys.argv[1:] or ['all']
    if 'extract' in actions or 'all' in actions:
        print('== extract thinkpersona ==')
        tp = build_thinkpersona_personas()
        with open(THINKPERSONA_OUT, 'w', encoding='utf-8') as f:
            json.dump(tp, f, ensure_ascii=False, indent=1)
        print(f'  wrote {len(tp)} personas -> {os.path.relpath(THINKPERSONA_OUT, ROOT)}')

        print('== extract real-persona-chat (Japanese -> English) ==')
        rpc = build_rpc_personas()
        with open(RPC_OUT, 'w', encoding='utf-8') as f:
            json.dump(rpc, f, ensure_ascii=False, indent=1)
        print(f'  wrote {len(rpc)} personas -> {os.path.relpath(RPC_OUT, ROOT)}')

    if 'build' in actions or 'all' in actions:
        print('== build DBs ==')
        build()

    if 'verify' in actions or 'all' in actions:
        print('== verify ==')
        verify()


if __name__ == '__main__':
    main()
