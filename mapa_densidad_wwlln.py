#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mapa_densidad_wwlln.py
======================
Mapas de densidad espacial de rayos WWLLN. Genérico: sirve para cualquier año,
en modo anual, mensual o ambos, todo por parámetros.

Antes había tres copias de este script con las rutas escritas a mano, y dos de
ellas apuntaban al parquet equivocado (los mapas de 2025 salieron del archivo
contaminado que mezclaba `.mat` con `.loc`, y el script dentro de `mapas_2024/`
seguía leyendo el parquet de 2021). Esta versión recibe todo por argumento y
además valida que el parquet corresponda al año que le pides.

Uso
---
    # Mapa anual
    python3 mapa_densidad_wwlln.py --entrada peru_wwlln_2025_FINAL.parquet \
                                   --anio 2025 --modo anual --salida mapas_2025

    # Los doce mapas mensuales
    python3 mapa_densidad_wwlln.py --entrada peru_wwlln_2025_FINAL.parquet \
                                   --anio 2025 --modo mensual \
                                   --salida mapas_mensuales_2025

    # Ambos, en densidad por km2 y recortado al territorio peruano
    python3 mapa_densidad_wwlln.py --entrada peru_wwlln_2024_limpio.parquet \
                                   --anio 2024 --modo ambos \
                                   --densidad --recortar-peru

Sobre el dominio
----------------
La caja 19°S-1°N / 82-68°W tiene 3.40 millones de km2: es 2.6 veces el Perú
continental, e incluye Ecuador, Colombia, Brasil, Bolivia y bastante Pacífico.
Por eso el título dice "dominio", no "Perú", salvo que uses --recortar-peru.

Sobre --densidad
----------------
Convierte el conteo por celda a rayos/km2. Las celdas de una grilla lat/lon NO
tienen área constante, así que la división se hace celda por celda con el área
real:

    A = R^2 * dlambda * (sin(phi2) - sin(phi1))

Es lo que hace falta para comparar con literatura publicada; el conteo crudo por
celda no es comparable con nada.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import cartopy.crs as ccrs
import cartopy.feature as cfeature

MESES = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo",
         6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre",
         10: "Octubre", 11: "Noviembre", 12: "Diciembre"}

R_TIERRA = 6371.0088  # km

# Cartografía de respaldo (Natural Earth 1:110m) para máquinas sin salida a
# internet, donde cartopy no puede descargar la suya.
RESPALDO = (Path(__file__).resolve().parent / "recursos"
            / "naturalearth_lowres" / "naturalearth_lowres.shp")


# ----------------------------------------------------------------------
# Cartografía
# ----------------------------------------------------------------------
def cartopy_disponible(resolucion: str) -> bool:
    try:
        f = cfeature.NaturalEarthFeature("physical", "coastline", resolucion)
        next(iter(f.geometries()))
        return True
    except Exception:
        return False


def geometrias_respaldo():
    import shapefile
    from shapely.geometry import shape
    r = shapefile.Reader(str(RESPALDO))
    # campos: pop_est, continent, name, iso_a3, gdp_md_est
    return [(sr.record[2], shape(sr.shape.__geo_interface__))
            for sr in r.iterShapeRecords()]


def poner_cartografia(ax, resolucion: str, usar_cartopy: bool):
    if usar_cartopy:
        ax.add_feature(cfeature.LAND.with_scale(resolucion),
                       facecolor="lightgray", alpha=0.5)
        ax.add_feature(cfeature.OCEAN.with_scale(resolucion),
                       facecolor="aliceblue", alpha=0.7)
        ax.add_feature(cfeature.COASTLINE.with_scale(resolucion), linewidth=0.8)
        ax.add_feature(cfeature.BORDERS.with_scale(resolucion), linewidth=1.0)
        return
    # Respaldo 1:110m: solo el contorno, sin rellenar tierra ni oceano. Con esta
    # resolucion el poligono no calza con la costa real y el relleno deja una
    # franja gris falsa a lo largo del litoral.
    from cartopy.feature import ShapelyFeature
    ax.add_feature(ShapelyFeature([g for _, g in geometrias_respaldo()],
                                  ccrs.PlateCarree(), facecolor="none",
                                  edgecolor="black", linewidth=0.9))


