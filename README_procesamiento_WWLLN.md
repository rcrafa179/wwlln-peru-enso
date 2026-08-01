# Pipeline de procesamiento WWLLN - Perú

Guía para correr tú mismo, en tu máquina, todo el proceso que ya hicimos juntos
(leer los `.mat` crudos del disco externo, filtrarlos a Perú, limpiarlos y
analizarlos). No necesitas reorganizar ninguna carpeta: los scripts buscan los
archivos donde sea que estén.

## 1. Qué hay en la carpeta `WWLLN` de Descargas

| Archivo | Para qué sirve |
|---|---|
| `Leer_WWLLN_recursivo.py` | Lee `.mat`/`.loc`, filtra a Perú, guarda un `.parquet`. Busca en subcarpetas automáticamente. |
| `Leer_WWLLN.py` | Versión original (solo lee la carpeta que le indiques, sin bajar a subcarpetas). |
| `duplicados_parquet.py` | Diagnóstico: cuenta cuántas filas duplicadas hay en un parquet. |
| `limpiar_parquet.py` | Elimina duplicados de un parquet (se queda con la versión que trae energía). |
| `revisar_WWLL.py` | Inspección rápida de un parquet (filas, columnas, rango de fechas, nulos). |
| `analisis_anual_wwlln.py` | Análisis mensual/diario/horario/energía de un año. Recibe `--entrada`, `--anio` y `--salida`. |
| `mapa_densidad_wwlln.py` | Mapas de densidad espacial, anuales y mensuales, para cualquier año. Recibe `--entrada`, `--anio`, `--modo`, y opcionalmente `--densidad` y `--recortar-peru`. |
| `Test_datos.py` | Para revisar si un `.mat` puntual está dañado. |
| `descargar_oni.py` | Baja índices ENSO del CPC/NOAA (ONI, Niño 1+2, ...). |
| `regionalizar_peru.py` | Separa los rayos en Costa / Andes / Amazonía por elevación y arma una serie mensual por región. Ver `REGIONES_LEEME.md`. |
| `graficar_regiones.py` | Figuras del análisis por región. |
| `muestrear_elevacion.py` | Baja una malla densa de elevación por API para refinar los límites de región. No necesita GDAL ni ningún archivo. |
| `construir_serie_mensual.py` | Une los CSV mensuales de cada año en la serie 2021-2025 que consume el cruce con ONI. |
| `oni+wwlln.py` | Cruza la serie WWLLN mensual con el ONI y calcula anomalías por fase ENSO. |
| `graficar_enso.py` | Gráficas del cruce WWLLN × ONI. |

Los `.parquet` que ya te dejé (`peru_wwlln_2021_limpio.parquet` ... `2025`) son
el resultado final de correr este pipeline sobre todos los años.

## 2. Requisitos (instalar una sola vez)

```bash
pip install pandas scipy pyarrow matplotlib cartopy
```

Si `cartopy` da problemas al instalar (es común en Mac/Windows), instálalo con
conda en vez de pip:

```bash
conda install -c conda-forge cartopy
```

No necesitas `cartopy` para leer, limpiar o analizar los datos — solo para el
mapa de densidad.

## 3. Estructura de datos (tal como está hoy, no hace falta tocarla)

- `WWLLN/2021`, `2021 2` ... `2021 8` → fragmentos del año 2021 (quedaron así
  porque el zip original venía en 8 partes). Todos tienen `Mat/AE*.mat`.
- `WWLLN/2022`, `2022 2` ... `2022 9` → igual, 9 fragmentos.
- `WWLLN/2023/Mat`, `WWLLN/2024/Mat` → un único folder por año, sin fragmentar.
- `WWLLN/2025/MATfiles` → los `.mat` de 2025 (ignora `AEfiles` y `Afiles`, son
  el mismo dato en otros formatos — ver sección 5).
- `WWLLN/Datos corruptos` → días marcados aparte, revisar antes de usar.

`Leer_WWLLN_recursivo.py` acepta patrones con comodín, así que puedes apuntar
directo a `2021*` y te toma las 8 subcarpetas de una sola vez.

## 4. Pipeline paso a paso

### 4.1 Leer y filtrar a Perú

