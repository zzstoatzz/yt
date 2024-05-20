import networkx as nx
import numpy as np
from matplotlib import pyplot as plt
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from settings import settings
from variables import (
    CLIENT_LIFETIMES,
    CONSOLE,
    LOAD_BALANCERS,
    LOCK,
    LOG_BUFFER,
    NETWORK,
    ONLINE_CLIENTS,
    SERVERS,
    update_event,
)


def get_colors(status: dict[str, int], cmap_name: str = "viridis") -> dict[str, str]:
    max_connections = max(status.values()) or 1
    norm = plt.Normalize(vmin=0, vmax=max_connections)
    cmap = plt.get_cmap(cmap_name)
    return {node: cmap(norm(count)) for node, count in status.items()}


def get_server_status() -> dict[str, bool]:
    with LOCK:
        return {server: NETWORK.degree(server) > 0 for server in SERVERS}


def get_load_balancer_status() -> dict[str, int]:
    with LOCK:
        status = {load_balancer: 0 for load_balancer in LOAD_BALANCERS}
        for load_balancer in LOAD_BALANCERS:
            for neighbor in NETWORK.neighbors(load_balancer):
                if NETWORK.nodes[neighbor]["type"] == "client":
                    status[load_balancer] += 1
    return status


def get_CLIENT_LIFETIMES() -> dict[str, int]:
    with LOCK:
        return CLIENT_LIFETIMES.copy()


def create_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", ratio=1),
        Layout(name="main", ratio=6),
        Layout(name="settings_panel", ratio=1),
    )
    layout["main"].split_row(
        Layout(name="left_panel", ratio=2),
        Layout(name="right_panel", ratio=3),
    )
    layout["left_panel"].split_column(
        Layout(name="client_panel", ratio=1),
        Layout(name="server_panel", ratio=1),
        Layout(name="load_balancer_panel", ratio=1),
    )
    layout["right_panel"].split_column(
        Layout(name="logs", ratio=1),
    )
    return layout


def update_header() -> Panel:
    current_clients = len(ONLINE_CLIENTS)
    active_servers = len([server for server in SERVERS if NETWORK.degree(server) > 0])
    return Panel(
        Text(
            f"Active Clients: {current_clients} | Active Servers: {active_servers}",
            style="bold cyan",
            justify="center",
        ),
        title="Network Status",
        border_style="blue",
    )


def update_server_panel() -> Panel:
    return Panel(
        Text(
            "\n".join(
                [
                    f"{server} is {'active' if connections else 'idle'}"
                    for server, connections in sorted(get_server_status().items())
                ]
            ),
            style="cyan",
        ),
        title="Server Status",
        border_style="blue",
    )


def update_client_panel() -> Panel:
    with LOCK:
        CLIENT_LIFETIMES_copy = CLIENT_LIFETIMES.copy()
    client_text = "\n".join(
        [
            f"{client}: {lifetime}"
            for client, lifetime in sorted(CLIENT_LIFETIMES_copy.items())
        ]
    )
    return Panel(
        Text(client_text, style="green"), title="Client Lifetimes", border_style="green"
    )


def update_log_panel() -> Panel:
    return Panel(
        Text("\n".join(LOG_BUFFER), overflow="ellipsis", justify="left"),
        title="Logs",
        border_style="red",
    )


def update_load_balancer_panel() -> Panel:
    return Panel(
        Text(
            "\n".join(
                [
                    f"{load_balancer} has {connections} connected client(s)"
                    for load_balancer, connections in sorted(
                        get_load_balancer_status().items()
                    )
                ]
            ),
            style="magenta",
        ),
        title="Load Balancer Status",
        border_style="magenta",
    )


def update_settings_panel() -> Panel:
    return Panel(
        Text(repr(settings), style="magenta", justify="left"),
        title="Active Settings",
        border_style="magenta",
    )


def live_rich_console():
    layout = create_layout()

    with Live(layout, console=CONSOLE, screen=True, refresh_per_second=1):
        while True:
            try:
                update_event.wait()
                update_event.clear()
                layout["header"].update(update_header())
                layout["client_panel"].update(update_client_panel())
                layout["server_panel"].update(update_server_panel())
                layout["load_balancer_panel"].update(update_load_balancer_panel())
                layout["logs"].update(update_log_panel())
                layout["settings_panel"].update(update_settings_panel())
            except Exception as e:
                print(e, file=open("error.log", "a"))


def circular_layout(network, radius=1) -> dict[str, tuple[float, float]]:
    pos = {}
    num_servers = len(
        [n for n in network.nodes if network.nodes[n]["type"] == "server"]
    )
    angle_step = 2 * np.pi / num_servers

    for i, server in enumerate(
        [n for n in network.nodes if network.nodes[n]["type"] == "server"]
    ):
        angle = i * angle_step
        pos[server] = (radius * np.cos(angle), radius * np.sin(angle))

    pos.update(nx.spring_layout(network, pos=pos, fixed=pos.keys()))

    return pos


def visualize_network(step: int, ax):
    ax.clear()
    pos = circular_layout(NETWORK)

    server_status = get_server_status()
    load_balancer_status = get_load_balancer_status()

    load_balancer_colors = get_colors(load_balancer_status, "viridis")

    nx.draw_networkx_nodes(
        NETWORK,
        pos,
        nodelist=[
            node
            for node, data in NETWORK.nodes(data=True)
            if data["type"] == "load_balancer"
        ],
        node_color=[load_balancer_colors[node] for node in LOAD_BALANCERS],
        node_size=settings.load_balancer_node_size,
        label="Load Balancers",
        ax=ax,
    )

    nx.draw_networkx_nodes(
        NETWORK,
        pos,
        nodelist=[
            node for node, data in NETWORK.nodes(data=True) if data["type"] == "server"
        ],
        node_color=[
            "orange" if server_status[server] else "gray" for server in SERVERS
        ],
        node_size=settings.server_node_size,
        label="Servers",
        ax=ax,
    )

    nx.draw_networkx_nodes(
        NETWORK,
        pos,
        nodelist=[
            node for node, data in NETWORK.nodes(data=True) if data["type"] == "client"
        ],
        node_color="green",
        node_size=settings.client_node_size,
        label="Clients",
        ax=ax,
    )

    nx.draw_networkx_edges(
        NETWORK,
        pos,
        edgelist=[
            (u, v)
            for u, v in NETWORK.edges()
            if NETWORK.nodes[u]["type"] == "load_balancer"
            and NETWORK.nodes[v]["type"] == "client"
        ],
        edge_color="green",
        ax=ax,
    )

    nx.draw_networkx_edges(
        NETWORK,
        pos,
        edgelist=[
            (u, v)
            for u, v in NETWORK.edges()
            if NETWORK.nodes[u]["type"] == "load_balancer"
            and NETWORK.nodes[v]["type"] == "server"
        ],
        edge_color="orange",
        ax=ax,
    )

    nx.draw_networkx_labels(NETWORK, pos, ax=ax)
    ax.legend()
    ax.set_title(
        f"Server-Client Network Simulation with Load Balancers - Step {step + 1}"
    )
