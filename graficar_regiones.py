#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
graficar_regiones.py
====================
Figuras del análisis estratificado por región (salida de regionalizar_peru.py).

Genera:
  mapa_regiones.png             el mapa de las tres regiones y las curvas límite
  ciclo_anual_por_region.png    climatología mensual, escala logarítmica
  serie_costa.png               serie mensual de la costa, con 2023 destacado
  anomalia_por_fase_region.png  anomalía z por fase de Niño 1+2 y por región

Uso:
    python3 graficar_regiones.py --entrada analisis_regiones
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

import regionalizar_peru as R

COLOR = {"Costa": "#e8c547", "Andes": "#a0522d", "Amazonia": "#2e8b57"}
ETIQ = {"Costa": "Costa", "Andes": "Andes", "Amazonia": "Amazonía"}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]
FASES = [("La Nina", "Fría"), ("Neutral", "Neutral"), ("El Nino", "Cálida")]


def mapa(entrada: Path, salida: Path):
    lim = pd.read_csv(entrada / "limites_regiones.csv")
    f_w, f_e = R.interpoladores(lim)
    geom = R.cargar_peru()
    from shapely.geometry import Point
    from shapely.prepared import prep
    p = prep(geom)

    paso = 0.05
    glat = np.arange(-19, 1, paso)
    glon = np.arange(-82, -68, paso)
    campo = np.full((len(glat), len(glon)), np.nan)
    for i, la in enumerate(glat):
        lw, le = float(f_w(la)), float(f_e(la))
        for j, lo in enumerate(glon):
            if not p.contains(Point(lo + paso / 2, la + paso / 2)):
                continue
            campo[i, j] = 0 if lo < lw else (1 if lo <= le else 2)

    fig, ax = plt.subplots(figsize=(8, 10))
    cmap = ListedColormap([COLOR["Costa"], COLOR["Andes"], COLOR["Amazonia"]])
    ax.pcolormesh(glon, glat, campo, cmap=cmap, vmin=-0.5, vmax=2.5,
                  shading="auto")

    # contorno del Peru
    geoms = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for g in geoms:
        x, y = g.exterior.xy
        ax.plot(x, y, color="black", lw=1.0)

    lat_f = np.linspace(-19, 1, 400)
    ax.plot(f_w(lat_f), lat_f, color="black", ls="--", lw=1.6,
            label="límite Costa / Andes")
    ax.plot(f_e(lat_f), lat_f, color="black", ls=":", lw=1.8,
            label="límite Andes / Amazonía")
    ax.scatter(lim["lon_w"], lim["lat"], color="black", s=22, zorder=5)
    ax.scatter(lim["lon_e"], lim["lat"], color="black", s=22, marker="s", zorder=5)

    ax.set_xlim(-82, -68)
    ax.set_ylim(-19, 1)
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.set_title("Regiones derivadas de la elevación (umbral 1000 m)\n"
                 "Puntos = transectos ETOPO1 muestreados", fontsize=12)
    handles = [Patch(facecolor=COLOR[r], label=ETIQ[r]) for r in COLOR]
    handles += ax.get_legend_handles_labels()[0]
    ax.legend(handles=handles, loc="lower left", fontsize=9)
    ax.set_aspect("equal")
    plt.tight_layout()
    plt.savefig(salida / "mapa_regiones.png", dpi=200)
    plt.close()


def ciclo_anual(d: pd.DataFrame, salida: Path):
    clim = d.groupby(["region", "mes"])["n_rayos_norm"].mean().unstack()
    plt.figure(figsize=(9, 5.5))
    for r in ["Amazonia", "Andes", "Costa"]:
        plt.plot(range(1, 13), clim.loc[r], marker="o", lw=2,
                 color=COLOR[r], label=ETIQ[r])
    plt.yscale("log")
    plt.xticks(range(1, 13), MESES)
    plt.ylabel("Rayos por mes (media 2021-2025, escala log)")
    plt.xlabel("Mes")
    plt.grid(alpha=0.3, which="both")
    plt.legend()
    plt.title("Ciclo anual de actividad eléctrica por región — Perú 2021-2025")
    plt.tight_layout()
    plt.savefig(salida / "ciclo_anual_por_region.png", dpi=200)
    plt.close()


def serie_costa(d: pd.DataFrame, salida: Path):
    c = d[d["region"] == "Costa"].sort_values(["anio", "mes"]).reset_index(drop=True)
    fecha = pd.to_datetime(dict(year=c["anio"], month=c["mes"], day=1))
    plt.figure(figsize=(12, 5))
    colores = ["#d62728" if a == 2023 else "#e8c547" for a in c["anio"]]
    plt.bar(fecha, c["n_rayos"] + 1, width=22, color=colores)
    plt.yscale("log")
    plt.ylabel("Rayos por mes en la costa (+1, escala log)")
    plt.xlabel("Fecha")
    pico = c.loc[c["n_rayos"].idxmax()]
    plt.annotate(f"abril 2023: {int(pico['n_rayos']):,}",
                 xy=(pd.Timestamp("2023-04-01"), pico["n_rayos"]),
                 xytext=(pd.Timestamp("2023-08-01"), pico["n_rayos"] * 1.6),
                 arrowprops=dict(arrowstyle="->", lw=1.2), fontsize=10)
    plt.title("Actividad eléctrica en la costa peruana — el Niño costero de 2023\n"
              "(rojo = 2023)")
    plt.grid(alpha=0.3, axis="y", which="both")
    plt.tight_layout()
    plt.savefig(salida / "serie_costa.png", dpi=200)
    plt.close()


def anomalia_por_fase(entrada: Path, salida: Path):
    filas = []
    for r in ["Costa", "Andes", "Amazonia"]:
        f = pd.read_csv(entrada / f"enso_{r.lower()}" / "wwlln_por_fase.csv")
        f = f.set_index("fase_enso")
        for fase, etiq in FASES:
            filas.append({"region": r, "fase": etiq, "z": f.loc[fase, "z_medio"],
                          "n": int(f.loc[fase, "n_meses"])})
    t = pd.DataFrame(filas)

    x = np.arange(3)
    ancho = 0.26
    plt.figure(figsize=(9, 5.5))
    for k, (_, etiq) in enumerate(FASES):
        sub = t[t["fase"] == etiq].set_index("region").loc[["Costa", "Andes", "Amazonia"]]
        plt.bar(x + (k - 1) * ancho, sub["z"], ancho, label=f"{etiq} (n={sub['n'].iloc[0]})",
                color=["#1f77b4", "#7f7f7f", "#d62728"][k], alpha=0.85)
    plt.axhline(0, color="black", lw=0.9)
    plt.xticks(x, [ETIQ[r] for r in ["Costa", "Andes", "Amazonia"]])
    plt.ylabel("Anomalía estandarizada de rayos (z)")
    plt.title("Anomalía de rayos por fase de Niño 1+2 y por región\n"
              "Perú 2021-2025 — el signo se invierte de la costa a la Amazonía")
    plt.legend(fontsize=9)
    plt.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(salida / "anomalia_por_fase_region.png", dpi=200)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", type=Path, default=Path("analisis_regiones"))
    args = ap.parse_args()
    d = pd.read_csv(args.entrada / "wwlln_mensual_por_region.csv")
    mapa(args.entrada, args.entrada)
    ciclo_anual(d, args.entrada)
    serie_costa(d, args.entrada)
    anomalia_por_fase(args.entrada, args.entrada)
    print("Figuras escritas en:", args.entrada.resolve())


if __name__ == "__main__":
    main()
