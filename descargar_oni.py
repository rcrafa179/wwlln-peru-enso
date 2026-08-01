#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
descargar_oni.py
================
Descarga y parsea indices ENSO del CPC/NOAA y genera CSV wide y tidy listos
para unir con la serie mensual de WWLLN.

Indices soportados
------------------
  oni     ONI oficial. Media movil de 3 meses de la anomalia de TSM ERSSTv5 en
          Nino 3.4, climatologia movil 1991-2020. Ya viene estacional.
          Fuente: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt

  roni    ONI relativo (ONI menos la media tropical). Ya viene estacional.
          Fuente: https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt

  nino12  Anomalia de TSM en la region Nino 1+2 (0-10 S, 90-80 W), la que esta
  nino3   frente a la costa de Peru y Ecuador. Estas cuatro salen del mismo
  nino34  archivo MENSUAL del CPC (ERSSTv5, base 1991-2020), asi que aqui se les
  nino4   aplica la media movil de 3 meses centrada para dejarlas en la misma
          convencion estacional que el ONI.
          Fuente: https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii

  rnino12 Version RELATIVA de las anteriores (OISSTv2.1, base 1991-2020): a cada
  rnino3  region se le resta la TSM media de los tropicos. Quita la tendencia de
  rnino34 calentamiento global y deja solo el gradiente zonal, que es lo que en
  rnino4  realidad controla la conveccion. Mismo tratamiento de media movil.
          Fuente: https://www.cpc.ncep.noaa.gov/data/indices/rel_mthsst9120.txt

Por que Nino 1+2 y no ONI para Peru
-----------------------------------
El ONI mide Nino 3.4 (Pacifico central). El "Nino costero" peruano -- el que
manda sobre la conveccion y las lluvias en la costa norte -- se ve en Nino 1+2,
y puede ocurrir sin que el ONI se mueva (2017 es el caso de libro). Ademas
Nino 1+2 tiene mucha mas varianza que Nino 3.4, asi que el umbral de +-0.5 C
del ONI NO aplica.

Umbrales
--------
Para nino12 el default replica las categorias del ICEN (indice costero El Nino,
ENFEN/IGP), que son asimetricas:

    <= -1.4   Fria fuerte
    <= -1.2   Fria moderada
    <= -1.0   Fria debil
     < +0.4   Neutra
     < +1.0   Calida debil
     < +1.7   Calida moderada
     < +3.0   Calida fuerte
    >= +3.0   Calida extraordinaria

    => fase: frio si <= -1.0, calido si >= +0.4, neutral en medio.

OJO: esto es un ICEN-proxy, no el ICEN oficial. El ICEN del ENFEN se calcula
sobre ERSST v3b/v5 con su propia climatologia y lo publica el IGP. Las
categorias coinciden, los decimales pueden diferir un poco. Si vas a citar el
ICEN en un paper, usa el del IGP; para este analisis el proxy sirve.

Para el resto de indices el default sigue siendo +-0.5 C.

Uso
---
    python descargar_oni.py --indice nino12                  # 2021-2025
    python descargar_oni.py --indice nino12 --desde 2010 --hasta 2025
    python descargar_oni.py --indice oni                     # comportamiento previo
    python descargar_oni.py --indice nino12 --local ersst5.nino.mth.91-20.ascii

