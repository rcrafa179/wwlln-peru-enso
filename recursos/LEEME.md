# recursos/

`naturalearth_lowres/` — cartografía Natural Earth 1:110m (fronteras de países),
extraída del paquete `geopandas==0.14.4`. Dominio público (Natural Earth).

La usa `mapa_densidad_wwlln.py` **solo como respaldo**, cuando la máquina no
tiene salida a internet y cartopy no puede descargar su propia cartografía a
10m/50m. En tu Mac, con internet, cartopy usa la de 10m y esta carpeta se
ignora.

---

`perfiles_etopo1_peru.csv` — 10 transectos este-oeste de elevación ETOPO1
(NOAA/NCEI, 1 arcmin ≈ 1.8 km), muestreados cada 0.5° de longitud vía la API
pública de OpenTopoData (https://www.opentopodata.org). 141 puntos en total.

Los usa `regionalizar_peru.py` para construir las curvas que separan
Costa / Andes / Amazonía. Es la versión de baja resolución: el mismo script
acepta un DEM completo con `--dem`, que es lo que conviene usar para la versión
final. Ver `REGIONES_LEEME.md` en la raíz.
