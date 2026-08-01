# Actividad eléctrica sobre el Perú y su relación con ENSO

Análisis de 41.2 millones de descargas eléctricas detectadas por la **World Wide
Lightning Location Network (WWLLN)** sobre el Perú entre 2021 y 2025, y su
relación con la variabilidad del Pacífico oriental.

**Rafael Ruales** · Datos WWLLN 2021-2025 · Última actualización: julio de 2026

---

## 1. Qué contiene este repositorio

Un pipeline completo y reproducible que va desde los archivos `.mat` crudos de
WWLLN hasta el resultado final, pasando por control de calidad, análisis
climatológico, cartografía y el cruce con índices oceánicos.

El resultado principal es que **la respuesta de la actividad eléctrica a ENSO
cambia de signo entre la costa y la Amazonía peruana**, y que por eso un promedio
sobre todo el país da cero: las dos señales se cancelan.

El resultado secundario, e independiente de ENSO, es que **2025 fue un año
anómalamente bajo** (−29% respecto a la media 2021-2024), y que ese déficit no es
un artefacto de la red de detección.

Documentos relacionados:

| Documento | Para qué |
|---|---|
| `README.md` (este) | Visión general, decisiones metodológicas, resultados |
| `SUMMARY_EN.md` | Resumen de 2 páginas en inglés |
| `README_procesamiento_WWLLN.md` | Manual operativo: cómo correr cada script |
| `REGIONES_LEEME.md` | Método de regionalización, en detalle |
| `GUIA_PRESENTACION.md` | Qué figura usar, cómo leerla, qué no afirmar |
| `analisis_ENSO/DIAGNOSTICO_anomalia_neutral.md` | Por qué el primer resultado era engañoso |
| `_obsoleto_2025/LEEME.md` | Qué se descartó y por qué |

---

## 2. La pregunta

El Perú tiene tres dominios climáticos muy distintos separados por una barrera
orográfica de 6,000 m, y está justo frente a la región oceánica donde nace El
Niño costero. La pregunta natural es si la actividad eléctrica responde a la
variabilidad del Pacífico oriental, y si responde igual en las tres regiones.

Formulada de forma operativa:

> ¿Existe una relación detectable, a escala mensual, entre la temperatura
> superficial del mar frente al Perú y la actividad eléctrica sobre el
> territorio? ¿Es la misma en la costa, los Andes y la Amazonía?

---

## 3. Datos

### 3.1 WWLLN

WWLLN es una red global de ~70 estaciones que localiza descargas por
triangulación del tiempo de llegada de las ondas VLF. Cada evento trae fecha y
hora con precisión de microsegundos, latitud, longitud, energía radiada,
residual de ajuste y número de estaciones que lo detectaron.

| | |
|---|---|
| Periodo | 2021-01-01 a 2025-12-31 |
| Dominio | 19°S-1°N, 82°W-68°W (3.40 millones de km²) |
| Eventos en el dominio | **41,165,104** |
| Eventos dentro del Perú | **20,881,167** |
| Cobertura temporal | 1,821 de 1,826 días (99.7%) |
| Formato original | `.mat` (MATLAB), ~67 GB |

**Importante sobre el dominio:** la caja es **2.6 veces** el Perú continental e
incluye Ecuador, Colombia, Brasil, Bolivia y océano Pacífico. Los análisis
climatológicos se hacen sobre la caja; los análisis por región, solo sobre
territorio peruano.

**Sobre la eficiencia de detección:** WWLLN detecta del orden del 10-30% de las
descargas nube-tierra, con una eficiencia que varía en el espacio y en el tiempo
según la geometría y el número de estaciones activas. Por eso **todo el análisis
se hace en anomalías estandarizadas contra la climatología del mismo mes
calendario**, nunca en conteos absolutos, y por eso el déficit de 2025 se validó
contra el conteo global (sección 6.2).

### 3.2 Índices oceánicos

- **Niño 1+2** (0-10°S, 90-80°W), OISSTv2.1 base 1991-2020, del CPC/NOAA.
  Índice principal.