```bash
cd /Users/rafaelruales/Downloads/WWLLN

# Un año fragmentado (usa comillas y el comodín *):
python3 Leer_WWLLN_recursivo.py "/Volumes/TOSHIBA_EXT/WWLLN/2021*" ./peru_wwlln_2021.parquet --workers 4

# Un año en una sola carpeta:
python3 Leer_WWLLN_recursivo.py "/Volumes/TOSHIBA_EXT/WWLLN/2023" ./peru_wwlln_2023.parquet --workers 4

# 2025 (usa solo MATfiles, no mezcles con AEfiles/Afiles):
python3 Leer_WWLLN_recursivo.py "/Volumes/TOSHIBA_EXT/WWLLN/2025/MATfiles" ./peru_wwlln_2025.parquet --workers 4
```

`--workers` = núcleos a usar en paralelo (pon `--workers 6` si tu Mac tiene
más núcleos, así corre más rápido). En tu propia máquina, leyendo del disco
externo conectado directo por USB, esto va a ser mucho más rápido que cuando
lo corrí yo en el sandbox (ahí tardaba ~25s por cada 40 archivos por la
latencia de red; en tu máquina debería ser cuestión de minutos para un año
completo, no de horas).

### 4.2 Revisar duplicados (opcional pero recomendado)

```bash
python3 duplicados_parquet.py
```

Antes de correrlo, edita la línea `path = "..."` del script para que apunte
al parquet que acabas de generar.

### 4.3 Limpiar duplicados

```bash
python3 limpiar_parquet.py
```

Edita `entrada` y `salida` al inicio del script. Esto te deja el
`_limpio.parquet` final, que es el que debes usar para análisis.

### 4.4 Inspeccionar el resultado

```bash
python3 revisar_WWLL.py
```

Edita la ruta `path` para apuntar al `_limpio.parquet`. Te muestra filas,
columnas, rango de fechas y valores nulos — úsalo siempre como chequeo final
antes de analizar.

### 4.5 Análisis mensual / anual

Para 2021-2024 ya te dejé los resultados en `analisis_2021` ... `analisis_2024`
(CSV diario/mensual/horario/energía + 4 gráficas + un texto interpretativo,
igual que ya tenías para 2025). Para un año nuevo, usa el script genérico:

```bash
python3 analisis_anual_wwlln.py --entrada peru_wwlln_2026_limpio.parquet --anio 2026 --salida analisis_2026
```

No necesitas editar nada dentro del script, todo se pasa por parámetro.

### 4.6 Mapas

Todo por parámetros, sin editar el script:

```bash
# Mapa anual
python3 mapa_densidad_wwlln.py --entrada peru_wwlln_2025_FINAL.parquet \
                               --anio 2025 --modo anual --salida mapas_2025

# Los doce mapas mensuales (escala de color común, para que sean comparables)
python3 mapa_densidad_wwlln.py --entrada peru_wwlln_2025_FINAL.parquet \
                               --anio 2025 --modo mensual \
                               --salida mapas_mensuales_2025

# En rayos/km2 y recortado al territorio peruano
python3 mapa_densidad_wwlln.py --entrada peru_wwlln_2024_limpio.parquet \
                               --anio 2024 --modo ambos --densidad --recortar-peru
```

El script **valida que el parquet corresponda al `--anio` que le pides** y aborta
si no. Esa comprobación no existía antes, y por eso el script que estaba dentro
de `mapas_2024/` llevaba tiempo leyendo el parquet de 2021 sin que nadie lo
notara.

**Sobre el título.** La caja 19°S-1°N / 82°W-68°W tiene 3.40 millones de km²,
**2.6 veces el Perú continental**: incluye Ecuador, Colombia, Brasil, Bolivia y
bastante Pacífico. Por eso el título ya no dice "en Perú" sino "dominio 19°S-1°N
/ 82°W-68°W", salvo que uses `--recortar-peru`.

**Sobre `--densidad`.** Convierte el conteo por celda a rayos/km². Las celdas de
una grilla lat/lon no tienen área constante, así que la división se hace celda
por celda con `A = R² · Δλ · (sin φ₂ − sin φ₁)`. Sin esto los números no son
comparables con nada publicado.

**Si no hay internet**, cartopy no puede descargar su cartografía y el script cae
automáticamente al respaldo 1:110m de `recursos/`. El dato de rayos sale igual de
bien, pero la costa y las fronteras salen toscas: vuelve a correrlo en una
máquina con conexión antes de usar los mapas en una presentación.

### 4.7 Cruce con ENSO (ONI, Niño 1+2, ...)

Pipeline aparte, de cuatro pasos. Los tres scripts son genéricos respecto al
índice. Resultados en `analisis_ENSO/` (ONI) y `analisis_ENSO_nino12/`
(Niño 1+2).

