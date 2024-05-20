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
    min_servers: int = Field(1, description="Minimum number of servers")
    server_scale_up_threshold: float = Field(
        0.8, description="Server pressure threshold for scaling up"
    )
    server_scale_down_threshold: float = Field(
        0.4, description="Server pressure threshold for scaling down"
    )
    max_pressure_history: int = Field(
        100, description="Number of pressure values to keep for moving average"
    )
    emwa_alpha: float = Field(
        0.5, description="Exponential moving average alpha value for pressure"
    )
    max_connections: int = Field(
        10, description="Maximum number of connections per server"
    )
    client_pool_size: int = Field(50, description="Number of clients in the pool")
    client_lifetime_mean: int = Field(
        10, description="Average connection lifetime for clients"
    )
    client_lifetime_stddev: int = Field(
        2, description="Standard deviation of connection lifetime for clients"
    )
    SINUSOIDAL: bool = Field(False, description="Whether to add clients sinusoidally")
    LOG_TAIL: int = Field(40, description="Number of log entries to display")

    server_node_size: int = Field(700, description="Size of server nodes")
    client_node_size: int = Field(100, description="Size of client nodes")

    num_load_balancers: int = Field(2, description="Number of load balancers")
    load_balancer_node_size: int = Field(500, description="Size of load balancer nodes")
    load_balancer_color: str = Field(
        "orange", description="Color of load balancer nodes"
    )

    refresh_interval: int = Field(
        1000, description="Refresh interval for the animation"
    )


settings = DemoSettings()
