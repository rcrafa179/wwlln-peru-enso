"""
Version generalizada de analisis_mensual_anual_wwlln2025.py: sirve para
cualquier anio, no solo 2025. Genera los mismos resumenes (anual, mensual,
horario, energia) + graficas + texto interpretativo automatico.

Uso:
    python analisis_anual_wwlln.py --entrada peru_wwlln_2021_limpio.parquet --anio 2021 --salida analisis_2021

Si no pasas --anio, lo detecta automaticamente a partir de los datos
(usa el anio mas frecuente en el parquet).
"""
import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre",
    12: "Diciembre"
}


def main():
    ap = argparse.ArgumentParser(description="Analisis mensual/anual WWLLN (generico, cualquier anio)")
    ap.add_argument("--entrada", required=True, help="Parquet limpio de entrada")
    ap.add_argument("--anio", type=int, default=None, help="Anio a analizar (si se omite, se detecta solo)")
    ap.add_argument("--salida", required=True, help="Carpeta de salida")
    args = ap.parse_args()

    os.makedirs(args.salida, exist_ok=True)

    df = pd.read_parquet(args.entrada)
    df["datetime"] = pd.to_datetime(df["datetime"])

    anio = args.anio or int(df["datetime"].dt.year.mode()[0])
    df = df[df["datetime"].dt.year == anio].copy()

    if df.empty:
        print(f"No hay datos para el anio {anio} en {args.entrada}")
        return

    print(f"Analizando anio {anio}")
    print("Total de eventos:", len(df))
    print("Rango temporal:", df["datetime"].min(), "->", df["datetime"].max())

    df["date"] = df["datetime"].dt.date
    df["month"] = df["datetime"].dt.month
    df["hour"] = df["datetime"].dt.hour

    # ============================================================
    # 1. ANALISIS ANUAL
    # ============================================================
    total_anual = len(df)
    eventos_con_energia = df["energy_j"].notna().sum()
    eventos_sin_energia = df["energy_j"].isna().sum()

    resumen_anual = pd.DataFrame({
        "variable": [
            "anio", "total_eventos", "eventos_con_energia", "eventos_sin_energia",
            "porcentaje_con_energia", "porcentaje_sin_energia",
            "fecha_inicio", "fecha_fin",
            "lat_min", "lat_max", "lon_min", "lon_max",
            "residual_promedio_km", "nstations_promedio"
        ],
        "valor": [
            anio, total_anual, eventos_con_energia, eventos_sin_energia,
            eventos_con_energia / total_anual * 100,
            eventos_sin_energia / total_anual * 100,
            df["datetime"].min(), df["datetime"].max(),
            df["lat"].min(), df["lat"].max(),
            df["lon"].min(), df["lon"].max(),
            df["residual_km"].mean(), df["nstations"].mean()
        ]
    })
    resumen_anual.to_csv(f"{args.salida}/resumen_anual_wwlln_peru_{anio}.csv", index=False)

    energia_valida = df.loc[df["energy_j"].notna(), "energy_j"]
    if not energia_valida.empty:
        energia_valida.describe().to_csv(f"{args.salida}/resumen_energia_anual_wwlln_peru_{anio}.csv")
    del energia_valida

    # ============================================================
    # 2. ANALISIS MENSUAL
    # ============================================================
    mensual = (
        df.groupby("month")
          .agg(
              n_eventos=("datetime", "count"),
              eventos_con_energia=("energy_j", lambda x: x.notna().sum()),
              eventos_sin_energia=("energy_j", lambda x: x.isna().sum()),
              energia_media_j=("energy_j", "mean"),
              energia_mediana_j=("energy_j", "median"),
              energia_max_j=("energy_j", "max"),
              residual_promedio_km=("residual_km", "mean"),
              nstations_promedio=("nstations", "mean")
          )
          .reset_index()
    )

    dias_por_mes = df.groupby("month")["date"].nunique().reset_index(name="dias_con_datos")
    mensual = mensual.merge(dias_por_mes, on="month", how="left")

    mensual["porcentaje_anual"] = mensual["n_eventos"] / total_anual * 100
    mensual["promedio_diario"] = mensual["n_eventos"] / mensual["dias_con_datos"]
    mensual["porcentaje_con_energia"] = mensual["eventos_con_energia"] / mensual["n_eventos"] * 100
    mensual["porcentaje_sin_energia"] = mensual["eventos_sin_energia"] / mensual["n_eventos"] * 100
    mensual["mes"] = mensual["month"].map(MESES)

    mensual = mensual[[
        "month", "mes", "n_eventos", "porcentaje_anual", "dias_con_datos",
        "promedio_diario", "eventos_con_energia", "eventos_sin_energia",
        "porcentaje_con_energia", "porcentaje_sin_energia",
        "energia_media_j", "energia_mediana_j", "energia_max_j",
        "residual_promedio_km", "nstations_promedio"
    ]]
    mensual.to_csv(f"{args.salida}/analisis_mensual_wwlln_peru_{anio}.csv", index=False)

    # ============================================================
    # 3. ANALISIS DIARIO Y HORARIO (igual que analizar_wwlln.py)
    # ============================================================
    diario = df.groupby("date").size().reset_index(name="n_eventos")
    diario.to_csv(f"{args.salida}/wwlln_peru_diario_{anio}.csv", index=False)

    horario = df.groupby("hour").size().reset_index(name="n_eventos")
    horario.to_csv(f"{args.salida}/wwlln_peru_horario_{anio}.csv", index=False)

    # ============================================================
    # 4. MAXIMOS Y MINIMOS
    # ============================================================
    mes_max = mensual.loc[mensual["n_eventos"].idxmax()]
    mes_min = mensual.loc[mensual["n_eventos"].idxmin()]

    print("\nResumen mensual:")
    print(mensual)
    print("\nMes con mayor actividad:", mes_max["mes"], int(mes_max["n_eventos"]))
    print("Mes con menor actividad:", mes_min["mes"], int(mes_min["n_eventos"]))

    # ============================================================
    # 5. GRAFICAS
    # ============================================================
    plt.figure(figsize=(10, 5))
    plt.bar(mensual["mes"], mensual["n_eventos"])
    plt.xlabel("Mes")
    plt.ylabel("Numero de eventos WWLLN")
    plt.title(f"Actividad electrica mensual en Peru - WWLLN {anio}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{args.salida}/grafico_eventos_mensuales_wwlln_peru_{anio}.png", dpi=300)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(mensual["mes"], mensual["porcentaje_anual"], marker="o")
    plt.xlabel("Mes")
    plt.ylabel("Porcentaje respecto al total anual (%)")
    plt.title(f"Contribucion mensual a la actividad electrica anual - WWLLN {anio}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{args.salida}/grafico_porcentaje_mensual_wwlln_peru_{anio}.png", dpi=300)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.bar(mensual["mes"], mensual["promedio_diario"])
    plt.xlabel("Mes")
    plt.ylabel("Promedio diario de eventos")
    plt.title(f"Promedio diario mensual de eventos WWLLN - Peru {anio}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{args.salida}/grafico_promedio_diario_mensual_wwlln_peru_{anio}.png", dpi=300)
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.bar(horario["hour"], horario["n_eventos"])
    plt.xlabel("Hora del dia (UTC)")
    plt.ylabel("Numero de eventos WWLLN")
    plt.title(f"Ciclo horario de actividad electrica - WWLLN Peru {anio}")
    plt.tight_layout()
    plt.savefig(f"{args.salida}/grafico_ciclo_horario_wwlln_peru_{anio}.png", dpi=300)
    plt.close()

    # ============================================================
    # 6. TEXTO RESUMEN AUTOMATICO
    # ============================================================
    texto = f"""
ANALISIS MENSUAL Y ANUAL WWLLN - PERU {anio}

Se analizaron {total_anual:,} eventos WWLLN dentro del dominio de Peru
para el anio {anio}. El rango temporal cubre desde {df["datetime"].min()}
hasta {df["datetime"].max()}.

Del total anual, {eventos_con_energia:,} eventos presentan informacion de
energia, lo que equivale al {eventos_con_energia / total_anual * 100:.2f}%.
Por otro lado, {eventos_sin_energia:,} eventos no presentan informacion de
energia, equivalente al {eventos_sin_energia / total_anual * 100:.2f}%.

El mes con mayor actividad electrica fue {mes_max["mes"]}, con
{int(mes_max["n_eventos"]):,} eventos, equivalente al
{mes_max["porcentaje_anual"]:.2f}% del total anual.

El mes con menor actividad electrica fue {mes_min["mes"]}, con
{int(mes_min["n_eventos"]):,} eventos, equivalente al
{mes_min["porcentaje_anual"]:.2f}% del total anual.
"""
    with open(f"{args.salida}/interpretacion_mensual_anual_wwlln_{anio}.txt", "w") as f:
        f.write(texto)

    print("\nArchivos generados en:", args.salida)


if __name__ == "__main__":
    main()
