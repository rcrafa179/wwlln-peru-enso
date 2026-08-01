"""
Pipeline de lectura unificada WWLLN (.loc / .mat) -> filtrado a dominio Peru
Compatible con archivos 2005-2025, formato AE (Average Energy).

Uso:
    python Leer_WWLLN.py /ruta/a/carpeta_con_archivos /ruta/salida/peru_wwlln.parquet

Uso con varios nucleos:
    python Leer_WWLLN.py /ruta/a/carpeta_con_archivos /ruta/salida/peru_wwlln.parquet --workers 8
"""

import sys
import glob
import os
import argparse
import numpy as np
import pandas as pd
from scipy.io import loadmat
from concurrent.futures import ProcessPoolExecutor, as_completed


# --- Dominio Peru ---
LAT_MIN, LAT_MAX = -19.0, 1.0
LON_MIN, LON_MAX = -82.0, -68.0

COLUMNS = [
    'datetime', 'lat', 'lon', 'residual_km', 'nstations',
    'energy_j', 'energy_err', 'nstations_energy'
]


def leer_loc(path):
    """Lee un archivo .loc y devuelve DataFrame normalizado."""
    df = pd.read_csv(
        path,
        header=None,
        names=[
            'date', 'time', 'lat', 'lon', 'residual_km', 'nstations',
            'energy_j', 'energy_err', 'nstations_energy'
        ],
        sep=r',\s*',
        engine='python'
    )

    df['datetime'] = pd.to_datetime(
        df['date'] + ' ' + df['time'],
        format='%Y/%m/%d %H:%M:%S.%f'
    )

    return df[COLUMNS]


def leer_mat(path):
    """Lee un archivo .mat formato AE y devuelve DataFrame normalizado."""
    mat = loadmat(path)
    arr = mat['data']

    dt = pd.to_datetime(dict(
        year=arr[:, 0].astype(int),
        month=arr[:, 1].astype(int),
        day=arr[:, 2].astype(int),
        hour=arr[:, 3].astype(int),
        minute=arr[:, 4].astype(int)
    )) + pd.to_timedelta(arr[:, 5], unit='s')

    df = pd.DataFrame({
        'datetime': dt,
        'lat': arr[:, 6],
        'lon': arr[:, 7],
        'residual_km': arr[:, 8],
        'nstations': arr[:, 9],
        'energy_j': arr[:, 10],
        'energy_err': arr[:, 11],
        'nstations_energy': arr[:, 12],
    })

    return df[COLUMNS]


def filtrar_peru(df):
    """Filtra eventos dentro del dominio de Perú."""
    return df[
        (df['lat'].between(LAT_MIN, LAT_MAX)) &
        (df['lon'].between(LON_MIN, LON_MAX))
    ].reset_index(drop=True)


def procesar_archivo(path):
    """Procesa un archivo individual .loc o .mat."""
    if path.lower().endswith('.loc'):
        df = leer_loc(path)
    elif path.lower().endswith('.mat'):
        df = leer_mat(path)
    else:
        raise ValueError(f"Extensión no soportada: {path}")

    return filtrar_peru(df)


def procesar_carpeta(carpeta, salida, workers):
    archivos = sorted(
        glob.glob(os.path.join(carpeta, '*.loc')) +
        glob.glob(os.path.join(carpeta, '*.mat'))
    )

    if not archivos:
        print(f"No se encontraron archivos .loc/.mat en {carpeta}")
        return

    print(f"Archivos encontrados: {len(archivos)}")
    print(f"Usando {workers} procesos/nucleos")

    piezas = []
    errores = 0

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futuros = {
            executor.submit(procesar_archivo, archivo): archivo
            for archivo in archivos
        }

        for i, futuro in enumerate(as_completed(futuros), 1):
            archivo = futuros[futuro]

            try:
                df = futuro.result()
                if not df.empty:
                    piezas.append(df)

            except Exception as e:
                errores += 1
                print(f"  [ERROR] {os.path.basename(archivo)}: {e}")

            if i % 50 == 0 or i == len(archivos):
                print(f"  procesados {i}/{len(archivos)} archivos...")

    if not piezas:
        print("Ningún archivo procesado correctamente.")
        return

    print("\nUniendo resultados...")
    df_total = pd.concat(piezas, ignore_index=True)

    print("Ordenando por fecha...")
    df_total = df_total.sort_values('datetime').reset_index(drop=True)

    carpeta_salida = os.path.dirname(salida)
    if carpeta_salida:
        os.makedirs(carpeta_salida, exist_ok=True)

    print("Guardando archivo parquet...")
    df_total.to_parquet(salida, index=False)

    print(f"\nTotal eventos en dominio Peru: {len(df_total):,}")
    print(f"Rango temporal: {df_total['datetime'].min()} -> {df_total['datetime'].max()}")
    print(f"Archivos con error: {errores}")
    print(f"Guardado en: {salida}")


def main():
    parser = argparse.ArgumentParser(
        description="Lectura paralela WWLLN .loc/.mat y filtrado a Peru"
    )

    parser.add_argument(
        "carpeta",
        help="Carpeta con archivos .loc o .mat"
    )

    parser.add_argument(
        "salida",
        help="Archivo de salida .parquet"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, os.cpu_count() - 1),
        help="Numero de procesos a usar. Por defecto usa casi todos los nucleos."
    )

    args = parser.parse_args()

    procesar_carpeta(args.carpeta, args.salida, args.workers)


if __name__ == '__main__':
    main()