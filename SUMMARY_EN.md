# Lightning Activity over Peru and Its Relationship to ENSO

**WWLLN observations, 2021–2025**

Rafael Ruales · July 2026

---

## Motivation

Peru contains three sharply distinct climatic domains — a hyper-arid coastal
strip, the Andes, and western Amazonia — separated by a 6,000 m orographic
barrier, and it sits directly against the ocean region where coastal El Niño
develops. This makes it a natural place to ask whether lightning activity
responds to eastern Pacific variability, and whether it responds the same way
across the three domains.

This document reports what five years of observations can establish, and — more
importantly for what I would like to work on — where they stop being able to
answer the question at all. That boundary is the subject of the final section.

## Data

41,165,104 lightning strokes detected by the World Wide Lightning Location
Network (WWLLN) between 2021-01-01 and 2025-12-31 over 19°S–1°N, 82°W–68°W;
20,881,167 of them inside Peruvian territory. Temporal coverage is 1,821 of
1,826 days (99.7%). Source data are ~67 GB of raw MATLAB files.

Ocean indices are the Niño 1+2 SST anomaly (0–10°S, 90–80°W) and the ONI, both
from NOAA/CPC. Elevation is ETOPO1.

Because WWLLN detection efficiency is on the order of 10–30% for cloud-to-ground
strokes and varies in space and time, **the entire analysis is performed on
standardized anomalies relative to the same-calendar-month climatology**, never
on absolute counts.

---

## Three methodological decisions that changed the result

**1. Format-induced double counting.** WWLLN distributes the same stroke in
three formats. Reading them together counts each stroke two or three times, and
coordinate-based deduplication does not catch it, because the text and binary
formats store coordinates at slightly different decimal precision. The effect
inflated 2025 from 6.21 M to 9.31 M strokes (+50%) — and, critically, made 2025
appear to be the *highest* year in the series when it is in fact the lowest.
That inversion reversed one of the two main findings. The error was found by
cross-checking 2025 against the other four years, which were mutually
consistent.

**2. Percentage anomalies are not comparable across seasons.** An initial
analysis using percentage anomalies produced an implausible ordering, with the
ENSO-neutral phase appearing more deficient than either warm or cold. The cause
is that July climatology is ~73,000 strokes and February climatology is
~1,244,000 — a factor of 17. The same absolute fluctuation yields a large
percentage in a dry month and a small one in a wet month. All results were
recomputed as standardized anomalies (z) against same-month climatology, with a
log-transformed z reported alongside, since stroke counts are multiplicative.

**3. The ONI is the wrong index for Peru.** The ONI measures Niño 3.4 in the
central Pacific. Coastal El Niño, which governs convection along the Peruvian
coast, is captured by Niño 1+2 and can occur without any ONI signal. Over these
60 months the two indices correlate at r = 0.70 and disagree on phase in 23 of
60 months; Niño 1+2 dates the 2023 event from February, the ONI only from
mid-year. Switching indices also removed a structural bias: under the ONI, the
neutral phase was disproportionately loaded with dry months (58% vs 25% for the
cold phase), because the ONI crosses zero during boreal spring. Phase thresholds
follow the ICEN convention of Peru's ENFEN (cold ≤ −1.0 °C, warm ≥ +0.4 °C),
which is asymmetric — Niño 1+2 has far greater variance than Niño 3.4, so the
ONI's ±0.5 °C threshold does not transfer.

---

## Results

### Climatology (robust; assumption-free)

- **Annual cycle:** a factor of 17 between July and February; wet season October
  to April.
- **Diurnal cycle:** maximum at 16:00 local, minimum at 09:00, max/min ratio
  4.7–8.2. **Identical in all five years without exception** — five independent
  realizations collapsing onto the same curve. Consistent with continental
  afternoon convection.
- **Regional distribution** (within Peru): Amazonia 4.25 strokes km⁻² yr⁻¹,
  Andes 2.63, Coast 0.09. The Peruvian coast is electrically a desert — 47 times
  lower stroke density than Amazonia — consistent with the Humboldt inversion
  suppressing deep convection year-round.

### A genuine 2025 deficit

2025 is 29% below the 2021–2024 mean. Testing whether this reflects data loss or
network degradation, against WWLLN's **global** count (~60-day sample per year):
the global count falls 8%, Peru's falls 32%, and Peru's share of the global
total falls 26.3%. Detection quality in 2025 was equal or better (7.65 stations
per stroke vs 7.24–7.44; residual 11.89 km vs 12.0–12.2). The deficit is real;
its cause remains open.

### Main result: an ENSO signal that cancels in the domain mean

Without stratification, the correlation between Niño 1+2 and lightning anomaly
over Peru is essentially zero (r = −0.039, n_eff = 28.7). Stratifying by
elevation-derived region:

| Region | Cold phase | Neutral | Warm phase | Pearson r | n_eff |
|---|---|---|---|---|---|
| **Coast** | −0.13 | −0.11 | **+0.46** | **+0.202** | 13.9 |
| Andes | +0.14 | −0.08 | +0.04 | −0.061 | 18.1 |
| **Amazonia** | **+0.51** | −0.20 | −0.09 | **−0.151** | 31.9 |

**The sign reverses from coast to Amazonia**, with a monotonic west-to-east
gradient. Averaging the three yields ≈ 0. The signal was not absent; it was
cancelling.

