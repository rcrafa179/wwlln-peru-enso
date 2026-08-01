#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
oni+wwlln.py
============
Une la serie mensual de WWLLN con un indice ENSO estacional (ONI, Nino 1+2,
RONI, ...) y calcula anomalias de actividad electrica por fase.

Generico respecto al indice: lee la columna 'valor' que produce
descargar_oni.py (y acepta la columna 'oni' de archivos antiguos).

Entradas
--------
  --wwlln   wwlln_2021_2025_mensual.csv   (salida de construir_serie_mensual.py)
  --indice  nino12_2021_2025_tidy.csv     (salida de descargar_oni.py)

Salidas
-------
  wwlln_indice_mensual.csv    serie unida con anomalia absoluta, % y z
  wwlln_por_fase.csv          resumen por fase (frio / neutral / calido)
  wwlln_ciclo_anual.csv       climatologia mensual del periodo
  correlaciones_lag.csv       correlacion indice vs z con rezagos 0..N meses
  resumen_por_temporada.csv   lo mismo estratificado por temporada seca/lluviosa
  estadisticos.txt            n efectivo, correlaciones, Kruskal-Wallis

Nota metodologica
-----------------
Cada estacion de 3 meses se asigna al MES CENTRAL (DJF -> enero, JFM -> febrero,
..., NDJ -> diciembre), de modo que season_idx == mes y el join es directo por
(anio, mes).

La anomalia estandarizada z se calcula contra la climatologia del MISMO mes
calendario. Sin ese paso cualquier comparacion entre fases estaria dominada por
el ciclo estacional, no por ENSO.

Uso
---
    python "oni+wwlln.py" --wwlln wwlln_2021_2025_mensual.csv \
                          --indice nino12_2021_2025_tidy.csv \
                          --nombre-indice "Nino 1+2" \
                          --salida ./analisis_ENSO_nino12
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from scipy import stats as _stats
except ImportError:      # el script funciona igual, solo sin p-valores
    _stats = None

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]

# Temporada lluviosa en Peru segun la climatologia WWLLN 2021-2025
MESES_LLUVIOSOS = {10, 11, 12, 1, 2, 3, 4}


def cargar_indice(ruta: Path) -> tuple[pd.DataFrame, str]:
    idx = pd.read_csv(ruta)
    if "valor" not in idx.columns:
        if "oni" not in idx.columns:
            raise ValueError(f"{ruta} no tiene columna 'valor' ni 'oni'.")
        idx = idx.rename(columns={"oni": "valor"})
    nombre = (idx["indice"].iloc[0] if "indice" in idx.columns else "indice")
    idx = idx.rename(columns={"year": "anio", "season_idx": "mes",
                              "phase": "fase_enso"})
    cols = ["anio", "mes", "season", "valor", "fase_enso"]
    if "categoria" in idx.columns:
        cols.append("categoria")
    return idx[cols], nombre


def n_efectivo(x: np.ndarray, y: np.ndarray) -> float:
    """Tamano de muestra efectivo de Bretherton et al. (1999), que corrige por
    la autocorrelacion de lag 1 de ambas series."""
    def r1(v):
        v = np.asarray(v, dtype=float)
        v = v - v.mean()
        if len(v) < 3 or v.std() == 0:
            return 0.0
        return float(np.corrcoef(v[:-1], v[1:])[0, 1])
    rx, ry = r1(x), r1(y)
    factor = (1 - rx * ry) / (1 + rx * ry)
    return max(3.0, len(x) * factor)


def p_de_r(r: float, n: float) -> float | None:
    """p bilateral de una correlacion de Pearson con n grados de libertad
    efectivos."""
    if _stats is None or n <= 2 or abs(r) >= 1:
        return None
    t = r * np.sqrt((n - 2) / (1 - r ** 2))
    return float(2 * _stats.t.sf(abs(t), df=n - 2))


