import os
import subprocess
from tqdm import tqdm

# Vérifier dans tous les dossiers les fichiers .py
for root, dirs, files in os.walk("."):
    for file in tqdm(files):
        if (file.startswith("formatage") and file != "formatage_global.py" and file.endswith(".py")):
            subprocess.run(["python", file],cwd=root,shell=True)