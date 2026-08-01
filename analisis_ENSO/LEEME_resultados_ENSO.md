# Cruce WWLLN × ONI (Niño 3.4) — Perú 2021-2025

> **Actualizado.** Esta versión se rehízo con los 60 meses completos y con el
> `oni+wwlln.py` genérico. La versión anterior de este archivo reportaba 57
> meses (descartaba feb/mar/abr de 2025 por baja cobertura) y valores de z que
> ya no corresponden. Si tienes esos números apuntados en algún lado, están
> obsoletos: usa los de aquí.
>
> **Y antes de citar nada de este archivo:** para Perú el índice pertinente es
> Niño 1+2, no el ONI. Ver `../analisis_ENSO_nino12/LEEME_resultados_nino12.md`.
> Esta carpeta queda como referencia y como comparación entre índices.

## Cómo se construyó

1. Serie mensual de rayos por año (de `analisis_YYYY/`), normalizada a mes
   completo para corregir días faltantes. Entran los 60 meses.
2. ONI del CPC/NOAA (media móvil de 3 meses de anomalías de TSM ERSSTv5 en
   Niño 3.4, climatología base móvil), cada trimestre asignado a su mes central.
3. Anomalía estandarizada z contra la climatología del mismo mes calendario.

## Resultados

**Meses por fase:** La Niña 24 · Neutral 24 · El Niño 12

| Fase | n meses | z medio | z log medio | anomalía % media | ONI medio |
|---|---|---|---|---|---|
| El Niño | 12 | +0.112 | +0.143 | +5.3% | +1.42 |
| La Niña | 24 | +0.065 | +0.049 | +3.0% | −0.77 |
| Neutral | 24 | −0.121 | −0.120 | −5.6% | −0.15 |

**Correlaciones:**

- Pearson r = −0.020 (n = 60)
- Spearman ρ = −0.058
- r con z logarítmico = +0.001
- n efectivo (Bretherton) = 28.2
- p aproximado con n efectivo = 0.92
- Solo temporada lluviosa (oct-abr): r = +0.042 (n = 35)
- Solo temporada seca (may-set): r = −0.139 (n = 25)
- Kruskal-Wallis entre fases: H = 1.33, p = 0.515
- Con rezago 0-6 meses: r entre −0.02 y −0.18, perfil plano

## Interpretación

Con el ONI **no se detecta relación apreciable con la actividad eléctrica en
Perú a escala mensual**. Las tres fases tienen anomalías medias prácticamente
indistinguibles de cero y las correlaciones son nulas en todos los rezagos.

Las razones están desarrolladas en `DIAGNOSTICO_anomalia_neutral.md`, y son
tres:

1. La anomalía porcentual no es comparable entre fases (bases muy distintas
   entre mes seco y mes húmedo). Usar z, o mejor z logarítmico.
2. La fase Neutral está cargada de meses secos (58% contra 25% de La Niña),
   porque el ONI cruza cero durante la primavera-verano boreal. **Este sesgo
   desaparece al usar Niño 1+2.**
3. Por debajo de todo manda el efecto de año: 2025 es un año anómalamente bajo
   (z medio −0.95, todos los meses negativos) y aporta 9 de los 24 meses
   Neutral. Quitando 2025, Neutral pasa de −0.12 a +0.34.

Y en cualquier caso hay un solo evento El Niño (2023-24) en la ventana, con n
efectivo ≈ 28 de 60 meses nominales.

## Archivos

| Archivo | Contenido |
|---|---|
| `wwlln_indice_mensual.csv` | Serie unida: rayos, ONI, fase, anomalía, z, z log |
| `wwlln_por_fase.csv` | Resumen agregado por fase |
| `resumen_por_temporada.csv` | Estratificado por temporada seca/lluviosa |
| `correlaciones_lag.csv` | Correlación por rezago 0-6 meses, con n efectivo |
| `wwlln_ciclo_anual.csv` | Climatología mensual 2021-2025 |
| `estadisticos.txt` | Estadísticos en texto plano |
| `serie_indice_vs_rayos.png`, `dispersion_indice_vs_z.png`, `boxplot_por_fase.png`, `correlacion_lags.png`, `ciclo_anual_rayos.png` | Figuras |
| `DIAGNOSTICO_anomalia_neutral.md` | Por qué Neutral salía peor que El Niño |
| `conteo_global_20XX.csv` | Conteos globales vs Perú (sustentan el déficit de 2025) |

**Archivos obsoletos en esta carpeta** (quedaron de la corrida de 57 meses, se
pueden borrar): `wwlln_oni_mensual.csv`, `wwlln_por_fase_enso.csv`,
`serie_oni_vs_rayos.png`, `dispersion_oni_vs_z.png`.
