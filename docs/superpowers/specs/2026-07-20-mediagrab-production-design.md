# MediaGrab — Mise en production (design)

Date : 2026-07-20
Statut : approuvé (exécution en phases)

## Contexte

MediaGrab est une application de bureau Windows (Python 3.12 + PySide6) qui,
via `yt-dlp` et `ffmpeg`, analyse une URL, télécharge une vidéo ou en extrait
l'audio, avec choix du dossier de destination. Fonctionnement 100 % local :
aucun compte, serveur distant ni télémétrie.

Le code existant (~1450 lignes) est déjà propre : séparation nette
`models` / `utils` / `parsers` / `services` / `ui`, écritures JSON atomiques,
aucune exécution shell (tout passe par `QProcess.setProgram` + `setArguments`),
validation d'URL (anti-SSRF), rédaction des secrets dans les logs, tests + Ruff
au vert. L'objectif n'est pas de corriger de la dette mais d'élever le MVP au
rang de produit fini.

## Décisions produit (validées)

- **Installateur** : Inno Setup (`.exe`).
- **Binaires** (yt-dlp, ffmpeg, ffprobe, ~220 Mo) : **téléchargés au premier
  lancement** depuis leurs sources officielles → installateur léger.
- **Interface** : refonte visuelle complète, **barre latérale moderne**, thème
  sombre uniquement, interface en français.
- **Extras** : icône d'application dédiée, notifications de fin, tests élargis.
- **Hors périmètre (YAGNI)** : CI GitHub Actions, thème clair, MSI, analyse
  avancée de playlists.

## Architecture cible

Les couches existantes sont conservées. Ajouts :

```
app/
  services/
    bootstrap_service.py   (NOUVEAU) téléchargement/màj des binaires
    notification_service.py(NOUVEAU) toasts de fin (QSystemTrayIcon)
  ui/
    sidebar.py             (NOUVEAU) barre de navigation verticale
    first_run_dialog.py    (NOUVEAU) assistant de premier lancement
    pages/                 (NOUVEAU) pages extraites de main_window
      download_page.py
      history_page.py      (déplace history_widget)
      settings_page.py     (déplace settings_dialog)
  version.py               (NOUVEAU) source unique de la version
assets/
  icons/*.svg              (NOUVEAU) icônes nav + actions
  logo.svg / make_icon.py  (NOUVEAU) logo + génération du .ico
  MediaGrab.ico            (généré)
installer/
  MediaGrab.iss            (NOUVEAU) script Inno Setup
  build-installer.ps1      (NOUVEAU) PyInstaller + ISCC
```

## Composants

### 1. Refonte UI — barre latérale

- `QMainWindow` → `Sidebar` (gauche) + `QStackedWidget` (contenu).
- Barre : bouton logo/titre en haut, entrées de nav (icône SVG + libellé) avec
  indicateur actif coloré, bas de barre = état binaires + version.
- Pages : `DownloadPage`, `HistoryPage`, `SettingsPage`. `main_window.py` est
  réduit à l'assemblage + câblage des services (les widgets déménagent dans
  `ui/pages/`).
- `DownloadPage` : champ URL « héro » + Analyser ; carte d'aperçu média ;
  bascule segmentée Vidéo/Audio ; options avancées repliables ; destination ;
  actions ; file de téléchargements (liste de cartes `DownloadItemWidget`).
- Nouveau `dark.qss` : tokens cohérents (couleurs, rayons, espacements, échelle
  typo), tous les composants restylés. Contrat de `objectName` conservé pour ne
  pas casser les widgets existants (`card`, `primaryButton`, `statusPill`, …).
- Nettoyage : suppression du sélecteur de thème (non fonctionnel) des
  paramètres ; `settings.theme` reste `"dark"`.

### 2. Bootstrap des binaires (premier lancement)

- `BootstrapService` (QObject) télécharge en HTTPS vers un dossier
  **inscriptible** `%LOCALAPPDATA%\MediaGrab\bin` :
  - `yt-dlp.exe` : release officielle GitHub (URL stable `latest`).
  - `ffmpeg.exe` + `ffprobe.exe` : build officiel (archive ZIP), extraction des
    deux exécutables uniquement.
- Progression émise par signaux ; vérification post-téléchargement par exécution
  (`--version`). Téléchargement réseau isolé et testable (fonction pure de
  planification + couche I/O mince).