- **ONI** (Niño 3.4), del CPC/NOAA. Usado solo para comparación.

---

## 4. Pipeline

```
.mat crudos (67 GB)
   │  Leer_WWLLN_recursivo.py       lectura paralela, filtro al dominio
   ▼
peru_wwlln_YYYY.parquet
   │  duplicados_parquet.py         diagnóstico
   │  limpiar_parquet.py            deduplicación
   ▼
peru_wwlln_YYYY_limpio.parquet
   │  analisis_anual_wwlln.py       series mensual/diaria/horaria + energía
   ├─────────────────────────────►  analisis_YYYY/
   │  mapa_densidad_wwlln.py        densidad espacial anual y mensual
   ├─────────────────────────────►  mapas_YYYY/, mapas_mensuales_YYYY/
   │  construir_serie_mensual.py    une los cinco años
   ▼
wwlln_2021_2025_mensual.csv                descargar_oni.py ──► índice ENSO
   │                                                │
   │  regionalizar_peru.py                          │
   ▼                                                │
analisis_regiones/  (una serie por región)          │
   │                                                │
   └──────────────►  oni+wwlln.py  ◄────────────────┘
                          │  anomalías, correlaciones, n efectivo, rezagos
                          ▼
                  graficar_enso.py / graficar_regiones.py / figuras_presentacion.py
```

---

## 5. Decisiones metodológicas

Esta es la sección que importa. Cada decisión aquí cambió el resultado.

### 5.1 Usar solo `.mat`, nunca mezclar con `.loc`

WWLLN distribuye el mismo evento en tres formatos (`A*.loc`, `AE*.loc`,
`AE*.mat`). Leerlos juntos cuenta cada rayo dos o tres veces, y una
deduplicación por lat/lon **no lo detecta**, porque el formato de texto y el
binario guardan la coordenada con precisión decimal ligeramente distinta.

Efecto: 2025 pasaba de 6.21 M a 9.31 M de eventos (+50%).

**Por qué importa más de lo que parece:** con los conteos inflados, 2025
aparecía como el año *más alto* de la serie. El resultado real es que es el más
bajo, y ese déficit es uno de los dos hallazgos del trabajo. El error invertía
la conclusión.

Se detectó comparando 2025 contra los otros cuatro años: era el único
inconsistente. Los archivos afectados están en `_obsoleto_2025/`, con el detalle
en su LEEME.

### 5.2 Normalizar los meses incompletos

Cinco meses de la serie tienen días faltantes (entre 29 y 30 de 30-31). El
conteo se extrapola a mes completo:

```
n_rayos_norm = n_rayos / días_con_datos × días_del_mes
```

Sin esto, un mes al que le faltan dos días parece un 6% menos activo de lo que
fue, y ese 6% es del mismo orden que las anomalías que se quieren medir.

### 5.3 Anomalía estandarizada, no porcentual

El primer análisis usó anomalía porcentual y dio un resultado absurdo: la fase
Neutral aparecía como la más deficitaria, por debajo de La Niña y El Niño.

El problema es que la anomalía porcentual promedia porcentajes calculados sobre
bases muy distintas. La climatología de julio es de ~73,000 rayos; la de
febrero, ~1,244,000: **17 veces más**. Una misma fluctuación absoluta produce un
porcentaje enorme en un mes seco y uno pequeño en un mes húmedo:

| Año | Mes | Anomalía absoluta | Anomalía % |
|---|---|---|---|
| 2024 | Feb | **+416,541** rayos | +30.5% |
| 2022 | Jul | +88,529 rayos | **+121.0%** |

Julio de 2022 aporta un quinto de los rayos que febrero de 2024 y cuadruplica su
porcentaje.

**Solución:** anomalía estandarizada z contra la climatología del mismo mes
calendario. Se reporta además el **z logarítmico**, porque los conteos de rayos
son multiplicativos y el logaritmo estabiliza la varianza entre estación seca y
húmeda.

El diagnóstico completo está en `analisis_ENSO/DIAGNOSTICO_anomalia_neutral.md`.

