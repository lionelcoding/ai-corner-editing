# Parcours de bout en bout

Du rush tourné à la vidéo approuvée. Ce dépôt couvre la **relecture** (l'app et l'adaptateur `review`). Le montage lui-même (coupe, animations, sous-titres, mixage, rendu) est fait par Claude avec les skills AI Corner, ou à la main dans l'outil de ton choix.

```
rush ──► analyse ──► storyboard ──► relecture storyboard ──► montage + rendu ──► relecture finale ──► approuvé
          (skill)      (skill)       (cette app, N tours)       (skill / à la main)   (cette app, N tours)
```

## 0. Installer
```bash
git clone https://github.com/lionelcoding/ai-corner-editing.git
cd ai-corner-editing
npm ci && npm run build && npm link
```
Il faut Node 22+, Python 3 et ffmpeg. `npm link` installe `ai-corner-editing` (l'app) et `ai-corner-review` (l'adaptateur).
Pour essayer sans tes propres médias, lance `npm run demo` et suis les étapes 3 à 6 avec `examples/demo` comme projet.

## 1. Créer le projet
Un dossier par vidéo, gardé **du storyboard au final** (il porte l'historique des tours) :
```
mon-short/
  review.config.json    la config de relecture (voir adapter/README.md)
  index.html            la composition (HyperFrames ou autre page avec data-rid), si tu veux cliquer les éléments
  edit/                 rush, analyse, transcription
  frames/               maquettes du storyboard
  out/                  rendus, un nom de fichier par tour
  review/               écrit par l'adaptateur et l'app : ne pas éditer à la main
```

## 2. Analyser le rush et préparer le storyboard
Avec Claude et les skills AI Corner :
- **rush-analyse** : « analyse le rush » → transcription mot à mot, pauses, reprises, coupe serrée (`cut_tight.mp4`).
- **storyboard-review** : « fais le storyboard » → un panneau par plan, maquettes dans `frames/`, suggestions 💡 préremplies, `review.config.json` avec `"stage": "storyboard"`.

Sans skill : écris toi-même `review.config.json` avec `"stage": "storyboard"`, `video` (animatique ou coupe) et `panels` (voir l'exemple).

## 3. Relire le storyboard
```bash
ai-corner-review mon-short
```
Dans l'app, onglet **Storyboard** :
- **Approve** sur un panneau = accepté (avec ses suggestions encore ouvertes) ;
- clic dans une image ou dans le clip = commentaire épinglé à ce point ; <kbd>C</kbd> = commentaire général ;
- supprimer une suggestion = la refuser.

Chaque commentaire est enregistré dans `review/review.json`, avec une capture de l'image dans `review/shots/`.

## 4. Appliquer les retours, tour suivant
Dis à Claude « applique la relecture ». Il lit les commentaires (`ai-corner-editing comments mon-short`), corrige, marque chaque commentaire `resolved` ou `wontfix` avec une ligne d'explication, met un nom dans `"version"`, puis :
```bash
ai-corner-review mon-short --next-round
```
Le tour précédent est archivé (`review/versions/round-N.json`) et reste consultable, en lecture seule, dans le menu **Versions**. Les commentaires résolus affichent « recheck » jusqu'à ce que tu les confirmes.

On boucle 3 → 4 jusqu'à ce que tous les panneaux soient approuvés et qu'aucun commentaire ne reste ouvert : `ai-corner-editing status mon-short` affiche alors `"status": "approved"`.

## 5. Monter et rendre
- **facecam-montage** : « lance le montage » → face cam coupée et étalonnée, animations recalées sur la voix, sous-titres, effets sonores, mixage −14 LUFS, rendu dans `out/`.
- À la main : monte dans le logiciel de ton choix (Premiere, DaVinci, CapCut…) et exporte un MP4 dans `out/`. Aucun logiciel n'est requis par l'app.

## 6. Relire la vidéo finale
Dans `review.config.json` : `"stage": "final"`, `"video": "out/<rendu>.mp4"`, un nouveau `"version"`, et les pistes (`segments`, `components`, `regions`, `captions`, `sfx`, `html_layer`). Puis :
```bash
ai-corner-review mon-short
```
L'adaptateur voit le changement d'étape : il garde le storyboard (`review/manifest.storyboard.json`, onglet Storyboard toujours visible) et ouvre le final au tour suivant.

Dans l'onglet **Final video** : lecture image par image, clic sur un élément (carte, ligne d'une carte, mot de sous-titre, zone) ou sur un bloc de la timeline (plan, effet sonore, son), puis commentaire. Même boucle qu'à l'étape 4, avec un nouveau nom de rendu à chaque tour.

**Approve the video** quand tout est bon : le statut passe à `approved` dès qu'aucun commentaire n'est ouvert.

## Commandes utiles
| Commande | Rôle |
|---|---|
| `ai-corner-review <projet> [--next-round] [--video f] [--round N] [--no-open]` | config → manifeste → app |
| `ai-corner-editing open <projet>` | rouvrir l'app sans régénérer le manifeste |
| `ai-corner-editing status <projet>` | état JSON (étape, tour, statut, panneaux) |
| `ai-corner-editing comments <projet> [--all]` | commentaires en texte |
| `ai-corner-editing validate <projet>` | vérifier `review/manifest.json` |

## Skills de montage
Ils vivent dans `~/.claude/skills/`, pas dans ce dépôt, avec leurs propres dépendances. L'app et l'adaptateur n'en dépendent pas : n'importe quel outil qui écrit `review.config.json` (ou directement `review/manifest.json`) peut s'en servir.

| Étape | Skill | Ce qu'il fait |
|---|---|---|
| Comprendre une vidéo | `watch` | télécharge, extrait les images et la transcription d'une vidéo (référence, rendu à vérifier) |
| Analyse du rush | `rush-analyse` | transcription mot à mot (mlx_whisper), pauses, reprises, regard hors caméra, coupe serrée |
| Long format → shorts | `short-form-clipping` | choisit les passages d'une vidéo longue à transformer en shorts |
| Interview client | `interview-temoignage` | sélection des passages d'une interview témoignage, export XML FCP7 |
| Storyboard + relecture | `storyboard-review` | panneaux, maquettes, suggestions, boucle « applique la relecture » avec cette app |
| Montage face cam | `facecam-montage` | coupe, étalonnage, **détourage** du présentateur, animations, sous-titres, SFX, mixage, rendu |
| Séparer le sujet du fond | `facecam-montage` → `scripts/matte.py` | RobustVideoMatting sur GPU (MPS) : vidéo d'alpha, puis `cam_composite.py` pour le pop-out hors du cadre |
| | `media-use` / `hyperframes-cli` | `remove-background` de la CLI HyperFrames, pour une image ou une vidéo hors du flux face cam |
| B-roll animé | `motion-broll`, `motion-graphics`, `motion-builder` | B-roll calé sur la voix, titres animés, motion « style verrouillé » via modèles vidéo |
| Composition et rendu | `hyperframes` (+ `-core`, `-animation`, `-audio`, `-registry`, `-cli`…), `general-video` | la composition HTML/GSAP rendue en vidéo, c'est elle que l'app rend cliquable |
| Médias | `media-use` | musique, effets sonores, voix off, LUT, recadrage |
| Vidéo sans face cam | `faceless-explainer` | explainer à partir d'un texte |
| Coupe faite dans un autre logiciel (Premiere, DaVinci, CapCut…) | aucun : exporter un MP4 | le poser dans `out/` et le déclarer dans `review.config.json` ; avec Premiere, `storyboard-review` peut aussi reprendre la coupe via le MCP `premiere-pro` (optionnel) |

`matte.py` utilise un environnement Python posé dans un ancien projet (`~/hyperframes-videos/cctv-tuto/.venv-matte`) : à recréer si ce dossier disparaît (`torch`, `numpy` ; les poids RobustVideoMatting sont téléchargés par `torch.hub` au premier lancement).
