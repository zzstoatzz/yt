import random

from settings import settings
from variables import (
    CLIENT_LIFETIMES,
    CLIENT_POOL,
    LOAD_BALANCERS,
    LOCK,
    LOG_BUFFER,
    NETWORK,
    SERVERS,
    UPDATE_EVENT,
)


def add_client(client: str):
    if client in CLIENT_LIFETIMES:
        raise ValueError(f"❌ {client} is already online")

    load_balancer = random.choice(LOAD_BALANCERS)
    with LOCK:
        if len(CLIENT_LIFETIMES) >= len(SERVERS) * settings.max_connections:
            LOG_BUFFER.append(f"⛔️ {client} connection refused: network is full")
            return
        NETWORK.add_node(client, type="client")
        NETWORK.add_edge(client, load_balancer)
        LOG_BUFFER.append(f"🟢 {client} connected to {load_balancer}")
        CLIENT_LIFETIMES[client] = max(
            1,
            int(
                random.gauss(
                    settings.client_lifetime_mean, settings.client_lifetime_stddev
                )
            ),
        )

    if available_servers := [
        server
        for server in SERVERS
        if NETWORK.degree(server) < settings.max_connections
    ]:
        server = random.choice(available_servers)
        with LOCK:
            NETWORK.add_edge(load_balancer, server, client=client)
            LOG_BUFFER.append(f"🤝 {load_balancer} connected {client} to {server}")
            SERVERS[server].append(client)

    UPDATE_EVENT.set()


def add_random_client():
    if offline_clients := list(set(CLIENT_POOL) - set(CLIENT_LIFETIMES.keys())):
        add_client(random.choice(offline_clients))


def initialize_network(num_clients: int, reset=False):
    if reset:
        with LOCK:
            NETWORK.clear()
            NETWORK.add_nodes_from(SERVERS, type="server")
            NETWORK.add_nodes_from(LOAD_BALANCERS, type="load_balancer")
            CLIENT_LIFETIMES.clear()
            LOG_BUFFER.clear()
            [server_cnxs.clear() for server_cnxs in SERVERS.values()]
    for i in range(num_clients):
        add_random_client()


def update_client_lifetimes():
    clients_to_remove = []
    with LOCK:
        for client in list(CLIENT_LIFETIMES.keys()):
            CLIENT_LIFETIMES[client] -= 1
            if CLIENT_LIFETIMES[client] <= 0:
                clients_to_remove.append(client)

        for client in clients_to_remove:
            load_balancer = next(NETWORK.neighbors(client))
            server = None
            for neighbor in NETWORK.neighbors(load_balancer):
                if NETWORK.nodes[neighbor]["type"] == "server":
                    edge_data = NETWORK.get_edge_data(load_balancer, neighbor)
                    if any(client == data.get("client") for data in edge_data.values()):
                        server = neighbor
                        break

            if server is None:
                print(
                    f"EDGE DATA: {NETWORK.get_edge_data(load_balancer, server)}",
                    file=open("error_log.txt", "a"),
                )
                LOG_BUFFER.append(
                    f"❌ {load_balancer} failed to disconnect {client} from server"
                )

            edges_to_remove = [
                (load_balancer, server, key)
                for key, data in NETWORK.get_edge_data(load_balancer, server).items()
                if data.get("client") == client
            ]
            for edge in edges_to_remove:
                NETWORK.remove_edge(*edge)
            if client in (server_ctxs := SERVERS[server]):
                server_ctxs.remove(client)
            LOG_BUFFER.append(f"💤 {load_balancer} disconnected {client} from {server}")

            NETWORK.remove_node(client)
            del CLIENT_LIFETIMES[client]
            LOG_BUFFER.append(f"🔘 {client} disconnected from {load_balancer}")

    if clients_to_remove:
        UPDATE_EVENT.set()
