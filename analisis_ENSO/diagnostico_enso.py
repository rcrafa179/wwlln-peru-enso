#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnostico_enso.py
===================
Diagnostico critico de la relacion ENSO - actividad electrica.
Responde a: "la senial que veo, ¿es fisica o es artefacto?"

Ejecuta seis pruebas:
  1. Media vs varianza por fase ENSO  (¿desplazamiento o dispersion?)
  2. Deriva interanual                (¿es efecto ENSO o tendencia del dato?)
  3. Cobertura temporal por anio-mes  (¿huecos que aplanan la serie?)
  4. Grados de libertad efectivos     (¿cuantas muestras INDEPENDIENTES hay?)
  5. Correlacion ONI-rayos con rezagos 0..6 meses
  6. Sensibilidad de la climatologia  (¿el z-score es estable con n=5 anios?)

Uso:
    python diagnostico_enso.py --datos salida_wwlln/wwlln_oni_mensual.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from scipy import stats as sps
    HAY_SCIPY = True
except ImportError:
    HAY_SCIPY = False


def sep(titulo: str) -> None:
    print("\n" + "=" * 72)
    print(titulo)
    print("=" * 72)


# --------------------------------------------------------------------------
# 1. Media vs varianza
# --------------------------------------------------------------------------
def prueba_media_varianza(df: pd.DataFrame, var: str) -> None:
    sep("1. ¿DESPLAZAMIENTO DE MEDIA O CAMBIO DE VARIANZA?")

    res = df.groupby("fase_enso", observed=True)[var].agg(
        n="size", media="mean", mediana="median", sd="std",
        min="min", max="max").round(3)
    print(res.to_string())

    grupos = [g[var].dropna().values for _, g in
              df.groupby("fase_enso", observed=True) if len(g) > 2]

    if HAY_SCIPY and len(grupos) >= 2:
        f_k, p_k = sps.kruskal(*grupos)          # diferencia de medianas
        f_l, p_l = sps.levene(*grupos, center="median")  # diferencia de varianzas
        print(f"\nKruskal-Wallis (medias/medianas): H={f_k:.3f}  p={p_k:.4f}")
        print(f"Levene (varianzas)             : W={f_l:.3f}  p={p_l:.4f}")
        print("\nSi Levene sale significativo y Kruskal no, lo que cambia entre")
        print("fases es la DISPERSION, no el nivel medio. Eso NO es la hipotesis")
        print("de que 'El Nino reduce los rayos'.")
    else:
        sds = {k: round(float(np.std(v, ddof=1)), 3) for k, v in
               zip([n for n, g in df.groupby("fase_enso", observed=True)
                    if len(g) > 2], grupos)}
        print(f"\nDesviaciones por fase: {sds}")
        print("(instala scipy para los tests formales)")

    print("\nOJO: cuenta los EVENTOS, no los meses. 12 meses de un solo")
    print("El Nino son n=1, no n=12.")


# --------------------------------------------------------------------------
# 2. Deriva interanual
# --------------------------------------------------------------------------
def prueba_deriva(df: pd.DataFrame, var: str, col_conteo: str) -> None:
    sep("2. DERIVA INTERANUAL (¿ENSO o tendencia instrumental?)")

    por_anio = df.groupby("anio").agg(
        n_meses=(var, "size"),
        z_medio=(var, "mean"),
        z_sd=(var, "std"),
        conteo_medio=(col_conteo, "mean"),
    ).round(3)
    print(por_anio.to_string())

    x = por_anio.index.values.astype(float)
    y = por_anio["conteo_medio"].values
    if len(x) > 2:
        b, a = np.polyfit(x, y, 1)
        cambio = 100 * b * (x[-1] - x[0]) / y.mean()
        print(f"\nTendencia lineal del conteo: {b:+,.0f} rayos/mes por anio")
        print(f"Cambio total en la ventana : {cambio:+.1f} % respecto a la media")
        print("\nLa red WWLLN GANO estaciones en el periodo, asi que se espera")
        print("una tendencia POSITIVA de origen instrumental. Si la ves negativa,")
        print("es problema de cobertura, no de clima. Si la ves positiva, hay que")
        print("removerla ANTES de comparar fases ENSO.")

    if por_anio["z_sd"].max() / max(por_anio["z_sd"].min(), 1e-9) > 2:
        print("\n[!] La dispersion cambia mas del doble entre anios. Revisa la")
        print("    cobertura antes de interpretar cualquier senial ENSO.")


# --------------------------------------------------------------------------
# 3. Cobertura
# --------------------------------------------------------------------------
def prueba_cobertura(df: pd.DataFrame, mensual: Path | None) -> None:
    sep("3. COBERTURA TEMPORAL")

    if mensual is None or not mensual.exists():
        print("Sin archivo mensual crudo (--mensual). Se omite.")
        return

    m = pd.read_csv(mensual)
    if "cobertura" not in m.columns:
        print("El archivo no trae columna 'cobertura'.")
        return

    tabla = m.pivot_table(index="anio", columns="mes", values="cobertura")
    print("Fraccion de dias con datos (1.0 = mes completo):")
    print(tabla.round(2).to_string())

    malos = m[m["cobertura"] < 0.9]
    print(f"\nMeses con cobertura < 90 %: {len(malos)} de {len(m)}")
    if len(malos):
        print(malos[["anio", "mes", "dias_con_datos", "dias_del_mes",
                     "cobertura"]].to_string(index=False))
        print("\nCada uno de estos meses subestima el conteo y aparece como")
        print("anomalia NEGATIVA espuria. Usa 'n_rayos_norm', no 'n_rayos'.")


