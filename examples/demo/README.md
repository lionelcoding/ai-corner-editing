# Projet exemple

Un short de 9 s, sans rush ni skill, pour essayer tout le parcours de relecture en quelques minutes.

| Fichier | Rôle |
|---|---|
| `review.config.json` | la config lue par l'adaptateur : 3 panneaux de storyboard, puis les pistes de la relecture finale |
| `index.html` | la couche HTML cliquable (cartes avec `data-rid`, timeline minimale `window.__timelines.main`) |
| `edit/words.json` | les mots des sous-titres (format `json` de l'adaptateur) |
| `make-media.sh` | fabrique avec ffmpeg les rendus `out/demo-v1.mp4`, `out/demo-v2.mp4` et les maquettes `frames/*.png` |

Les médias et le dossier `review/` sont générés, pas versionnés.

## Essayer
```bash
npm run demo
```
Puis suivre les étapes 3 à 6 du [guide du parcours](../../docs/parcours.md) avec ce dossier comme projet.

Les rendus sont des mires : les cartes de `index.html` ne s'y voient pas, mais elles restent cliquables (vers 4,8 s, clique au milieu de l'image pour sélectionner « Liste des étapes »). Dans un vrai projet, la couche HTML est la composition qui a servi au rendu.

Pour repartir de zéro : `rm -rf examples/demo/review`.
