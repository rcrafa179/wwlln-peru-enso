#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
graficar_enso.py
================
Gráficas del cruce WWLLN × índice ENSO, a partir de wwlln_indice_mensual.csv
(salida de oni+wwlln.py). Genérico respecto al índice.

Genera:
  - serie_indice_vs_rayos.png   índice y anomalía de rayos en el tiempo
  - dispersion_indice_vs_z.png  scatter índice vs anomalía estandarizada
  - boxplot_por_fase.png        distribución de la anomalía por fase
  - ciclo_anual_rayos.png       climatología mensual del periodo
  - correlacion_lags.png        correlación por rezago (si existe el CSV)

Uso:
    python graficar_enso.py --entrada analisis_ENSO_nino12/wwlln_indice_mensual.csv \
                            --salida analisis_ENSO_nino12 \
                            --nombre-indice "Niño 1+2" \
                            --umbral-frio -1.0 --umbral-calido 0.4
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORES = {"El Nino": "#d62728", "La Nina": "#1f77b4", "Neutral": "#7f7f7f"}
ETIQ_FASE = {"El Nino": "Cálida", "La Nina": "Fría", "Neutral": "Neutral"}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]


def simetrizar(ax):
    """Deja el 0 del eje en el centro vertical, para que los dos ejes gemelos
    compartan la línea de cero."""
    lo, hi = ax.get_ylim()
    m = max(abs(lo), abs(hi))
    ax.set_ylim(-m, m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", type=Path,
                    default=Path("analisis_ENSO/wwlln_indice_mensual.csv"))
    ap.add_argument("--salida", type=Path, default=Path("analisis_ENSO"))
    ap.add_argument("--nombre-indice", default="Índice ENSO")
    ap.add_argument("--umbral-frio", type=float, default=-0.5)
    ap.add_argument("--umbral-calido", type=float, default=0.5)
    args = ap.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.entrada, parse_dates=["fecha"])
    if "valor" not in df.columns and "oni" in df.columns:
        df = df.rename(columns={"oni": "valor"})
    col = "n_rayos_norm" if "n_rayos_norm" in df.columns else "n_rayos"
    nom = args.nombre_indice
    per = f"{df['anio'].min()}-{df['anio'].max()}"

    # ------------------------------------------------------------------
    # 1. Serie temporal
    # ------------------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(13, 5.5))

    ax1.axhline(0, color="black", lw=0.8)
    ax1.fill_between(df["fecha"], 0, df["valor"], where=df["valor"] >= 0,
                     color=COLORES["El Nino"], alpha=0.35,
                     label=f"{nom} > 0 (cálido)", interpolate=True)
    ax1.fill_between(df["fecha"], 0, df["valor"], where=df["valor"] < 0,
                     color=COLORES["La Nina"], alpha=0.35,
                     label=f"{nom} < 0 (frío)", interpolate=True)
    ax1.axhline(args.umbral_calido, color=COLORES["El Nino"], ls=":", lw=1.1)
    ax1.axhline(args.umbral_frio, color=COLORES["La Nina"], ls=":", lw=1.1)
    ax1.set_ylabel(f"{nom} (°C)")
    ax1.set_xlabel("Fecha")
    simetrizar(ax1)

    ax2 = ax1.twinx()
    ax2.plot(df["fecha"], df["z"], color="black", marker="o", ms=3.5, lw=1.4,
             label="Anomalía de rayos (z)")
    ax2.set_ylabel("Anomalía estandarizada de rayos (z)")
    simetrizar(ax2)

    l1, e1 = ax1.get_legend_handles_labels()
    l2, e2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, e1 + e2, loc="upper left", fontsize=9, framealpha=0.9)
    ax1.set_title(f"{nom} y anomalía mensual de actividad eléctrica — Perú {per}")
    plt.tight_layout()
    plt.savefig(args.salida / "serie_indice_vs_rayos.png", dpi=300)
    plt.close()

    # ------------------------------------------------------------------
    # 2. Dispersión
    # ------------------------------------------------------------------
    sub = df.dropna(subset=["valor", "z"])

    plt.figure(figsize=(7.5, 6))
    for fase, g in sub.groupby("fase_enso"):
        plt.scatter(g["valor"], g["z"], s=55, alpha=0.8,
                    color=COLORES.get(fase, "gray"), edgecolor="white",
                    linewidth=0.6, label=ETIQ_FASE.get(fase, fase))
    if len(sub) > 3:
        m, b = np.polyfit(sub["valor"], sub["z"], 1)
        xs = np.linspace(sub["valor"].min(), sub["valor"].max(), 100)
        r = np.corrcoef(sub["valor"], sub["z"])[0, 1]
        plt.plot(xs, m * xs + b, color="black", ls="--", lw=1.2,
                 label=f"ajuste lineal (r = {r:+.3f})")
    plt.axhline(0, color="gray", lw=0.7)
    plt.axvline(0, color="gray", lw=0.7)
    plt.xlabel(f"{nom} (°C)")
    plt.ylabel("Anomalía estandarizada de rayos (z)")
    plt.title(f"{nom} vs anomalía de rayos — Perú (n={len(sub)} meses)")
    plt.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(args.salida / "dispersion_indice_vs_z.png", dpi=300)
    plt.close()

    # ------------------------------------------------------------------
    # 3. Boxplot por fase
    # ------------------------------------------------------------------
    orden = [f for f in ["La Nina", "Neutral", "El Nino"]
             if (sub["fase_enso"] == f).any()]
    datos = [sub.loc[sub["fase_enso"] == f, "z"].dropna().values for f in orden]
    etiquetas = [ETIQ_FASE.get(f, f) for f in orden]

    plt.figure(figsize=(7.5, 5.5))
    try:
        bp = plt.boxplot(datos, tick_labels=etiquetas, patch_artist=True, widths=0.55)
    except TypeError:      # matplotlib < 3.9
        bp = plt.boxplot(datos, labels=etiquetas, patch_artist=True, widths=0.55)
    for parche, fase in zip(bp["boxes"], orden):
        parche.set_facecolor(COLORES[fase])
        parche.set_alpha(0.55)
    for mediana in bp["medians"]:
        mediana.set_color("black")
        mediana.set_linewidth(1.6)
    for i, valores in enumerate(datos, start=1):
        x = np.random.normal(i, 0.055, len(valores))
        plt.scatter(x, valores, s=22, color="black", alpha=0.45, zorder=3)
        plt.text(i, plt.ylim()[1] * 0.92, f"n={len(valores)}",
                 ha="center", fontsize=9)
    plt.axhline(0, color="gray", ls="--", lw=0.9)
    plt.ylabel("Anomalía estandarizada de rayos (z)")
    plt.title(f"Anomalía de rayos por fase de {nom}\nPerú {per}")
    plt.tight_layout()
    plt.savefig(args.salida / "boxplot_por_fase.png", dpi=300)
    plt.close()

    # ------------------------------------------------------------------
    # 4. Ciclo anual
    # ------------------------------------------------------------------
    clim = df.groupby("mes")[col].agg(["mean", "std"]).reset_index()
    plt.figure(figsize=(9, 5))
    plt.bar(clim["mes"], clim["mean"], yerr=clim["std"], capsize=4,
            color="#2b7bba", alpha=0.85)
    plt.xticks(range(1, 13), MESES)
    plt.xlabel("Mes")
    plt.ylabel("Rayos por mes (normalizado a mes completo)")
    plt.title(f"Ciclo anual de actividad eléctrica — Perú {per}\n"
              "(barras = media, líneas = desviación estándar)")
    plt.tight_layout()
    plt.savefig(args.salida / "ciclo_anual_rayos.png", dpi=300)
    plt.close()

    # ------------------------------------------------------------------
    # 5. Correlación por rezago
    # ------------------------------------------------------------------
    ruta_lags = args.entrada.parent / "correlaciones_lag.csv"
    if ruta_lags.exists():
        lg = pd.read_csv(ruta_lags)
        plt.figure(figsize=(8, 4.5))
        plt.bar(lg["lag_meses"], lg["pearson_r"], color="#5a5a8a", alpha=0.85)
        # banda de |r| no distinguible de cero con el n efectivo mediano
        ne = lg["n_efectivo"].median()
        if ne > 3:
            crit = 1.96 / np.sqrt(ne)
            plt.axhspan(-crit, crit, color="gray", alpha=0.18,
                        label=f"|r| < {crit:.2f} (ruido, n efectivo ≈ {ne:.0f})")
            plt.legend(fontsize=9)
        plt.axhline(0, color="black", lw=0.8)
        plt.xlabel(f"Rezago (meses; {nom} adelanta a los rayos)")
        plt.ylabel("Pearson r")
        plt.ylim(-1, 1)
        plt.title(f"Correlación {nom} vs anomalía de rayos por rezago — Perú {per}")
        plt.tight_layout()
        plt.savefig(args.salida / "correlacion_lags.png", dpi=300)
        plt.close()

    print("Gráficas escritas en:", args.salida.resolve())


if __name__ == "__main__":
    main()
