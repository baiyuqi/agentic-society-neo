# ESS PVQ-21 microdata (the human baseline)

The human reference for the value curves. `tools/importers/import_ess_human.py` downloads the
bulk files on first run and builds `data/db/value/backup/human.db` plus
`data/cross_section/age_mean_ESS.csv` from them.

## Source

ESS Round 11 (fieldwork 2023), four countries — Portugal, Spain, France, United Kingdom —
released as the teaching/analysis dataset **ESS11_4countries_values**:

- DOI: [10.5281/zenodo.18401503](https://doi.org/10.5281/zenodo.18401503)
- Authors: Madalena Ramos, Pedro Abrantes, Alice Ramos
- Licence: CC BY 4.0
- 6,672 respondents

| File | Committed | Contents |
|---|---|---|
| `ESS11_4countries_values.csv` | no (gitignored, 5.8 MB) | one row per respondent; demographics + the 21 raw items + the depositors' own scored columns |
| `sintax_values.sps` | yes | the depositors' SPSS scoring syntax — the reference for the keying and the centring rule |
| `ESS11_4countries_values.sav` | no | the SPSS twin of the CSV; `import_ess_human.py` does not need it |

The official ESS route (`https://ess.sikt.no/…`) validates a registered `userId` even for
"anonymous-research" access, so this open CC BY 4.0 release is used instead. It carries the same
21 ESS items; the difference is coverage — four countries rather than the full European sample,
so per-band n is smaller (roughly 300–1,150 per band) and the bands above 80 are thin.

## Item order

The CSV's 21 item variables are in ESS questionnaire order, which is exactly the order of
`data/PVQ/PVQ21.json` ids `1..21`:

```
 1 ipcrtiv   2 imprich   3 ipeqopt   4 ipshabt   5 impsafe   6 impdiff   7 ipfrule
 8 ipudrst   9 ipmodst  10 ipgdtim  11 impfree  12 iphlppl  13 ipsuces  14 ipstrgv
15 ipadvnt  16 ipbhprp  17 iprspot  18 iplylfr  19 impenv   20 imptrad  21 impfun
```

`sintax_values.sps` keys these to the same values `PVQ21.json` carries, item for item, so the
import needs no mapping — only the position.

## Scale direction

**The ESS response scale runs opposite to our instrument.** The ESS questionnaire prints
1 = "Very much like me" … 6 = "Not like me at all", whereas `PVQ21.json` and the administered
prompt use 1 = "Not like me at all" … 6 = "Very much like me". The importer therefore reverses
every ESS code with `ours = 7 - ess` *before* scoring. `sintax_values.sps` does the same thing
with `RECODE (1=6) (2=5) … (6=1)`, so after the reversal both scorings are identical: the CSV's
own `sdms … OCms` centred columns can be compared directly against our recomputed scores as a
check.

## Scoring

Identical to `sintax_values.sps` and to `asociety/value/pvq.py`: each of the 21 items scored
1–6, the respondent's mean over all 21 subtracted from each item, and each value the mean of its
centred items; each higher-order value the mean of its constituent values.

## Selection and weighting

Respondents are kept only if all 21 items are answered `1..6`, sex is coded, and age is in
`16..110` — 6,088 of 6,672 rows. Rows are **not** weighted: `human.db` is read as a set of
individual (age, value-vector) rows and the panels average them per age band, so the ESS
`pspwght`/`dweight` would have to be applied as replication to matter. `age_mean_BHPS.csv` /
`age_mean_GSOEP.csv` on the personality side are likewise unweighted, so the two baselines are
treated alike.

## Licensing

CC BY 4.0. Cite Ramos, Abrantes & Ramos (2024) and the ESS when publishing results derived from
these data. The item wordings originate with Shalom H. Schwartz's Portrait Values Questionnaire
and remain the copyright of their authors.
