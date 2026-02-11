"""Point d'entree pour l'application Meteo Toulouse."""

import sys

from meteo_toulouse.app import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur.")
        sys.exit(0)