### 5.4 Niño 1+2, no el ONI

El ONI mide Niño 3.4, en el Pacífico central. El **Niño costero** peruano —el
que gobierna la convección y las lluvias en la costa norte— se ve en Niño 1+2, y
puede ocurrir sin que el ONI se mueva (2017 es el caso de libro).

En estos 60 meses los dos índices correlacionan **r = 0.70** y difieren de fase
en **23 de 60 meses**. Niño 1+2 fecha el evento de 2023 desde febrero; el ONI,
recién a mitad de año.

El cambio además **elimina un sesgo estructural**: con el ONI la fase Neutral
quedaba cargada de meses secos (58%, contra 25% de La Niña), porque el ONI cruza
cero durante la primavera boreal. Con Niño 1+2 la mezcla estacional queda pareja
(39 / 47 / 42%) y la reponderación deja de mover el resultado.

**Umbrales:** los del **ICEN** del ENFEN/IGP (frío ≤ −1.0 °C, cálido ≥ +0.4 °C),
que son asimétricos. Niño 1+2 tiene mucha más varianza que Niño 3.4; aplicarle
el ±0.5 °C del ONI clasificaría como evento casi la mitad de los meses
neutrales.

### 5.5 Regionalización por elevación, con regla de envolvente

Los Andes cruzan el Perú en diagonal: el eje está en −79° a la altura de Piura y
en −70° en Tacna. Cortar por meridianos metería sierra en la costa al norte y
selva en la sierra al sur.

**Método:** para cada latitud se toma un perfil de elevación oeste-este (ETOPO1)
y se buscan la longitud **más occidental** y la **más oriental** con elevación
≥ 1000 m. Eso define la envolvente del terreno alto.

**Por qué la envolvente y no el primer cruce del umbral.** Perfil real a 13°S:

| Longitud | −76.0 | −75.5 | −75.0 | −74.5 | −74.0 | **−73.5** | −73.0 | −72.5 | −72.0 | **−71.5** |
|---|---|---|---|---|---|---|---|---|---|---|
| Elevación (m) | 3049 | 4329 | 4680 | 3695 | 3335 | **774** | 3775 | 2126 | 3535 | **1251** |

Ese 774 es el cañón del Apurímac, encajonado entre macizos de 3300 y 3800 m. Con
la regla del "primer descenso" la cordillera se partiría en −73.7° y un macizo de
3775 m quedaría clasificado como Amazonía. Con la envolvente, el límite queda en
−71.2°, que es el frente andino real.

Validación: el área total del polígono da 1,315,209 km² contra 1,285,216 reales
(2.3% de error). El reparto entre regiones se reporta con sensibilidad a 500,
1000 y 2000 m. Detalle completo en `REGIONES_LEEME.md`.

### 5.6 Grados de libertad efectivos

Las series mensuales de rayos y de TSM están fuertemente autocorrelacionadas, así
que los 60 meses nominales no son 60 observaciones independientes. Se reporta el
**n efectivo de Bretherton et al. (1999)**:

```
n_eff = n · (1 − r₁ˣ·r₁ʸ) / (1 + r₁ˣ·r₁ʸ)
```

Para el dominio completo da **28.7 de 60**. Para la costa, **13.9**. Todos los
p-valores se calculan con n efectivo, no con n nominal.

Se añaden dos controles más: **jackknife** dejando un año fuera cada vez, y
**correlaciones con rezago** de 0 a 6 meses.

---

## 6. Resultados

### 6.1 Climatología (robusta, no depende de ninguna hipótesis)

- **Ciclo anual:** contraste de **17×** entre julio y febrero. Temporada
  lluviosa de octubre a abril.
- **Ciclo diurno:** máximo a las **16 h** local, mínimo a las **9 h**, con razón
  máx/mín de 4.7 a 8.2. **Idéntico los cinco años, sin excepción.** Convección
  vespertina continental. Cinco realizaciones independientes que colapsan sobre
  la misma curva.
