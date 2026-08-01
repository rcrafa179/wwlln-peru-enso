# Mapas de 2025 — regenerados, cartografía provisional

## Qué pasó

Los mapas anteriores de 2025 salieron de `peru_wwlln_2025_limpio.parquet`, el
archivo contaminado que mezclaba `.mat` con `.loc` y contaba cada rayo dos o
tres veces. Decían **9,313,334** eventos en el año y **1,299,776** en enero.

Los de esta carpeta salen de `peru_wwlln_2025_FINAL.parquet`: **6,214,356**
eventos, 364 días. Coinciden con `analisis_2025/` y con la serie mensual que
alimenta el cruce ENSO.

Los viejos quedaron en `_obsoleto_2025/`.

## Ojo: la costa y las fronteras están a baja resolución

Se generaron en una máquina sin salida a internet, así que cartopy no pudo bajar
su cartografía de 10m y se usó el respaldo local de 1:110m que está en
`recursos/`. El **dato de rayos es correcto**; lo que se ve tosco es el contorno
de la costa y las fronteras, y no calza con los mapas de 2021-2024.

**Antes de presentar, regenéralos en tu Mac** (ahí cartopy sí baja la de 10m):

```bash
cd /Users/rafaelruales/Downloads/WWLLN

python3 mapa_densidad_wwlln.py --entrada peru_wwlln_2025_FINAL.parquet \
                               --anio 2025 --modo anual --salida mapas_2025

python3 mapa_densidad_wwlln.py --entrada peru_wwlln_2025_FINAL.parquet \
                               --anio 2025 --modo mensual \
                               --salida mapas_mensuales_2025
```

## Un cambio en el título

Antes decía "en Perú". La caja del mapa (19°S-1°N / 82°W-68°W) tiene 3.40
millones de km², **2.6 veces el Perú continental**, e incluye Ecuador, Colombia,
Brasil, Bolivia y bastante Pacífico — los focos más intensos del mapa de 2024
están en territorio brasileño. Ahora el título dice "dominio 19°S-1°N /
82°W-68°W", que es lo que realmente se está mostrando.

Si quieres el mapa recortado de verdad al territorio peruano, el script ya lo
hace:

```bash
python3 mapa_densidad_wwlln.py --entrada peru_wwlln_2025_FINAL.parquet \
                               --anio 2025 --modo ambos --recortar-peru --densidad
```

`--densidad` además convierte el conteo por celda a rayos/km², que es lo que
hace falta para comparar con literatura publicada (las celdas de una grilla
lat/lon no tienen área constante; el script divide celda por celda por su área
real).
