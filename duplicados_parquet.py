import pandas as pd

path = "./peru_wwlln_2025.parquet"
df = pd.read_parquet(path)

print("Total original:", len(df))

# Duplicados exactos en todas las columnas
dup_exactos = df.duplicated().sum()
print("Duplicados exactos:", dup_exactos)

# Duplicados por evento físico aproximado
cols_evento = ["datetime", "lat", "lon", "residual_km", "nstations"]

dup_evento = df.duplicated(subset=cols_evento).sum()
print("Duplicados por datetime, lat, lon, residual_km, nstations:", dup_evento)

# Cuántos tienen energía
print("\nEventos con energy_j:")
print(df["energy_j"].notna().sum())

print("\nEventos sin energy_j:")
print(df["energy_j"].isna().sum())

# Ejemplo de eventos repetidos
repetidos = df[df.duplicated(subset=cols_evento, keep=False)]
print("\nEjemplo de repetidos:")
print(repetidos.head(20))