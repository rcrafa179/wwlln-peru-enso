#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
muestrear_elevacion.py
======================
Descarga una malla de elevación sobre el dominio peruano usando la API pública
de OpenTopoData, y la deja en el mismo formato de `recursos/perfiles_etopo1_peru.csv`
para que `regionalizar_peru.py` la consuma directo.

Para qué sirve
--------------
La versión que está en `recursos/` tiene solo 135 puntos (10 transectos cada
0.5° de longitud). Con eso los límites de región quedan con ~25-50 km de
incertidumbre, y la costa sale más estrecha de lo real (8.5% del área contra
~12%). Ver la sección 3.1 de REGIONES_LEEME.md.

Este script consigue el mismo dato a 0.1° de longitud (~11 km) sin que tengas
que bajar ni instalar nada: solo pandas y la librería estándar. No hace falta
GDAL, ni rioxarray, ni un GeoTIFF.

Cuánto tarda
------------
Con los valores por defecto (0.25° en latitud, 0.1° en longitud) son 11,421
puntos = 115 llamadas. La API pública admite 100 ubicaciones por llamada,
1 llamada por segundo y 1000 llamadas al día, así que son unos **2 minutos** y
te quedas muy por debajo del límite diario.

Es reanudable: si lo cortas a la mitad, al volver a correrlo sigue donde quedó.

Uso
---
    python3 muestrear_elevacion.py
    python3 muestrear_elevacion.py --dataset srtm90m --paso-lon 0.05
    python3 regionalizar_peru.py --perfiles recursos/perfiles_etopo1_peru_denso.csv \
                                 --umbral 1000 --salida analisis_regiones_denso
    python3 graficar_regiones.py --entrada analisis_regiones_denso

Datasets disponibles en OpenTopoData (--dataset)
------------------------------------------------
    etopo1    1 arcmin (~1.8 km). El que se usó en la versión preliminar.
              Mantenlo si quieres comparar peras con peras.
    srtm90m   90 m. Mucho mejor para el flanco occidental andino, que es donde
              el muestreo grueso más se equivoca. Cubre hasta 56°S: el Perú
              entero entra.
    mapzen    DEM global fusionado (~30 m donde hay SRTM).

Cortesía con el servicio: OpenTopoData es gratuito y lo mantiene una sola
persona. El script respeta 1 llamada por segundo. No le bajes el --espera.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

URL = "https://api.opentopodata.org/v1/{dataset}?locations={locs}"
POR_LLAMADA = 100          # límite de la API pública


def pedir(dataset: str, puntos, intentos: int = 4):
    locs = "|".join(f"{la:.4f},{lo:.4f}" for la, lo in puntos)
    url = URL.format(dataset=dataset, locs=locs)
    for k in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "wwlln-peru/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode())
            if d.get("status") != "OK":
                raise RuntimeError(d.get("error", "respuesta sin status OK"))
            return [(p["location"]["lat"], p["location"]["lng"], p["elevation"])
                    for p in d["results"]]
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError,
                json.JSONDecodeError) as e:
            espera = 3 * (k + 1)
            print(f"    [!] {type(e).__name__}: {e}. Reintento en {espera}s "
                  f"({k+1}/{intentos})", file=sys.stderr)
            time.sleep(espera)
    raise SystemExit("[!] La API falló 4 veces seguidas. Revisa tu conexión y "
                     "vuelve a correr: el script continúa donde quedó.")


def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    ap.add_argument("--dataset", default="etopo1",
                    choices=["etopo1", "srtm90m", "srtm30m", "mapzen", "aster30m"])
    ap.add_argument("--lat", nargs=2, type=float, default=[-19.0, 1.0])
    ap.add_argument("--lon", nargs=2, type=float, default=[-82.0, -68.0])
    ap.add_argument("--paso-lat", type=float, default=0.25)
    ap.add_argument("--paso-lon", type=float, default=0.10)
    ap.add_argument("--espera", type=float, default=1.05,
                    help="segundos entre llamadas (la API pide >= 1)")
    ap.add_argument("--salida", type=Path,
                    default=Path("recursos/perfiles_etopo1_peru_denso.csv"))
    args = ap.parse_args()
    args.salida.parent.mkdir(parents=True, exist_ok=True)

    lats = np.round(np.arange(args.lat[0], args.lat[1] + 1e-9, args.paso_lat), 4)
    lons = np.round(np.arange(args.lon[0], args.lon[1] + 1e-9, args.paso_lon), 4)
    todos = [(float(la), float(lo)) for la in lats for lo in lons]

    hechos = set()
    if args.salida.exists():
        prev = pd.read_csv(args.salida)
        hechos = set(zip(prev["lat"].round(4), prev["lon"].round(4)))
        print(f"Ya había {len(hechos):,} puntos en {args.salida}; se reanuda.")
    else:
        args.salida.write_text("lat,lon,elev_m\n")

    faltan = [p for p in todos if (round(p[0], 4), round(p[1], 4)) not in hechos]
    lotes = [faltan[i:i + POR_LLAMADA] for i in range(0, len(faltan), POR_LLAMADA)]

    print(f"Dataset      : {args.dataset}")
    print(f"Malla        : {len(lats)} lat x {len(lons)} lon = {len(todos):,} puntos")
    print(f"Por descargar: {len(faltan):,} puntos en {len(lotes)} llamadas")
    print(f"Tiempo estim.: ~{len(lotes) * args.espera / 60:.1f} min\n")
    if not lotes:
        print("Nada que hacer.")
        return

    t0 = time.time()
    with args.salida.open("a") as f:
        for i, lote in enumerate(lotes, 1):
            for la, lo, ele in pedir(args.dataset, lote):
                if ele is not None:
                    f.write(f"{la},{lo},{ele}\n")
            f.flush()
            hecho = i / len(lotes)
            queda = (time.time() - t0) / hecho * (1 - hecho)
            print(f"\r  {i}/{len(lotes)} llamadas  ({100*hecho:5.1f}%)  "
                  f"faltan ~{queda/60:4.1f} min", end="", flush=True)
            if i < len(lotes):
                time.sleep(args.espera)

    d = pd.read_csv(args.salida)
    print(f"\n\nListo: {len(d):,} puntos en {args.salida}")
    print(f"Elevación de {d.elev_m.min():.0f} a {d.elev_m.max():.0f} m")
    print("\nAhora corre:")
    print(f"  python3 regionalizar_peru.py --perfiles {args.salida} "
          f"--umbral 1000 --salida analisis_regiones_denso")
    print("  python3 graficar_regiones.py --entrada analisis_regiones_denso")


if __name__ == "__main__":
    main()
