# PVQ instrument assets (ESS PVQ-21)

Fetched verbatim on 2026-09-25 from
[holi-lab/Human-Psychometric-Questionnaires-Mischaracterize-LLM-Behavior](https://github.com/holi-lab/Human-Psychometric-Questionnaires-Mischaracterize-LLM-Behavior)
(`surveys/PVQ.json`, `prompts/PVQ.txt`, `LICENSE`).

| File | Contents |
|---|---|
| `PVQ21.json` | **The administered instrument.** 21 items keyed `"1".."21"` in ESS order. Each has `en_male` / `en_female` / `en_neutral` wordings plus `meta_data: {value, higher_order_value}`. |
| `PVQ.json` | The upstream PVQ-40 release, verbatim — kept as the reference bank `PVQ21.json` was drawn from. Not administered. |
| `PVQ.txt` | Upstream single-sheet prompt (reference only — see the adaptation note below). |
| `UPSTREAM-LICENSE` | The upstream repository's MIT license (covers the code and this release). |

## The instrument is PVQ-21, not PVQ-40

The experiment administers the 21-item ESS short form, so that the simulated and human curves come
from the *same* instrument rather than from a subset relation. `PVQ21.json` is `PVQ.json` reordered
to ESS item order and truncated to the 21 ESS items.

The ESS publishes no table mapping its numbering onto the 40, so the correspondence was
reconstructed by matching ESS item wording against `PVQ.json`, then validated by the result
reproducing the documented ESS structure exactly (21 distinct items, 2 per value, 3 for
Universalism, all four higher-order values covered). In ESS order the items are these PVQ-40 items:

    1 2 3 4 5 6 7 8 38 26 11 12 13 14 15 16 17 18 19 20 10

ESS 1–8 and 11–20 are verbatim PVQ-40 1–8 and 11–20; ESS 9 is PVQ-40 38, the "humble and modest"
item ESS reworded; ESS 10 and ESS 21 are the two Hedonism items, PVQ-40 26 and 10. The one slot
wording alone cannot settle is ESS 10, PVQ-40 **26 vs 37** — both Hedonism, one item of 21, so no
value score moves materially.

## Keying

Ten primary values, 2 items each except Universalism (3) — 21 total. Four higher-order values:
Conservation 6, Openness to change 6, Self-Transcendence 5, Self-Enhancement 4.

Scale: 6-point, "Not like me at all" (1) … "Very much like me" (6). **No reverse-scored items.**

Scoring (ESS PVQ instructions): each item is scored 1–6, the mean over all 21 items is subtracted
from every item, and each value score is the mean of its centred items. Each higher-order value is
the mean of its constituent primary values.

## Local adaptations

- Only the `en_neutral` wording is used. The repo builds one shared sheet text per quiz sheet, so
  per-persona sex-matched wording is not expressible; `en_neutral` is the correct neutral choice.
- This repo's `answer_extractor` parses an option **number**, so the `pvq_21` prompt group in
  `prompts/experiment.json` asks for `1..6` rather than the upstream prompt's phrase answer. The
  response options in the `question` table are the six numbered scale points.

## Licensing

The upstream release is MIT (`UPSTREAM-LICENSE`). The PVQ item wordings originate with Shalom H.
Schwartz's Portrait Values Questionnaire and remain the copyright of their authors; they are
redistributed here under the upstream release's terms for research use. Cite the upstream paper and
Schwartz's PVQ when publishing results derived from these items.
