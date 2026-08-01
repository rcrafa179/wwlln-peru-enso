#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
figuras_presentacion.py
=======================
Versiones de presentación de las dos figuras que faltaban.

Las gráficas que hay dentro de `analisis_YYYY/` son de trabajo: una por año,
ejes en UTC, sin tildes, sin barras de error. Sirven para revisar el
procesamiento, no para proyectar. Estas dos son las que van a la charla.

  ciclo_diurno_local.png
      Ciclo diurno en HORA LOCAL (UTC−5), los cinco años superpuestos.
      El punto es que las cinco curvas son la misma: máximo a las 16 h,
      mínimo a las 9 h, sin excepción. En UTC el máximo cae a las 21 h y
      parece un fenómeno nocturno, que es justo lo contrario de lo que pasa.

  deficit_2025.png
      El déficit de 2025 y su control. Panel izquierdo: totales anuales.
      Panel derecho: participación del Perú en el conteo global de WWLLN.
      Si la caída fuera por pérdida de archivos o degradación de la red, la
      participación no se movería. Se mueve un 26%.

Uso:
    python3 figuras_presentacion.py --salida figuras_presentacion
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ANIOS = [2021, 2022, 2023, 2024, 2025]
UTC_A_LOCAL = -5          # Perú es UTC−5 todo el año, sin horario de verano
COLORES = ["#4c72b0", "#55a868", "#c44e52", "#8172b2", "#d62728"]


def ciclo_diurno(salida: Path):
    fig, ax = plt.subplots(figsize=(11, 6))
    curvas = []
    for anio, color in zip(ANIOS, COLORES):
        h = pd.read_csv(f"analisis_{anio}/wwlln_peru_horario_{anio}.csv")
        h["hora_local"] = (h["hour"] + UTC_A_LOCAL) % 24
        h = h.sort_values("hora_local")
        pct = 100 * h["n_eventos"] / h["n_eventos"].sum()
        curvas.append(pct.values)
        grosor = 3.0 if anio == 2025 else 1.6
        ax.plot(h["hora_local"], pct, color=color, lw=grosor, marker="o", ms=4,
                label=f"{anio}", alpha=0.9)

    media = np.mean(curvas, axis=0)
    ax.plot(range(24), media, color="black", lw=2.6, ls="--", label="media 2021-2025")

    ax.axvspan(12, 20, color="orange", alpha=0.08)
    ax.text(16, ax.get_ylim()[1] * 0.96, "tarde", ha="center", fontsize=10,
            color="#996600")
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("Hora local (UTC−5)")
    ax.set_ylabel("% de los rayos del año")
    ax.set_xlim(-0.5, 23.5)
    ax.grid(alpha=0.3)
    ax.legend(ncol=3, fontsize=9)
    ax.set_title("Ciclo diurno de la actividad eléctrica — Perú, 2021-2025\n"
                 "Máximo a las 16 h y mínimo a las 9 h, idéntico los cinco años",
                 fontsize=12)
    plt.tight_layout()
    plt.savefig(salida / "ciclo_diurno_local.png", dpi=200)
    plt.close()

    pico = [int((np.argmax(c))) for c in curvas]
    valle = [int((np.argmin(c))) for c in curvas]
    razon = [c.max() / c.min() for c in curvas]
    return pd.DataFrame({"anio": ANIOS, "hora_pico_local": pico,
                         "hora_valle_local": valle,
                         "razon_max_min": np.round(razon, 1)})


