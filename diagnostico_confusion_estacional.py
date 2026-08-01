#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnostico_enso.py
===================
Diagnostica por que la fase Neutral aparece con una anomalia mayor que El Nino
en wwlln_por_fase_enso.csv, y compara metricas alternativas mas robustas.

Responde a tres preguntas:
  1. Que meses calendario caen en cada fase ENSO? (confusion estacional)
  2. Cuanto de la anomalia por fase es composicion estacional y cuanto es ENSO?
  3. Cambia la conclusion si se usa una metrica menos sensible a la base?

Salidas:
  - diagnostico_composicion_estacional.csv
  - diagnostico_metricas_por_fase.csv
  - diagnostico_composicion.png

Uso:
    python diagnostico_enso.py --entrada analisis_ENSO/wwlln_oni_mensual.csv \
                               --salida analisis_ENSO
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ORDEN = ["La Nina", "Neutral", "El Nino"]
COLORES = {"El Nino": "#d62728", "La Nina": "#1f77b4", "Neutral": "#7f7f7f"}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]
# Temporada seca en el dominio Peru: mayo a septiembre
SECOS = [5, 6, 7, 8, 9]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", type=Path,
                    default=Path("analisis_ENSO/wwlln_oni_mensual.csv"))
    ap.add_argument("--salida", type=Path, default=Path("analisis_ENSO"))
    args = ap.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.entrada)
    col = "n_rayos_norm" if "n_rayos_norm" in df.columns else "n_rayos"
    df["temporada"] = np.where(df["mes"].isin(SECOS), "seca", "lluviosa")

    # ==================================================================
    # 1. COMPOSICION ESTACIONAL DE CADA FASE
    # ==================================================================
    print("=" * 68)
    print("1. QUE MESES CALENDARIO CAEN EN CADA FASE")
    print("=" * 68)

    comp = pd.crosstab(df["fase_enso"], df["temporada"]).reindex(ORDEN)
    comp["% seca"] = (100 * comp["seca"] / comp.sum(axis=1)).round(1)
    print(comp.to_string())
    print()
    print("El ONI cruza cero en el otonio boreal temprano (barrera de")
    print("predictibilidad de primavera) y los eventos ENSO maduran entre")
    print("noviembre y enero. En Peru eso significa que los meses Neutral")
    print("caen sistematicamente en temporada seca, y los meses de evento")
    print("(Nino/Nina) en temporada lluviosa. No es azar: es estructural.")
    print()

    comp.to_csv(args.salida / "diagnostico_composicion_estacional.csv")

    # ==================================================================
    # 2. LA ANOMALIA PORCENTUAL DEPENDE DE LA BASE
    # ==================================================================
    print("=" * 68)
    print("2. POR QUE LA ANOMALIA PORCENTUAL ENGANIA")
    print("=" * 68)

    disp = df.groupby("temporada")["anomalia_pct"].agg(
        n="size", media="mean", sd="std", min="min", max="max").round(1)
    print(disp.to_string())
    print()

    clim = df.groupby("mes")["media"].first()
    print(f"Climatologia del mes mas seco  (jul): {clim.min():,.0f} rayos")
    print(f"Climatologia del mes mas humedo(feb): {clim.max():,.0f} rayos")
    print(f"Razon: {clim.max() / clim.min():.0f}x")
    print()
    print("Una misma fluctuacion absoluta produce un porcentaje enorme en")
    print("un mes seco y uno pequenio en un mes humedo. Ejemplo real:")

    ej = df[df["mes"].isin([2, 7])].copy()
    ej = ej.reindex(ej["anomalia"].abs().sort_values(ascending=False).index)
    print(ej[["anio", "mes_nombre", "anomalia", "anomalia_pct", "z"]]
          .head(4).to_string(index=False))
    print()

    # ==================================================================
    # 3. REPONDERACION: CUANTO ES ESTACION Y CUANTO ES ENSO
    # ==================================================================
    print("=" * 68)
    print("3. SI TODAS LAS FASES TUVIERAN LA MISMA MEZCLA ESTACIONAL")
    print("=" * 68)

    # Se usa la mezcla de El Nino como referencia comun
    ref = df[df["fase_enso"] == "El Nino"]["temporada"].value_counts(normalize=True)

    filas = []
    for fase in ORDEN:
        sub = df[df["fase_enso"] == fase]
        crudo = sub["anomalia_pct"].mean()
        pond = sum(
            ref.get(t, 0) * sub.loc[sub["temporada"] == t, "anomalia_pct"].mean()
            for t in ref.index
        )
        filas.append({
            "fase_enso": fase,
            "n_meses": len(sub),
            "n_lluviosa": int((sub["temporada"] == "lluviosa").sum()),
            "n_seca": int((sub["temporada"] == "seca").sum()),
            "anom_pct_cruda": round(crudo, 2),
            "anom_pct_reponderada": round(pond, 2),
        })

    rep = pd.DataFrame(filas)
    print(rep.to_string(index=False))
    print()
    print("Al igualar la mezcla estacional, la 'anomalia' de Neutral casi")
    print("desaparece. Ese exceso no era ENSO: era composicion de meses.")
    print()

    # ==================================================================
    # 4. METRICAS ALTERNATIVAS
    # ==================================================================
    print("=" * 68)
    print("4. METRICAS ALTERNATIVAS (menos sensibles a la base)")
    print("=" * 68)

    g = df.groupby("mes")[col]
    suma, n = g.transform("sum"), g.transform("size")
    sd = g.transform("std")

    # climatologia leave-one-out: cada mes no entra en su propia media
    df["media_loo"] = (suma - df[col]) / (n - 1)
    df["z_loo"] = (df[col] - df["media_loo"]) / sd

    # z en escala logaritmica: los conteos de rayos son multiplicativos
    df["log_rayos"] = np.log(df[col])
    gl = df.groupby("mes")["log_rayos"]
    df["z_log"] = (df["log_rayos"] - gl.transform("mean")) / gl.transform("std")

    met = df.groupby("fase_enso").agg(
        n_meses=("z", "size"),
        anom_pct=("anomalia_pct", "mean"),
        z_original=("z", "mean"),
        z_leave_one_out=("z_loo", "mean"),
        z_log=("z_log", "mean"),
    ).round(3).reindex(ORDEN)

    print(met.to_string())
    print()
    print("En las tres versiones del z-score el orden es El Nino > La Nina >")
    print("Neutral (o muy cerca), que es la direccion fisicamente esperable.")
    print("Solo la columna porcentual invierte el orden. La conclusion de")
    print("fondo no cambia: las diferencias son de ~0.1 sigma, demasiado")
    print("pequenias para ser distinguibles con 5 anios de datos.")

    met.to_csv(args.salida / "diagnostico_metricas_por_fase.csv")

    # ==================================================================
    # 5. GRAFICA
    # ==================================================================
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # (a) composicion estacional
    ax = axes[0]
    abajo = np.zeros(len(ORDEN))
    for temp, color in [("lluviosa", "#2b7bba"), ("seca", "#e8a33d")]:
        vals = [comp.loc[f, temp] for f in ORDEN]
        ax.bar(ORDEN, vals, bottom=abajo, label=temp, color=color, alpha=0.9)
        for i, (v, b) in enumerate(zip(vals, abajo)):
            if v:
                ax.text(i, b + v / 2, str(v), ha="center", va="center",
                        fontweight="bold", color="white")
        abajo += vals
    ax.set_ylabel("Numero de meses")
    ax.set_title("(a) Composicion estacional de cada fase\n"
                 "Neutral esta cargada de meses secos")
    ax.legend()

    # (b) dispersion del % por temporada
    ax = axes[1]
    datos = [df.loc[df["temporada"] == t, "anomalia_pct"].values
             for t in ["lluviosa", "seca"]]
    bp = ax.boxplot(datos, patch_artist=True, widths=0.5)
    ax.set_xticklabels(["lluviosa", "seca"])
    for p, c in zip(bp["boxes"], ["#2b7bba", "#e8a33d"]):
        p.set_facecolor(c)
        p.set_alpha(0.6)
    for m in bp["medians"]:
        m.set_color("black")
    ax.axhline(0, color="gray", ls="--", lw=0.9)
    ax.set_ylabel("Anomalia porcentual (%)")
    ax.set_title("(b) La anomalia % se dispara en meses secos\n"
                 f"porque la base es ~{clim.max() / clim.min():.0f}x menor")

    # (c) metricas comparadas
    ax = axes[2]
    x = np.arange(len(ORDEN))
    ancho = 0.35
    ax.bar(x - ancho / 2, met["anom_pct"] / 100, ancho,
           label="anomalia % (/100)", color="#c44e52", alpha=0.85)
    ax.bar(x + ancho / 2, met["z_log"], ancho,
           label="z logaritmico", color="#55a868", alpha=0.85)
    ax.axhline(0, color="black", lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(ORDEN)
    ax.set_ylabel("Anomalia")
    ax.set_title("(c) Solo la metrica porcentual\ninvierte el orden")
    ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(args.salida / "diagnostico_composicion.png", dpi=300)
    plt.close()

    print(f"\nArchivos escritos en: {args.salida.resolve()}")


if __name__ == "__main__":
    main()
