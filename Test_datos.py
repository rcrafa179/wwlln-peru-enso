from scipy.io import whosmat, loadmat

archivos = [
    "AE20250907.mat",
    "AE20250908.mat",
    "AE20250909.mat"
]

base = "/Users/rafaelruales/Downloads/WWLLN/Uncompressed_DATA"

for archivo in archivos:
    path = f"{base}/{archivo}"
    print("\nArchivo:", archivo)

    try:
        print("whosmat:", whosmat(path))
    except Exception as e:
        print("ERROR whosmat:", e)

    try:
        mat = loadmat(path)
        print("loadmat OK")
        print("keys:", mat.keys())
        print("shape data:", mat["data"].shape)
    except Exception as e:
        print("ERROR loadmat:", e)