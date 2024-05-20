from collections import deque
from typing import Annotated

from pydantic import Field
from settings import settings
from variables import (
    CLIENT_LIFETIMES,
    LOCK,
    LOG_BUFFER,
    NETWORK,
    SERVER_PRESSURE_HISTORY,
    SERVERS,
    UPDATE_EVENT,
)

ServerPressure = Annotated[float, Field(ge=0, le=1)]


def calculate_server_pressure() -> ServerPressure:
    """must be called within a lock context"""
    max_connections = len(SERVERS) * settings.max_connections
    return (
        sum(len(SERVERS[server]) for server in SERVERS) / max_connections
        if max_connections
        else 0
    )


def calculate_ewma(alpha: float) -> ServerPressure:
    """Calculate the exponentially weighted moving average (EWMA) of the server pressures."""
    if not SERVER_PRESSURE_HISTORY:
        return 0
    ewma = 0
    weight = 1
    for pressure in reversed(SERVER_PRESSURE_HISTORY):
        ewma += alpha * weight * pressure
        weight *= 1 - alpha
    return ewma / (1 - weight)


def add_server():
    new_server_id = f"Server_{chr(65 + len(SERVERS))}"
    SERVERS[new_server_id] = deque(maxlen=settings.max_connections)
    NETWORK.add_node(new_server_id, type="server")
    LOG_BUFFER.append(f"🔺 Added new server: {new_server_id}")
    UPDATE_EVENT.set()


def remove_server():
    if len(SERVERS) > settings.min_servers:
        server_to_remove = next(iter(SERVERS))
        for client in list(SERVERS[server_to_remove]):
            NETWORK.remove_node(client)
            del CLIENT_LIFETIMES[client]
        NETWORK.remove_node(server_to_remove)
        del SERVERS[server_to_remove]
        LOG_BUFFER.append(f"🔻 Spun down server: {server_to_remove}")
    UPDATE_EVENT.set()


def manage_servers():
    with LOCK:
        pressure = calculate_server_pressure()
        SERVER_PRESSURE_HISTORY.append(pressure)
        moving_average_pressure = calculate_ewma(settings.emwa_alpha)

        if moving_average_pressure > settings.server_scale_up_threshold:
            add_server()
        elif moving_average_pressure < settings.server_scale_down_threshold:
            remove_server()
