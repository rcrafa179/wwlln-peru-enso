# Lightning activity over Peru and its relationship with ENSO

*Léelo en [español](README.es.md).*

Analysis of 41.2 million lightning strokes detected by the **World Wide Lightning
Location Network (WWLLN)** over Peru between 2021 and 2025, and their relationship
with eastern Pacific variability.

**Rafael Ruales** · WWLLN data 2021–2025 · Last updated: July 2026

---

## 1. What this repository contains

A complete, reproducible pipeline running from the raw WWLLN `.mat` files to the
final result, by way of quality control, climatological analysis, mapping, and the
cross-comparison against ocean indices.

The main result is that **the response of lightning activity to ENSO reverses sign
between the Peruvian coast and Amazonia**, and that this is why a country-wide
average comes out at zero: the two signals cancel.

The secondary result, independent of ENSO, is that **2025 was an anomalously low
year** (−29% relative to the 2021–2024 mean), and that this deficit is not an
artefact of the detection network.

Related documents:

| Document | Purpose |
|---|---|
| `README.md` (this one) | Overview, methodological decisions, results |
| `README.es.md` | The same document, in Spanish |
| `README_procesamiento_WWLLN.md` | Operations manual: how to run each script (Spanish) |
| `REGIONES_LEEME.md` | Regionalisation method, in detail (Spanish) |
| `GUIA_PRESENTACION.md` | Which figure to use, how to read it, what not to claim (Spanish) |
| `analisis_ENSO/DIAGNOSTICO_anomalia_neutral.md` | Why the first result was misleading (Spanish) |

---

## 2. The question

Peru holds three sharply distinct climatic domains separated by a 6,000 m
orographic barrier, and it sits directly opposite the ocean region where coastal
El Niño develops. The natural question is whether lightning activity responds to
eastern Pacific variability, and whether it responds the same way in all three
regions.

Stated operationally:

> Is there a detectable relationship, at monthly scale, between sea surface
> temperature off Peru and lightning activity over the territory? Is it the same
> on the coast, in the Andes and in Amazonia?

---

## 3. Data

### 3.1 WWLLN

WWLLN is a global network of ~70 stations that locates strokes by triangulating
the time of arrival of VLF waves. Each event carries a date and time accurate to
microseconds, latitude, longitude, radiated energy, fit residual, and the number
of stations that detected it.

| | |
|---|---|
| Period | 2021-01-01 to 2025-12-31 |
| Domain | 19°S–1°N, 82°W–68°W (3.40 million km²) |
| Events in the domain | **41,165,104** |
| Events inside Peru | **20,881,167** |
| Temporal coverage | 1,821 of 1,826 days (99.7%) |
| Original format | `.mat` (MATLAB), ~67 GB |

**Important note on the domain:** the box is **2.6 times** continental Peru and
includes Ecuador, Colombia, Brazil, Bolivia and open Pacific. Climatological
analyses are performed over the box; regional analyses only over Peruvian
territory.

**On detection efficiency:** WWLLN detects on the order of 10–30% of
cloud-to-ground strokes, with an efficiency that varies in space and time
according to network geometry and the number of active stations. For this reason
**the entire analysis is carried out on standardised anomalies against the
climatology of the same calendar month**, never on absolute counts, and this is
why the 2025 deficit was validated against the global count (section 6.2).

### 3.2 Ocean indices

- **Niño 1+2** (0–10°S, 90–80°W), OISSTv2.1 with 1991–2020 base period, from
  CPC/NOAA. Primary index.
- **ONI** (Niño 3.4), from CPC/NOAA. Used for comparison only.

---

## 4. Pipeline

```
raw .mat (67 GB)
   │  Leer_WWLLN_recursivo.py       parallel reading, filter to domain
   ▼
peru_wwlln_YYYY.parquet
   │  duplicados_parquet.py         diagnostics
   │  limpiar_parquet.py            deduplication
   ▼
peru_wwlln_YYYY_limpio.parquet
   │  analisis_anual_wwlln.py       monthly/daily/hourly series + energy
   ├─────────────────────────────►  analisis_YYYY/
   │  mapa_densidad_wwlln.py        annual and monthly spatial density
   ├─────────────────────────────►  mapas_YYYY/, mapas_mensuales_YYYY/
   │  construir_serie_mensual.py    joins the five years
   ▼
wwlln_2021_2025_mensual.csv                descargar_oni.py ──► ENSO index
   │                                                │
   │  regionalizar_peru.py                          │
   ▼                                                │
analisis_regiones/  (one series per region)         │
   │                                                │
   └──────────────►  oni+wwlln.py  ◄────────────────┘
                          │  anomalies, correlations, effective n, lags
                          ▼
                  graficar_enso.py / graficar_regiones.py / figuras_presentacion.py
```

