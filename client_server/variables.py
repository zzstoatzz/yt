import logging
from collections import deque
from threading import Event, Lock

import networkx as nx
from rich.console import Console
from rich.logging import RichHandler
from settings import settings

CONSOLE = Console()
rich_handler = RichHandler(console=CONSOLE)
logging.basicConfig(level=logging.INFO, handlers=[rich_handler])

NETWORK = nx.MultiGraph()
CLIENT_POOL = [f"Client_{i:02d}" for i in range(settings.CLIENT_POOL_size)]
CLIENT_LIFETIMES = {}
LOAD_BALANCERS = [f"LoadBalancer_{i+1}" for i in range(settings.num_LOAD_BALANCERS)]
NETWORK.add_nodes_from(LOAD_BALANCERS, type="load_balancer")
ONLINE_CLIENTS = set()
LOCK = Lock()
update_event = Event()

SERVERS = [f"Server_{chr(65 + i)}" for i in range(settings.num_servers)]
NETWORK.add_nodes_from(SERVERS, type="server")

LOG_BUFFER = deque(maxlen=settings.LOG_TAIL)