- **Distribución por región** (dentro del Perú, 2021-2025):

| Región | Rayos | % | Área (km²) | Rayos/km²/año |
|---|---|---|---|---|
| Amazonía | 13,165,547 | 63.1% | 620,182 | **4.25** |
| Andes | 7,665,961 | 36.7% | 583,129 | **2.63** |
| Costa | 49,659 | **0.24%** | 111,898 | **0.09** |

La costa peruana es, eléctricamente, un desierto: **47 veces menos densidad que
la Amazonía**. Coherente con la inversión térmica de la corriente de Humboldt,
que suprime la convección profunda casi todo el año.

### 6.2 El déficit de 2025

2025 cae **−29%** respecto a la media 2021-2024. La pregunta obligada es si se
perdieron datos o si la red se degradó. Contraste contra el conteo **global** de
WWLLN (muestra de ~60 días por año, todo el planeta):

| Año | Global/día | Perú/día | Perú por millón global |
|---|---|---|---|
| 2023 | 722,092 | 24,833 | 34,390 |
| 2024 | 688,545 | 24,124 | 35,036 |
| **2025** | 650,054 | 16,635 | **25,589** |

El conteo global cae **−8%**; el del Perú, **−32%**. La participación del Perú en
el total global cae **−26.3%**. Si fuera pérdida de archivos o degradación de la
red, ambos caerían en la misma proporción. No lo hacen.

Además la calidad de detección de 2025 fue **igual o mejor**: 7.65 estaciones por
evento contra 7.24-7.44 en años previos, y residual de 11.89 km contra 12.0-12.2.

**Conclusión:** 2025 fue genuinamente un año de baja actividad eléctrica sobre el
Perú. La causa queda como pregunta abierta.

### 6.3 El resultado principal: la señal que se cancelaba

Sin estratificar, el cruce con Niño 1+2 da esencialmente cero (r = −0.039,
n_eff = 28.7). Estratificando:

| Región | Fase fría | Neutral | Fase cálida | Pearson r | n_eff |
|---|---|---|---|---|---|
| **Costa** | −0.13 | −0.11 | **+0.46** | **+0.202** | 13.9 |
| Andes | +0.14 | −0.08 | +0.04 | −0.061 | 18.1 |
| **Amazonía** | **+0.51** | −0.20 | −0.09 | **−0.151** | 31.9 |

**El signo se invierte de la costa a la Amazonía**, con un gradiente monótono de
oeste a este. Promediar las tres regiones da ≈ 0: la señal no estaba ausente,
estaba cancelada.

Físicamente cierra: en un Niño costero el calentamiento del mar frente al Perú
rompe la inversión térmica y dispara convección sobre una costa que normalmente
no la tiene; en paralelo la fase cálida se asocia a subsidencia y déficit de
lluvia sobre la Amazonía occidental.

### 6.4 El caso 2023, donde no hace falta estadística

| Abril de | 2021 | 2022 | **2023** | 2024 | 2025 |
|---|---|---|---|---|---|
| Rayos en la costa | 181 | 222 | **21,793** | 195 | 1,071 |

Factor **~100** contra los años vecinos. En el año completo la costa pasa de
~4,300 rayos a **32,377** (7.5×), con marzo y abril concentrando el 84%.
Coincide con el Niño costero de 2023 (Niño 1+2 de −0.11 en enero a +2.08 en
abril-junio) y con el ciclón Yaku de marzo de 2023. En paralelo, la Amazonía cayó
**−19.1%** respecto a 2022.

---

## 7. Limitaciones

Estas limitaciones no son una formalidad: acotan de verdad lo que se puede
afirmar.

1. **Cinco años no alcanzan.** Hay **un solo evento cálido** (2023) en toda la
   ventana. El jackknife dejando un año fuera mueve la media de la fase cálida
   **1.47 z** — más que cualquiera de las diferencias que se están interpretando.
   No se puede hacer estadística sobre "el efecto de El Niño costero" con un solo
   evento; a lo sumo describir el caso 2023.
