# Qué presentar y cómo — WWLLN Perú 2021-2025

Tienes 106 figuras y 130 CSV. **Para la charla necesitas 7.** Este documento
dice cuáles, cómo se leen, qué decir y qué no afirmar.

---

## Veredicto rápido

| Familia | Cuántas | Veredicto |
|---|---|---|
| `figuras_presentacion/` | 2 | **Listas.** Hechas para proyectar |
| `analisis_regiones/` | 4 | **Listas.** Tu resultado más interesante |
| `mapas_2021..2025/` (anual) | 5 | **Listas tras regenerarlas** en tu Mac |
| `analisis_ENSO_nino12/` | 5 | **Una sola sirve** (`serie_indice_vs_rayos`) |
| `analisis_YYYY/` | 20 | **Material de trabajo, no de charla** |
| `mapas_mensuales_YYYY/` | 60 | **Respaldo.** Solo si te preguntan |
| `analisis_ENSO/` (ONI) | 8 | **No presentar.** Superadas por Niño 1+2 |

Por qué las 20 de `analisis_YYYY/` no van: son una por año, con el eje en UTC,
sin tildes y sin barras de error. Te sirven para verificar el procesamiento.
Proyectadas, obligan a cinco slides para decir lo que las versiones compuestas
dicen en una — y el eje en UTC hace que el máximo caiga a las 21 h y parezca un
fenómeno nocturno, que es justo lo contrario de lo que pasa.

---

## Las 7 slides

### 1 — Datos y control de calidad

*Sin figura. Tabla o texto.*

**Qué decir:** 41,165,104 rayos en el dominio 19°S-1°N / 82°W-68°W, 2021-2025,
de los archivos `.mat` de WWLLN. 20,881,167 dentro del territorio peruano.

**Los tres controles que te dan credibilidad:**

- Se detectó y corrigió un doble conteo: leer a la vez `.mat`, `A*.loc` y
  `AE*.loc` del mismo día contaba cada rayo 2-3 veces. Inflaba 2025 de 6.21 M a
  9.31 M (+50%).
- `AE20250908.mat` está dañado de origen, confirmado en las tres copias. 2025
  cubre 364 de 365 días.
- Se recuperaron 16 días que estaban solo en la carpeta "Datos corruptos".

**Por qué importa decirlo:** con los datos contaminados 2025 salía como el año
más alto de la serie. Es lo contrario del resultado de la slide 5. Mencionarlo
convierte un error en evidencia de que controlaste el dato.

---

### 2 — Ciclo diurno

**Figura:** `figuras_presentacion/ciclo_diurno_local.png`

**Cómo se lee:** cada curva es un año, normalizada al % de rayos de ese año, en
hora local (UTC−5). La línea negra punteada es la media.

**Qué decir:** máximo a las **16 h**, mínimo a las **9 h**, **idéntico los cinco
años sin excepción**. La razón máximo/mínimo va de 4.7 a 8.2. Es convección
vespertina continental de manual: el suelo se calienta, la capa límite se
desarrolla, la convección dispara por la tarde.

**Por qué esta figura es fuerte:** cinco realizaciones independientes que
colapsan sobre la misma curva. No depende de ninguna hipótesis ni de ningún
ajuste. Si alguien duda de tu procesamiento, esta figura lo responde: un
artefacto de datos no reproduce cinco veces el mismo ciclo físico.

**Qué NO afirmar:** que el pico es a las 16 h *en todo el país*. Es el promedio
del dominio; la Amazonía y los Andes tienen fases algo distintas. No lo has
medido por separado todavía.

---

### 3 — Ciclo anual y distribución espacial

**Figuras:** `analisis_ENSO_nino12/ciclo_anual_rayos.png` y
`mapas_2024/mapa_densidad_wwlln_peru_2024.png`

**Cómo se lee el ciclo anual:** barras = media mensual 2021-2025, líneas = ±1
desviación estándar entre años.

**Qué decir:** contraste de **17×** entre julio (~73,000) y febrero
(~1,244,000). Temporada lluviosa de octubre a abril. El mapa muestra el
gradiente: la Amazonía saturada, el piedemonte andino con los máximos locales,
la costa prácticamente vacía.

**Ojo con el mapa:** el dominio es 3.40 millones de km², **2.6 veces el Perú**.
Los focos más intensos del mapa de 2024 están en territorio brasileño. El título
ya dice "dominio", no "en Perú" — no lo llames "mapa del Perú" al hablar. Si
quieres el recorte real, `mapa_densidad_wwlln.py --recortar-peru --densidad`.

