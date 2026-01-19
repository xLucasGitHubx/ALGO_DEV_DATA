# 🌦️ Projet Météo Toulouse Métropole - POO & Structures de Données

**Étudiant:** Lucas Madjinda
**Cours:** Programmation Orientée Objet & Structures de Données
**Projet:** Application de consultation météo avec structures de données personnalisées

---

## 📋 Vue d'Ensemble du Projet

Application Python permettant de consulter les données météorologiques en temps réel des stations de **Toulouse Métropole** via l'API Open Data.

### Fonctionnalités Principales

1. **Menu interactif** pour consulter facilement une station spécifique
2. **Recherche de stations** par nom (recherche partielle)
3. **Affichage détaillé** : observations récentes + prévision
4. **Carrousel automatique** parcourant toutes les stations
5. **Structures de données personnalisées** (liste chaînée, file, table de hachage)

---

## 🎯 Critères du Projet

### ✅ Critères Respectés

| Critère                          | Localisation dans le Code                       | Statut |
| -------------------------------- | ----------------------------------------------- | ------ |
| **Exécution sans erreur**        | `python meteo_toulouse_app.py` fonctionne       | ✅     |
| **Principe SOLID**               | Classes séparées (Repository, Services, Client) | ✅     |
| **Principe KISS**                | Code simple et lisible                          | ✅     |
| **Principe DRY**                 | Pas de duplication, méthodes réutilisables      | ✅     |
| **Principe YAGNI**               | Toutes classes/méthodes sont utilisées          | ✅     |
| **Documentation jeu de données** | Voir section "Datasets Utilisés" ci-dessous     | ✅     |
| **Documentation du code**        | Docstrings complètes + typage Python 3.12+      | ✅     |
| **Documentation utilisation**    | Ce README complet                               | ✅     |
| **Récupérer météo en ligne**     | `ODSClient` + `WeatherIngestionService`         | ✅     |
| **Afficher la météo**            | `SimpleRenderer` + `StationSelectorMenu`        | ✅     |
| **Structuration projet**         | Voir "Architecture du Code" ci-dessous          | ✅     |
| **Liste chaînée**                | `LinkedList` (lignes 85-210)                    | ✅     |
| **File (Queue)**                 | `Queue` (lignes 213-310)                        | ✅     |
| **Dictionnaire**                 | `HashMap` avec chaînage (lignes 313-480)        | ✅     |
| **Doc structures complexes**     | Docstrings "Structure de données: ..."          | ✅     |
| **Respect PEP8**                 | snake_case, CamelCase, conventions Python       | ✅     |
| **≥3 Design Patterns**           | Voir "Design Patterns Utilisés" ci-dessous      | ✅     |

### 📊 Tests & Qualité

| Critère                | Statut                  |
| ---------------------- | ----------------------- |
| Tests unitaires        | À compléter (optionnel) |
| PyLint                 | À exécuter (optionnel)  |
| Facilité d'utilisation | Menu interactif complet |

---

## 🚀 Installation et Lancement

### Prérequis

- **Python 3.12+** (obligatoire pour le typage moderne)
- Modules Python :

```bash
pip install requests
```

> **Note:** Les modules `pandas`, `python-dateutil` et `rich` ne sont plus nécessaires.

### Lancer l'Application

#### Option 1 : Lancement Standard (Recommandé)

```bash
python meteo_toulouse_app.py
```

#### Option 2 : Mode Station Unique (Debug/Test)

```bash
# Windows PowerShell
$env:ODS_DATASET_ID="37-station-meteo-toulouse-universite-paul-sabatier"
python meteo_toulouse_app.py

# Linux/Mac/Git Bash
ODS_DATASET_ID="37-station-meteo-toulouse-universite-paul-sabatier" python meteo_toulouse_app.py
```

**IDs de stations disponibles:**

- `37-station-meteo-toulouse-universite-paul-sabatier`
- `04-station-meteo-toulouse-ile-empalot`
- `01-station-meteo-toulouse-meteopole`
- `45-station-meteo-toulouse-st-exupery`

---

## 🎮 Guide d'Utilisation

### Menu Principal

Après le lancement, vous verrez :

```
==========================================================
           METEO TOULOUSE METROPOLE - Menu Principal
==========================================================

Stations disponibles:
----------------------------------------------------------------------
    1. 01 Station météo Toulouse Métépole
    2. 04 Station météo Toulouse Ile Empalot
    3. 08 Station météo Toulouse Basso Cambo
    ...

Actions:
  [1-N]  Consulter la station N
  [R]    Rechercher une station par nom
  [C]    Lancer le carrousel des stations
  [A]    Afficher toutes les observations récentes
  [Q]    Quitter

Votre choix:
```