2. **Nada es estadísticamente significativo.** El n efectivo de la costa es 13.9
   de 60 meses (p ≈ 0.49). La inversión de signo es coherente y físicamente
   esperable, pero es **generadora de hipótesis**, no confirmatoria.
3. **El efecto de año contamina la comparación por fases.** 2023 es casi toda la
   fase cálida; 2022, casi toda la fría; 2025 pesa en la neutral. La
   clasificación por fase está reetiquetando, en parte, un efecto de año.
4. **Los límites de Costa y Andes son provisionales.** El muestreo de elevación a
   0.5° de longitud sesga el límite occidental hacia el mar en pendientes
   fuertes: la costa sale en 8.5% del área en vez del ~12% convencional. La
   partición Amazonía/resto sí es robusta. Corregible con `muestrear_elevacion.py`.
5. **Eficiencia de detección no corregida explícitamente.** Se mitiga trabajando
   en anomalías y con el control global, pero no se aplicó un modelo de
   eficiencia.
6. **Un día perdido:** `AE20250908.mat` está dañado de origen (confirmado en tres
   copias). 2025 cubre 364 de 365 días.

---

## 8. Dónde se agota este enfoque

La limitación 1 no es incidental: define qué tipo de método necesita el problema.

Las observaciones **caracterizan** el evento de abril de 2023 con confianza alta:
la magnitud es un factor ~100 sobre la línea base local, el momento coincide con
la evolución de Niño 1+2, el patrón espacial está confinado a la región donde
aplica el mecanismo físico, y los controles de calidad descartan artefactos
instrumentales.

Lo que las observaciones **no pueden** decir es qué tan probable era ese evento,
ni si esa probabilidad ha cambiado. Un evento en cinco años —o dos en quince— no
sustenta inferencia sobre probabilidad de ocurrencia, por más cuidado que se
tenga con el procesamiento. Extender la ventana ayuda con el muestreo, pero la
restricción de fondo permanece: el clima real entrega una sola realización.

Ese es exactamente el vacío que llena la **atribución de eventos con ensembles
grandes**, y es la dirección que quiero seguir.

**Dirección propuesta.** Usar los Niños costeros de 2017 y 2023 como eventos
objetivo, con la actividad convectiva sobre la costa peruana como variable de
interés, contrastando ensembles históricos contra contrafactuales sin
calentamiento (d4PDF: 100 miembros, MRI-AGCM3.2, histórico y *non-warming*).

**Por qué los rayos son una variable objetivo favorable.** En la costa peruana
se comportan como un indicador casi binario, no como la cola de una distribución
continua: la línea base de abril es ~190 rayos y abril de 2023 registró 21,793.
La atribución normalmente tiene que resolver una cola desplazada; aquí el
contraste se acerca a ocurrencia contra no ocurrencia, lo que agudiza la razón
de probabilidades. Además los rayos son un proxy más directo de intensidad
convectiva profunda que la precipitación acumulada, y están mucho menos
explorados como objetivo de atribución.

**Qué haría falta de mi lado.** Extender el registro WWLLN hacia atrás hasta
cubrir 2017. El pipeline ya lo resuelve: es trabajo de procesamiento sobre un
camino validado, no diseño nuevo. La estratificación regional, el marco de
anomalías y el manejo de índices se transfieren sin cambios.

**Una pregunta metodológica abierta.** El Niño costero *es* una anomalía de TSM,
y el AGCM de d4PDF está forzado por TSM. Eso vuelve no trivial el planteamiento:
si la pregunta bien puesta es el cambio de probabilidad de la respuesta
convectiva *condicionada* a la anomalía de TSM observada, o de la anomalía misma,
y cómo la construcción *non-warming* separa ambas cosas. No creo que la respuesta
sea obvia en la literatura.

**Pasos independientes de lo anterior:**

1. Refinar los límites de región con muestreo denso de elevación
   (`muestrear_elevacion.py`, 2 minutos).
