import argparse

import pandas as pd
import networkx as nx
from dotenv import load_dotenv
from nx2dw import nx2dw

# reads DW_API_KEY, DW_TEAM_ID and DW_FOLDER_ID from a .env file next to this script.
# alternatively, pass them directly: nx2dw(dw_api_key=..., dw_team_id=..., dw_folder_id=...)
load_dotenv()

MOVIES = {
    4: ("IV", "the original 1977 Star Wars movie, nowadays called Star Wars: Episode IV - A New Hope"),
    5: ("V", "the 1980 Star Wars movie Episode V - The Empire Strikes Back"),
    6: ("VI", "the 1983 Star Wars movie Episode VI - Return of the Jedi"),
}


def load_episodes(episodes):
    edges = pd.concat([pd.read_csv(f"./data/star-wars-{episode}/edges.csv") for episode in episodes])
    # the network is undirected, so sum up the scenes of each pair regardless of its order
    edges[["source", "target"]] = pd.DataFrame(
        [sorted(pair) for pair in zip(edges["source"], edges["target"])], index=edges.index
    )
    edges = edges.groupby(["source", "target"], as_index=False)["edge_width"].sum()

    # characters can change groups between episodes (e.g. Lando), the latest episode wins
    nodes = pd.concat([pd.read_csv(f"./data/star-wars-{episode}/nodes.csv") for episode in episodes])
    nodes = nodes.drop_duplicates("node_id", keep="last")

    G = nx.from_pandas_edgelist(edges, "source", "target", edge_attr=True)
    # attach a group to every node, nodes are colored by group
    nx.set_node_attributes(G, nodes.set_index("node_id")["node_group"].to_dict(), "node_group")
    return G


# layouts that can use the number of shared scenes to pull characters closer together
WEIGHTED_LAYOUTS = {
    "forceatlas2": nx.forceatlas2_layout,
    "spring": nx.spring_layout,
    "kamada-kawai": nx.kamada_kawai_layout,
    "spectral": nx.spectral_layout,
}
LAYOUTS = {
    **WEIGHTED_LAYOUTS,
    "arf": nx.arf_layout,
    "circular": nx.circular_layout,
    "shell": nx.shell_layout,
    "spiral": nx.spiral_layout,
    "random": nx.random_layout,
    "multipartite": lambda G: nx.multipartite_layout(G, subset_key="node_group"),  # one column per group
    "bfs": None,  # needs a start character, see below
}

parser = argparse.ArgumentParser(description="Create a Datawrapper chart of a Star Wars social network.")
parser.add_argument(
    "--episode",
    choices=[str(episode) for episode in MOVIES] + ["all"],
    default="4",
    help="episode to visualize, or all to combine the whole trilogy (default: 4)",
)
parser.add_argument("--layout", choices=LAYOUTS, default="forceatlas2", help="layout algorithm (default: forceatlas2)")
parser.add_argument(
    "--weighted",
    action="store_true",
    help=f"use the number of shared scenes as edge weight, only for: {', '.join(WEIGHTED_LAYOUTS)}",
)
parser.add_argument("--start", default="Luke", help="character the bfs layout starts from (default: Luke)")
args = parser.parse_args()
episode = args.episode

if args.weighted and args.layout not in WEIGHTED_LAYOUTS:
    parser.error(f"--weighted is not supported by the {args.layout} layout")

if episode == "all":
    G = load_episodes(sorted(MOVIES))
    title = "The social network of the Star Wars trilogy"
    movie_description = "the original Star Wars trilogy (Episodes IV - VI)"
else:
    G = load_episodes([int(episode)])
    roman_numeral, movie_description = MOVIES[int(episode)]
    title = f"The social network of Star Wars {roman_numeral}"

if args.layout == "bfs":
    if args.start not in G:
        parser.error(f"--start: {args.start} does not appear in this episode")
    layout_algorithm = lambda G: nx.bfs_layout(G, start=args.start)
elif args.weighted:
    layout_algorithm = lambda G: WEIGHTED_LAYOUTS[args.layout](G, weight="edge_width")
else:
    layout_algorithm = LAYOUTS[args.layout]

chart_url = nx2dw().create_datawrapper_graph(
    G,
    layout_algorithm=layout_algorithm,
    title=title,
    description=f"The network shows characters from {movie_description}. Characters who are speaking together within the same scene at least once according to the script have an edge between them. Edge thickness increases based on the amount of such scenes.",
    node_color={"Rebels": "#faab55", "Empire": "#ff5a5e", "Others": "#9191e9"},
    node_size=16,
    default_edge_color="#C2AFF0",
    default_edge_opacity=0.5,
)

print(f"your network is ready @ {chart_url}")
