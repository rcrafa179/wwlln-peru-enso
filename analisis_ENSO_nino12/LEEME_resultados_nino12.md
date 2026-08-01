# WWLLN × Niño 1+2 — Perú 2021-2025

Cruce de la actividad eléctrica sobre Perú con el índice **Niño 1+2**, la región
oceánica (0-10°S, 90-80°W) que está frente a la costa peruana. Reemplaza al
cruce con ONI (Niño 3.4) del análisis anterior, que está en `../analisis_ENSO/`.

---

## 0. Aviso sobre qué versión del índice se usó

Estos resultados salieron con la variante **relativa** del Niño 1+2
(`--indice rnino12`): OISSTv2.1, base 1991-2020, a la que el CPC le resta la
TSM media de los trópicos. Se usó esa porque es el archivo del CPC que se pudo
descargar desde el entorno donde se corrió el análisis.

La versión cruda (ERSSTv5, la que sirve de base al ICEN del ENFEN) está
implementada y se baja con:

```bash
python3 descargar_oni.py --indice nino12 --desde 2021 --hasta 2025
python3 "oni+wwlln.py" --wwlln wwlln_2021_2025_mensual.csv \
                       --indice nino12_2021_2025_tidy.csv \
                       --nombre-indice "Nino 1+2" \
                       --salida ./analisis_ENSO_nino12_crudo
```

Las dos versiones se diferencian sobre todo por la tendencia de calentamiento
global (que la relativa quita); la forma interanual de la serie es casi la
misma, así que **no espero que las conclusiones cambien**, pero conviene
correrlo y confirmar antes de presentar. Si algo se mueve, serán las cuentas de
meses por fase, no las correlaciones.

---

## 1. Cómo se construyó

1. Serie mensual de rayos 2021-2025 (`wwlln_2021_2025_mensual.csv`),
   normalizada a mes completo. Los 60 meses entran; ninguno se descarta por
   cobertura.
2. Niño 1+2 mensual del CPC → **media móvil de 3 meses centrada**, asignada al
   mes central (DJF→enero, ..., NDJ→diciembre). Misma convención que el ONI, así
   que el join es directo por (año, mes).
3. Clasificación de fase con los **umbrales del ICEN** (ENFEN/IGP), que son
   asimétricos porque Niño 1+2 tiene mucha más varianza que Niño 3.4:

   | | umbral |
   |---|---|
   | Fría (La Niña costera) | ≤ −1.0 °C |
   | Neutral | −1.0 a +0.4 |
   | Cálida (El Niño costero) | ≥ +0.4 °C |

   Aplicar el ±0.5 del ONI a Niño 1+2 habría sido un error: clasificaría como
   evento casi la mitad de los meses neutrales.
4. Anomalía estandarizada z contra la climatología del **mismo mes calendario**.
   Sin ese paso la comparación entre fases estaría midiendo el ciclo estacional.

---

## 2. Lo que cambia respecto al ONI

**El índice sí es distinto.** Correlación ONI vs Niño 1+2 en estos 60 meses:
**r = +0.696**. Coinciden en fase solo **37 de 60 meses**:

| Niño 1+2 ↓ / ONI → | El Niño | La Niña | Neutral |
|---|---|---|---|
| **El Niño** | 8 | 0 | 4 |
| **La Niña** | 0 | 12 | 3 |
| **Neutral** | 4 | 12 | 17 |

El caso más claro: para el ONI, 2023 empieza en La Niña y solo entra en El Niño
a mitad de año. Para Niño 1+2, **el Niño costero arranca en febrero de 2023** —
que es cuando efectivamente ocurrió (el ciclón Yaku fue en marzo de 2023). El
índice correcto para Perú captura el evento tres o cuatro meses antes.

**Se arregla el sesgo estacional.** Este era uno de los tres problemas del
diagnóstico anterior: con ONI la fase Neutral quedaba cargada de meses secos
(58% seca) frente a La Niña (25%), lo que inflaba artificialmente los
porcentajes. Con Niño 1+2 la mezcla queda pareja:

| Fase | % meses secos — ONI | % meses secos — Niño 1+2 |
|---|---|---|
| La Niña | 25.0% | 46.7% |
| El Niño | 41.7% | 41.7% |
| Neutral | **58.3%** | **39.4%** |

Y en consecuencia la reponderación estacional ya no mueve nada
(La Niña +0.410 → +0.428; Neutral −0.215 → −0.213). **Ese confundidor se cayó.**

---

## 3. Resultados

**Meses por fase:** El Niño costero 12 · La Niña costera 15 · Neutral 33

**Anomalía media de rayos por fase:**

| Fase | n meses | z medio | z log medio | anomalía % media |
|---|---|---|---|---|
| **La Niña costera** | 15 | **+0.410** | +0.410 | +11.9% |
| El Niño costero | 12 | +0.080 | +0.084 | +4.6% |
| Neutral | 33 | −0.215 | −0.217 | −7.1% |

**Correlaciones:**

- Pearson r = **−0.039** (n = 60)
- Spearman ρ = −0.175
- r con z logarítmico = −0.039
- n efectivo (Bretherton) = **28.7** de 60 nominales
- p aproximado con n efectivo = 0.84
- Solo temporada lluviosa (oct-abr): r = −0.004 (n = 35)
- Solo temporada seca (may-set): r = −0.075 (n = 25)
- Kruskal-Wallis entre las tres fases: H = 5.06, **p = 0.080** (nominal)