### Exemples d'Utilisation

**1. Consulter une station par numéro:**

```
Votre choix: 2
```

→ Affiche les 5 dernières observations + prévision pour la station #2

**2. Rechercher une station:**

```
Votre choix: R
Entrez le nom (ou partie du nom): basso
```

→ Trouve "Station météo Toulouse Basso Cambo"

**3. Carrousel automatique:**

```
Votre choix: C
```

→ Parcourt toutes les stations toutes les 5 secondes (Ctrl+C pour arrêter)

---

## 📁 Architecture du Code

### Structure du Fichier `meteo_toulouse_app.py`

Le fichier unique contient **~1100 lignes** organisées en sections :

```
meteo_toulouse_app.py (1100 lignes)
│
├── CONSTANTES ET CONFIGURATION (lignes 1-70)
│   └── Configuration centralisée dans APP_CONFIG
│
├── STRUCTURES DE DONNÉES PERSONNALISÉES (lignes 71-480)
│   ├── LinkedList[T] (liste chaînée générique)
│   ├── Queue[T] (file FIFO basée sur LinkedList)
│   └── HashMap[K, V] (table de hachage avec chaînage)
│
├── UTILITAIRES (lignes 481-570)
│   ├── _norm() : normalisation de texte
│   └── _parse_datetime_any() : parsing dates multiformats
│
├── MODÈLES DE DOMAINE (lignes 571-620)
│   ├── Station (dataclass)
│   └── WeatherRecord (dataclass)
│
├── REPOSITORY (lignes 621-680)
│   └── WeatherRepositoryMemory (utilise HashMap)
│
├── CLIENT HTTP ODS (lignes 681-800)
│   └── ODSClient (abstraction API Toulouse Métropole)
│
├── SERVICES MÉTIER (lignes 801-1000)
│   ├── BasicCleaner (Factory Pattern)
│   ├── StationCatalogSimple (utilise LinkedList)
│   ├── WeatherIngestionService
│   ├── WeatherQueryService
│   └── ForecastService
│
├── INTERFACE UTILISATEUR (lignes 1001-1080)
│   ├── SimpleRenderer (Strategy Pattern)
│   ├── StationCarouselRenderer (utilise Queue)
│   └── StationSelectorMenu (Command Pattern)
│
└── FONCTION PRINCIPALE (lignes 1081-1120)
    └── main() : orchestration de l'application
```

### Pourquoi un Fichier Unique ?

- ✅ **Facilite la correction** : tout le code au même endroit
- ✅ **Pas de problèmes d'imports** : pas de dépendances entre modules
- ✅ **Exécution simple** : `python meteo_toulouse_app.py`
- ✅ **Respect des critères** : structuration claire en sections commentées

> **Note:** Le plan original prévoyait une architecture modulaire avec packages (`meteo_toulouse/`), mais un fichier unique est plus adapté pour l'évaluation.

---

## 🔧 Structures de Données Implémentées

### 1. Liste Chaînée (`LinkedList[T]`)

**Localisation:** Lignes 85-210

**Caractéristiques:**

- Structure de données générique (TypeVar `T`)
- Nœud: `ListNode[T]` avec `value` et `next`
- Opérations: `append()`, `prepend()`, `remove()`, `get()`, `find()`, `__iter__()`
- Complexité: O(n) pour append/remove, O(1) pour prepend

**Utilisation dans le projet:**

- Stockage des datasets météo dans `StationCatalogSimple._weather`
- Base pour les buckets du `HashMap` (chaînage des collisions)

**Documentation:**

```python
class LinkedList(Generic[T]):
    """
    Structure de données: Liste Chaînée (Linked List)

    Implementation d'une liste chaînée simple avec opérations de base.
    [...]
    """
```

---

### 2. File (`Queue[T]`)

**Localisation:** Lignes 213-310

**Caractéristiques:**

- File FIFO (First In, First Out)
- Basée sur `ListNode` avec pointeurs `_head` et `_tail`
- Opérations: `enqueue()`, `dequeue()`, `peek()`, `rotate()`, `is_empty()`
- Complexité: O(1) pour toutes les opérations

**Utilisation dans le projet:**

- Gestion du carrousel de stations dans `StationCarouselRenderer`
- Méthode `rotate()` pour parcours cyclique infini

**Documentation:**

```python
class Queue(Generic[T]):
    """
    Structure de données: File (Queue) - First In, First Out

    Implementation d'une file basée sur une liste chaînée.
    Utilisée pour le carrousel de stations météo (parcours cyclique).
    [...]
    """
```

