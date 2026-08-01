# Estratificación por regiones: Costa / Andes / Amazonía

Cómo se separó el Perú en tres regiones y qué salió al repetir el cruce con
ENSO por separado en cada una.

**Resultado corto:** el signo de la respuesta a ENSO **se invierte** entre la
costa y la Amazonía. Por eso el promedio de todo el país daba cero: las dos
señales se cancelaban.

---

## 1. Por qué no se puede cortar por longitud

La tentación es partir el dominio en tres bandas de longitud. No sirve: los
Andes cruzan el Perú en **diagonal**, del noroeste al sureste. El eje andino
está en −79° a la altura de Piura y en −70° a la altura de Tacna. Un corte por
meridianos metería sierra dentro de la costa en el norte y selva dentro de la
sierra en el sur.

La separación tiene que ser por **elevación**.

---

## 2. El método

### 2.1 Fuente de elevación

**ETOPO1** (NOAA/NCEI, 1 arcmin ≈ 1.8 km), consultado a través de la API pública
de [OpenTopoData](https://www.opentopodata.org).

Se muestrearon **10 transectos este-oeste**, a las latitudes 2°S, 5°S, 6.5°S,
8°S, 9°S, 10.5°S, 13°S, 14.5°S, 16°S y 18°S, cada **0.5° de longitud**. En
total 135 puntos, guardados en `recursos/perfiles_etopo1_peru.csv`.

Las latitudes no están repartidas de forma uniforme: hay más muestreo entre 5°S
y 10°S, donde la cordillera se deflecta (la depresión de Huancabamba), y entre
13°S y 16°S, donde el frente oriental andino retrocede hacia Madre de Dios.

### 2.2 De los perfiles a los límites: la regla de la envolvente

En cada perfil se buscan dos longitudes:

- **`lon_w`** = la longitud **más occidental** con elevación ≥ umbral
- **`lon_e`** = la longitud **más oriental** con elevación ≥ umbral

El valor exacto se obtiene interpolando linealmente entre las dos muestras que
rodean el cruce del umbral.

Fíjate en que **no** es "el primer punto donde el terreno sube del umbral y el
primero donde vuelve a bajar". Es la **envolvente** del terreno alto. La
diferencia importa mucho. Mira el perfil real de 13°S:

| Longitud | −76.0 | −75.5 | −75.0 | −74.5 | −74.0 | **−73.5** | −73.0 | −72.5 | −72.0 | **−71.5** | −71.0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Elevación (m) | 3049 | 4329 | 4680 | 3695 | 3335 | **774** | 3775 | 2126 | 3535 | **1251** | 795 |

Ese 774 de −73.5° es el cañón del Apurímac, encajonado entre dos macizos de
3300 y 3800 m. Con la regla del "primer descenso" la cordillera se cortaría en
−73.7° y todo lo que sigue al este quedaría clasificado como Amazonía, incluido
el macizo de 3775 m. Con la envolvente, el límite queda en −71.2°, que es donde
de verdad termina el frente andino.

### 2.3 Interpolación y clasificación

Las dos curvas `lon_w(lat)` y `lon_e(lat)` se interpolan linealmente entre
transectos. Cada rayo se clasifica por su longitud comparada con las curvas de
su latitud:

```
lon < lon_w(lat)                  ->  Costa
lon_w(lat) <= lon <= lon_e(lat)   ->  Andes
lon > lon_e(lat)                  ->  Amazonía
```

Y aparte se marca si el rayo cae dentro del territorio peruano, usando el
polígono de Natural Earth. **El análisis se hace solo con los rayos dentro del
Perú**: de los 41,165,104 del dominio completo, quedan **20,881,167** (50.7%).
El resto está en Ecuador, Colombia, Brasil, Bolivia y el Pacífico.

Límites obtenidos con umbral de 1000 m:

| Latitud | Costa / Andes | Andes / Amazonía |
|---|---|---|
| 2°S | −79.29 | −77.99 |
| 5°S | −80.18 | −78.46 |
| 6.5°S | −79.34 | −75.87 |
| 8°S | −78.88 | −76.00 |
| 9°S | −78.38 | −75.99 |
| 10.5°S | −77.69 | −74.42 |
| 13°S | −76.34 | −71.22 |
| 14.5°S | −75.28 | −69.50 |
| 16°S | −73.74 | −68.50 |
| 18°S | −70.31 | −68.50 |

Al sur de 15°S el límite oriental toca el borde del dominio: a esa latitud, al
este de los Andes ya no hay Amazonía peruana sino altiplano (Titicaca, y luego
Bolivia). Es correcto, no es un artefacto.

### 2.4 Umbral

**1000 m como valor principal**, con sensibilidad a 500 y 2000 m.

---

## 3. Validación

### 3.1 Por área

El área total que devuelve el polígono es **1,315,209 km²**, contra los
1,285,216 km² reales del Perú continental: **2.3% de error**. El polígono
sirve.

El reparto entre regiones sí depende del umbral:

| Umbral | Costa | Andes | Amazonía |
|---|---|---|---|
| 500 m | 6.8% | 50.9% | 42.2% |
| **1000 m** | **8.5%** | **44.3%** | **47.2%** |
| 2000 m | 13.7% | 31.7% | 54.7% |
| *referencia INEI* | *~12%* | *~28%* | *~60%* |

**Con 1000 m la región andina sale más ancha de lo convencional** (44% contra
28%). Hay dos causas y conviene tenerlas claras:

1. **La convención peruana es asimétrica.** En la clasificación de Pulgar
   Vidal la costa (Chala) llega hasta 500 m y la selva alta (Rupa-Rupa) empieza
   por debajo de 1000 m. O sea que el terreno entre 1000 y 2000 m del flanco
   oriental es "selva alta" para la convención nacional y "Andes" para este
   método.
2. **El muestreo a 0.5° es grueso en pendientes fuertes.** En el flanco
   occidental la elevación salta de ~150 m a ~3000 m entre dos muestras
   contiguas; interpolar linealmente ahí coloca el cruce del umbral demasiado
   al oeste, lo que **estrecha la costa**. Por eso la costa sale en 8.5% y no
   en 12%.

**Consecuencia práctica:** los números absolutos de Costa y Andes son
provisionales. La partición Amazonía / resto es la robusta, y es donde está el
grueso de los rayos. Con un DEM completo (`--dem`) esto se corrige.

### 3.2 Por geografía

`analisis_regiones/mapa_regiones.png` muestra las tres regiones. La franja
costera, la diagonal andina y la llanura amazónica salen donde tienen que
salir, y el retroceso del frente oriental hacia Madre de Dios entre 13°S y 15°S
se reproduce.

---

## 4. Resultados

### 4.1 Reparto de la actividad eléctrica

20,881,167 rayos dentro del Perú, 2021-2025:

| Región | Rayos | % | Área (km²) | Rayos/km²/año |
|---|---|---|---|---|
| Amazonía | 13,165,547 | 63.05% | 620,182 | **4.25** |
| Andes | 7,665,961 | 36.71% | 583,129 | **2.63** |
| Costa | 49,659 | **0.24%** | 111,898 | **0.09** |

La costa peruana es, en términos de actividad eléctrica, prácticamente un
desierto: **47 veces menos densidad que la Amazonía**. Es coherente con su
climatología — la inversión térmica de la corriente de Humboldt suprime la
convección profunda casi todo el año.

Sensibilidad al umbral (reparto de rayos):

| Umbral | Costa | Andes | Amazonía |
|---|---|---|---|
| 500 m | 0.20% | 46.05% | 53.75% |
| **1000 m** | **0.24%** | **36.71%** | **63.05%** |
| 2000 m | 0.60% | 27.48% | 71.92% |

El reparto Andes/Amazonía sí se mueve con el umbral — hay que reportarlo. Lo
que **no** cambia con el umbral es el resultado de la sección siguiente.

### 4.2 El hallazgo: el signo de la respuesta a ENSO se invierte

Anomalía estandarizada de rayos (z) por fase de Niño 1+2:

| Región | Fría (n=15) | Neutral (n=33) | Cálida (n=12) |
|---|---|---|---|
| **Costa** | −0.128 | −0.110 | **+0.462** |
| Andes | +0.136 | −0.078 | +0.044 |
| **Amazonía** | **+0.514** | −0.201 | −0.090 |

Correlación con el índice Niño 1+2:

| Región | Pearson r | Spearman | Solo temporada lluviosa | n efectivo |
|---|---|---|---|---|
| **Costa** | **+0.202** | +0.291 | +0.254 | 13.9 |
| Andes | −0.061 | −0.071 | −0.002 | 18.1 |
| **Amazonía** | **−0.151** | −0.273 | −0.148 | 31.9 |

**La costa responde en positivo, la Amazonía en negativo, y los Andes quedan en
medio.** Es un gradiente monótono de oeste a este. Promediar las tres regiones
da ≈ 0, que es exactamente el resultado nulo que salía antes de estratificar.

Físicamente tiene sentido: durante un Niño costero, el calentamiento del mar
frente al Perú rompe la inversión térmica y dispara convección sobre una costa
que normalmente no la tiene; al mismo tiempo, la fase cálida se asocia a
subsidencia y déficit de lluvia sobre la Amazonía occidental.

### 4.3 El caso 2023, que es donde se ve sin estadística

Rayos en la costa por año:

| Año | Rayos en la costa |
|---|---|
| 2021 | 6,399 |
| 2022 | 2,845 |
| **2023** | **32,377** |
| 2024 | 3,391 |
| 2025 | 4,647 |

2023 tiene **7.5 veces** el promedio de los otros cuatro años. Y no está
repartido: **marzo y abril de 2023 concentran 27,253 rayos, el 84% del año**.

Abril de 2023, mes a mes:

| Abril de | 2021 | 2022 | **2023** | 2024 | 2025 |
|---|---|---|---|---|---|
| Rayos en la costa | 181 | 222 | **21,793** | 195 | 1,071 |

Es un factor de **~100** contra los años vecinos. Coincide con el Niño costero
de 2023 (el índice Niño 1+2 pasa de −0.11 en enero a +2.08 en abril-junio) y
con el ciclón Yaku, que tocó la costa norte en marzo de 2023.

Y al mismo tiempo, en la Amazonía: 2023 tuvo 2,540,291 rayos contra 3,140,346
en 2022 (fase fría), un **−19.1%**.

---

## 5. Lo que este resultado NO dice

- **No es significativo en el sentido estadístico.** El n efectivo de la costa
  es 13.9 de 60 meses nominales; p ≈ 0.49. Con 12 meses en fase cálida y un
  solo evento (2023), no hay potencia para afirmar nada.
- **Buena parte de la correlación de la costa es un solo evento.** Si quitas
  2023, la señal costera se desploma. Lo honesto es presentarlo como
  **descripción del caso 2023**, no como "la costa responde a ENSO con r = 0.2".
- **La Amazonía sigue arrastrando el efecto de 2025**, el año anómalamente bajo.
  Su fase fría (+0.51) está dominada por 2022, y la neutral (−0.20) por 2025.
  El mismo problema del análisis sin estratificar.
- **Los límites de Costa y Andes son provisionales** por lo del muestreo grueso
  (sección 3.1).

Lo que sí queda establecido, y es bastante:

> Estratificar por región cambia el resultado de "no hay señal" a "hay dos
> señales de signo opuesto que se cancelaban". Eso justifica por sí solo repetir
> todo el análisis con una ventana temporal más larga.

---

## 6. Cómo reproducirlo

```bash
# Estratificación y series mensuales por región
python3 regionalizar_peru.py --umbral 1000 --salida analisis_regiones

# Sensibilidad
python3 regionalizar_peru.py --umbral 500  --salida analisis_regiones/sensibilidad_500m
python3 regionalizar_peru.py --umbral 2000 --salida analisis_regiones/sensibilidad_2000m

# Cruce con ENSO, región por región
for r in costa andes amazonia; do
  python3 "oni+wwlln.py" --wwlln analisis_regiones/wwlln_2021_2025_mensual_$r.csv \
                         --indice rnino12_2021_2025_tidy.csv \
                         --nombre-indice "Nino 1+2" \
                         --salida analisis_regiones/enso_$r
done

# Figuras
python3 graficar_regiones.py --entrada analisis_regiones
```

### Refinar el muestreo (recomendado antes de publicar)

La forma más simple de quitar el sesgo de la sección 3.1 **no necesita bajar
ningún archivo ni instalar GDAL**. `muestrear_elevacion.py` pide la misma malla
de elevación a la API de OpenTopoData, pero mucho más densa:

```bash
python3 muestrear_elevacion.py                     # ~2 min, 0.25° lat x 0.1° lon
python3 regionalizar_peru.py --perfiles recursos/perfiles_etopo1_peru_denso.csv \
                             --umbral 1000 --salida analisis_regiones_denso
python3 graficar_regiones.py --entrada analisis_regiones_denso
```

Pasa de 135 puntos a 11,421, y la resolución del límite de ~50 km a ~11 km. Es
reanudable: si se corta, al volver a correrlo sigue donde quedó.

Para el flanco occidental andino, que es donde el muestreo grueso más se
equivoca, conviene además subir de ETOPO1 (1.8 km) a SRTM:

```bash
python3 muestrear_elevacion.py --dataset srtm90m --paso-lon 0.05 \
                               --salida recursos/perfiles_srtm90m_peru.csv
```

Esto debería subir la costa de 8.5% a ~12% del área. **No espero que cambie el
resultado de la sección 4.2** — la inversión de signo es demasiado grande para
depender de dónde exactamente pongas la línea — pero hay que comprobarlo.

### Con un archivo DEM propio

Si ya tienes o prefieres bajar un GeoTIFF/NetCDF, `regionalizar_peru.py` también
lo acepta directo (necesita `rioxarray` y `xarray`):

```bash
python3 regionalizar_peru.py --dem ruta/al/etopo.tif --umbral 1000 \
                             --salida analisis_regiones_dem
```

Fuente: ETOPO 2022, NOAA NCEI —
https://www.ncei.noaa.gov/products/etopo-global-relief-model

---

## 7. Archivos

| Archivo | Contenido |
|---|---|
| `regionalizar_peru.py` | Clasificación y series mensuales por región |
| `graficar_regiones.py` | Las cuatro figuras |
| `recursos/perfiles_etopo1_peru.csv` | Los 135 puntos de elevación muestreados |
| `analisis_regiones/limites_regiones.csv` | Las curvas `lon_w(lat)` y `lon_e(lat)` |
| `analisis_regiones/areas_por_region.csv` | Área de cada región dentro del Perú |
| `analisis_regiones/wwlln_mensual_por_region.csv` | Serie mensual, las tres regiones juntas |
| `analisis_regiones/wwlln_2021_2025_mensual_{costa,andes,amazonia}.csv` | Una serie por región, lista para `oni+wwlln.py` |
| `analisis_regiones/resumen_por_region.csv` | Totales, área y densidad por región |
| `analisis_regiones/enso_{costa,andes,amazonia}/` | Cruce con Niño 1+2 de cada región |
| `analisis_regiones/sensibilidad_{500m,2000m}/` | Lo mismo con los otros umbrales |
| `analisis_regiones/mapa_regiones.png` | Mapa de las tres regiones y las curvas límite |
| `analisis_regiones/ciclo_anual_por_region.png` | Climatología mensual, escala log |
| `analisis_regiones/serie_costa.png` | Serie de la costa con 2023 destacado |
| `analisis_regiones/anomalia_por_fase_region.png` | La inversión de signo, en una figura |