Si la maquina no tiene salida a internet, baja el .ascii a mano desde la URL
que imprime el error y pasalo con --local.
"""

from __future__ import annotations

import argparse
import io
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

URL_ESTACIONAL = {
    "oni": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    "roni": "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt",
}

URL_MENSUAL = "https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii"
URL_RELATIVO = "https://www.cpc.ncep.noaa.gov/data/indices/rel_mthsst9120.txt"

# Layout de cada archivo mensual: (url, marca de cabecera, nombres de columna)
COLS_MENSUAL = ["year", "month",
                "sst_nino12", "anom_nino12",
                "sst_nino3", "anom_nino3",
                "sst_nino4", "anom_nino4",
                "sst_nino34", "anom_nino34"]

COLS_RELATIVO = ["year", "month",
                 "anom_rnino12", "anom_rnino3", "anom_rnino4", "anom_rnino34"]

FUENTE_MENSUAL = {
    "nino12": (URL_MENSUAL, "YR", COLS_MENSUAL, "anom_nino12"),
    "nino3": (URL_MENSUAL, "YR", COLS_MENSUAL, "anom_nino3"),
    "nino34": (URL_MENSUAL, "YR", COLS_MENSUAL, "anom_nino34"),
    "nino4": (URL_MENSUAL, "YR", COLS_MENSUAL, "anom_nino4"),
    "rnino12": (URL_RELATIVO, "YEAR", COLS_RELATIVO, "anom_rnino12"),
    "rnino3": (URL_RELATIVO, "YEAR", COLS_RELATIVO, "anom_rnino3"),
    "rnino34": (URL_RELATIVO, "YEAR", COLS_RELATIVO, "anom_rnino34"),
    "rnino4": (URL_RELATIVO, "YEAR", COLS_RELATIVO, "anom_rnino4"),
}

ETIQUETA = {
    "oni": "ONI (Nino 3.4)",
    "roni": "RONI",
    "nino12": "Nino 1+2",
    "nino3": "Nino 3",
    "nino34": "Nino 3.4",
    "nino4": "Nino 4",
    "rnino12": "Nino 1+2 relativo",
    "rnino3": "Nino 3 relativo",
    "rnino34": "Nino 3.4 relativo",
    "rnino4": "Nino 4 relativo",
}

# (umbral_frio, umbral_calido). Un mes es frio si valor <= umbral_frio.
UMBRALES = {
    "oni": (-0.5, 0.5),
    "roni": (-0.5, 0.5),
    "nino34": (-0.5, 0.5),
    "nino3": (-0.5, 0.5),
    "nino4": (-0.5, 0.5),
    "nino12": (-1.0, 0.4),    # ICEN (ENFEN/IGP)
    "rnino12": (-1.0, 0.4),   # ICEN aplicado al indice relativo: ver aviso abajo
    "rnino3": (-0.5, 0.5),
    "rnino34": (-0.5, 0.5),
    "rnino4": (-0.5, 0.5),
}

# Indices a los que se les puede poner categoria ICEN.
INDICES_ICEN = {"nino12", "rnino12"}

# Categorias ICEN del ENFEN. Ojo con los bordes: del lado frio los intervalos
# son cerrados por arriba (ICEN <= -1.4 es fuerte), del lado calido son cerrados
# por abajo (ICEN >= 0.4 es debil).
CATEGORIAS_ICEN = [
    (-1.4, "le", "Fria fuerte"),
    (-1.2, "le", "Fria moderada"),
    (-1.0, "le", "Fria debil"),
    (0.4, "lt", "Neutra"),
    (1.0, "lt", "Calida debil"),
    (1.7, "lt", "Calida moderada"),
    (3.0, "lt", "Calida fuerte"),
    (np.inf, "lt", "Calida extraordinaria"),
]

SEASONS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
           "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]

INDICES = list(URL_ESTACIONAL) + list(FUENTE_MENSUAL)


# ----------------------------------------------------------------------
# Descarga
# ----------------------------------------------------------------------
def url_de(indice: str) -> str:
    if indice in URL_ESTACIONAL:
        return URL_ESTACIONAL[indice]
    return FUENTE_MENSUAL[indice][0]


def obtener_texto(indice: str, local: Path | None) -> str:
    if local:
        return local.read_text(errors="replace")
    url = url_de(indice)
    print(f"Descargando {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", errors="replace")


def _recortar_a_cabecera(texto: str, marca: str) -> str:
    """Descarta cualquier basura previa a la linea de cabecera (util con --local
    si el archivo se guardo desde el navegador y trae la URL arriba)."""
    lineas = texto.splitlines()
    for i, ln in enumerate(lineas):
        if ln.strip().upper().startswith(marca):
            return "\n".join(lineas[i:])
    return texto


# ----------------------------------------------------------------------
# Parseo
# ----------------------------------------------------------------------
def parsear_estacional(texto: str) -> pd.DataFrame:
    """Archivo ONI/RONI: SEAS YR [TOTAL] ANOM. RONI omite TOTAL."""
    texto = _recortar_a_cabecera(texto, "SEAS")
    df = pd.read_csv(io.StringIO(texto), sep=r"\s+", engine="python")
    df.columns = [c.strip().upper() for c in df.columns]
    if "ANOM" not in df.columns or "SEAS" not in df.columns:
        raise ValueError(f"Columnas inesperadas: {list(df.columns)}")
    out = df[["SEAS", "YR", "ANOM"]].rename(
        columns={"SEAS": "season", "YR": "year", "ANOM": "valor"})
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["valor"] = pd.to_numeric(out["valor"], errors="coerce")
    out = out.dropna(subset=["year", "valor"])
    out["season_idx"] = out["season"].map({s: i + 1 for i, s in enumerate(SEASONS)})
    return out.dropna(subset=["season_idx"])


def parsear_mensual(texto: str, indice: str, rolling: bool = True) -> pd.DataFrame:
    """Archivos mensuales del CPC (ERSSTv5 crudo o relativo OISSTv2.1).

    Devuelve la serie con la media movil de 3 meses CENTRADA, asignada al mes
    central, de modo que season_idx == numero de mes (misma convencion que el
    ONI: DJF -> enero, JFM -> febrero, ..., NDJ -> diciembre).
    """
    _, marca, columnas, col_valor = FUENTE_MENSUAL[indice]
    texto = _recortar_a_cabecera(texto, marca)
    df = pd.read_csv(io.StringIO(texto), sep=r"\s+", engine="python",
                     skiprows=1, names=columnas)
    for c in columnas:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["year", "month", col_valor])
    df = df.sort_values(["year", "month"]).reset_index(drop=True)

    # Chequeo de continuidad: la media movil solo es valida si no faltan meses.
    fechas = pd.to_datetime(dict(year=df["year"].astype(int),
                                 month=df["month"].astype(int), day=1))
    esperado = pd.date_range(fechas.min(), fechas.max(), freq="MS")
    if len(fechas) != len(esperado) or not (fechas.values == esperado.values).all():
        raise ValueError("La serie mensual tiene huecos; revisa el archivo de entrada.")

    serie = df[col_valor].astype(float)
    if rolling:
        # min_periods=3 => los extremos quedan NaN y se descartan, igual que el ONI.
        valor = serie.rolling(3, center=True, min_periods=3).mean().round(2)
    else:
        valor = serie.round(2)

    out = pd.DataFrame({
        "year": df["year"].astype(int),
        "season_idx": df["month"].astype(int),
        "valor": valor,
    })
    out["season"] = out["season_idx"].map(lambda m: SEASONS[m - 1])
    return out.dropna(subset=["valor"])


# ----------------------------------------------------------------------
# Clasificacion
# ----------------------------------------------------------------------
def clasificar(df: pd.DataFrame, frio: float, calido: float) -> pd.DataFrame:
    df = df.copy()
    df["phase"] = np.select(
        [df["valor"] <= frio, df["valor"] >= calido],
        ["La Nina", "El Nino"],
        default="Neutral",
    )
    return df


def categoria_icen(v: float) -> str:
    for limite, cmp, etiqueta in CATEGORIAS_ICEN:
        if (v <= limite) if cmp == "le" else (v < limite):
            return etiqueta
    return CATEGORIAS_ICEN[-1][2]


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    ap.add_argument("--indice", default="oni", choices=INDICES)
    ap.add_argument("--desde", type=int, default=2021)
    ap.add_argument("--hasta", type=int, default=2025)
    ap.add_argument("--local", type=Path, default=None,
                    help="Parsea un .ascii ya descargado en vez de bajarlo")
    ap.add_argument("--salida", type=Path, default=Path("."))
    ap.add_argument("--umbral-frio", type=float, default=None,
                    help="Override del umbral frio (default segun indice)")
    ap.add_argument("--umbral-calido", type=float, default=None,
                    help="Override del umbral calido (default segun indice)")
    ap.add_argument("--sin-media-movil", action="store_true",
                    help="Para indices mensuales: usa el valor mensual crudo, "
                         "sin la media movil de 3 meses")
    args = ap.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)

    indice = args.indice
    frio_def, calido_def = UMBRALES[indice]
    frio = args.umbral_frio if args.umbral_frio is not None else frio_def
    calido = args.umbral_calido if args.umbral_calido is not None else calido_def

    try:
        texto = obtener_texto(indice, args.local)
    except Exception as e:
        print(f"[!] No se pudo obtener el archivo: {e}\n"
              f"    Bajalo a mano desde {url_de(indice)} y usa --local.",
              file=sys.stderr)
        sys.exit(1)

    if indice in URL_ESTACIONAL:
        df = parsear_estacional(texto)
        nota_suavizado = "media movil de 3 meses (ya viene asi del CPC)"
    else:
        df = parsear_mensual(texto, indice, rolling=not args.sin_media_movil)
        nota_suavizado = ("valor mensual crudo" if args.sin_media_movil
                          else "media movil de 3 meses centrada, calculada aqui")

    df = df[df["year"].between(args.desde, args.hasta)].copy()
    if df.empty:
        print("[!] Rango de anios sin datos.", file=sys.stderr)
        sys.exit(1)

    df = clasificar(df, frio, calido)
    df["indice"] = indice
    if indice in INDICES_ICEN:
        df["categoria"] = df["valor"].map(categoria_icen)

    df = df.sort_values(["year", "season_idx"]).reset_index(drop=True)

    cols = ["year", "season", "season_idx", "indice", "valor", "phase"]
    if "categoria" in df.columns:
        cols.append("categoria")
    tidy = df[cols].copy()
    # Alias de compatibilidad: los scripts viejos leen una columna 'oni'.
    tidy["oni"] = tidy["valor"]

    tag = f"{indice}_{args.desde}_{args.hasta}"
    tidy.to_csv(args.salida / f"{tag}_tidy.csv", index=False)

    wide = tidy.pivot(index="year", columns="season", values="valor") \
               .reindex(columns=SEASONS)
    wide.to_csv(args.salida / f"{tag}_wide.csv")

    # ------------------------------------------------------------------
    print(f"\nIndice     : {ETIQUETA[indice]}")
    print(f"Suavizado  : {nota_suavizado}")
    print(f"Umbrales   : frio <= {frio:+.2f} C   |   calido >= {calido:+.2f} C")
    print(f"Periodo    : {args.desde}-{args.hasta}  ({len(tidy)} estaciones)")
    print(f"Rango      : {tidy['valor'].min():+.2f} a {tidy['valor'].max():+.2f} C")
    print("\nMeses por fase:")
    print(tidy["phase"].value_counts().to_string())
    if "categoria" in tidy.columns:
        print("\nCategorias ICEN:")
        print(tidy["categoria"].value_counts().to_string())
    print(f"\nEscrito en: {args.salida.resolve()}/{tag}_tidy.csv")


if __name__ == "__main__":
    main()