---

### 4 — Por qué Niño 1+2 y no el ONI

**Figura:** `analisis_ENSO_nino12/serie_indice_vs_rayos.png`

**Qué decir:** el ONI mide Niño 3.4, en el Pacífico central. El Niño costero
peruano se ve en Niño 1+2 (0-10°S, 90-80°W) y puede ocurrir sin que el ONI se
mueva. En estos 60 meses los dos índices correlacionan **r = 0.70** y difieren
de fase en **23 de 60 meses**. El caso claro: Niño 1+2 marca el evento de 2023
desde **febrero**; el ONI recién a mitad de año.

Además el cambio de índice **elimina un sesgo**: con el ONI la fase Neutral
quedaba cargada de meses secos (58% contra 25% de La Niña), lo que distorsionaba
cualquier comparación. Con Niño 1+2 la mezcla queda pareja (39 / 47 / 42%).

**Umbrales:** se usaron los del **ICEN** del ENFEN/IGP (frío ≤ −1.0 °C, cálido
≥ +0.4 °C), no el ±0.5 del ONI. Niño 1+2 tiene mucha más varianza; aplicarle el
umbral del ONI clasificaría como evento casi la mitad de los meses neutrales.

**Qué NO afirmar:** que usaste el ICEN oficial. Usaste un ICEN-proxy sobre datos
del CPC. Las categorías coinciden, los decimales pueden diferir.

---

### 5 — El déficit de 2025

**Figura:** `figuras_presentacion/deficit_2025.png`

**Cómo se lee:** panel izquierdo, totales anuales. Panel derecho, cuántos rayos
del Perú hay por cada millón de rayos que WWLLN detecta en todo el planeta, en
una muestra de ~60 días por año.

**Qué decir:** 2025 cae **−29%** respecto a la media 2021-2024. La pregunta
obvia es si se perdieron archivos o si la red se degradó. El panel derecho lo
descarta: si fuera la red, la participación del Perú en el total global no se
movería. Cae **−26.3%**. Y la calidad de detección de 2025 fue igual o mejor:
7.65 estaciones por evento contra 7.24-7.44, residual 11.89 km contra 12.0-12.2.

**Cuidado con dos números que parecen contradecirse:**

- **−29%** = total anual completo de 2025 contra la media 2021-2024.
- **−32%** = rayos/día en el Perú en la muestra de ~60 días, 2025 contra
  2023-24.

Son cantidades distintas, ambas correctas. Usa **−29%** si hablas del año
completo y **−32%** solo cuando estés comparando contra el conteo global, que se
hizo sobre esa muestra. Si mezclas, te lo van a preguntar.

**Qué NO afirmar:** no tienes la causa. Es un hallazgo descriptivo. Lo honesto es
"2025 fue genuinamente un año de baja actividad eléctrica en el Perú y no es un
artefacto de datos", y dejar la explicación como pregunta abierta.

---

### 6 — Estratificación regional: la señal que se cancelaba

**Figuras:** `analisis_regiones/mapa_regiones.png` y
`analisis_regiones/anomalia_por_fase_region.png`

**Cómo se lee el mapa:** las tres regiones salen de la elevación, no de bandas de
longitud. Los puntos negros son los transectos ETOPO1 muestreados; las líneas,
los límites interpolados.

**Menciona el detalle metodológico** — es lo que distingue un análisis serio de
uno hecho a ojo: los límites usan la **envolvente** del terreno sobre 1000 m, no
el primer cruce del umbral. A 13°S el cañón del Apurímac baja a 774 m entre
macizos de 3300 y 3800 m; con la regla ingenua la cordillera se partiría en dos y
un macizo de 3775 m quedaría clasificado como Amazonía.

**Cómo se lee la figura de anomalías:** z medio de la actividad eléctrica en cada
fase de Niño 1+2, por región.

**Qué decir — este es el punto de la charla:**

| Región | Fase fría | Neutral | Fase cálida |
|---|---|---|---|
| Costa | −0.13 | −0.11 | **+0.46** |
| Andes | +0.14 | −0.08 | +0.04 |
| Amazonía | **+0.51** | −0.20 | −0.09 |

**El signo se invierte de la costa a la Amazonía.** Es un gradiente monótono de
oeste a este. Promediar las tres da ≈ 0 — que es exactamente el resultado nulo
que salía antes de estratificar. La señal no estaba ausente: estaba cancelada.

