"""Cuenta eventos GLOBALES (sin filtrar) y de Peru por dia, para un anio."""
import sys, glob, os
from concurrent.futures import ProcessPoolExecutor
from scipy.io import loadmat
import pandas as pd

LAT = (-19.0, 1.0)
LON = (-82.0, -68.0)


def contar(p):
    try:
        a = loadmat(p)['data']
        peru = ((a[:, 6] >= LAT[0]) & (a[:, 6] <= LAT[1]) &
                (a[:, 7] >= LON[0]) & (a[:, 7] <= LON[1])).sum()
        base = os.path.basename(p)
        return base, len(a), int(peru)
    except Exception:
        return os.path.basename(p), None, None


if __name__ == '__main__':
    carpeta, salida, paso = sys.argv[1], sys.argv[2], int(sys.argv[3])
    archivos = sorted(glob.glob(os.path.join(carpeta, '*.mat')))
    archivos = [a for a in archivos if not os.path.basename(a).startswith('._')]
    archivos = archivos[::paso]
    with ProcessPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(contar, archivos))
    df = pd.DataFrame(res, columns=['archivo', 'global', 'peru']).dropna()
    df['fecha'] = pd.to_datetime(df['archivo'].str.extract(r'(\d{8})')[0], format='%Y%m%d')
    df['anio'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month
    df.to_csv(salida, index=False)
    print(f'{len(df)} dias -> {salida}')
    print('global medio:', int(df['global'].mean()), '| peru medio:', int(df['peru'].mean()))
