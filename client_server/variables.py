from collections import deque
from threading import Event, Lock

import networkx as nx
from rich.console import Console
from settings import settings

CONSOLE = Console()
LOG_BUFFER = deque(maxlen=settings.LOG_TAIL)

CLIENT_LIFETIMES = {}
CLIENT_QUEUE = deque()
CLIENT_POOL = deque([f"Client_{i:02d}" for i in range(settings.client_pool_size)])
SERVERS = {
    f"Server_{chr(65 + i)}": deque(maxlen=settings.max_connections)
    for i in range(settings.num_servers)
}
SERVER_PRESSURE_HISTORY = deque(maxlen=settings.max_pressure_history)
LOAD_BALANCERS = deque(
    [f"LoadBalancer_{i+1}" for i in range(settings.num_load_balancers)]
)

NETWORK = nx.MultiGraph()
NETWORK.add_nodes_from(LOAD_BALANCERS, type="load_balancer")
NETWORK.add_nodes_from(SERVERS, type="server")

LOCK = Lock()
UPDATE_EVENT = Event()
