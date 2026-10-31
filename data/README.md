# Data

Star Wars social networks for episodes IV, V and VI, one directory per episode:

- `edges.csv`: characters who speak within the same scene at least once are connected, `edge_width` is the number of such scenes.
- `nodes.csv`: the group (`Rebels`, `Empire` or `Others`) of each character, used to color the nodes.

## Source

The edges are converted from the `starwars-episode-N-interactions-allCharacters.json` networks in [Evelina Gabasova's StarWars-social-network](https://github.com/evelinag/StarWars-social-network/tree/master/networks), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Characters without any connection (Gold Five in episode IV) are left out, character names use proper casing (e.g. `Darth Vader` instead of `DARTH VADER`), and Anakin's appearance in episode VI is counted as Darth Vader (his only connections were to Darth Vader himself and to Luke, with whom Darth Vader already shares that scene).

The groups in `nodes.csv` are not part of the original data, they were assigned by hand for this example.