---

## 5. Methodological decisions

This is the section that matters. Every decision here changed the result.

### 5.1 Use only `.mat`, never mix with `.loc`

WWLLN distributes the same event in three formats (`A*.loc`, `AE*.loc`,
`AE*.mat`). Reading them together counts each stroke two or three times, and
deduplicating by lat/lon **does not catch it**, because the text and binary
formats store coordinates at slightly different decimal precision.

Effect: 2025 went from 6.21 M to 9.31 M events (+50%).

**Why this matters more than it appears:** with the inflated counts, 2025 looked
like the *highest* year in the series. The real result is that it is the lowest,
and that deficit is one of the two findings of this work. The error inverted the
conclusion.

It was caught by comparing 2025 against the other four years: it was the only
inconsistent one. The affected files are kept in quarantine outside the
repository (`_obsoleto_2025/`, local), with the details in its LEEME.

### 5.2 Normalise incomplete months

Five months in the series have missing days (between 29 and 30 out of 30–31). The
count is extrapolated to a full month:

```
n_strokes_norm = n_strokes / days_with_data × days_in_month
```

Without this, a month missing two days looks 6% less active than it was, and that
6% is the same order as the anomalies being measured.

### 5.3 Standardised anomaly, not percentage

The first analysis used percentage anomalies and gave an absurd result: the
Neutral phase appeared to be the most deficient, below both La Niña and El Niño.

The problem is that percentage anomalies average percentages computed over very
different bases. July climatology is ~73,000 strokes; February's, ~1,244,000:
**17 times more**. The same absolute fluctuation produces an enormous percentage
in a dry month and a small one in a wet month:

| Year | Month | Absolute anomaly | Anomaly % |
|---|---|---|---|
| 2024 | Feb | **+416,541** strokes | +30.5% |
| 2022 | Jul | +88,529 strokes | **+121.0%** |

July 2022 contributes a fifth of the strokes of February 2024 and quadruples its
percentage.

**Solution:** standardised anomaly z against the climatology of the same calendar
month. A **log z** is also reported, because stroke counts are multiplicative and
the logarithm stabilises the variance between dry and wet seasons.

The full diagnosis is in `analisis_ENSO/DIAGNOSTICO_anomalia_neutral.md`.

### 5.4 Niño 1+2, not the ONI

The ONI measures Niño 3.4, in the central Pacific. The Peruvian **coastal El
Niño** — the one that governs convection and rainfall on the northern coast — is
seen in Niño 1+2, and can occur without the ONI moving at all (2017 is the
textbook case).

Over these 60 months the two indices correlate at **r = 0.70** and disagree on
phase in **23 of 60 months**. Niño 1+2 dates the 2023 event from February; the
ONI, only from mid-year.

The switch also **removes a structural bias**: under the ONI the Neutral phase
was loaded with dry months (58%, against 25% for La Niña), because the ONI crosses
zero during boreal spring. With Niño 1+2 the seasonal mix is even (39 / 47 / 42%)
and reweighting no longer moves the result.

**Thresholds:** those of the **ICEN** convention from ENFEN/IGP (cold ≤ −1.0 °C,
warm ≥ +0.4 °C), which are asymmetric. Niño 1+2 has far greater variance than
Niño 3.4; applying the ONI's ±0.5 °C would classify nearly half of neutral months
as events.

### 5.5 Regionalisation by elevation, with an envelope rule

The Andes cross Peru diagonally: the axis is at −79° at the latitude of Piura and
at −70° at Tacna. Cutting by meridians would put highlands in the coast in the
north and rainforest in the highlands in the south.

**Method:** for each latitude a west–east elevation profile is taken (ETOPO1) and
the **westernmost** and **easternmost** longitudes with elevation ≥ 1000 m are
located. That defines the envelope of high terrain.

