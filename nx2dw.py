from datawrapper import Datawrapper
import networkx as nx


class nx2dw:
    def __init__(
        self,
        dw_access_token,
        dw_team_id=None,
        dw_folder_id=None,
        scale_factor=1,
        boundary_padding=0.1,
    ):
        self.dw = Datawrapper(access_token=dw_access_token)
        self.TEAM_ID = dw_team_id
        self.FOLDER_ID = dw_folder_id
        self.SCALE_FACTOR = scale_factor
        self.BOUNDARY_PADDING = boundary_padding

    def _get_node_data(self, layout):
        header_line = "node_id,&nbsp;,&nbsp;&nbsp;\n"  # encode label x and y as empty spaces to avoid showing axis labels
        node_data = header_line + "\n".join(
            [
                f"{node_id.replace(',', '&#44;')},{position[0] * self.SCALE_FACTOR},{position[1] * self.SCALE_FACTOR}"
                for node_id, position in layout.items()
            ]
        )
        return node_data

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

        node_data = self._get_node_data(layout)

        edge_data = self._get_edge_data(
            G, layout, default_edge_color, default_edge_opacity, default_edge_width
        )

        boundary_scale_factor = (1 + self.BOUNDARY_PADDING) * self.SCALE_FACTOR
        boundaries = {
            "x_min": float(x_min * boundary_scale_factor),
            "x_max": float(x_max * boundary_scale_factor),
            "y_min": float(y_min * boundary_scale_factor),
            "y_max": float(y_max * boundary_scale_factor),
        }

        return node_data, edge_data, boundaries

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

        node_data, edge_data, boundaries = self._compute_graph_layout_data(
            G, layout_algorithm, default_edge_color, default_edge_opacity, default_edge_width
        )

        chart_info = self.dw.create_chart(
            title=title,
            chart_type="d3-scatter-plot",
            data=node_data,
            organization_id=self.TEAM_ID,
            folder_id=self.FOLDER_ID,
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
                    "base-color": node_color,
                    "plotHeightFixed": 600,
                    "tooltip": {
                        "body": "",
                        "title": "{{ node_id }}",
                        "sticky": False,
                        "enabled": True,
                    },
                    "auto-labels": True,
                },
                "axes": {"labels": "node_id"},
            },
        )
        return f'https://app.datawrapper.de/edit/{chart_info["id"]}/visualize#annotate'
