# Adaptateur `review`

Ouvre n'importe quel projet vidéo dans AI Corner editing à partir d'un seul fichier, `review.config.json`, à la racine du projet.
L'adaptateur écrit `review/manifest.json` (le format de l'app, voir le [README](../README.md#the-contract)), le valide et lance l'app.
Il gère aussi les tours, les versions et le passage du storyboard au final.

Prérequis : Python 3 (bibliothèque standard seulement), Node 22+, ffmpeg.

```
adapter/review <projet>                    # génère review/manifest.json, valide, ouvre l'app
adapter/review <projet> --no-open          # génère et valide seulement
adapter/review <projet> --video out/v8.mp4 # relire un autre rendu que celui de la config
adapter/review <projet> --next-round       # tour suivant, après avoir appliqué les commentaires
adapter/review <projet> --round N          # impose un numéro de tour (rattrapage d'historique)
```

Après `npm link`, la commande s'appelle aussi `ai-corner-review`. Pour garder le nom court `review` utilisé par les skills :
```bash
ln -sf "$PWD/adapter/review" ~/.local/bin/review
```
Le lanceur appelle la CLI de ce même dépôt (`bin/ai-corner-editing.mjs`) : pas besoin que `ai-corner-editing` soit sur le PATH.

## review.config.json
Les chemins sont relatifs à la racine du projet ; l'adaptateur les rebase sur `review/`. Les temps sont en secondes dans la vidéo relue.

| Clé | Rôle |
|---|---|
| `project`, `title`, `stage` | `stage` vaut `storyboard` ou `final` (défaut `final`) |
| `canvas` | `{"w":1080,"h":1920,"fps":30}` (1920×1080 pour du 16:9) |
| `video` | rendu à relire (final) ou animatique / coupe serrée (storyboard) |
| `panels` | storyboard : panneaux au format du schéma (`id`, `title`, `images`, `clip`, `excerpt`, `description`…) |
| `segments` | plans : `{id,label,start,end,text?}` → piste « Plans » |
| `components` | éléments cliquables : `{id,label,start,end,rid?,bbox?,source?,children?}`. `rid` = `data-rid` dans le HTML |
| `regions` | zones sans HTML (face cam incrustée…) : `{id,label,start,end,bbox:[x,y,w,h]}` |
| `captions` | `{"from":"hyperframes-subs"\|"whisper"\|"json","file","offset","bbox","zones":[{"before":t,"bbox"}]}` → un item par mot |
| `sfx` | `{"from":"mixpy"\|"json","file","offset"}` ou une liste `{id,label,start,end}` |
| `html_layer` | `{"src":"index.html","timeline":"main","track":"components","vars":{...}?}`. Avec `vars`, l'adaptateur écrit `index.review.html`, qui simule les variables HyperFrames (ex. `{"arrows":true}`) |
| `version` | nom du tour, affiché dans le menu Versions |
| `notes`, `chapters`, `duration`, `audio_track` | optionnels (`audio_track: false` retire la forme d'onde) |

Pour rendre un élément HyperFrames cliquable, ajouter `data-rid="<id>"` sur son nœud et le déclarer dans `components` avec le même `rid`.
La page doit exposer `window.__timelines[<timeline>]`, un objet qui a une méthode `seek(t)` (la timeline GSAP en pause d'une composition HyperFrames).

Exemple complet et exécutable : [`examples/demo`](../examples/demo).

## Tours et versions
- `--next-round` archive le tour qui se termine dans `review/versions/round-N.json`, puis écrit le tour N+1.
- La clé `version` (ou `--label`) nomme le tour dans `review/versions/index.json`.
- **Storyboard → final** : changer `"stage"` dans la config suffit. L'adaptateur garde le dernier storyboard dans `review/manifest.storyboard.json`, l'archive comme version, et le final commence au tour suivant. Rester dans le même dossier du début à la fin, sinon l'app perd l'onglet Storyboard et l'historique.
- Reconstituer un ancien tour depuis une config sauvegardée, sans toucher au tour courant :
  `adapter/review_manifest.py <projet> --archive-config ancienne.json --round N --label "V1 · …"`.
- Donner un nouveau nom de fichier au rendu de chaque tour, pour que les anciennes versions restent lisibles.

## Limites
- Une composition HyperFrames charge GSAP depuis un CDN : il faut être en ligne pour cliquer ses éléments.
- Le parseur `mixpy` reconnaît trois formes : les tuples `("fichier", t, vol, ss, dur)`, les boucles `for t in (…)` et les boucles `round(x*i,2) for i in range(a,b)`.