**Why the envelope and not the first threshold crossing.** Real profile at 13°S:

| Longitude | −76.0 | −75.5 | −75.0 | −74.5 | −74.0 | **−73.5** | −73.0 | −72.5 | −72.0 | **−71.5** |
|---|---|---|---|---|---|---|---|---|---|---|
| Elevation (m) | 3049 | 4329 | 4680 | 3695 | 3335 | **774** | 3775 | 2126 | 3535 | **1251** |

That 774 is the Apurímac canyon, hemmed in between 3,300 m and 3,800 m massifs.
Under a "first descent" rule the cordillera would be split at −73.7° and a
3,775 m massif would be classified as Amazonia. With the envelope, the boundary
falls at −71.2°, which is the real Andean front.

Validation: the total polygon area gives 1,315,209 km² against 1,285,216 actual
(2.3% error). The split between regions is reported with sensitivity at 500, 1000
and 2000 m. Full detail in `REGIONES_LEEME.md`.

### 5.6 Effective degrees of freedom

The monthly lightning and SST series are strongly autocorrelated, so the 60
nominal months are not 60 independent observations. The **effective n of
Bretherton et al. (1999)** is reported:

```
n_eff = n · (1 − r₁ˣ·r₁ʸ) / (1 + r₁ˣ·r₁ʸ)
```

For the full domain this gives **28.7 of 60**. For the coast, **13.9**. All
p-values are computed with the effective n, not the nominal one.

Two further controls are added: **jackknife** leaving one year out at a time, and
**lagged correlations** from 0 to 6 months.

---

## 6. Results

### 6.1 Climatology (robust, assumption-free)

- **Annual cycle:** a **17×** contrast between July and February. Wet season from
  October to April.
- **Diurnal cycle:** maximum at **16:00** local, minimum at **09:00**, with a
  max/min ratio of 4.7 to 8.2. **Identical across all five years, without
  exception.** Continental afternoon convection. Five independent realisations
  collapsing onto the same curve.
- **Regional distribution** (within Peru, 2021–2025):

| Region | Strokes | % | Area (km²) | Strokes/km²/yr |
|---|---|---|---|---|
| Amazonia | 13,165,547 | 63.1% | 620,182 | **4.25** |
| Andes | 7,665,961 | 36.7% | 583,129 | **2.63** |
| Coast | 49,659 | **0.24%** | 111,898 | **0.09** |

The Peruvian coast is, electrically, a desert: **47 times lower density than
Amazonia**. Consistent with the thermal inversion of the Humboldt Current, which
suppresses deep convection for most of the year.

### 6.2 The 2025 deficit

2025 falls **−29%** relative to the 2021–2024 mean. The obvious question is
whether data were lost or the network degraded. Contrast against WWLLN's
**global** count (a ~60-day sample per year, worldwide):

| Year | Global/day | Peru/day | Peru per million global |
|---|---|---|---|
| 2023 | 722,092 | 24,833 | 34,390 |
| 2024 | 688,545 | 24,124 | 35,036 |
| **2025** | 650,054 | 16,635 | **25,589** |

The global count falls **−8%**; Peru's, **−32%**. Peru's share of the global total
falls **−26.3%**. If this were file loss or network degradation, both would fall
in the same proportion. They do not.

Detection quality in 2025 was moreover **equal or better**: 7.65 stations per
event against 7.24–7.44 in previous years, and a residual of 11.89 km against
12.0–12.2.

**Conclusion:** 2025 was genuinely a year of low lightning activity over Peru. The
cause remains an open question.

### 6.3 The main result: the signal that was cancelling

Without stratification, the cross-comparison with Niño 1+2 gives essentially zero
(r = −0.039, n_eff = 28.7). Stratifying:

| Region | Cold phase | Neutral | Warm phase | Pearson r | n_eff |
|---|---|---|---|---|---|
| **Coast** | −0.13 | −0.11 | **+0.46** | **+0.202** | 13.9 |
| Andes | +0.14 | −0.08 | +0.04 | −0.061 | 18.1 |
| **Amazonia** | **+0.51** | −0.20 | −0.09 | **−0.151** | 31.9 |

**The sign reverses from the coast to Amazonia**, with a monotonic west-to-east
gradient. Averaging the three regions gives ≈ 0: the signal was not absent, it was
cancelling.