# --------------------------------------------------------------------------
# 4. Grados de libertad efectivos
# --------------------------------------------------------------------------
def prueba_gdl(df: pd.DataFrame, var: str) -> None:
    sep("4. GRADOS DE LIBERTAD EFECTIVOS")

    s = df.sort_values("fecha")[var].dropna().values
    n = len(s)
    if n < 10:
        print("Serie demasiado corta.")
        return

    # autocorrelacion lag-1
    r1 = float(np.corrcoef(s[:-1], s[1:])[0, 1])
    n_ef = min(n, n * (1 - r1) / (1 + r1)) if r1 > -1 else n
    print(f"n nominal                  : {n}")
    print(f"Autocorrelacion lag-1 (r1) : {r1:+.3f}")
    print(f"n efectivo (Bretherton)    : {n_ef:.1f}")

    # numero de eventos ENSO distintos (bloques contiguos por fase)
    fases = df.sort_values("fecha")["fase_enso"].astype(str).values
    bloques = 1 + int(np.sum(fases[1:] != fases[:-1]))
    print(f"\nBloques ENSO contiguos     : {bloques}")
    conteo_fase = (pd.Series(fases).groupby(
        (pd.Series(fases) != pd.Series(fases).shift()).cumsum())
        .first().value_counts())
    print("Eventos por fase:")
    print(conteo_fase.to_string())
    print("\nEste ultimo numero es tu verdadero tamanio muestral para afirmar")
    print("'El Nino hace X'. Con 1 evento El Nino no se puede concluir nada")
    print("estadisticamente; a lo sumo describir el caso 2023-24.")


# --------------------------------------------------------------------------
# 5. Rezagos
# --------------------------------------------------------------------------
def prueba_rezagos(df: pd.DataFrame, var: str, max_lag: int = 6) -> None:
    sep("5. CORRELACION ONI - RAYOS CON REZAGOS")

    d = df.sort_values("fecha").reset_index(drop=True)
    print("lag  n    Pearson   Spearman")
    print("-" * 34)
    for lag in range(max_lag + 1):
        oni = d["oni"].shift(lag)
        sub = pd.DataFrame({"oni": oni, "z": d[var]}).dropna()
        if len(sub) < 8:
            continue
        rp = sub["oni"].corr(sub["z"])
        rs = sub["oni"].corr(sub["z"], method="spearman")
        print(f"{lag:>3}  {len(sub):>3}  {rp:+7.3f}   {rs:+7.3f}")
    print("\nLa respuesta convectiva a la TSM del Pacifico central no es")
    print("instantanea. Si el maximo de |r| aparece en lag 1-3, reportalo;")
    print("si el perfil es plano y cercano a cero en todos los rezagos,")
    print("no hay senial que extraer con esta ventana.")


# --------------------------------------------------------------------------
# 6. Sensibilidad de la climatologia
# --------------------------------------------------------------------------
def prueba_climatologia(df: pd.DataFrame, col_conteo: str) -> None:
    sep("6. ESTABILIDAD DEL Z-SCORE (jackknife dejando un anio fuera)")

    anios = sorted(df["anio"].unique())
    print(f"La climatologia se calcula con n = {len(anios)} anios por mes.")
    print("Recalculo el z-score quitando un anio a la vez:\n")

    filas = []
    for fuera in anios:
        base = df[df["anio"] != fuera]
        clim = (base.groupby("mes")[col_conteo]
                    .agg(_mu="mean", _sd="std"))          # nombres propios
        tmp = df[["mes", "fase_enso", col_conteo]].merge(
            clim, left_on="mes", right_index=True, how="left")
        tmp["z_alt"] = (tmp[col_conteo] - tmp["_mu"]) / tmp["_sd"].replace(0, np.nan)
        med = tmp.groupby("fase_enso", observed=True)["z_alt"].mean()
        filas.append(pd.Series(med, name=f"sin_{fuera}"))

    tab = pd.DataFrame(filas).round(3)
    print(tab.to_string())
    rango = (tab.max() - tab.min()).round(3)
    print(f"\nRango de variacion de la media por fase:\n{rango.to_string()}")
    print("\nSi quitar un solo anio mueve la media de una fase mas de ~0.3 z,")
    print("tu climatologia es demasiado corta para definir anomalias. Solucion:")
    print("extender la ventana (2010-2025) para tener varios eventos ENSO y una")
    print("base climatologica que no dependa del evento que quieres estudiar.")


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", required=True, type=Path,
                    help="wwlln_oni_mensual.csv")
    ap.add_argument("--mensual", type=Path, default=None,
                    help="wwlln_2021_2025_mensual.csv (para cobertura)")
    ap.add_argument("--var", default="z", help="Columna de anomalia")
    ap.add_argument("--conteo", default="n_rayos_norm")
    args = ap.parse_args()

    df = pd.read_csv(args.datos, parse_dates=["fecha"])
    col = args.conteo if args.conteo in df.columns else "n_rayos"

    print(f"Archivo : {args.datos}")
    print(f"Registros: {len(df)}  |  anios: {df['anio'].min()}-{df['anio'].max()}")
    print(f"Variable de anomalia: '{args.var}'  |  conteo: '{col}'")

    prueba_media_varianza(df, args.var)
    prueba_deriva(df, args.var, col)
    prueba_cobertura(df, args.mensual)
    prueba_gdl(df, args.var)
    prueba_rezagos(df, args.var)
    prueba_climatologia(df, col)

    sep("LECTURA RAPIDA")
    print("La senial es defendible solo si: (a) la diferencia esta en la MEDIA")
    print("y no solo en la varianza, (b) sobrevive al quitar la tendencia")
    print("instrumental, (c) no depende de meses con baja cobertura, (d) el")
    print("z-score es estable al jackknife, y (e) tienes mas de un evento de")
    print("cada fase. Si falla cualquiera, extiende la ventana temporal.")


if __name__ == "__main__":
    main()