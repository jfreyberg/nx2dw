import pandas as pd
import networkx as nx
from dotenv import load_dotenv
from nx2dw import nx2dw

# reads DW_API_KEY, DW_TEAM_ID and DW_FOLDER_ID from a .env file next to this script.
# alternatively, pass them directly: nx2dw(dw_api_key=..., dw_team_id=..., dw_folder_id=...)
load_dotenv()

starwars_network = pd.read_csv("./starwars.csv")

G = nx.from_pandas_edgelist(starwars_network, "source", "target", edge_attr=True)

chart_url = nx2dw().create_datawrapper_graph(
    G,
    title="The social network of Star Wars IV",
    description="The network shows characters from the original 1977 Star Wars movie, nowadays called Star Wars: Episode IV - A New Hope. Characters who are speaking together within the same scene least once according to the script have an edge between them. Edge thickness increases based on the amount of such scenes.",
    node_color="#9191E9",
    node_size=16,
    default_edge_color="#C2AFF0",
    default_edge_opacity=0.5,
)

print(f"your network is ready @ {chart_url}")
