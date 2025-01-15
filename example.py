import pandas as pd
import networkx as nx
from nx2dw import nx2dw

ACCESS_TOKEN = "YOUR_API_TOKEN"
TEAM_ID = "YOUR_TEAM_ID"
FOLDER_ID = 12345  # your folder ID

starwars_network = pd.read_csv("./starwars.csv")

G = nx.from_pandas_edgelist(starwars_network, "source", "target", edge_attr=True)

chart_url = nx2dw(ACCESS_TOKEN, TEAM_ID, FOLDER_ID).create_datawrapper_graph(
    G,
    title="The social network of Star Wars IV",
    description="The network shows characters from the original 1977 Star Wars movie, nowadays called Star Wars: Episode IV - A New Hope. Characters who are speaking together within the same scene least once according to the script have an edge between them. Edge thickness increases based on the amount of such scenes.",
    node_color="#9191E9",
    layout_algorithm=nx.circular_layout,
    node_size=16,
    default_edge_color="#C2AFF0",
    default_edge_opacity=0.5,
)

print(f"your network is ready @ {chart_url}")