It closes physically: during a coastal El Niño the warming of the sea off Peru
breaks the thermal inversion and triggers convection over a coast that normally
has none; in parallel, the warm phase is associated with subsidence and a rainfall
deficit over western Amazonia.

### 6.4 The 2023 case, where statistics are not needed

| April of | 2021 | 2022 | **2023** | 2024 | 2025 |
|---|---|---|---|---|---|
| Strokes on the coast | 181 | 222 | **21,793** | 195 | 1,071 |

A factor of **~100** against neighbouring years. Over the full year the coast goes
from ~4,300 strokes to **32,377** (7.5×), with March and April accounting for 84%.
This coincides with the 2023 coastal El Niño (Niño 1+2 from −0.11 in January to
+2.08 in April–June) and with cyclone Yaku in March 2023. In parallel, Amazonia
fell **−19.1%** relative to 2022.

---

## 7. Limitations

These limitations are not a formality: they genuinely bound what can be claimed.

1. **Five years are not enough.** There is **exactly one warm event** (2023) in the
   whole window. Leave-one-year-out jackknife moves the warm-phase mean by
   **1.47 z** — more than any of the differences being interpreted. Statistics on
   "the effect of coastal El Niño" cannot be done with a single event; at most the
   2023 case can be described.
2. **Nothing is statistically significant.** The effective n for the coast is 13.9
   of 60 months (p ≈ 0.49). The sign reversal is coherent and physically expected,
   but it is **hypothesis-generating**, not confirmatory.
3. **A year effect contaminates the phase comparison.** 2023 is nearly the entire
   warm phase; 2022, nearly all of the cold one; 2025 weighs on the neutral phase.
   Classification by phase is partly relabelling a year effect.
4. **The Coast and Andes boundaries are provisional.** Elevation sampling at 0.5°
   of longitude biases the western boundary seaward on steep slopes: the coast
   comes out at 8.5% of the area instead of the conventional ~12%. The
   Amazonia/rest partition is robust. Correctable with `muestrear_elevacion.py`.
5. **Detection efficiency is not explicitly corrected.** It is mitigated by working
   in anomalies and with the global control, but no efficiency model was applied.
6. **One day lost:** `AE20250908.mat` is corrupt at source (confirmed across three
   copies). 2025 covers 364 of 365 days.

---

## 8. Where this approach runs out

Limitation 1 is not incidental: it defines what kind of method the problem
actually requires.

Observations **characterise** the April 2023 event with high confidence: the
magnitude is a factor of ~100 above the local baseline, the timing matches the
evolution of Niño 1+2, the spatial pattern is confined to the region where the
physical mechanism applies, and quality controls rule out instrumental artefacts.

What observations **cannot** say is how likely that event was, or whether that
likelihood has changed. One event in five years — or two in fifteen — does not
support inference about occurrence probability, however carefully the record is
processed. Extending the window helps with sampling, but the underlying constraint
remains: the real climate delivers a single realisation.

This is precisely the gap filled by **large-ensemble event attribution**, and it is
the direction I would like to pursue.

**Proposed direction.** Use the 2017 and 2023 coastal El Niño events as target
events, with convective activity over the Peruvian coast as the variable of
interest, contrasting historical ensembles against non-warming counterfactuals
(d4PDF: 100 members, MRI-AGCM3.2, historical and *non-warming*).

**Why lightning is a favourable target variable.** On the Peruvian coast it
behaves as a near-binary indicator rather than the tail of a continuous
distribution: the April baseline is ~190 strokes and April 2023 recorded 21,793.
Attribution normally has to resolve a shifted tail; here the contrast is closer to
occurrence versus non-occurrence, which sharpens the probability ratio. Lightning
is also a more direct proxy for deep convective intensity than accumulated
precipitation, and it is far less explored as an attribution target.

**What would be required on my side.** Extending the WWLLN record backwards to
cover 2017. The pipeline already handles this: it is processing work along a
validated path, not new design. The regional stratification, the anomaly framework
and the index handling all transfer unchanged.

**An open methodological question.** Coastal El Niño *is* an SST anomaly, and the
d4PDF AGCM is SST-forced. That makes the framing non-trivial: whether the
well-posed question is the change in probability of the convective response
*conditional on* the observed SST anomaly, or of the anomaly itself, and how the
*non-warming* construction separates the two. I do not think the answer is obvious
from the literature.

