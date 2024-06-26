import threading

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from network import (
    add_random_client,
    initialize_network,
    update_client_lifetimes,
)
from servers import manage_servers
from settings import settings
from viz import (
    live_rich_console,
    visualize_network,
)

A = 12
ƒ = 4 / 5
ø = settings.clients_per_step

if __name__ == "__main__":
    threading.Thread(target=live_rich_console, daemon=True).start()

    fig, ax = plt.subplots(figsize=(12, 8))

    def animate(step):
        if step == 0:
            initialize_network(settings.initial_clients)
        else:
            for _ in range(
                ø
                if not settings.SINUSOIDAL
                else int(A * np.sin(2 * np.pi * ƒ * step) + ø)
            ):
                add_random_client()

        update_client_lifetimes()
        visualize_network(step, ax)
        manage_servers()

        if step == settings.num_steps - 1:
            initialize_network(settings.initial_clients, reset=settings.reset_clients)

    ani = animation.FuncAnimation(
        fig, animate, frames=settings.num_steps, interval=settings.refresh_interval
    )

    plt.show()