def poligono_peru(resolucion: str, usar_cartopy: bool):
    if usar_cartopy:
        import cartopy.io.shapereader as shpreader
        from shapely.ops import unary_union
        ruta = shpreader.natural_earth(resolution=resolucion,
                                       category="cultural",
                                       name="admin_0_countries")
        geoms = [rec.geometry for rec in shpreader.Reader(ruta).records()
                 if "Peru" in (str(rec.attributes.get("ADMIN")),
                               str(rec.attributes.get("NAME")))]
        if geoms:
            return unary_union(geoms)
    for nombre, geom in geometrias_respaldo():
        if nombre == "Peru":
            return geom
    raise RuntimeError("No se encontró el polígono del Perú")


# ----------------------------------------------------------------------
# Grilla
# ----------------------------------------------------------------------
def areas_celdas(lon_edges: np.ndarray, lat_edges: np.ndarray) -> np.ndarray:
    """Área en km2 de cada celda. Devuelve forma (n_lat, n_lon)."""
    dlon = np.radians(np.diff(lon_edges))
    dsin = np.diff(np.sin(np.radians(lat_edges)))
    return (R_TIERRA ** 2) * np.outer(dsin, dlon)


def mascara_fuera_peru(lon_edges, lat_edges, geom) -> np.ndarray:
    """True donde el centro de la celda cae FUERA del Perú."""
    from shapely.geometry import Point
    from shapely.prepared import prep
    p = prep(geom)
    clon = 0.5 * (lon_edges[:-1] + lon_edges[1:])
    clat = 0.5 * (lat_edges[:-1] + lat_edges[1:])
    fuera = np.ones((len(clat), len(clon)), dtype=bool)
    for i, la in enumerate(clat):
        for j, lo in enumerate(clon):
            if p.contains(Point(lo, la)):
                fuera[i, j] = False
    return fuera