def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    ap.add_argument("--wwlln", required=True, type=Path)
    ap.add_argument("--indice", type=Path, default=None,
                    help="CSV tidy del indice (salida de descargar_oni.py)")
    ap.add_argument("--oni", type=Path, default=None,
                    help="Alias historico de --indice")
    ap.add_argument("--nombre-indice", default=None,
                    help="Etiqueta para reportes (ej. 'Nino 1+2')")
    ap.add_argument("--salida", default=Path("."), type=Path)
    ap.add_argument("--col-conteo", default="n_rayos_norm",
                    help="Columna de conteo (n_rayos o n_rayos_norm)")
    ap.add_argument("--cobertura-min", type=float, default=0.8,
                    help="Descarta meses con cobertura de dias bajo este umbral")
    ap.add_argument("--max-lag", type=int, default=6,
                    help="Rezago maximo, en meses, para las correlaciones")
    args = ap.parse_args()

    ruta_idx = args.indice or args.oni
    if ruta_idx is None:
        ap.error("hace falta --indice (o --oni)")
    args.salida.mkdir(parents=True, exist_ok=True)

    ww = pd.read_csv(args.wwlln)
    idx, nombre_detectado = cargar_indice(ruta_idx)
    nombre = args.nombre_indice or nombre_detectado

    col = args.col_conteo if args.col_conteo in ww.columns else "n_rayos"
    if col != args.col_conteo:
        print(f"[i] '{args.col_conteo}' no existe; se usa '{col}'.")

    # ---- Control de cobertura temporal ----
    if "cobertura" in ww.columns:
        fuera = ww[ww["cobertura"] < args.cobertura_min]
        if len(fuera):
            print(f"[!] {len(fuera)} mes(es) con cobertura < {args.cobertura_min}:")
            print(fuera[["anio", "mes", "dias_con_datos", "cobertura"]]
                  .to_string(index=False))
        ww = ww[ww["cobertura"] >= args.cobertura_min].copy()

    df = ww.merge(idx, on=["anio", "mes"], how="left", validate="one_to_one")
    faltan = df["valor"].isna().sum()
    if faltan:
        print(f"[!] {faltan} mes(es) sin valor del indice asociado.")

    df["mes_nombre"] = df["mes"].map(lambda m: MESES[m - 1])
    df["fecha"] = pd.to_datetime(dict(year=df["anio"], month=df["mes"], day=1))
    df["temporada"] = np.where(df["mes"].isin(MESES_LLUVIOSOS), "lluviosa", "seca")

    # ---- Climatologia y anomalia estandarizada por mes calendario ----
    clim = df.groupby("mes")[col].agg(media="mean", sd="std").reset_index()
    df = df.merge(clim, on="mes", how="left")
    df["anomalia"] = df[col] - df["media"]
    df["anomalia_pct"] = (100 * df["anomalia"] / df["media"]).round(1)
    df["z"] = (df["anomalia"] / df["sd"].replace(0, np.nan)).round(3)
    # z logaritmico: los conteos de rayos son multiplicativos, el log estabiliza
    # la varianza entre estacion seca y humeda.
    # log(0) daria -inf: en la costa hay meses con cero rayos de verdad. Se usa
    # log(1+x), que para conteos grandes es indistinguible de log(x).
    df["log_conteo"] = np.log1p(df[col])
    clim_log = df.groupby("mes")["log_conteo"].agg(media_log="mean",
                                                   sd_log="std").reset_index()
    df = df.merge(clim_log, on="mes", how="left")
    df["z_log"] = ((df["log_conteo"] - df["media_log"])
                   / df["sd_log"].replace(0, np.nan)).round(3)

    df = df.sort_values(["anio", "mes"]).reset_index(drop=True)

    cols_out = ["fecha", "anio", "mes", "mes_nombre", "temporada", "season",
                "valor", "fase_enso"]
    if "categoria" in df.columns:
        cols_out.append("categoria")
    cols_out += [col, "media", "anomalia", "anomalia_pct", "z", "z_log"]
    df[cols_out].to_csv(args.salida / "wwlln_indice_mensual.csv", index=False)

    clim.rename(columns={"media": f"{col}_medio", "sd": f"{col}_sd"}) \
        .to_csv(args.salida / "wwlln_ciclo_anual.csv", index=False)

    # ---- Resumen por fase ----
    fase = df.groupby("fase_enso", observed=True).agg(
        n_meses=(col, "size"),
        rayos_medios=(col, "mean"),
        anomalia_media=("anomalia", "mean"),
        anomalia_pct_media=("anomalia_pct", "mean"),
        z_medio=("z", "mean"),
        z_log_medio=("z_log", "mean"),
        indice_medio=("valor", "mean"),
    ).round(3).reset_index()
    fase.to_csv(args.salida / "wwlln_por_fase.csv", index=False)

    # ---- Estratificado por temporada ----
    temp = df.groupby(["temporada", "fase_enso"], observed=True).agg(
        n_meses=(col, "size"),
        z_medio=("z", "mean"),
        z_log_medio=("z_log", "mean"),
        anomalia_pct_media=("anomalia_pct", "mean"),
    ).round(3).reset_index()
    temp.to_csv(args.salida / "resumen_por_temporada.csv", index=False)

    # ---- Correlaciones con rezago ----
    sub = df.dropna(subset=["valor", "z"]).reset_index(drop=True)
    filas = []
    for lag in range(0, args.max_lag + 1):
        # lag>0: el indice ADELANTA a los rayos (indice en t, rayos en t+lag)
        a = sub["valor"].iloc[:len(sub) - lag].to_numpy(dtype=float)
        b = sub["z"].iloc[lag:].to_numpy(dtype=float)
        if len(a) < 6:
            continue
        r = float(np.corrcoef(a, b)[0, 1])
        ne = n_efectivo(a, b)
        filas.append({"lag_meses": lag, "n": len(a), "n_efectivo": round(ne, 1),
                      "pearson_r": round(r, 3), "p_aprox": p_de_r(r, ne)})
    lags = pd.DataFrame(filas)
    lags.to_csv(args.salida / "correlaciones_lag.csv", index=False)

    # ---- Estadisticos ----
    lineas = [f"Indice: {nombre}",
              f"Serie WWLLN: {args.wwlln.name}   columna: {col}",
              f"Meses usados: {len(sub)}  ({sub['anio'].min()}-{sub['anio'].max()})",
              ""]

    r_p = float(np.corrcoef(sub["valor"], sub["z"])[0, 1])
    r_s = float(sub[["valor", "z"]].corr(method="spearman").iloc[0, 1])
    r_log = float(np.corrcoef(sub["valor"], sub["z_log"].fillna(0))[0, 1])
    ne = n_efectivo(sub["valor"].to_numpy(float), sub["z"].to_numpy(float))
    p = p_de_r(r_p, ne)
    lineas += [f"Correlacion {nombre} vs anomalia de rayos (n={len(sub)}):",
               f"  Pearson  r = {r_p:+.3f}",
               f"  Spearman r = {r_s:+.3f}",
               f"  Pearson r (z logaritmico) = {r_log:+.3f}",
               f"  n efectivo (Bretherton) = {ne:.1f}",
               f"  p aproximado con n efectivo = "
               f"{'n/d (falta scipy)' if p is None else f'{p:.3f}'}",
               ""]

    for t, g in sub.groupby("temporada"):
        if len(g) > 3:
            rr = float(np.corrcoef(g["valor"], g["z"])[0, 1])
            lineas.append(f"  Solo temporada {t}: r = {rr:+.3f} (n={len(g)})")
    lineas.append("")

    if _stats is not None:
        grupos = [g["z"].dropna().values
                  for _, g in sub.groupby("fase_enso", observed=True)
                  if len(g) > 1]
        if len(grupos) >= 2:
            H, pk = _stats.kruskal(*grupos)
            lineas.append(f"Kruskal-Wallis entre fases: H = {H:.2f}, p = {pk:.3f}")
            lineas.append("  (p nominal; con n efectivo mucho menor que n, tomarlo "
                          "como orientativo)")
    lineas.append("")
    lineas.append("Correlaciones con rezago (indice adelanta a los rayos):")
    lineas.append(lags.to_string(index=False))
    lineas.append("")
    lineas.append("Resumen por fase:")
    lineas.append(fase.to_string(index=False))
    lineas.append("")
    lineas.append("Por temporada:")
    lineas.append(temp.to_string(index=False))

    texto = "\n".join(lineas)
    (args.salida / "estadisticos.txt").write_text(texto + "\n")
    print("\n" + texto)
    print(f"\nArchivos escritos en: {args.salida.resolve()}")


if __name__ == "__main__":
    main()