def deficit_2025(salida: Path):
    tot = {}
    for a in ANIOS:
        r = pd.read_csv(f"analisis_{a}/resumen_anual_wwlln_peru_{a}.csv") \
              .set_index("variable")["valor"]
        tot[a] = int(r["total_eventos"])

    glob_filas = []
    for f in sorted(glob.glob("analisis_ENSO/conteo_global_*.csv")):
        d = pd.read_csv(f)
        glob_filas.append({"anio": int(d["anio"].iloc[0]), "n_dias": len(d),
                           "global_dia": d["global"].mean(),
                           "peru_dia": d["peru"].mean(),
                           "peru_por_millon": 1e6 * d["peru"].sum() / d["global"].sum()})
    g = pd.DataFrame(glob_filas).sort_values("anio")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.5))

    colores = ["#4c72b0"] * 4 + ["#d62728"]
    a1.bar(ANIOS, [tot[a] / 1e6 for a in ANIOS], color=colores, alpha=0.9)
    media4 = np.mean([tot[a] for a in ANIOS[:4]]) / 1e6
    a1.axhline(media4, color="black", ls="--", lw=1.2,
               label=f"media 2021-2024 = {media4:.2f} M")
    caida = 100 * (tot[2025] / np.mean([tot[a] for a in ANIOS[:4]]) - 1)
    a1.annotate(f"{caida:+.0f}%", xy=(2025, tot[2025] / 1e6),
                xytext=(2025, media4 * 0.97), ha="center", fontsize=13,
                color="#d62728", fontweight="bold")
    for a in ANIOS:
        a1.text(a, tot[a] / 1e6 + 0.15, f"{tot[a]/1e6:.2f}", ha="center", fontsize=9)
    a1.set_ylabel("Millones de rayos en el dominio")
    a1.set_xlabel("Año")
    a1.set_xticks(ANIOS)
    a1.set_ylim(0, 11)
    a1.legend(fontsize=9)
    a1.set_title("2025 es el año más bajo de la serie")
    a1.grid(alpha=0.3, axis="y")

    cg = ["#4c72b0", "#4c72b0", "#d62728"]
    a2.bar(g["anio"], g["peru_por_millon"], color=cg, alpha=0.9, width=0.6)
    base = g[g["anio"] < 2025]["peru_por_millon"].mean()
    a2.axhline(base, color="black", ls="--", lw=1.2,
               label=f"media 2023-2024 = {base:,.0f}")
    d = 100 * (g[g["anio"] == 2025]["peru_por_millon"].iloc[0] / base - 1)
    a2.annotate(f"{d:+.1f}%",
                xy=(2025, g[g['anio'] == 2025]['peru_por_millon'].iloc[0]),
                xytext=(2025, base * 0.93), ha="center", fontsize=13,
                color="#d62728", fontweight="bold")
    for _, r in g.iterrows():
        a2.text(r["anio"], r["peru_por_millon"] + 700,
                f"{r['peru_por_millon']:,.0f}", ha="center", fontsize=9)
    a2.set_ylabel("Rayos en Perú por millón de rayos globales")
    a2.set_xlabel("Año")
    a2.set_xticks(g["anio"])
    a2.set_ylim(0, 42000)
    a2.legend(fontsize=9)
    a2.set_title("No es la red: la participación del Perú también cae")
    a2.grid(alpha=0.3, axis="y")

    fig.suptitle("El déficit de actividad eléctrica de 2025 sobre el Perú",
                 fontsize=13)
    plt.tight_layout()
    plt.savefig(salida / "deficit_2025.png", dpi=200)
    plt.close()

    g["global_vs_2023_24_pct"] = np.round(
        100 * (g["global_dia"] / g[g["anio"] < 2025]["global_dia"].mean() - 1), 1)
    g["peru_vs_2023_24_pct"] = np.round(
        100 * (g["peru_dia"] / g[g["anio"] < 2025]["peru_dia"].mean() - 1), 1)
    return g.round(0), tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", type=Path, default=Path("figuras_presentacion"))
    args = ap.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)

    d = ciclo_diurno(args.salida)
    print("=== Ciclo diurno en hora local ===")
    print(d.to_string(index=False))
    d.to_csv(args.salida / "ciclo_diurno_resumen.csv", index=False)

    g, tot = deficit_2025(args.salida)
    print("\n=== Control global del déficit de 2025 ===")
    print(g.to_string(index=False))
    g.to_csv(args.salida / "deficit_2025_control_global.csv", index=False)

    print("\n=== Totales anuales (dominio completo) ===")
    for a, v in tot.items():
        print(f"  {a}: {v:>10,}")

    print(f"\nFiguras en: {args.salida.resolve()}")


if __name__ == "__main__":
    main()
