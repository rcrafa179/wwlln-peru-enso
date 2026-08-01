#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regionalizar_peru.py
====================
Clasifica cada rayo WWLLN en Costa / Andes / Amazonía y produce las series
mensuales por región.

Método (resumen; el detalle está en REGIONES_LEEME.md)
------------------------------------------------------
La separación es por ELEVACIÓN, no por bandas de longitud: los Andes cruzan el
Perú en diagonal, así que cortar por meridianos mete sierra en la costa al norte
y selva en la sierra al sur.

1. Se toma un perfil de elevación oeste→este para varias latitudes.
2. En cada perfil se buscan dos longitudes:
     lon_w = la longitud MÁS OCCIDENTAL con elevación >= umbral
     lon_e = la longitud MÁS ORIENTAL  con elevación >= umbral
   Es deliberadamente la ENVOLVENTE del terreno alto, no el primer cruce del
   umbral. Así los valles interandinos profundos (el Apurímac a 13°S baja a
   774 m entre dos macizos de 3300 y 3800 m) no parten la cordillera en dos.
3. Esas dos curvas se interpolan linealmente en latitud.
4. Cada rayo se clasifica por su longitud respecto a las curvas de su latitud:
     lon < lon_w(lat)            -> Costa
     lon_w(lat) <= lon <= lon_e(lat) -> Andes
     lon > lon_e(lat)            -> Amazonía
   y aparte se marca si cae dentro o fuera del territorio peruano.

Umbral por defecto: 1000 m, con sensibilidad a 500 y 2000 m (--umbral).

Dos fuentes de elevación
------------------------
  --perfiles recursos/perfiles_etopo1_peru.csv   (por defecto)
      10 transectos ETOPO1 muestreados cada 0.5° de longitud vía OpenTopoData.
      Resolución efectiva de los límites: ~25-50 km. Sirve para un preliminar.

  --dem ruta/al/dem.tif
      DEM completo (GeoTIFF o NetCDF). Los límites se derivan a la resolución
      del DEM. Es lo que hay que usar para la versión final.

Uso
---
    python3 regionalizar_peru.py --anios 2021 2022 2023 2024 2025 \
                                 --salida analisis_regiones

    python3 regionalizar_peru.py --anios 2025 --umbral 500 --salida pruebas/u500