**Con rezago** (el índice adelanta a los rayos): r va de −0.04 en lag 0 a −0.19
en lag 5. Perfil plano, ningún rezago se despega del ruido (con n efectivo ≈ 25,
|r| tendría que pasar de ~0.39 para ser distinguible de cero).

---

## 4. Cómo leer esto (importante)

El orden por fase cambió respecto al ONI: ahora **La Niña costera es la fase con
más rayos**, no El Niño. Y el Kruskal-Wallis bajó de p = 0.52 (ONI) a p = 0.080.
Es tentador leerlo como "aparece una señal al usar el índice correcto".

**No lo presentes así.** El diagnóstico dice otra cosa.

### 4.1 Cada fase es, básicamente, un año

| Año | z medio | El Niño | La Niña | Neutral |
|---|---|---|---|---|
| 2021 | +0.077 | 0 | 2 | 10 |
| 2022 | +0.550 | 0 | **10** | 2 |
| 2023 | +0.218 | **11** | 0 | 1 |
| 2024 | +0.107 | 0 | 3 | 9 |
| 2025 | **−0.951** | 1 | 0 | **11** |

El Niño costero = 2023. La Niña costera = 2022 (el año con más rayos de la
serie). Neutral = 2021 + 2024 + 2025 (y 2025 es el año más bajo). La
clasificación por fase está reetiquetando el efecto de año.

### 4.2 El jackknife lo confirma

Dejando un año fuera cada vez, la media por fase se mueve:

| Fase | rango de z medio | amplitud |
|---|---|---|
| El Niño | −1.269 a +0.203 | **1.47 z** |
| Neutral | −0.382 a +0.138 | 0.52 z |
| La Niña | +0.176 a +0.576 | 0.40 z |

Quitando 2023, El Niño costero pasa de +0.08 a **−1.27**. Quitando 2025, Neutral
pasa de −0.22 a +0.14. Las diferencias entre fases que estás comparando (~0.6 z)
son **más chicas que lo que se mueve el resultado al quitar un solo año**.

### 4.3 Y sigue habiendo un solo evento

Bloques contiguos en los 60 meses: **2 de El Niño** (uno de 11 meses seguidos y
otro de 1), 3 de La Niña, 6 Neutral. Con un único evento cálido no hay
estadística que hacer sobre "el efecto de El Niño costero"; a lo sumo se puede
describir el caso 2023.

Esto se ve también en el n efectivo: 28.7 de 60. La mitad de los meses no aporta
información independiente.

---

## 5. Qué sí se puede decir en la presentación

1. **Niño 1+2 es el índice correcto para Perú y no es intercambiable con el
   ONI.** r = 0.70 entre ellos, difieren en 23 de 60 meses, y fechan el evento
   2023 con meses de diferencia. Esto justifica el cambio metodológico por sí
   solo.
2. **Cambiar de índice eliminó el sesgo estacional** que contaminaba la
   comparación por fases con ONI. Es una mejora real y demostrable.
3. **Aun con el índice correcto, 5 años no alcanzan.** El efecto de año domina
   sobre el efecto de fase, hay un solo evento cálido, y el n efectivo es la
   mitad del nominal. Presentar esto como resultado negativo bien diagnosticado
   es más sólido que forzar una conclusión con p = 0.08.
4. **El déficit de 2025 sigue siendo el hallazgo fuerte** y es independiente de
   ENSO: −32% en Perú contra −7.8% global, con calidad de detección igual o
   mejor. Ver `../analisis_ENSO/DIAGNOSTICO_anomalia_neutral.md`.

---

## 6. Siguiente paso, en orden de retorno

1. **Extender a 2010-2025.** Es lo único que resuelve el problema de fondo. En
   ese periodo hay Niño costero 2017 (moderado), El Niño 2015-16, Niña 2010-11,
   2020-22 — varios eventos de cada signo. `descargar_oni.py` ya acepta
   `--desde 2010`; lo que falta es procesar los `.mat` de 2010-2020.
2. **Estratificar por subregión** (costa norte / sierra / Amazonía). El Niño
   costero afecta sobre todo a la costa norte; promediar todo el dominio
   probablemente cancela la señal. Es barato con los parquet que ya existen.
3. **Correr también `--indice nino12`** (versión cruda ERSSTv5) y verificar que
   nada se mueve. Ver sección 0.
4. **Comparar contra precipitación** (SENAMHI o CHIRPS) en la misma ventana: si
   la lluvia sí responde al Niño 1+2 y los rayos no, eso es un resultado; si
   ninguna de las dos responde, es que la ventana es corta.

---

## 7. Archivos

| Archivo | Contenido |
|---|---|
| `wwlln_indice_mensual.csv` | Serie unida: rayos, Niño 1+2, fase, categoría ICEN, anomalía, z, z log |
| `wwlln_por_fase.csv` | Resumen agregado por fase |
| `resumen_por_temporada.csv` | Lo mismo estratificado por temporada seca/lluviosa |
| `correlaciones_lag.csv` | Correlación por rezago 0-6 meses, con n efectivo |
| `wwlln_ciclo_anual.csv` | Climatología mensual 2021-2025 |
| `estadisticos.txt` | Todos los estadísticos en texto plano |
| `serie_indice_vs_rayos.png` | Niño 1+2 y anomalía de rayos en el tiempo |
| `dispersion_indice_vs_z.png` | Scatter con ajuste lineal |
| `boxplot_por_fase.png` | Distribución de la anomalía por fase |
| `correlacion_lags.png` | Correlación por rezago, con banda de ruido |
| `ciclo_anual_rayos.png` | Ciclo anual de actividad eléctrica |
