# MFQ-30 human microdata (the human baseline)

The human reference for the morality curves. `tools/importers/import_mfq_human.py` downloads the
deposit on first run and builds `data/db/morality/backup/human.db` plus
`data/cross_section/age_mean_MFQ.csv` from it.

## Source

The **"D and Moral Foundations"** deposit on OSF, node [`37eht`](https://osf.io/37eht/) (public,
created 2025-11-05), file `dataset/d_mft_analysis_addmods.csv` (23.9 MB):

- Download: `https://osf.io/download/6a1fd980487f4335837df50c/`
- N = 101,433 respondents; 99,575 with a parseable age (18–89, median 22)
- myPersonality-derived online volunteer sample
- **No licence declared** (`node_license: null`)

| File | Committed | Contents |
|---|---|---|
| `d_mft_analysis_addmods.csv` | no (gitignored, 23.9 MB) | one row per respondent; demographics + the 32 raw MFQ columns + the depositors' D-scale items and country covariates |

The deposit also ships `dataset/d-mfq-mp.dat` (the myPersonality source, no header) and
`dataset/by_country/d_mft_c{1..32}.inp` (Mplus inputs naming the item key per country). The
importer needs only the CSV; the `.inp` files were used to verify the item map.

## Item order

The deposit's 32 columns (`MFQ_1`…`MFQ_32`) number the *upstream interleaved* instrument, which
rotates foundations (harm, fair, ingroup, respect, purity, harm, …) and inserts the MATH/GOOD
catch items at positions 6 and 22. Our `data/MFQ/MFQ30.json` is **part-major** — ids `1–15` are
the relevance block, `16–30` the agreement block, with a care/fairness/loyalty/authority/sanctity
block order inside each — so the two numberings do not line up and a positional zip would
silently scramble the items. `MFQ_6` and `MFQ_22` (MATH/GOOD) have no counterpart and are
dropped. The map is verified three ways:

1. the Mplus factor loadings in `dataset/by_country/d_mft_c*.inp` — e.g.
   `harm BY mfq1 mfq7 mfq12 mfq17 mfq23 mfq28`, with `USEVARIABLES` listing everything except
   mfq6 and mfq22, which is what proves those two are the catch items;
2. the July-2008 printed MFQ-30 item key;
3. a text-by-text match against `data/MFQ/MFQ30.json` — a 30/30 bijection.

```
mfq1→1  mfq2→4  mfq3→7  mfq4→10 mfq5→13 [mfq6 DROP] mfq7→2  mfq8→5  mfq9→8
mfq10→11 mfq11→14 mfq12→3 mfq13→6 mfq14→9 mfq15→12 mfq16→15 mfq17→16 mfq18→19
mfq19→22 mfq20→25 mfq21→28 [mfq22 DROP] mfq23→17 mfq24→20 mfq25→23 mfq26→26
mfq27→29 mfq28→18 mfq29→21 mfq30→24 mfq31→27 mfq32→30
```

## Scale

**The deposit codes every item 1–6; our instrument is 0–5.** The importer shifts with
`ours = theirs - 1` *before* scoring. MFQ scores are raw foundation means with no within-person
centring, so unlike the ESS/PVQ case there is no reversal sitting under a centring and the shift
is a pure level translation.

## Scoring

Identical to `asociety/morality/mfq.py`: each of the 30 items scored 0–5, each foundation the raw
mean of its six items, each higher-order cluster the mean of its constituent foundations. No
centring.

## Selection and weighting

Respondents are kept only if all 30 items are answered `1..6`, sex is coded `0/1`, and age is in
`16..110`. Rows are **not** weighted; `human.db` is read as a set of individual
(age, moral-vector) rows and the panels average them per age band.

## Caveats

- **No licence is declared on the OSF node.** These data are used locally for research; they are
  not redistributed (the CSV is gitignored). Citation of the deposit is required if results
  derived from them are published, and redistribution rights would need to be cleared with the
  depositor first.
- **Young-skewed.** The sample is an online volunteer pool; the bands above 60 are thin (60s =
  1,758, 70+ = 377) versus the 20s (49,989). The age trend above 60 is correspondingly noisy.
- **`sex` direction unverified.** The deposit codes sex `0/1` and ships no codebook. The importer
  assumes `1 → Male`, `0 → Female`. This is not load-bearing for the age curves, which read
  `dimension='age'`, `sex_filter='All'`.