**Para Perú usa Niño 1+2, no el ONI.** El ONI mide Niño 3.4 (Pacífico central);
el Niño costero peruano se ve en Niño 1+2 (0-10°S, 90-80°W) y puede ocurrir sin
que el ONI se mueva. En 2021-2025 los dos índices correlacionan r = 0.70 y
difieren de fase en 23 de 60 meses.

```bash
# 1. Bajar el índice del CPC/NOAA
python3 descargar_oni.py --indice nino12 --desde 2021 --hasta 2025   # Niño 1+2 (ERSSTv5)
python3 descargar_oni.py --indice rnino12 --desde 2021 --hasta 2025  # Niño 1+2 relativo (OISST)
python3 descargar_oni.py --indice oni --desde 2021 --hasta 2025      # ONI, comportamiento previo

# 2. Unir los CSV mensuales de cada año en una sola serie
python3 construir_serie_mensual.py --base . --salida wwlln_2021_2025_mensual.csv

# 3. Cruzar WWLLN con el índice
python3 "oni+wwlln.py" --wwlln wwlln_2021_2025_mensual.csv \
                       --indice nino12_2021_2025_tidy.csv \
                       --nombre-indice "Nino 1+2" \
                       --salida ./analisis_ENSO_nino12

# 4. Graficar
python3 graficar_enso.py --entrada analisis_ENSO_nino12/wwlln_indice_mensual.csv \
                         --salida analisis_ENSO_nino12 \
                         --nombre-indice "Niño 1+2" \
                         --umbral-frio -1.0 --umbral-calido 0.4
```

Índices soportados por `descargar_oni.py`: `oni`, `roni`, `nino12`, `nino3`,
`nino34`, `nino4` (ERSSTv5 crudo) y `rnino12`, `rnino3`, `rnino34`, `rnino4`
(versión relativa OISSTv2.1, a la que el CPC le resta la TSM media tropical).
Las variantes mensuales se convierten aquí a media móvil de 3 meses centrada,
para quedar en la misma convención estacional que el ONI.

**Umbrales.** Para `nino12`/`rnino12` el default son los del **ICEN** del
ENFEN/IGP, que son asimétricos (frío ≤ −1.0 °C, cálido ≥ +0.4 °C), porque
Niño 1+2 tiene mucha más varianza que Niño 3.4. Aplicarle el ±0.5 del ONI sería
un error. Se pueden cambiar con `--umbral-frio` / `--umbral-calido`. El CSV de
salida trae además la columna `categoria` con la escala completa del ICEN
(débil / moderada / fuerte / extraordinaria).

**Estadísticos que salen del paso 3:** además del resumen por fase, ahora se
calculan el z logarítmico (los conteos de rayos son multiplicativos), el n
efectivo de Bretherton (corrige por autocorrelación mensual: en esta serie da
~28 de 60 meses nominales), las correlaciones con rezago de 0 a 6 meses, y la
estratificación por temporada seca/lluviosa.

Si la máquina no tiene salida a internet, baja el `.ascii`/`.txt` a mano desde
la URL que imprime el error y pásalo con `--local`. En la carpeta quedó
`rel_mthsst9120_cache_2020_2026.txt`, que es un recorte 2020-2026 del archivo
relativo del CPC, usable con `--indice rnino12 --local`.

El paso 2 es el que faltaba: `oni+wwlln.py` esperaba un
`wwlln_2021_2025_mensual.csv` producido por un `procesar_wwlln.py` que nunca
existió en la carpeta. `construir_serie_mensual.py` lo arma a partir de los
`analisis_YYYY/analisis_mensual_wwlln_peru_YYYY.csv` que ya tienes.

**Normalización usada:** como algunos meses tienen días faltantes, el conteo se
extrapola a mes completo (`n_rayos_norm = n_rayos / días_con_datos ×
días_del_mes`), y `oni+wwlln.py` descarta por defecto los meses con cobertura
< 80% (`--cobertura-min`). Con eso quedan 57 de 60 meses; se caen feb, mar y
abr de 2025, que tienen entre 45% y 57% de días.

**Asignación estacional:** cada trimestre del ONI se asigna a su mes central
(DJF→enero, JFM→febrero, ... NDJ→diciembre), por eso `season_idx` coincide
con el número de mes y el cruce es directo.

### 4.8 Estratificación por región (Costa / Andes / Amazonía)

Separa los rayos por elevación, no por bandas de longitud (los Andes cruzan el
Perú en diagonal). El método completo está en **`REGIONES_LEEME.md`**.

