"""
miseajour.py - Mise à jour de l'index deputes avec le champ photo_url
Placer ce fichier à la racine du dossier backend/ et lancer : python miseajour.py
"""

import sys
import os

# S'assurer que le dossier backend est dans le path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.elasticsearch_service import es_service
from app.utils.csv_importer import csv_importer
from app.config import settings

def etape1_supprimer_index():
    print("=" * 50)
    print("ÉTAPE 1 — Suppression de l'ancien index deputes")
    print("=" * 50)
    try:
        if es_service.es.indices.exists(index=settings.index_deputes):
            es_service.es.indices.delete(index=settings.index_deputes)
            print(f"✓ Index '{settings.index_deputes}' supprimé.")
        else:
            print(f"⚠ Index '{settings.index_deputes}' introuvable, on continue.")
    except Exception as e:
        print(f"✗ Erreur lors de la suppression : {e}")
        sys.exit(1)

def etape2_reimporter_deputes():
    print()
    print("=" * 50)
    print("ÉTAPE 2 — Recréation de l'index et réimport des députés")
    print("=" * 50)
    try:
        # Recrée l'index avec le nouveau mapping (photo_url inclus)
        es_service.create_indices()
        print(f"✓ Index '{settings.index_deputes}' recréé avec le nouveau mapping.")

        # Réimporte le CSV
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "deputes.csv")
        count = csv_importer.import_deputes(csv_path)
        print(f"✓ {count} députés importés avec photo_url.")
    except Exception as e:
        print(f"✗ Erreur lors de l'import : {e}")
        sys.exit(1)

def etape3_verifier():
    print()
    print("=" * 50)
    print("ÉTAPE 3 — Vérification")
    print("=" * 50)
    try:
        result = es_service.es.search(
            index=settings.index_deputes,
            body={"query": {"match_all": {}}, "size": 1}
        )
        hits = result["hits"]["hits"]
        if not hits:
            print("⚠ Aucun document trouvé dans l'index.")
            return

        doc = hits[0]["_source"]
        if "photo_url" in doc:
            print(f"✓ Champ photo_url présent.")
            print(f"  Exemple — {doc.get('prenom')} {doc.get('nom')} : {doc.get('photo_url')}")
        else:
            print("✗ Champ photo_url absent du document. Vérifie le CSV.")

        total = result["hits"]["total"]["value"]
        print(f"✓ Total documents indexés : {total}")
    except Exception as e:
        print(f"✗ Erreur lors de la vérification : {e}")
        sys.exit(1)

if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║       MISE À JOUR — champ photo_url deputes      ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    etape1_supprimer_index()
    etape2_reimporter_deputes()
    etape3_verifier()

    print()
    print("✓ Mise à jour terminée avec succès !")
    print()