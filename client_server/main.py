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


def wavy_demand(step: int, amplitude: int, frequency: float, offset: int) -> int:
    """
    Calculate the number of clients to add based on a sinusoidal function.

    only used if settings.SINUSOIDAL is True (e.g. export DEMO_SINUSOIDAL=1)

    Args:
        step: The current step in the simulation.
        amplitude: The maximum number of clients to add (peak of the wave).
        frequency: The frequency of the sine wave.
        offset: The offset to shift the entire wave vertically.

    Returns:
        int: The number of clients to add at the current step.
    """
    return int(amplitude * np.sin(2 * np.pi * frequency * step) + offset)


AMPLITUDE = 10
ƒ = 3 / 5
ø = settings.clients_per_step

if __name__ == "__main__":
    threading.Thread(target=live_rich_console, daemon=True).start()

    fig, ax = plt.subplots(figsize=(12, 8))

    def animate(step):
        if step == 0:
            initialize_network(settings.initial_clients)
        else:
            for _ in range(
                settings.clients_per_step
                if not settings.SINUSOIDAL
                else wavy_demand(step, AMPLITUDE, ƒ, ø)
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