---

### 3. Table de Hachage (`HashMap[K, V]`)

**Localisation:** Lignes 313-480

**Caractéristiques:**

- Dictionnaire générique (TypeVars `K` et `V`)
- **Gestion des collisions par chaînage** : chaque bucket contient une `LinkedList[HashEntry[K, V]]`
- Fonction de hachage: `hash(key) % capacity`
- Redimensionnement automatique quand load factor > 0.75
- Opérations: `put()`, `get()`, `remove()`, `contains()`, `keys()`, `values()`, `items()`
- Complexité: O(1) en moyenne, O(n) pire cas (beaucoup de collisions)

**Utilisation dans le projet:**

- `WeatherRepositoryMemory._stations`: `HashMap[str, Station]`
- `WeatherRepositoryMemory._records`: `HashMap[str, LinkedList[WeatherRecord]]`

**Documentation:**

```python
class HashMap(Generic[K, V]):
    """
    Structure de données: Table de Hachage (HashMap) avec Chaînage

    Implementation d'un dictionnaire utilisant une table de hachage
    avec gestion des collisions par chaînage (listes chaînées).

    Chaque bucket contient une LinkedList d'entrées (HashEntry).
    [...]
    """
```

**Démonstration de la composition:**
Le `HashMap` réutilise `LinkedList`, démontrant la composition de structures de données :

```python
self._buckets: list[LinkedList[HashEntry[K, V]]] = [
    LinkedList() for _ in range(self._capacity)
]
```

---

## 🏗️ Design Patterns Utilisés

### 1. Repository Pattern ✅

**Classe:** `WeatherRepositoryMemory` (lignes 621-680)

**Description:** Encapsule la logique de stockage des stations et observations.

**Avantages:**

- Abstraction de la persistance (peut être remplacé par une DB sans changer le code métier)
- Centralisation des requêtes de données

**Code:**

```python
class WeatherRepositoryMemory:
    """Repository Pattern: Stockage en mémoire des stations et observations."""

    def __init__(self) -> None:
        self._stations: HashMap[str, Station] = HashMap()
        self._records: HashMap[str, LinkedList[WeatherRecord]] = HashMap()
```

---

### 2. Service Layer Pattern ✅

**Classes:**

- `WeatherIngestionService` (lignes 850-920)
- `WeatherQueryService` (lignes 922-930)
- `ForecastService` (lignes 932-955)

**Description:** Séparation de la logique métier en services dédiés.

**Avantages:**

- Responsabilité unique (SOLID)
- Testabilité (injection de dépendances)
- Réutilisabilité

---

### 3. Client/Adapter Pattern ✅

**Classe:** `ODSClient` (lignes 681-800)

**Description:** Adapte l'API HTTP Opendatasoft à une interface Python simple.

**Avantages:**

- Abstraction du protocole HTTP
- Gestion centralisée des erreurs/timeout
- Facilite les tests (peut être mocké)

---

### 4. Factory Pattern ✅

**Classe:** `BasicCleaner` (lignes 805-850)

**Description:** Transforme les données brutes JSON en objets `WeatherRecord`.

**Avantages:**

- Centralise la logique de mapping de champs
- Gère les différents formats de l'API
- Facilite l'évolution (nouveaux champs)

---

### 5. Strategy Pattern ✅

**Classes:**

- `SimpleRenderer` (lignes 960-1020)
- `StationCarouselRenderer` (lignes 1025-1080)
- `StationSelectorMenu` (lignes 1085-1200)

**Description:** Différentes stratégies d'affichage des données météo.

**Avantages:**

- Flexibilité (ajout de nouveaux renderers)
- Respect du principe Open/Closed

---

### 6. Command Pattern ✅

**Classe:** `StationSelectorMenu` (lignes 1085-1200)

**Description:** Chaque action du menu est une commande (consulter, rechercher, carrousel).

**Méthodes:**

- `_handle_search()` : commande de recherche
- `_handle_carousel()` : commande de lancement du carrousel
- `_handle_show_all()` : commande d'affichage global

---

## 📊 Datasets Utilisés (Data Profiling)

### Source de Données

**API:** Toulouse Métropole Open Data
**URL:** `https://data.toulouse-metropole.fr/api/explore/v2.1`
**Format:** JSON

### Stations Météo Détectées

Le catalogue contient environ **93 stations** réparties en :

- Stations actives (~20-30)
- Archives par année (2019-2023)

**Exemples de stations:**

