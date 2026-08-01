#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
construir_serie_mensual.py
==========================
Une los CSV mensuales por anio (analisis_YYYY/analisis_mensual_wwlln_peru_YYYY.csv,
salida de analisis_anual_wwlln.py) en una sola serie 2021-2025 con el formato
que espera oni+wwlln.py.

Columnas de salida:
    anio, mes, n_rayos, dias_con_datos, dias_del_mes, cobertura, n_rayos_norm

  - cobertura    = dias_con_datos / dias_del_mes  (0 a 1)
  - n_rayos_norm = n_rayos / dias_con_datos * dias_del_mes
                   (conteo extrapolado a mes completo; corrige los meses en los
                    que faltan dias de datos, para que no parezcan menos activos
                    de lo que realmente fueron)

Uso:
    python construir_serie_mensual.py --base . --salida wwlln_2021_2025_mensual.csv
    python construir_serie_mensual.py --base . --anios 2021 2022 2023 2024 2025
"""

from __future__ import annotations

import argparse
import calendar
from pathlib import Path

import pandas as pd

# Una carpeta por anio, sin excepciones. La antigua bifurcacion
# analisis_2025 / analisis_2025_corregido se consolido: ahora analisis_2025 es
# la version buena (generada desde peru_wwlln_2025_FINAL.parquet, solo .mat) y
# la contaminada quedo en _obsoleto_2025/.
CARPETAS = {anio: f"analisis_{anio}" for anio in range(2021, 2031)}


def cargar_anio(base: Path, anio: int) -> pd.DataFrame:
    carpeta = base / CARPETAS.get(anio, f"analisis_{anio}")
    ruta = carpeta / f"analisis_mensual_wwlln_peru_{anio}.csv"

    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta}")

    df = pd.read_csv(ruta)

    out = pd.DataFrame({
        "anio": anio,
        "mes": df["month"].astype(int),
        "n_rayos": df["n_eventos"].astype(int),
        "dias_con_datos": df["dias_con_datos"].astype(int),
    })

    out["dias_del_mes"] = out["mes"].map(
        lambda m: calendar.monthrange(anio, m)[1]
    )
    out["cobertura"] = (out["dias_con_datos"] / out["dias_del_mes"]).round(4)
    out["n_rayos_norm"] = (
        out["n_rayos"] / out["dias_con_datos"] * out["dias_del_mes"]
    ).round(1)

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, default=Path("."),
                    help="Carpeta que contiene los analisis_YYYY")
    ap.add_argument("--anios", type=int, nargs="+",
                    default=[2021, 2022, 2023, 2024, 2025])
    ap.add_argument("--salida", type=Path,
                    default=Path("wwlln_2021_2025_mensual.csv"))
    args = ap.parse_args()

    piezas = []
    for anio in args.anios:
        try:
            piezas.append(cargar_anio(args.base, anio))
            print(f"  {anio}: OK")
        except FileNotFoundError as e:
            print(f"  [!] {e}")

    if not piezas:
        print("No se pudo cargar ningun anio.")
        return

    df = pd.concat(piezas, ignore_index=True).sort_values(["anio", "mes"])
    df.to_csv(args.salida, index=False)

    print(f"\n{len(df)} meses escritos en: {args.salida.resolve()}")
    print(f"Total de rayos: {df['n_rayos'].sum():,}")

    incompletos = df[df["cobertura"] < 1.0]
    if len(incompletos):
        print(f"\nMeses con dias faltantes ({len(incompletos)}):")
        print(incompletos[["anio", "mes", "dias_con_datos",
                           "dias_del_mes", "cobertura"]].to_string(index=False))
    else:
        print("\nTodos los meses tienen cobertura completa.")


if __name__ == "__main__":
    main()
