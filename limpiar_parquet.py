import pandas as pd
import os

entrada = "./peru_wwlln_2025.parquet"
salida = "./peru_wwlln_2025_limpio.parquet"

df = pd.read_parquet(entrada)

print("Total original:", len(df))

# Columnas que identifican aproximadamente un evento WWLLN
cols_evento = ["datetime", "lat", "lon", "residual_km", "nstations"]

# Crear prioridad: primero eventos con energía, luego eventos sin energía
df["tiene_energia"] = df["energy_j"].notna().astype(int)

# Ordenar para que la fila con energía quede primero
df = df.sort_values(
    by=cols_evento + ["tiene_energia"],
    ascending=[True, True, True, True, True, False]
)

# Eliminar duplicados conservando la versión más completa
df_limpio = df.drop_duplicates(subset=cols_evento, keep="first")

# Quitar columna auxiliar
df_limpio = df_limpio.drop(columns=["tiene_energia"])

# Ordenar por fecha
df_limpio = df_limpio.sort_values("datetime").reset_index(drop=True)

print("Total limpio:", len(df_limpio))
print("Eventos eliminados:", len(df) - len(df_limpio))

print("\nValores faltantes después de limpiar:")
print(df_limpio.isna().sum())

print("\nRango temporal:")
print(df_limpio["datetime"].min(), "->", df_limpio["datetime"].max())

df_limpio.to_parquet(salida, index=False)

print("\nGuardado en:", salida)