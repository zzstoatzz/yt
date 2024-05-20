import random

from settings import settings
from variables import (
    CLIENT_LIFETIMES,
    CLIENT_POOL,
    LOAD_BALANCERS,
    LOCK,
    LOG_BUFFER,
    NETWORK,
    ONLINE_CLIENTS,
    SERVERS,
    update_event,
)


def add_client(client: str):
    if client in ONLINE_CLIENTS:
        raise ValueError(f"{client} is already online")

    load_balancer = random.choice(LOAD_BALANCERS)
    with LOCK:
        NETWORK.add_node(client, type="client")
        NETWORK.add_edge(client, load_balancer)
        LOG_BUFFER.append(f"{client} connected to {load_balancer}")
        CLIENT_LIFETIMES[client] = max(
            1,
            int(
                random.gauss(
                    settings.client_lifetime_mean, settings.client_lifetime_stddev
                )
            ),
        )
        ONLINE_CLIENTS.add(client)
        update_event.set()

    if available_servers := [
        server
        for server in SERVERS
        if NETWORK.degree(server) < settings.max_connections
    ]:
        server = random.choice(available_servers)
        with LOCK:
            NETWORK.add_edge(load_balancer, server, client=client)
            LOG_BUFFER.append(f"{load_balancer} connected {client} to {server}")


def add_random_client():
    if offline_clients := set(CLIENT_POOL) - ONLINE_CLIENTS:
        add_client(random.choice(list(offline_clients)))


def initialize_network(num_clients: int, reset=False):
    if reset:
        with LOCK:
            NETWORK.clear()
            NETWORK.add_nodes_from(SERVERS, type="server")
            NETWORK.add_nodes_from(LOAD_BALANCERS, type="load_balancer")
            CLIENT_LIFETIMES.clear()
            ONLINE_CLIENTS.clear()
            LOG_BUFFER.clear()
    for i in range(num_clients):
        add_client(f"Client_{len(ONLINE_CLIENTS):02d}")


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
                if (
                    NETWORK.nodes[neighbor]["type"] == "server"
                    and NETWORK[load_balancer][neighbor].get("client") == client
                ):
                    server = neighbor
                    break
            if server is not None:
                NETWORK.remove_edge(load_balancer, server)
                LOG_BUFFER.append(
                    f"{load_balancer} disconnected {client} from {server}"
                )
            NETWORK.remove_node(client)
            del CLIENT_LIFETIMES[client]
            ONLINE_CLIENTS.remove(client)
            LOG_BUFFER.append(f"{client} disconnected from {load_balancer}")
    if clients_to_remove:
        update_event.set()
