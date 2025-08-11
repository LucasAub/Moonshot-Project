#!/usr/bin/env python3
"""
Script pour exécuter les tests unitaires du serveur PDF to HTML
"""

import subprocess
import sys
import os

def run_tests():
    """Exécute tous les tests"""
    print("🧪 Exécution des tests unitaires...")
    print("=" * 50)
    
    # Changer vers le répertoire Backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    try:
        # Exécuter pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_server.py", 
            "-v", 
            "--tb=short"
        ], capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ Tous les tests ont réussi !")
            print("\nTests exécutés :")
            print("- ✅ Endpoints API (/health, /)")
            print("- ✅ Détection des gros titres")
            print("- ✅ Fonction OCR sécurisée")
            print("- ✅ Validation des fichiers")
            print("- ✅ Conversion PDF vers HTML")
            print("- ✅ Génération des tags HTML")
            print("- ✅ Traitement des images")
        else:
            print("\n❌ Certains tests ont échoué")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution des tests: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
