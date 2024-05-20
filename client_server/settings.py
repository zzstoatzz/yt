from pydantic import Field
from pydantic_settings import BaseSettings


class DemoSettings(BaseSettings):
    model_config = dict(env_prefix="DEMO_", env_file=".env", extra="ignore")

    initial_clients: int = Field(30, description="Initial number of clients")
    num_steps: int = Field(100, description="Number of simulation steps")
    clients_per_step: int = Field(
        5, description="Maximum number of clients to add per step"
    )
    reset_clients: bool = Field(
        False, description="Whether to reset all clients after all steps"
    )

    num_servers: int = Field(5, description="Number of servers")
    max_group_size: int = Field(3, description="Maximum number of servers in a group")
    max_connections: int = Field(
        10, description="Maximum number of connections per server"
    )
    CLIENT_POOL_size: int = Field(50, description="Number of clients in the pool")
    client_lifetime_mean: int = Field(
        100, description="Average connection lifetime for clients"
    )
    client_lifetime_stddev: int = Field(
        2, description="Standard deviation of connection lifetime for clients"
    )
    LOG_TAIL: int = Field(40, description="Number of log entries to display")

    server_node_size: int = Field(700, description="Size of server nodes")
    client_node_size: int = Field(100, description="Size of client nodes")

    num_LOAD_BALANCERS: int = Field(1, description="Number of load balancers")
    load_balancer_node_size: int = Field(500, description="Size of load balancer nodes")
    load_balancer_color: str = Field(
        "orange", description="Color of load balancer nodes"
    )

    refresh_interval: int = Field(
        1000, description="Refresh interval for the animation"
    )


settings = DemoSettings()