"""

from __future__ import annotations

import argparse
import calendar
from pathlib import Path

import numpy as np
import pandas as pd

REGIONES = ["Costa", "Andes", "Amazonia"]

PARQUETS = {
    2021: "peru_wwlln_2021_limpio.parquet",
    2022: "peru_wwlln_2022_limpio.parquet",
    2023: "peru_wwlln_2023_limpio.parquet",
    2024: "peru_wwlln_2024_limpio.parquet",
    2025: "peru_wwlln_2025_FINAL.parquet",
}

RESPALDO_SHP = (Path(__file__).resolve().parent / "recursos"
                / "naturalearth_lowres" / "naturalearth_lowres.shp")


# ----------------------------------------------------------------------
# Límites de región a partir de perfiles de elevación
# ----------------------------------------------------------------------
def cruce(lon_a, ele_a, lon_b, ele_b, umbral):
    """Longitud donde el segmento a-b cruza el umbral, por interpolación lineal."""
    if ele_a == ele_b:
        return lon_a
    t = (umbral - ele_a) / (ele_b - ele_a)
    return lon_a + t * (lon_b - lon_a)


def limites_de_perfil(lons, eles, umbral):
    """Devuelve (lon_w, lon_e): envolvente del terreno con elevación >= umbral.

    lon_w = borde occidental del terreno alto
    lon_e = borde oriental
    Si el perfil nunca llega al umbral, devuelve (None, None).
    """
    orden = np.argsort(lons)
    lons, eles = np.asarray(lons)[orden], np.asarray(eles)[orden]
    altos = np.where(eles >= umbral)[0]
    if len(altos) == 0:
        return None, None

    i = altos[0]
    if i == 0:
        lon_w = lons[0]                       # ya empieza alto: borde del dominio
    else:
        lon_w = cruce(lons[i - 1], eles[i - 1], lons[i], eles[i], umbral)

    j = altos[-1]
    if j == len(lons) - 1:
        lon_e = lons[-1]                      # sigue alto al salir del dominio
    else:
        lon_e = cruce(lons[j], eles[j], lons[j + 1], eles[j + 1], umbral)

    return lon_w, lon_e


def limites_desde_perfiles(ruta: Path, umbral: float) -> pd.DataFrame:
    df = pd.read_csv(ruta)
    filas = []
    for lat, g in df.groupby("lat"):
        lw, le = limites_de_perfil(g["lon"].values, g["elev_m"].values, umbral)
        if lw is None:
            continue
        filas.append({"lat": lat, "lon_w": lw, "lon_e": le,
                      "n_puntos": len(g),
                      "lon_min": g["lon"].min(), "lon_max": g["lon"].max()})
    return pd.DataFrame(filas).sort_values("lat").reset_index(drop=True)


def limites_desde_dem(ruta: Path, umbral: float, paso_lat: float = 0.25) -> pd.DataFrame:
    """Igual que arriba pero recorriendo un DEM completo fila por fila."""
    import rioxarray  # noqa: F401
    import xarray as xr
    da = xr.open_dataarray(ruta) if ruta.suffix in (".nc", ".nc4") \
        else xr.open_dataarray(ruta, engine="rasterio").squeeze()
    ny = da.dims[-2]
    nx = da.dims[-1]
    lats = np.arange(-19, 1.0001, paso_lat)
    filas = []
    for la in lats:
        fila = da.sel({ny: la}, method="nearest")
        lw, le = limites_de_perfil(fila[nx].values, fila.values, umbral)
        if lw is None:
            continue
        filas.append({"lat": float(la), "lon_w": lw, "lon_e": le,
                      "n_puntos": len(fila),
                      "lon_min": float(fila[nx].min()),
                      "lon_max": float(fila[nx].max())})
    return pd.DataFrame(filas).sort_values("lat").reset_index(drop=True)


# ----------------------------------------------------------------------
# Clasificación
# ----------------------------------------------------------------------
def interpoladores(lim: pd.DataFrame):
    lat = lim["lat"].values
    return (lambda x: np.interp(x, lat, lim["lon_w"].values),
            lambda x: np.interp(x, lat, lim["lon_e"].values))


def clasificar(lat, lon, f_w, f_e) -> np.ndarray:
    lw, le = f_w(lat), f_e(lat)
    reg = np.full(len(lat), "Amazonia", dtype=object)
    reg[lon < lw] = "Costa"
    reg[(lon >= lw) & (lon <= le)] = "Andes"
    return reg


def cargar_peru():
    import shapefile
    from shapely.geometry import shape
    r = shapefile.Reader(str(RESPALDO_SHP))
    for sr in r.iterShapeRecords():
        if sr.record[2] == "Peru":
            return shape(sr.shape.__geo_interface__)
    raise RuntimeError("No se encontró el polígono del Perú")


def dentro_de_peru(lat, lon, geom) -> np.ndarray:
    """Máscara booleana. Se resuelve sobre una grilla de 0.05° y se asigna a cada
    rayo por su celda: 41 millones de tests punto-en-polígono serían inviables."""
    from shapely.geometry import Point
    from shapely.prepared import prep
    p = prep(geom)
    paso = 0.05
    glat = np.arange(-19, 1.0 + paso, paso)
    glon = np.arange(-82, -68 + paso, paso)
    malla = np.zeros((len(glat), len(glon)), dtype=bool)
    minx, miny, maxx, maxy = geom.bounds
    for i, la in enumerate(glat):
        if la < miny - paso or la > maxy + paso:
            continue
        for j, lo in enumerate(glon):
            if lo < minx - paso or lo > maxx + paso:
                continue
            if p.contains(Point(lo + paso / 2, la + paso / 2)):
                malla[i, j] = True
    ilat = np.clip(((lat + 19) / paso).astype(int), 0, len(glat) - 1)
    ilon = np.clip(((lon + 82) / paso).astype(int), 0, len(glon) - 1)
    return malla[ilat, ilon]


def areas_por_region(lim, geom, umbral) -> pd.DataFrame:
    """Área de cada región dentro del Perú. Sirve de validación: las
    proporciones conocidas son ~12% costa, ~28% sierra, ~60% selva."""
    from shapely.geometry import Point
    from shapely.prepared import prep
    R = 6371.0088
    p = prep(geom)
    f_w, f_e = interpoladores(lim)
    paso = 0.05
    filas = []
    for la in np.arange(-19, 1.0, paso):
        dsin = np.sin(np.radians(la + paso)) - np.sin(np.radians(la))
        a_celda = R ** 2 * np.radians(paso) * dsin
        lw, le = float(f_w(la)), float(f_e(la))
        for lo in np.arange(-82, -68, paso):
            if not p.contains(Point(lo + paso / 2, la + paso / 2)):
                continue
            reg = "Costa" if lo < lw else ("Andes" if lo <= le else "Amazonia")
            filas.append({"region": reg, "km2": a_celda})
    d = pd.DataFrame(filas).groupby("region")["km2"].sum().reset_index()
    d["pct"] = (100 * d["km2"] / d["km2"].sum()).round(1)
    return d


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    ap.add_argument("--anios", type=int, nargs="+",
                    default=[2021, 2022, 2023, 2024, 2025])
    ap.add_argument("--perfiles", type=Path,
                    default=Path("recursos/perfiles_etopo1_peru.csv"))
    ap.add_argument("--dem", type=Path, default=None,
                    help="DEM completo (GeoTIFF/NetCDF). Sustituye a --perfiles")
    ap.add_argument("--umbral", type=float, default=1000.0)
    ap.add_argument("--salida", type=Path, default=Path("analisis_regiones"))
    ap.add_argument("--solo-peru", action="store_true", default=True)
    ap.add_argument("--todo-el-dominio", dest="solo_peru", action="store_false")
    args = ap.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)

    print(f"Umbral de elevación: {args.umbral:.0f} m")
    if args.dem:
        print(f"Fuente de elevación: DEM completo {args.dem}")
        lim = limites_desde_dem(args.dem, args.umbral)
    else:
        print(f"Fuente de elevación: perfiles {args.perfiles}")
        lim = limites_desde_perfiles(args.perfiles, args.umbral)
    lim.to_csv(args.salida / "limites_regiones.csv", index=False)
    print("\nLímites derivados (longitud del borde occidental y oriental "
          "del terreno alto):")
    print(lim[["lat", "lon_w", "lon_e"]].round(2).to_string(index=False))

    f_w, f_e = interpoladores(lim)
    geom = cargar_peru()

    print("\nValidación por área (dentro del Perú):")
    areas = areas_por_region(lim, geom, args.umbral)
    areas.to_csv(args.salida / "areas_por_region.csv", index=False)
    print(areas.to_string(index=False))
    print(f"  total = {areas['km2'].sum():,.0f} km2 "
          f"(Perú continental real: 1,285,216 km2)")
    print("  referencia INEI: costa ~12%, sierra ~28%, selva ~60%")

    piezas = []
    for anio in args.anios:
        ruta = Path(PARQUETS[anio])
        if not ruta.exists():
            print(f"[!] falta {ruta}, se omite {anio}")
            continue
        print(f"\n{anio}: leyendo {ruta.name} ...")
        df = pd.read_parquet(ruta, columns=["lat", "lon", "datetime"])
        lat = df["lat"].to_numpy()
        lon = df["lon"].to_numpy()

        df["region"] = clasificar(lat, lon, f_w, f_e)
        df["en_peru"] = dentro_de_peru(lat, lon, geom)
        if args.solo_peru:
            n0 = len(df)
            df = df[df["en_peru"]]
            print(f"  {n0:,} eventos en el dominio -> {len(df):,} dentro del Perú "
                  f"({100*len(df)/n0:.1f}%)")
        df["mes"] = df["datetime"].dt.month
        df["dia"] = df["datetime"].dt.normalize()

        # Rejilla completa region x mes: si una region no registro ni un rayo
        # en un mes, eso es un CERO, no un dato ausente. En la costa pasa de
        # verdad (meses de invierno sin una sola descarga), y dejarlo como
        # ausente sesgaria la serie hacia arriba.
        idx = pd.MultiIndex.from_product([REGIONES, range(1, 13)],
                                         names=["region", "mes"])
        m = (df.groupby(["region", "mes"]).size()
               .reindex(idx, fill_value=0)
               .rename("n_rayos").reset_index())
        dias = df.groupby("mes")["dia"].nunique().rename("dias_con_datos")
        m = m.merge(dias, on="mes")
        m["anio"] = anio
        piezas.append(m)
        print("  " + df["region"].value_counts().to_string().replace("\n", "\n  "))

    if not piezas:
        print("Sin datos.")
        return

    ser = pd.concat(piezas, ignore_index=True)
    ser["dias_del_mes"] = [calendar.monthrange(a, m)[1]
                           for a, m in zip(ser["anio"], ser["mes"])]
    ser["cobertura"] = (ser["dias_con_datos"] / ser["dias_del_mes"]).round(4)
    ser["n_rayos_norm"] = (ser["n_rayos"] / ser["dias_con_datos"]
                           * ser["dias_del_mes"]).round(1)
    ser = ser[["anio", "mes", "region", "n_rayos", "dias_con_datos",
               "dias_del_mes", "cobertura", "n_rayos_norm"]]
    ser = ser.sort_values(["region", "anio", "mes"])
    ser.to_csv(args.salida / "wwlln_mensual_por_region.csv", index=False)

    # Una serie por región, en el formato que consume oni+wwlln.py
    for reg in REGIONES:
        sub = ser[ser["region"] == reg].drop(columns="region")
        sub.to_csv(args.salida / f"wwlln_2021_2025_mensual_{reg.lower()}.csv",
                   index=False)

    print("\n=== Totales por región ===")
    tot = ser.groupby("region")["n_rayos"].sum().reset_index()
    tot["pct"] = (100 * tot["n_rayos"] / tot["n_rayos"].sum()).round(2)
    tot = tot.merge(areas.rename(columns={"pct": "pct_area"}), on="region")
    tot["rayos_por_km2_por_anio"] = (tot["n_rayos"] / tot["km2"]
                                     / len(args.anios)).round(2)
    print(tot.to_string(index=False))
    tot.to_csv(args.salida / "resumen_por_region.csv", index=False)

    print(f"\nArchivos en: {args.salida.resolve()}")


if __name__ == "__main__":
    main()
