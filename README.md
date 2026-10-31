# nx2dw

A small utility to visualize [NetworkX](https://networkx.org/) graphs as [Datawrapper](https://www.datawrapper.de/) scatterplots. This tool helps transform your graph data into interactive, visually appealing scatterplots using Datawrapper.

## Installation

```bash
pip install nx2dw
```

Requires Python 3.10 or newer. Some NetworkX layouts (e.g. `kamada_kawai_layout`, or `spring_layout` on large graphs) also need [SciPy](https://scipy.org/): `pip install scipy`.

## Usage

1. Initialize the client with your [Datawrapper API token](https://developer.datawrapper.de/docs/getting-started) (chart write rights required):

   ```python
   from nx2dw import nx2dw

   client = nx2dw(DW_API_KEY, DW_TEAM_ID, DW_FOLDER_ID)
   ```

   - `DW_TEAM_ID` and `DW_FOLDER_ID` are optional parameters for organizing your output.
   - Any argument you don't pass is read from the environment variable of the same name, so with `DW_API_KEY` set you can simply call `nx2dw()`.

2. Create a visualization from a NetworkX graph:

   ```python
   chart_url = client.create_datawrapper_graph(networkx_graph_object)
   ```

   This creates the chart in Datawrapper and returns the link to edit it there.

## Customization

You can customize the network by passing additional arguments to `create_datawrapper_graph`, such as the layout algorithm, node colors (one color, or one per node group) and edge styling.
For details, see [the source code](https://github.com/jfreyberg/nx2dw/blob/main/nx2dw.py).
Refer to the [example usage script](https://github.com/jfreyberg/nx2dw/blob/main/example.py) for more insights.
After generating the network you can further customize and edit it in the Datawrapper editor.

## Example Output

Here's an example of what you can create with this tool:

<img src="https://raw.githubusercontent.com/jfreyberg/nx2dw/main/example.png" alt="Example output of nx2dw">

<sub>Data is from [Evelina Gabasova: Star Wars social networks](https://github.com/evelinag/StarWars-social-network) (CC BY 4.0), see [data/README.md](https://github.com/jfreyberg/nx2dw/blob/main/data/README.md).</sub>

To create it yourself, clone this repository, copy `.env.example` to `.env` and add your API token, then run:

```bash
pip install -e ".[examples]"
python example.py --episode 4
```

Run `python example.py --help` to see the other episodes and layouts.

## About

This tool was originally created to generate a network for my blog post [Social (and other) networks in Datawrapper](https://www.datawrapper.de/blog/social-networks-datawrapper).

## License

[MIT](https://github.com/jfreyberg/nx2dw/blob/main/LICENSE)