- `BinaryService.locate()` : ordre de recherche = dossier géré
  (`managed_binary_dir()`) → `bin/` embarqué → `PATH`.
- `FirstRunDialog` : affiché au démarrage si un binaire manque ; barre de
  progression, messages clairs, gestion d'erreur réseau (réessayer / ignorer).
- Bouton **« Mettre à jour yt-dlp »** dans les Paramètres (réutilise le service).

### 3. Notifications de fin

- `NotificationService` autour d'un `QSystemTrayIcon` : toast Windows à la fin
  d'un job (succès/échec), conditionné par `settings.notifications`.
- Icône de tray = icône de l'app ; clic sur la notification/tray ré-affiche la
  fenêtre.

### 4. Icône d'application

- `assets/logo.svg` (logo dessiné) → `make_icon.py` (PySide6 QtSvg, sans
  dépendance nouvelle) rend le SVG en PNG 16→256 px et empaquette un
  `MediaGrab.ico` multi-résolutions (ICO à PNG embarqués).
- Câblage : `QApplication.setWindowIcon`, tray, `mediagrab.spec` (`icon=`),
  `MediaGrab.iss` (`SetupIconFile` + `UninstallDisplayIcon`).

### 5. Qualité / prod-readiness

- `app/version.py` : `__version__` unique, consommé par l'« À propos », la barre
  latérale et l'installateur.
- Ruff : jeu de règles élargi (E, F, I, UP, B, SIM au minimum). Black conservé.
  mypy configuré (non bloquant au build dans un premier temps).
- `.gitattributes` : normalisation des fins de ligne (LF pour le code).
- Tests élargis : `BootstrapService` (planification + réseau mocké),
  `FormatService` (bornes qualité/codec/conteneur), `BinaryService` (ordre de
  résolution), + smoke test `pytest-qt` (construction `MainWindow`, bascule
  Vidéo/Audio, navigation entre pages).

### 6. Build + installateur

- `mediagrab.spec` : ajout `icon=`, `version` ; **retrait** des `.exe` de `bin/`
  du paquet (téléchargés au 1er lancement) ; conservation de `assets/`.
- `installer/MediaGrab.iss` : install dans `{autopf}\MediaGrab`, raccourcis menu
  Démarrer + bureau, désinstalleur, données `%APPDATA%`/`%LOCALAPPDATA%`
  préservées à la désinstallation. Sortie : `MediaGrab-Setup-<version>.exe`.
- `installer/build-installer.ps1` : lance le build PyInstaller (`build.ps1`) puis
  `ISCC.exe` ; échoue proprement si Inno Setup est absent (message d'aide).
- README refondu (FR) : installation utilisateur, dev, build, dépannage.

## Flux de données (inchangé sur le cœur)

Analyse : URL → `MetadataService` (`yt-dlp --dump-single-json`) →
`parse_metadata` → `MediaInfo` → aperçu UI.
Téléchargement : `DownloadJob` → `DownloadManager` → `DownloadRunner`
(`QProcess yt-dlp`) → `parse_progress` → mises à jour UI + historique +
notification de fin.

## Gestion des erreurs

- Erreurs métier via `MediaGrabError` (messages FR sûrs), affichées en dialog +
  loggées (secrets rédigés).
- Binaires manquants : plus de blocage — l'assistant de 1er lancement guide le
  téléchargement ; échec réseau → réessayer/ignorer.
- Aucune commande shell ; arguments passés en liste ; URLs validées (anti-SSRF).

## Tests

- Unitaires (pytest) : parsers, services purs, utils, bootstrap (réseau mocké).
- UI (pytest-qt) : smoke test de la fenêtre et des interactions clés.
- Gate build : Ruff + pytest doivent passer avant packaging (déjà dans
  `build.ps1`).

## Plan d'exécution (phases, commit + tests verts à chaque étape)

0. Git initialisé + commit de référence. ✅
1. Version + housekeeping (`version.py`, `.gitattributes`, config Ruff/mypy).
2. Refonte UI (sidebar, pages, nouveau QSS, nettoyage thème).
3. Bootstrap binaires + assistant 1er lancement + bouton màj yt-dlp.
4. Notifications de fin (tray).
5. Icône (logo SVG, génération .ico, câblage).
6. Tests élargis.
7. Build (`mediagrab.spec`) + installateur Inno Setup + README.
