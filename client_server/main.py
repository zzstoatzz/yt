import threading

import matplotlib.animation as animation
import matplotlib.pyplot as plt
from network import (
    add_random_client,
    initialize_network,
    update_client_lifetimes,
)
from settings import settings
from viz import (
    live_rich_console,
    visualize_network,
)

if __name__ == "__main__":
    threading.Thread(target=live_rich_console, daemon=True).start()

    fig, ax = plt.subplots(figsize=(12, 8))

    def animate(step):
        if step == 0:
            initialize_network(settings.initial_clients)
        else:
            for _ in range(settings.clients_per_step):
                add_random_client()

        update_client_lifetimes()
        visualize_network(step, ax)

        if settings.reset_clients and step == settings.num_steps:
            initialize_network(settings.initial_clients, reset=True)

    ani = animation.FuncAnimation(
        fig, animate, frames=settings.num_steps, interval=settings.refresh_interval
    )

    plt.show()