Físicamente cierra: en un Niño costero el mar caliente frente al Perú rompe la
inversión térmica y dispara convección sobre una costa que normalmente no la
tiene; a la vez la fase cálida se asocia a subsidencia sobre la Amazonía
occidental.

**Qué NO afirmar:** que es estadísticamente significativo. El n efectivo de la
costa es 13.9 de 60 meses; p ≈ 0.49. Dilo tú antes de que te lo pregunten.

---

### 7 — El caso 2023

**Figura:** `analisis_regiones/serie_costa.png`

**Qué decir:** aquí no hace falta estadística.

| Abril de | 2021 | 2022 | **2023** | 2024 | 2025 |
|---|---|---|---|---|---|
| Rayos en la costa | 181 | 222 | **21,793** | 195 | 1,071 |

Factor **~100** contra los años vecinos. En el año completo la costa pasa de
~4,300 rayos a **32,377**, y marzo-abril concentran el 84%. Coincide con el Niño
costero (Niño 1+2 de −0.11 en enero a +2.08 en abril-junio) y con el ciclón Yaku
de marzo de 2023. En paralelo, la Amazonía cayó **−19.1%** respecto a 2022.

**Qué NO afirmar:** que "la costa responde a ENSO con r = 0.20". Buena parte de
esa correlación **es** este evento. Preséntalo como descripción del caso 2023,
que es más fuerte y más honesto.

---

### Cierre — Qué sigue

1. Extender a 2010-2025. Con la estratificación ya construida, es lo que
   convierte el hallazgo en resultado publicable: mete el Niño costero de 2017,
   El Niño 2015-16 y La Niña 2010-11.
2. Refinar los límites de región con muestreo denso (`muestrear_elevacion.py`,
   2 minutos).
3. Eficiencia de detección: estaciones WWLLN activas por año en la región.
4. Validación externa: GLM de GOES-16 o precipitación CHIRPS.

---

## Las tres preguntas que te van a hacer

**"¿Cuál es la eficiencia de detección de WWLLN?"**
Ronda 10-30% para descargas nube-tierra y varió con el crecimiento de la red.
Por eso todo el análisis está en **anomalías estandarizadas contra la
climatología del mismo mes**, no en conteos absolutos, y por eso el déficit de
2025 se validó contra el conteo global. Es la primera pregunta que hace
cualquiera que conozca la red: tenla lista.

**"¿Por qué solo cinco años?"**
Es lo que hay procesado. Y es la limitación principal: un solo evento cálido, n
efectivo ≈ 28 de 60 meses nominales. Dilo como limitación reconocida, no como
defensa.

**"¿El mapa es del Perú?"**
No: es una caja de 3.40 millones de km², 2.6 veces el país. Ten la respuesta
lista, y si puedes, lleva de respaldo la versión `--recortar-peru --densidad`.

---

## Checklist antes de proyectar

- [ ] Regenerar los mapas de los 5 años en tu Mac (ver `mapas_2025/LEEME.md`).
      Los de 2025 los generé sin la cartografía de 10m y los títulos ya no
      coinciden entre años.
- [ ] Correr `descargar_oni.py --indice nino12` y confirmar que la inversión de
      signo aguanta con el índice crudo (segundos).
- [ ] No mezclar el −29% con el −32%.
- [ ] No usar nada de `analisis_ENSO/` (ONI): está superado por Niño 1+2.
- [ ] No usar nada de `_obsoleto_2025/`: son los datos contaminados.

---

## De dónde sale cada número

| Afirmación | Archivo |
|---|---|
| Totales anuales y del dominio | `analisis_YYYY/resumen_anual_wwlln_peru_YYYY.csv` |
| Serie mensual 2021-2025 | `wwlln_2021_2025_mensual.csv` |
| Ciclo diurno por año | `analisis_YYYY/wwlln_peru_horario_YYYY.csv` |
| Resumen del ciclo diurno | `figuras_presentacion/ciclo_diurno_resumen.csv` |
| Control global del déficit de 2025 | `figuras_presentacion/deficit_2025_control_global.csv` |
| Índice Niño 1+2 y fases | `rnino12_2021_2025_tidy.csv` |
| Cruce ENSO del dominio | `analisis_ENSO_nino12/estadisticos.txt` |
| Series y anomalías por región | `analisis_regiones/` |
| Método de regionalización | `REGIONES_LEEME.md` |
| Diagnóstico del resultado nulo | `analisis_ENSO/DIAGNOSTICO_anomalia_neutral.md` |
