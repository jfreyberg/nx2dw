import networkx as nx
import pytest

from nx2dw import nx2dw


@pytest.fixture(autouse=True)
def dw_env(monkeypatch):
    monkeypatch.setenv("DW_API_KEY", "test-key")
    monkeypatch.delenv("DW_TEAM_ID", raising=False)
    monkeypatch.delenv("DW_FOLDER_ID", raising=False)


@pytest.fixture
def created_charts(monkeypatch):
    """Capture chart creation instead of calling the Datawrapper API."""
    charts = []

    def fake_create_chart(self, title, chart_type, data, metadata):
        charts.append({"title": title, "type": chart_type, "data": data, "metadata": metadata})
        return {"id": "abc12"}

    monkeypatch.setattr(nx2dw, "_create_chart", fake_create_chart)
    return charts


def grouped_graph():
    G = nx.Graph()
    G.add_edge("Luke", "Leia", edge_width=3)
    G.add_edge("Luke", "Darth Vader", edge_width=1)
    G.add_edge("Leia", "Darth Vader", edge_width=2)
    nx.set_node_attributes(G, {"Luke": "Rebels", "Leia": "Rebels", "Darth Vader": "Empire"}, "node_group")
    return G


def node_rows(data):
    header, *rows = data.splitlines()
    return header, [row.split(",") for row in rows]


def test_api_key_from_env():
    client = nx2dw()
    assert client.session.headers["Authorization"] == "Bearer test-key"


def test_api_key_argument_wins_over_env():
    client = nx2dw(dw_api_key="other-key")
    assert client.session.headers["Authorization"] == "Bearer other-key"


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("DW_API_KEY")
    with pytest.raises(ValueError, match="DW_API_KEY"):
        nx2dw()


def test_folder_id_from_env_is_numeric(monkeypatch):
    monkeypatch.setenv("DW_FOLDER_ID", "12345")
    assert nx2dw().FOLDER_ID == 12345


def test_returns_edit_url(created_charts):
    url = nx2dw().create_datawrapper_graph(grouped_graph(), title="Test")
    assert url == "https://app.datawrapper.de/edit/abc12/visualize#annotate"
    assert created_charts[0]["title"] == "Test"
    assert created_charts[0]["type"] == "d3-scatter-plot"


@pytest.mark.parametrize(
    "layout", [nx.circular_layout, nx.random_layout, nx.spiral_layout, nx.forceatlas2_layout]
)
def test_all_nodes_inside_chart_range(created_charts, layout):
    nx2dw().create_datawrapper_graph(grouped_graph(), layout_algorithm=layout)
    chart = created_charts[0]
    _, rows = node_rows(chart["data"])
    x_min, x_max = chart["metadata"]["visualize"]["x-axis"]["range"]
    y_min, y_max = chart["metadata"]["visualize"]["y-axis"]["range"]
    for _, x, y, *_ in rows:
        assert x_min < float(x) < x_max
        assert y_min < float(y) < y_max


def test_single_color(created_charts):
    nx2dw().create_datawrapper_graph(grouped_graph(), node_color="#ff0000")
    visualize = created_charts[0]["metadata"]["visualize"]
    assert visualize["base-color"] == "#ff0000"
    assert "color" not in created_charts[0]["metadata"]["axes"]


def test_group_colors(created_charts):
    colors = {"Rebels": "#faab55", "Empire": "#ff5a5e"}
    nx2dw().create_datawrapper_graph(grouped_graph(), node_color=colors)
    chart = created_charts[0]
    header, rows = node_rows(chart["data"])
    assert header.endswith(",group")
    assert {row[0]: row[3] for row in rows} == {"Luke": "Rebels", "Leia": "Rebels", "Darth Vader": "Empire"}
    assert chart["metadata"]["visualize"]["color-category"] == {"map": colors}
    assert chart["metadata"]["axes"]["color"] == "group"


def test_group_colors_without_groups_raises(created_charts):
    with pytest.raises(ValueError, match="node_group"):
        nx2dw().create_datawrapper_graph(nx.relabel_nodes(nx.path_graph(3), str), node_color={"A": "#000"})


def test_commas_in_names_are_escaped(created_charts):
    G = nx.Graph()
    G.add_edge("Solo, Han", "Chewbacca")
    nx2dw().create_datawrapper_graph(G)
    _, rows = node_rows(created_charts[0]["data"])
    assert {row[0] for row in rows} == {"Solo&#44; Han", "Chewbacca"}


def test_edge_attributes(created_charts):
    nx2dw().create_datawrapper_graph(grouped_graph(), default_edge_color="#123456", default_edge_opacity=0.3)
    lines = created_charts[0]["metadata"]["visualize"]["custom-lines"].splitlines()
    assert len(lines) == 3
    assert sorted(line.split("@width:")[1].split()[0] for line in lines) == ["1", "2", "3"]
    assert all("@color:#123456" in line and "@opacity:0.3" in line for line in lines)