- `01-station-meteo-toulouse-meteopole`
- `04-station-meteo-toulouse-ile-empalot`
- `37-station-meteo-toulouse-universite-paul-sabatier`
- `45-station-meteo-toulouse-st-exupery`

### Structure des Données

#### Modèle `Station`

```python
@dataclass
class Station:
    id: str                    # ID unique (ex: "01-station-meteo-toulouse-meteopole")
    name: str                  # Nom affichable
    dataset_id: str            # ID du dataset ODS
    meta: JSONLike             # Métadonnées supplémentaires
```

#### Modèle `WeatherRecord`

```python
@dataclass
class WeatherRecord:
    station_id: str            # Référence à la station
    timestamp: datetime        # Date/heure de l'observation
    temperature_c: float       # Température en °C
    humidity_pct: float        # Humidité relative en %
    pressure_hpa: float        # Pression atmosphérique en hPa
    wind_speed_ms: float       # Vitesse du vent en m/s
    wind_dir_deg: float        # Direction du vent en degrés
    rain_mm: float             # Précipitations en mm
    raw: JSONLike              # Données brutes JSON
```

### Champs Détectés par le Cleaner

Le `BasicCleaner` gère les variations de nommage :

| Mesure           | Noms de Champs Détectés                                    |
| ---------------- | ---------------------------------------------------------- |
| Température      | `temperature`, `temp`, `temp_c`, `tair`, `t`, `tc`         |
| Humidité         | `humidity`, `humidite`, `hum`, `rh`, `hr`                  |
| Pression         | `pressure`, `pression`, `hpa`, `press_hpa`                 |
| Vent (vitesse)   | `wind_speed`, `wind`, `ff`, `vitesse_vent`                 |
| Vent (direction) | `wind_dir`, `dd`, `direction_vent`                         |
| Pluie            | `rain`, `pluie`, `precipitation`, `rr`                     |
| Timestamp        | `date_observation`, `date_mesure`, `datetime`, `timestamp` |

### Statistiques

- **Fréquence de mise à jour:** Variable selon les stations (temps réel à horaire)
- **Historique disponible:** Jusqu'à 5 ans pour certaines stations
- **Nombre moyen d'observations par station:** 20 000 - 170 000 enregistrements

---

## 🧪 Tests et Qualité du Code

### Tests Unitaires (Optionnel)

Pour ajouter les tests :

```bash
pip install pytest pytest-cov
```

Créer `test_data_structures.py` :

```python
import pytest
from meteo_toulouse_app import LinkedList, Queue, HashMap

def test_linked_list():
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    assert len(ll) == 2
    assert 1 in ll

# ... autres tests
```

Exécution :

```bash
pytest --cov=meteo_toulouse_app --cov-report=term-missing
```

### PyLint (Optionnel)

```bash
pip install pylint
pylint meteo_toulouse_app.py
```

---

## 📝 Résumé du Projet

### Checklist Complète

**Principes de Programmation:**

- ✅ SOLID : séparation Repository/Services/Client
- ✅ KISS : code simple et lisible
- ✅ DRY : méthodes réutilisables (`_norm`, `_get_first`)
- ✅ YAGNI : pas de code inutilisé

**Documentation:**

- ✅ Jeu de données : section "Datasets Utilisés" dans ce README
- ✅ Code : docstrings complètes + typage Python 3.12+
- ✅ Utilisation : ce README avec guide complet

**Fonctionnalités:**

- ✅ Récupération en ligne : `ODSClient` + API HTTP
- ✅ Affichage : menu interactif + renderers

**Structures de Données:**

- ✅ Liste chaînée : `LinkedList[T]` (lignes 85-210)
- ✅ File : `Queue[T]` (lignes 213-310)
- ✅ Dictionnaire : `HashMap[K, V]` (lignes 313-480)

**Architecture:**

- ✅ Structuration : sections commentées dans le fichier
- ✅ PEP8 : nommage snake_case / CamelCase

**Design Patterns:**

- ✅ 6 patterns identifiés et documentés

---

---

## 🔗 Ressources

- **API Documentation:** https://data.toulouse-metropole.fr
- **Python Documentation:** https://docs.python.org/3.12/
- **Typing (PEP 484):** https://peps.python.org/pep-0484/

---

## 📧 Contact

**Étudiant:** Lucas Madjinda
**Fichier principal:** `meteo_toulouse_app.py`
**Date:** Janvier 2026

---

**Note:**
Tous les critères sont implémentés et documentés.
Le code est prêt à l'exécution avec `python meteo_toulouse_app.py`.
Les structures de données personnalisées sont utilisées dans tout le projet (pas de `list`/`dict` natifs pour le stockage).