This is physically consistent: during a coastal El Niño, warm SST off Peru
breaks the thermal inversion and triggers convection over a coast that normally
has none, while the same warm phase is associated with subsidence over western
Amazonia.

Regions were derived from elevation rather than longitude bands, since the Andes
cross Peru diagonally (axis at −79° at Piura, −70° at Tacna). Boundaries use the
**envelope** of terrain above 1000 m rather than the first threshold crossing: at
13°S the Apurímac canyon drops to 774 m between 3,300 m and 3,800 m massifs, and
a naive rule would split the cordillera and misclassify a 3,775 m massif as
lowland. Total area recovered is within 2.3% of Peru's true land area.

### The 2023 case, where statistics are not needed

| April of | 2021 | 2022 | **2023** | 2024 | 2025 |
|---|---|---|---|---|---|
| Coastal strokes | 181 | 222 | **21,793** | 195 | 1,071 |

A factor of ~100 against neighbouring years. Over the full year the coast goes
from ~4,300 to 32,377 strokes, with March–April accounting for 84%. This
coincides with the 2023 coastal El Niño (Niño 1+2 from −0.11 in January to +2.08
in April–June) and with cyclone Yaku in March 2023. Amazonia fell 19.1% relative
to 2022 over the same period.

---

## Limitations

These are binding, not formal.

1. **Five years is not enough.** There is exactly **one warm event** (2023) in
   the window. Leave-one-year-out jackknife moves the warm-phase mean by 1.47 z
   — larger than any of the differences being interpreted.
2. **Nothing here is statistically significant.** Effective sample size for the
   coast is 13.9 of 60 nominal months (p ≈ 0.49). The sign reversal is coherent
   and physically expected, but it is **hypothesis-generating, not
   confirmatory**.
3. **Year effects contaminate the phase comparison.** 2023 is nearly the entire
   warm phase, 2022 the cold phase, and 2025 weights the neutral phase.
4. **Coast/Andes boundaries are provisional** — 0.5° longitude sampling of
   elevation biases the western boundary seaward on steep slopes. The
   Amazonia/rest partition is robust.
5. **Detection efficiency is mitigated, not modelled.**

---

## Where this runs out, and why that is the interesting part

The limitation above is not incidental — it is structural, and it defines what
kind of method the problem actually needs.

Observations can **characterize** the April 2023 coastal event with high
confidence: the magnitude is a factor of ~100 above the local baseline, the
timing matches the Niño 1+2 evolution, the spatial pattern is confined to the
region where the physical mechanism applies, and the data quality controls rule
out instrumental artifacts. What observations cannot do is say **how likely** it
was, or whether that likelihood has changed. One event in a five-year record —
or two in a fifteen-year record — does not support inference about occurrence
probability, no matter how carefully the record is processed. Extending the
observational window helps with sampling, but the fundamental constraint
remains: the real climate provides one realization.

This is precisely the gap that large-ensemble event attribution fills, and it is
the direction I would like to pursue.

**Proposed direction.** Use coastal El Niño events (2017 and 2023) as attribution
targets, with convective activity over the Peruvian coast as the target
variable, contrasting historical and non-warming counterfactual ensembles.

Lightning is an unusually favourable target variable for this. On the Peruvian
coast it behaves as a near-binary indicator rather than the tail of a continuous
distribution: the April baseline is ~190 strokes, and April 2023 recorded
21,793. Attribution estimates normally have to resolve a shifted tail; here the
contrast is closer to occurrence versus non-occurrence, which sharpens the
probability ratio. Lightning is also a more direct proxy for deep convective
intensity than accumulated precipitation, and it is far less explored as an
attribution target.

**What this would require from my side.** Extending the WWLLN record back to
cover 2017. The pipeline already handles this — it is processing work along an
existing, validated path, not new design. The regional stratification, the
anomaly framework and the index handling all transfer unchanged.

**An open methodological question I would want to discuss.** Coastal El Niño is
itself an SST anomaly, and d4PDF's AGCM is SST-forced. That makes the framing of
the attribution question non-trivial: whether the well-posed question is the
change in probability of the convective response *conditional on* the observed
SST anomaly, or of the anomaly itself, and how the non-warming construction
handles that separation. I do not think the answer is obvious from the
literature, and it is the kind of question I would rather work through with
someone than guess at.

**Other next steps**, independent of the above: refine regional boundaries with
dense elevation sampling; model detection efficiency from active station counts;
validate externally against GOES-16 GLM or CHIRPS precipitation; and resolve the
diurnal cycle by region, since the 16:00 peak is a domain average and the three
regions likely differ in phase.

---

## Reproducibility

The full pipeline runs from raw `.mat` files to final figures, parameterized end
to end with no code editing. Each stage validates its inputs — the mapping script
aborts if the input file does not match the requested year, a check added after
discovering that a copy of the script had been silently reading the wrong year.
Discarded intermediate products are retained with written justification rather
than deleted.

Documentation: `README.md` (methodology and results), `REGIONES_LEEME.md`
(regionalization), `README_procesamiento_WWLLN.md` (operations manual),
`analisis_ENSO/DIAGNOSTICO_anomalia_neutral.md` (diagnosis of the initial
misleading result).

**Data:** World Wide Lightning Location Network (wwlln.net); NOAA/CPC ocean
indices; NOAA/NCEI ETOPO1 elevation.