**Steps independent of the above:**

1. Refine the region boundaries with dense elevation sampling
   (`muestrear_elevacion.py`, 2 minutes).
2. Model detection efficiency from the number of active stations per year.
3. External validation: GOES-16 GLM (2017+) or CHIRPS/SENAMHI precipitation.
4. Diurnal cycle by region: the 16:00 peak is a domain average, and the three
   regions probably differ in phase.

---

## 9. Reproducibility

The whole pipeline is run through parameters, without editing code. The operations
manual is in `README_procesamiento_WWLLN.md` (Spanish). Requirements:

```bash
pip install pandas numpy scipy pyarrow matplotlib cartopy shapely pyshp
```

Minimal example, from the `.mat` files to the result:

```bash
python3 Leer_WWLLN_recursivo.py "/path/to/2025/MATfiles" ./peru_wwlln_2025.parquet --workers 6
python3 limpiar_parquet.py
python3 analisis_anual_wwlln.py --entrada peru_wwlln_2025_FINAL.parquet --anio 2025 --salida analisis_2025
python3 construir_serie_mensual.py --base . --salida wwlln_2021_2025_mensual.csv
python3 descargar_oni.py --indice nino12 --desde 2021 --hasta 2025
python3 regionalizar_peru.py --umbral 1000 --salida analisis_regiones
python3 "oni+wwlln.py" --wwlln analisis_regiones/wwlln_2021_2025_mensual_costa.csv \
                       --indice nino12_2021_2025_tidy.csv --salida analisis_regiones/enso_costa
```

Every script validates its inputs. `mapa_densidad_wwlln.py`, for instance, aborts
if the parquet does not correspond to the requested year — a check added after
discovering that a copy of the script had been silently reading the wrong year.

Script names, command-line flags and figure labels are in Spanish.

---

## 10. Structure

```
├── README.md                        this document
├── README.es.md                     the same document, in Spanish
├── README_procesamiento_WWLLN.md    operations manual
├── REGIONES_LEEME.md                regionalisation method
├── GUIA_PRESENTACION.md             which figure to use and how to read it
│
├── Leer_WWLLN*.py                   reading .mat and filtering to the domain
├── limpiar_parquet.py               deduplication
├── analisis_anual_wwlln.py          per-year series
├── mapa_densidad_wwlln.py           density mapping
├── construir_serie_mensual.py       joins the five years
├── descargar_oni.py                 ENSO indices from CPC/NOAA
├── oni+wwlln.py                     cross-comparison, anomalies, effective n, lags
├── regionalizar_peru.py             stratification by elevation
├── muestrear_elevacion.py           dense elevation grid via API
├── graficar_*.py, figuras_presentacion.py
│
├── analisis_2021..2025/             monthly/daily/hourly series per year
├── mapas_2021..2025/                annual density map
├── mapas_mensuales_2021..2025/      twelve maps per year
├── analisis_ENSO/                   cross-comparison with ONI (reference)
├── analisis_ENSO_nino12/            cross-comparison with Niño 1+2 (primary)
├── analisis_regiones/               stratification and cross-comparison by region
├── figuras_presentacion/            final figures
└── recursos/                        cartography and elevation profiles
```

Excluded from the repository, by size or by publication criterion: the raw `.mat`
files, the intermediate `.parquet` files, and `_obsoleto_2025/` (what was
discarded, with its explanation).

---

## 11. Data and credits

**WWLLN.** The data come from the World Wide Lightning Location Network
(http://wwlln.net), a collaboration of more than 50 institutions. Use of these data
requires acknowledgement of the network and of the participating institutions;
check the terms with the institution that granted you access before publishing.

**Ocean indices.** NOAA/NWS Climate Prediction Center,
https://www.cpc.ncep.noaa.gov/data/indices/

**Elevation.** ETOPO1, NOAA/NCEI, queried through the public OpenTopoData API
(https://www.opentopodata.org).

**Cartography.** Natural Earth (public domain), via cartopy.

**ICEN thresholds.** ENFEN / Instituto Geofísico del Perú. The implementation here
is an ICEN-proxy computed on CPC data: the categories match, the decimals may
differ from the official ICEN.
