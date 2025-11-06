Voici une version **ultra-simple et épurée** de ton `README.md`, adaptée à **un terminal classique Bash** (pas de PowerShell, pas de Jupyter) et avec ton **chemin personnalisé “Lucas Madjinda”** intégré.

---

# 🌦️ POO_meteo — Stations météo Toulouse Métropole

Petit script Python pour afficher les **dernières observations météo** des stations de **Toulouse Métropole** via l’API Open Data.

---

## ⚙️ 1. Installation

### Prérequis

* Python **3.12+**
* Modules nécessaires :

```bash
pip install requests pandas python-dateutil rich
```

---

## 🚀 2. Lancer le script

### a) Mode normal (scan complet)

Ouvre un **terminal Bash classique** et exécute :

```bash
"C:/Users/Lucas Madjinda/AppData/Local/Microsoft/WindowsApps/python3.12.exe" \
"c:/Users/Lucas Madjinda/Desktop/ALGO_DEV_DATA/POO_meteo.py"
```

Le script :

* explore le catalogue Open Data,
* trouve les jeux de données météo,
* affiche les stations et leurs dernières mesures.

---

### b) Mode rapide (station précise)

Pour cibler directement une station, ajoute la variable d’environnement `ODS_DATASET_ID` :

```bash
ODS_DATASET_ID="34-station-meteo-toulouse-teso" \
"C:/Users/Lucas Madjinda/AppData/Local/Microsoft/WindowsApps/python3.12.exe" \
"c:/Users/Lucas Madjinda/Desktop/ALGO_DEV_DATA/POO_meteo.py"
```

Quelques IDs utiles :

* `34-station-meteo-toulouse-teso`
* `37-station-meteo-toulouse-universite-paul-sabatier`
* `01-station-meteo-toulouse-meteopole`
* `61-station-meteo-blagnac-mairie`

---

## 🧠 3. Astuce

Tu peux rester dans le terminal interactif Python (`>>>`) et relancer facilement :

```bash
>>> import os, runpy
>>> os.environ["ODS_DATASET_ID"] = "37-station-meteo-toulouse-universite-paul-sabatier"
>>> runpy.run_path(r"c:\Users\Lucas Madjinda\Desktop\ALGO_DEV_DATA\POO_meteo.py", run_name="__main__")
```

---

## ✅ 4. Résultat attendu

Le programme affiche :

* la **liste des stations météo** détectées,
* leurs **dernières observations** (température, humidité, vent, pluie),
* et une **petite prévision jouet** basée sur les dernières mesures.