# ----------------------------------------------------------------------
def dibujar(datos, lon_edges, lat_edges, titulo, ruta, vmax, etiqueta_barra,
            resolucion, usar_cartopy, extent):
    plt.figure(figsize=(8, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent(extent, crs=ccrs.PlateCarree())

    poner_cartografia(ax, resolucion, usar_cartopy)

    gl = ax.gridlines(draw_labels=True, linewidth=0.4, color="gray",
                      alpha=0.5, linestyle="--")
    gl.top_labels = False
    gl.right_labels = False

    lon_grid, lat_grid = np.meshgrid(lon_edges, lat_edges)
    plot = np.where(datos > 0, datos, np.nan)
    finitos = plot[np.isfinite(plot)]
    vmin = finitos.min() if finitos.size else 1e-9

    malla = ax.pcolormesh(lon_grid, lat_grid, plot, cmap="turbo",
                          norm=colors.LogNorm(vmin=vmin, vmax=vmax),
                          transform=ccrs.PlateCarree())

    cbar = plt.colorbar(malla, ax=ax, orientation="vertical", pad=0.03,
                        shrink=0.75)
    cbar.set_label(etiqueta_barra, fontsize=11)

    ax.set_title(titulo, fontsize=13)
    plt.tight_layout()
    plt.savefig(ruta, dpi=300)
    plt.close()


def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    ap.add_argument("--entrada", required=True, type=Path)
    ap.add_argument("--anio", required=True, type=int)
    ap.add_argument("--salida", type=Path, default=None)
    ap.add_argument("--modo", default="ambos",
                    choices=["anual", "mensual", "ambos"])
    ap.add_argument("--densidad", action="store_true",
                    help="rayos/km2 en vez de conteo crudo por celda")
    ap.add_argument("--recortar-peru", action="store_true",
                    help="enmascara las celdas fuera del territorio peruano")
    ap.add_argument("--resolucion", default="10m", choices=["10m", "50m", "110m"])
    ap.add_argument("--lon", nargs=2, type=float, default=[-82.0, -68.0])
    ap.add_argument("--lat", nargs=2, type=float, default=[-19.0, 1.0])
    ap.add_argument("--bins", nargs=2, type=int, default=[280, 300],
                    help="numero de celdas en lon y en lat")
    args = ap.parse_args()

    lon_min, lon_max = args.lon
    lat_min, lat_max = args.lat
    n_lon, n_lat = args.bins
    extent = [lon_min, lon_max, lat_min, lat_max]

    usar_cartopy = cartopy_disponible(args.resolucion)
    if not usar_cartopy:
        if not RESPALDO.exists():
            raise SystemExit(
                f"cartopy no puede descargar su cartografía y tampoco existe el "
                f"respaldo {RESPALDO}. Conéctate a internet y vuelve a correr.")
        print(f"[!] cartopy no pudo bajar Natural Earth {args.resolucion}; se usa "
              f"el respaldo local 1:110m.")
        print("    En una máquina con internet la costa y las fronteras saldrán "
              "a mayor resolución.")

    print(f"Leyendo {args.entrada} ...")
    df = pd.read_parquet(args.entrada, columns=["lat", "lon", "datetime"])
    anios = sorted(df["datetime"].dt.year.unique())
    if anios != [args.anio]:
        raise SystemExit(f"[!] El parquet contiene los años {anios}, pero pediste "
                         f"--anio {args.anio}. Revisa --entrada.")
    df["month"] = df["datetime"].dt.month
    dias = df["datetime"].dt.normalize().nunique()
    print(f"  {len(df):,} eventos, {dias} días con datos")

    salida = args.salida or Path(f"mapas_{args.anio}")
    salida.mkdir(parents=True, exist_ok=True)

    lon_edges = np.linspace(lon_min, lon_max, n_lon + 1)
    lat_edges = np.linspace(lat_min, lat_max, n_lat + 1)
    areas = areas_celdas(lon_edges, lat_edges)

    fuera = None
    if args.recortar_peru:
        print("Construyendo la máscara del territorio peruano ...")
        fuera = mascara_fuera_peru(lon_edges, lat_edges,
                                   poligono_peru(args.resolucion, usar_cartopy))
        dentro_km2 = areas[~fuera].sum()
        print(f"  {(~fuera).sum():,} de {fuera.size:,} celdas dentro "
              f"({dentro_km2/1e6:.2f} millones de km2)")

    ambito = ("Perú" if args.recortar_peru else
              f"dominio {abs(lat_min):.0f}°S-{lat_max:.0f}°N / "
              f"{abs(lon_min):.0f}°W-{abs(lon_max):.0f}°W")
    etiqueta = ("Rayos WWLLN por km$^2$" if args.densidad
                else "Número de eventos WWLLN por celda")

    def conteo_de(sub: pd.DataFrame) -> np.ndarray:
        c, _, _ = np.histogram2d(sub["lon"], sub["lat"], bins=[n_lon, n_lat],
                                 range=[[lon_min, lon_max], [lat_min, lat_max]])
        return c.T

    def para_plot(c: np.ndarray) -> np.ndarray:
        d = c / areas if args.densidad else c.astype(float)
        return np.where(fuera, np.nan, d) if fuera is not None else d

    if args.modo in ("anual", "ambos"):
        c = conteo_de(df)
        n = int(c[~fuera].sum()) if fuera is not None else len(df)
        d = para_plot(c)
        titulo = (f"Densidad espacial de rayos WWLLN — {ambito} — {args.anio}\n"
                  f"Total de eventos: {n:,}")
        ruta = salida / f"mapa_densidad_wwlln_peru_{args.anio}.png"
        dibujar(d, lon_edges, lat_edges, titulo, ruta, np.nanmax(d), etiqueta,
                args.resolucion, usar_cartopy, extent)
        print(f"  escrito {ruta.name}  (total {n:,})")

    if args.modo in ("mensual", "ambos"):
        conteos = {m: conteo_de(df[df["month"] == m]) for m in range(1, 13)}
        plots = {m: para_plot(c) for m, c in conteos.items()}
        # Escala de color común a los doce meses para que sean comparables
        vmax = max(np.nanmax(p) for p in plots.values())
        print(f"Escala común de los 12 meses, máximo = {vmax:,.4g}")
        for m in range(1, 13):
            n = (int(conteos[m][~fuera].sum()) if fuera is not None
                 else int(conteos[m].sum()))
            titulo = (f"Densidad espacial de rayos WWLLN — {ambito}\n"
                      f"{MESES[m]} {args.anio} | Eventos: {n:,}")
            ruta = salida / (f"mapa_densidad_wwlln_peru_{args.anio}_"
                             f"{m:02d}_{MESES[m]}.png")
            dibujar(plots[m], lon_edges, lat_edges, titulo, ruta, vmax,
                    etiqueta, args.resolucion, usar_cartopy, extent)
            print(f"  {MESES[m]:<11s} {n:>9,} eventos -> {ruta.name}")

    print(f"\nListo. Salida en: {salida.resolve()}")


if __name__ == "__main__":
    main()
