import os
import warnings

import networkx as nx
import requests

DW_API_URL = "https://api.datawrapper.de/v3"


def _from_arg_or_env(value, env_var, required):
    if value is None:
        value = os.environ.get(env_var) or None
    if value is None:
        message = f"{env_var} was neither passed as an argument nor found in the environment"
        if required:
            raise ValueError(message)
        warnings.warn(f"{message}, continuing without it", stacklevel=3)
    return value


class nx2dw:
    def __init__(
        self,
        dw_api_key=None,
        dw_team_id=None,
        dw_folder_id=None,
        scale_factor=1,
        boundary_padding=0.1,
    ):
        dw_api_key = _from_arg_or_env(dw_api_key, "DW_API_KEY", required=True)
        dw_team_id = _from_arg_or_env(dw_team_id, "DW_TEAM_ID", required=False)
        dw_folder_id = _from_arg_or_env(dw_folder_id, "DW_FOLDER_ID", required=False)

        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {dw_api_key}"})
        self.TEAM_ID = dw_team_id
        # env vars are strings, but the API expects a numeric folder id
        self.FOLDER_ID = int(dw_folder_id) if dw_folder_id is not None else None
        self.SCALE_FACTOR = scale_factor
        self.BOUNDARY_PADDING = boundary_padding

    def _get_node_data(self, G, layout):
        node_group = nx.get_node_attributes(G, "node_group")

        header_line = "node_id,&nbsp;,&nbsp;&nbsp;"  # encode label x and y as empty spaces to avoid showing axis labels
        if node_group:
            header_line += ",group"

        def get_node_row(node_id, position):
            row = f"{node_id.replace(',', '&#44;')},{position[0] * self.SCALE_FACTOR},{position[1] * self.SCALE_FACTOR}"
            if node_group:
                row += f",{str(node_group.get(node_id, '')).replace(',', '&#44;')}"
            return row

        node_data = header_line + "\n" + "\n".join(
            [get_node_row(node_id, position) for node_id, position in layout.items()]
        )
        return node_data, bool(node_group)

    def _get_edge_data(
        self, G, layout, default_edge_color, default_edge_opacity, default_edge_width
    ):
        edge_color = nx.get_edge_attributes(G, "edge_color")
        edge_opacity = nx.get_edge_attributes(G, "edge_opacity")
        edge_width = nx.get_edge_attributes(G, "edge_width")

        def get_edge_width(source, target):
            try:
                return edge_width[(source, target)]
            except KeyError:
                return default_edge_width

        def get_edge_color(source, target):
            try:
                return edge_color[(source, target)]
            except KeyError:
                return default_edge_color

        def get_edge_opacity(source, target):
            try:
                return edge_opacity[(source, target)]
            except KeyError:
                return default_edge_opacity

        edge_data = "\n".join(
            [
                f"{','.join([str(x * self.SCALE_FACTOR) for x in layout[source]])}, {','.join([str(x * self.SCALE_FACTOR) for x in layout[target]])} @width:{get_edge_width(source, target)} @color:{get_edge_color(source, target)} @opacity:{get_edge_opacity(source, target)}"
                for source, target in G.edges
            ]
        )
        return edge_data

    def _create_chart(self, title, chart_type, data, metadata):
        chart = {"title": title, "type": chart_type, "metadata": metadata}
        if self.TEAM_ID:
            chart["organizationId"] = self.TEAM_ID
        if self.FOLDER_ID:
            chart["folderId"] = self.FOLDER_ID

        response = self.session.post(f"{DW_API_URL}/charts", json=chart, timeout=30)
        response.raise_for_status()
        chart_info = response.json()

        response = self.session.put(
            f"{DW_API_URL}/charts/{chart_info['id']}/data",
            data=data.encode("utf-8"),
            headers={"Content-Type": "text/csv"},
            timeout=30,
        )
        response.raise_for_status()

        return chart_info

    def _compute_graph_layout_data(
        self,
        G,
        layout_algorithm,
        default_edge_color,
        default_edge_opacity,
        default_edge_width,
    ):
        layout = layout_algorithm(G)
        x_values = [pos[0] for pos in layout.values()]
        y_values = [pos[1] for pos in layout.values()]

        x_min, x_max = min(x_values), max(x_values)
        y_min, y_max = min(y_values), max(y_values)

        node_data, has_groups = self._get_node_data(G, layout)

        edge_data = self._get_edge_data(
            G, layout, default_edge_color, default_edge_opacity, default_edge_width
        )

        # pad each side by a share of the layout's extent, so the padding works
        # regardless of where the layout is positioned (it's not always centered on 0)
        x_padding = (x_max - x_min) * self.BOUNDARY_PADDING
        y_padding = (y_max - y_min) * self.BOUNDARY_PADDING
        boundaries = {
            "x_min": float((x_min - x_padding) * self.SCALE_FACTOR),
            "x_max": float((x_max + x_padding) * self.SCALE_FACTOR),
            "y_min": float((y_min - y_padding) * self.SCALE_FACTOR),
            "y_max": float((y_max + y_padding) * self.SCALE_FACTOR),
        }

        return node_data, has_groups, edge_data, boundaries

    def create_datawrapper_graph(
        self,
        G,
        layout_algorithm=nx.forceatlas2_layout,
        title="Network Graph",
        description="",
        node_color="#000000",
        node_size=20,
        default_edge_color="#686868",
        default_edge_opacity=0.5,
        default_edge_width=4,
    ):

        node_data, has_groups, edge_data, boundaries = self._compute_graph_layout_data(
            G, layout_algorithm, default_edge_color, default_edge_opacity, default_edge_width
        )

        # node_color is either a single color for all nodes, or a {node_group: color} dict
        # to color nodes by their "node_group" attribute
        axes = {"labels": "node_id"}
        color_settings = {"base-color": node_color}
        if isinstance(node_color, dict):
            if not has_groups:
                raise ValueError("node_color is a dict, but no node has a node_group attribute")
            axes["color"] = "group"
            color_settings = {
                "color-by-column": True,
                "color-category": {"map": node_color},
                "show-color-key": True,
            }

        chart_info = self._create_chart(
            title=title,
            chart_type="d3-scatter-plot",
            data=node_data,
            metadata={
                "describe": {
                    "intro": description,
                },
                "visualize": {
                    "custom-lines": edge_data,
                    "x-axis": {
                        "log": False,
                        "range": [boundaries["x_min"], boundaries["x_max"]],
                        "ticks": [],
                    },
                    "x-grid": "off",
                    "y-axis": {
                        "log": False,
                        "range": [boundaries["y_min"], boundaries["y_max"]],
                        "ticks": [],
                    },
                    "y-grid": "off",
                    "x-grid-lines": "off",
                    "y-grid-lines": "off",
                    "fixed-size": node_size,
                    "plotHeightFixed": 600,
                    "tooltip": {
                        "body": "",
                        "title": "{{ node_id }}",
                        "sticky": False,
                        "enabled": True,
                    },
                    "auto-labels": True,
                    **color_settings,
                },
                "axes": axes,
            },
        )
        return f'https://app.datawrapper.de/edit/{chart_info["id"]}/visualize#annotate'
