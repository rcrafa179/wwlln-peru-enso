import pandas as pd

path = "./peru_wwlln_2025_FINAL.parquet"

df = pd.read_parquet(path)

print("Filas y columnas:")
print(df.shape)

print("\nColumnas:")
print(df.columns)

print("\nPrimeras filas:")
print(df.head())

print("\nÚltimas filas:")
print(df.tail())

print("\nTipos de datos:")
print(df.dtypes)

print("\nRango temporal:")
print(df["datetime"].min(), "->", df["datetime"].max())

print("\nValores faltantes:")
print(df.isna().sum())

print("\nResumen lat/lon:")
print(df[["lat", "lon"]].describe())