```bash
python3 regionalizar_peru.py --umbral 1000 --salida analisis_regiones

for r in costa andes amazonia; do
  python3 "oni+wwlln.py" --wwlln analisis_regiones/wwlln_2021_2025_mensual_$r.csv \
                         --indice rnino12_2021_2025_tidy.csv \
                         --nombre-indice "Nino 1+2" \
                         --salida analisis_regiones/enso_$r
done

python3 graficar_regiones.py --entrada analisis_regiones
```

Aquí está el resultado más interesante de todo el trabajo: **la respuesta a
ENSO cambia de signo entre la costa (positiva) y la Amazonía (negativa)**, y por
eso el promedio de todo el país daba cero.

## 5. Cosas que aprendí procesando 2021-2025 (para que no te tropieces tú)

1. **Usa siempre `.mat`, nunca mezcles con `.loc`.** En `Uncompressed_DATA`
   tienes `A*.loc`, `AE*.loc` y `AE*.mat` del mismo día — son el mismo rayo en
   tres formatos. Si el script los lee todos juntos, cuenta cada rayo 2-3
   veces, y `limpiar_parquet.py` no lo detecta porque los números de lat/lon
   quedan con precisión decimal ligeramente distinta entre formato texto
   (`.loc`) y binario (`.mat`). Esto es lo que pasó con
   `peru_wwlln_2025_limpio.parquet` (9,313,334 filas) comparado con
   `peru_wwlln_2025_FINAL.parquet`, que usa solo `.mat` y suma los días
   recuperados de "Datos corruptos" (**6,214,356 filas**, consistente con los
   demás años). Regla simple: apunta siempre a la carpeta/subcarpeta que solo
   tenga `.mat`.

   **El costo de no notarlo a tiempo.** Con los conteos inflados, 2025 aparecía
   como el año MÁS alto de la serie; con los correctos es el más bajo, y ese
   déficit es el hallazgo principal del trabajo. Los mapas de 2025 y la carpeta
   `resumenes_2025/` estuvieron un mes contradiciendo al resto del análisis
   antes de que saliera a la luz. Todo eso está en `_obsoleto_2025/`, con el
   detalle en su LEEME.

   **Una sola fuente por año.** Ya no existen `analisis_2025_corregido` ni
   parquets intermedios de 2025 sueltos en la raíz. Para cada año hay un
   parquet y una carpeta `analisis_YYYY`, y punto. Si vuelves a generar
   versiones intermedias, bórralas o muévelas apenas termines.

2. **`AE20250908.mat` está dañado de origen.** Lo confirmé en las tres copias
   que tienes (disco externo, `Downloads/WWLLN/MATfiles` y
   `Downloads/WWLLN/Uncompressed_DATA`): mismo tamaño de archivo, mismo error
   ("Did not read any bytes"). El header MATLAB es válido pero el bloque de
   datos comprimido está truncado. No se arregla copiándolo de nuevo; habría
   que volver a descargar ese día desde WWLLN si te interesa recuperarlo.

3. **"Datos corruptos" no estaba tan corrupta.** De los archivos reales ahí
   (ignora los que empiezan con `._`, son basura de macOS), 16 `.mat` se leen
   perfectamente y cubren 16 días que faltan por completo en el `MATfiles`
   principal de 2025 (sin traslape de fechas). Quedaron en
   `peru_wwlln_datoscorruptos_revision.parquet` — revísalos y decide si los
   incorporas a tu dataset de 2025.

4. **No hace falta mover ni renombrar nada en el disco.** Las carpetas
   fragmentadas (`2021 2`...`2021 8`) son solo un efecto de haber
   descomprimido 8 zips distintos en el mismo sitio. El script recursivo las
   lee todas igual sin que muevas un solo archivo.

## 6. Checklist para procesar un año nuevo (ej. 2026)

1. Confirma dónde quedaron los `.mat` de ese año (`find` o revisa en Finder).
2. `python3 Leer_WWLLN_recursivo.py "<ruta o patrón>" ./peru_wwlln_2026.parquet --workers 6`
3. `python3 duplicados_parquet.py` (edita la ruta) → revisa que los
   duplicados sean pocos o cero.
4. `python3 limpiar_parquet.py` (edita rutas) → obtén `_limpio.parquet`.
5. `python3 revisar_WWLL.py` (edita ruta) → confirma rango de fechas completo
   y sin sorpresas en nulos.
6. Corre `analisis_anual_wwlln.py` / `mapa_densidad_wwlln.py` sobre el `_limpio.parquet`.
