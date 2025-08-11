# Tests Unitaires - PDF to HTML Converter

## Description
Ce fichier contient les tests unitaires pour le serveur backend `server_enhanced.py`.

## Tests inclus

### 🔗 Tests des endpoints API
- `test_health_endpoint()` - Vérifie que l'endpoint `/health` fonctionne
- `test_root_endpoint()` - Vérifie que l'endpoint racine `/` fonctionne

### 🏷️ Tests des tags HTML
- `test_html_tags_conversion()` - Vérifie que les tags HTML sont correctement générés
- `test_is_big_title_function()` - Teste la détection des gros titres

### 🖼️ Tests du traitement des images
- `test_image_processing()` - Vérifie que les images sont bien lues et converties
- `test_safe_ocr_function()` - Teste la fonction OCR sécurisée

### 📄 Tests de validation des fichiers
- `test_convert_endpoint_no_file()` - Test sans fichier
- `test_convert_endpoint_wrong_file_type()` - Test avec mauvais type de fichier
- `test_convert_endpoint_empty_file()` - Test avec fichier vide
- `test_convert_endpoint_valid_pdf()` - Test avec PDF valide

## Comment exécuter les tests

### Méthode 1 : Script automatique
```bash
python run_tests.py
```

### Méthode 2 : Pytest directement
```bash
python -m pytest test_server.py -v
```

### Méthode 3 : Un test spécifique
```bash
python -m pytest test_server.py::test_html_tags_conversion -v
```

## Prérequis
- pytest
- httpx
- fastapi
- PyMuPDF (fitz)
- PIL (Pillow)
- pytesseract

## Installation des dépendances
```bash
pip install pytest httpx
```

## Résultats attendus
Tous les tests doivent passer (10/10). Les tests vérifient :
- La génération correcte des tags HTML
- Le traitement des images avec OCR
- La validation des fichiers d'entrée
- Les endpoints de l'API
- La gestion des erreurs
