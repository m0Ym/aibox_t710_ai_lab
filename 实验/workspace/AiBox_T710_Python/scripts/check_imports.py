modules = [
    "lib.uart",
    "cv2",
    "PIL",
    "PIL.Image",
    "numpy",
    "pyaudio",
    "pygame",
    "serial",
    "keyboard",
    "torch",
]

results = {}
for m in modules:
    try:
        __import__(m)
        results[m] = True
    except Exception as e:
        results[m] = str(e)

print("IMPORT_CHECK_RESULTS")
for k, v in results.items():
    print(f"{k}: {v}")