2. Modelar la eficiencia de detección con el número de estaciones activas por año.
3. Validación externa: GLM de GOES-16 (2017+) o precipitación CHIRPS/SENAMHI.
4. Ciclo diurno por región: el pico de las 16 h es un promedio del dominio, y las
   tres regiones probablemente difieren en fase.

---

## 9. Reproducibilidad

Todo el pipeline se corre por parámetros, sin editar código. El manual operativo
está en `README_procesamiento_WWLLN.md`. Requisitos:

```bash
pip install pandas numpy scipy pyarrow matplotlib cartopy shapely pyshp
```

Ejemplo mínimo, de los `.mat` al resultado:

```bash
python3 Leer_WWLLN_recursivo.py "/ruta/a/2025/MATfiles" ./peru_wwlln_2025.parquet --workers 6
python3 limpiar_parquet.py
python3 analisis_anual_wwlln.py --entrada peru_wwlln_2025_FINAL.parquet --anio 2025 --salida analisis_2025
python3 construir_serie_mensual.py --base . --salida wwlln_2021_2025_mensual.csv
python3 descargar_oni.py --indice nino12 --desde 2021 --hasta 2025
python3 regionalizar_peru.py --umbral 1000 --salida analisis_regiones
python3 "oni+wwlln.py" --wwlln analisis_regiones/wwlln_2021_2025_mensual_costa.csv \
                       --indice nino12_2021_2025_tidy.csv --salida analisis_regiones/enso_costa
```

Cada script valida sus entradas. `mapa_densidad_wwlln.py`, por ejemplo, aborta si
el parquet no corresponde al año pedido — esa comprobación se añadió después de
descubrir que una copia del script llevaba tiempo leyendo el año equivocado.

---

## 10. Estructura

```
├── README.md                        este documento
├── SUMMARY_EN.md                    resumen de 2 páginas en inglés
├── README_procesamiento_WWLLN.md    manual operativo
├── REGIONES_LEEME.md                método de regionalización
├── GUIA_PRESENTACION.md             qué figura usar y cómo leerla
│
├── Leer_WWLLN*.py                   lectura de .mat y filtro al dominio
├── limpiar_parquet.py               deduplicación
├── analisis_anual_wwlln.py          series por año
├── mapa_densidad_wwlln.py           cartografía de densidad
├── construir_serie_mensual.py       une los cinco años
├── descargar_oni.py                 índices ENSO del CPC/NOAA
├── oni+wwlln.py                     cruce, anomalías, n efectivo, rezagos
├── regionalizar_peru.py             estratificación por elevación
├── muestrear_elevacion.py           malla densa de elevación por API
├── graficar_*.py, figuras_presentacion.py
│
├── analisis_2021..2025/             series mensual/diaria/horaria por año
├── mapas_2021..2025/                mapa de densidad anual
├── mapas_mensuales_2021..2025/      doce mapas por año
├── analisis_ENSO/                   cruce con ONI (referencia)
├── analisis_ENSO_nino12/            cruce con Niño 1+2 (principal)
├── analisis_regiones/               estratificación y cruce por región
├── figuras_presentacion/            figuras finales
├── recursos/                        cartografía y perfiles de elevación
└── _obsoleto_2025/                  lo descartado, con su explicación
```

---

## 11. Datos y créditos

**WWLLN.** Los datos provienen de la World Wide Lightning Location Network
(http://wwlln.net), una colaboración de más de 50 instituciones. El uso de estos
datos requiere el reconocimiento de la red y de las instituciones participantes;
verifica los términos con la institución que te dio acceso antes de publicar.

**Índices oceánicos.** NOAA/NWS Climate Prediction Center,
https://www.cpc.ncep.noaa.gov/data/indices/

**Elevación.** ETOPO1, NOAA/NCEI, consultado vía la API pública de OpenTopoData
(https://www.opentopodata.org).

**Cartografía.** Natural Earth (dominio público), vía cartopy.

**Umbrales ICEN.** ENFEN / Instituto Geofísico del Perú. La implementación aquí
es un ICEN-proxy calculado sobre datos del CPC: las categorías coinciden, los
decimales pueden diferir del ICEN oficial.
