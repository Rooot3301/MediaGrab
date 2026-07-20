# MediaGrab

MediaGrab est une application Windows locale en Python 3.12 et PySide6 pour analyser une URL compatible avec yt-dlp, télécharger une vidéo ou extraire son audio, et choisir précisément le dossier de destination. Aucun compte, serveur distant ou système de télémétrie n’est utilisé.

Utilisez MediaGrab uniquement pour les contenus que vous êtes autorisé à télécharger. Le logiciel ne contourne pas les DRM, abonnements, protections d’accès ou authentifications. Vous restez responsable du respect des droits d’auteur, licences et conditions des plateformes.

## Fonctionnalités du MVP

- analyse asynchrone par `yt-dlp --dump-single-json` ;
- titre, miniature, durée, auteur, plateforme et résolution maximale ;
- vidéo MP4/MKV/WebM avec limites de qualité et préférences de codec ;
- extraction MP3/M4A/FLAC/WAV/Opus ;
- dossier choisi pour chaque téléchargement et dernier dossier mémorisé ;
- file parallèle (deux téléchargements par défaut), progression, annulation et relance ;
- sous-titres, métadonnées, miniature et archive anti-doublons ;
- historique et paramètres JSON atomiques ;
- thème sombre, raccourcis clavier et panneau de logs ;
- build PyInstaller Windows en mode `onedir`.

La « pause » réelle n’est pas exposée dans ce MVP : annuler conserve les fichiers `.part`, puis Relancer permet à yt-dlp de reprendre. L’analyse des playlists volumineuses, les notifications natives et la mise à jour intégrée de yt-dlp sont prévues pour une version ultérieure.

## Prérequis et installation

Installez Python 3.12 x64. Téléchargez les exécutables officiels `yt-dlp.exe`, `ffmpeg.exe` et `ffprobe.exe`, puis placez-les dans `bin/`. Ils peuvent aussi être disponibles dans le `PATH` en développement.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

## Lancer et tester

```powershell
.\run.ps1
python -m pytest
python -m ruff check app tests
python -m black --check app tests
```

Raccourcis : Entrée analyse l’URL, `Ctrl+O` choisit un dossier, `Ctrl+Entrée` télécharge, `Ctrl+,` ouvre les paramètres et `Ctrl+L` affiche les logs.

## Construire l’exécutable

```powershell
.\build.ps1
```

Le script crée l’environnement si nécessaire, installe les dépendances, lance Ruff et pytest, nettoie `build/` et `dist/`, puis produit `dist\MediaGrab\MediaGrab.exe`. Le build s’arrête immédiatement si les validations échouent. Les trois binaires doivent être présents dans `bin/` pour qu’ils soient intégrés à la distribution.

## Données locales

- paramètres : `%APPDATA%\MediaGrab\settings.json`
- historique : `%APPDATA%\MediaGrab\history.json`
- archive : `%APPDATA%\MediaGrab\download_archive.txt`
- logs : `%LOCALAPPDATA%\MediaGrab\logs\`
- destination initiale : `%USERPROFILE%\Downloads\MediaGrab`

Les paramètres et l’historique sont écrits par remplacement atomique. Les cookies ne sont pas stockés et les secrets usuels sont masqués dans les logs.

## Dépannage

- « binaire introuvable » : vérifiez les noms exacts des trois `.exe` dans `bin/` ;
- contenu privé ou indisponible : MediaGrab ne tente pas de contourner l’accès ;
- destination inaccessible : choisissez un dossier existant où votre compte peut écrire ;
- fusion/extraction en erreur : vérifiez que FFmpeg et FFprobe proviennent de la même distribution et fonctionnent ;
- URL non supportée : mettez manuellement à jour `yt-dlp.exe` après avoir vérifié sa provenance.

## Architecture

La logique est séparée entre `models`, `utils`, `parsers`, `services` et `ui`. Toutes les commandes externes utilisent `QProcess.setProgram()` et `setArguments(list[str])` ; aucune commande shell ni option libre fournie par l’utilisateur n’est exécutée.
