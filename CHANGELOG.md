# Changelog — AI Corner editing

Toutes les évolutions notables de l'app de relecture AI Corner editing.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ; numéros : [SemVer](https://semver.org/lang/fr/)
(correctif = bug corrigé, mineur = nouvelle fonction compatible, majeur = format du manifeste ou de review.json cassé).

## [Non publié]
### Ajouté
- **Adaptateur `review`** dans le dépôt (`adapter/`, commande `ai-corner-review`) : `review.config.json` → `review/manifest.json`, tours, versions et passage storyboard → final. Il appelle la CLI du même dépôt.
- **Projet exemple** `examples/demo` et `npm run demo` : un short de 9 s (médias fabriqués par ffmpeg) avec storyboard, couche HTML cliquable, sous-titres, effets sonores.
- **Guide de bout en bout** `docs/parcours.md` : rush → storyboard → montage → relecture finale, avec la carte des skills de montage.
- README : rôle des fichiers de `review/` (`manifest.<stage>.json`, `versions/round-N.json`, `versions/index.json`).

## [0.3.0] — 2026-10-06
### Modifié
- **Nom définitif : AI Corner editing.** Paquet et commande `ai-corner-editing` (remplace `ai-corner`), en-tête « AI Corner · editing », titre de page, schémas `ai-corner-editing/…`.
- Dépôt GitHub : `lionelcoding/ai-corner-editing`.

## [0.2.0] — 2026-10-06
Première version AI Corner, reprise et développée par Lionel Louis.

### Ajouté
- **Versions** : menu « Versions » dans l'en-tête, qui liste les tours archivés (`review/versions/round-N.json`) avec leur nom (`review/versions/index.json`). Une version archivée s'ouvre en lecture seule, avec un bandeau et un bouton « Revenir à la version actuelle » ; l'URL `?v=N` l'ouvre directement.
- Serveur : route `GET /api/versions` et paramètre `GET /api/state?v=N`.
- Le menu Versions suit l'étape affichée : sur l'onglet Storyboard, il montre la version du storyboard ; choisir le dernier tour de l'autre étape bascule d'onglet.

### Modifié
- **Nom** : l'app s'appelle AI Corner (paquet `ai-corner`, commande `ai-corner`, titre « AI Corner · Relecture »). Les schémas JSON ont été renommés (`ai-corner/manifest.schema.json`, `ai-corner/review.schema.json`), leur contenu ne change pas.
- **Look Apple** (HIG macOS) : police San Francisco, thème clair ou sombre selon macOS, barre d'outils translucide, bleu système, contrôles segmentés, cartes et popovers arrondis, couleurs système pour les pistes de la timeline et les repères de commentaires.

### Corrigé
- En-tête : les contrôles ne passent plus sur deux lignes (« Final video », infos de tour).

## [0.1.0] — 2026-09
Version d'origine : aisance-video-editing (MIT, AISANCE). Relecture de storyboard (panneaux, approbation, commentaires épinglés) et relecture finale image par image (timeline multipiste, couche HTML cliquable), pilotées par `review/manifest.json`.
