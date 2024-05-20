# autoscaling client-server-loadbalancer simulation

### network topology animation
![network topology](/client_server/img/ani.gif)

## try these settings
`.env` file:
```shell
DEMO_NUM_STEPS=100
DEMO_SINUSOIDAL=true # sinusoidal client arrival rate
DEMO_NUM_SERVERS=20 # number of servers to start with
DEMO_num_load_balancers=2 # static number of load balancers
DEMO_MAX_CLIENTS_PER_STEP=10 # max number of clients to add per step
DEMO_CLIENT_LIFETIME_MEAN=6
DEMO_CLIENT_LIFETIME_STDDEV=1
DEMO_MAX_CONNECTIONS=5
DEMO_REFRESH_INTERVAL=800 # rate to evolve the simulation
```