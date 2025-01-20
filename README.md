# UDP network latency, jitter and packet loss tester

A small script that acts as a middleman between your game client and game server. The script itself
starts a UDP server and waits for incoming packages which it passes on to the other end with a
slight delay and some jitter added. The latency is specified as a constant delay in seconds. Jitter
is either a random value between 0 and a constant (uniform random), or when in burst mode it is
either 0 or your specified constant. Packet loss is specified in percent.

I found that using burst mode works well in simulating mobile network connections.


## Examples

This is 40 ms delay added (roundtrip 20+20), 300 ms jitter added (roundtrip 150+150, burst mode
simulating mobile connection) and 1.1% packet loss.

```bash
./udp_route.py 12.34.56.78:9090 0.0.0.0:9090 0.04 burst:0.3 1.1
```

A small, uniform random jitter of maximum 10 ms and a 1 in 10k packet loss.
```bash
./udp_route.py game_x.company.com:56789 0.0.0.0:51304 0.07 uniform:0.01 0.01
```

On your local machine only, with heavy packet losses.
```bash
./udp_route.py localhost:1793 localhost:1793 0.21 uniform:0.3 23.5
```


## Output

The script prints a dot ('.') every time it sends a packet or a colon (':') for every packet sent
in jitter burst (i.e. slowed down). A 'd' is printed if the packet is thrown out when the packet
loss kicks in.

It looks like so:

```
..................::::..::.............................................d.......
..............:::::.:...:..:...:.........:......:.............d..::..........:.
:::::::.:::.:::::.::.::.:..d..:.........................:......................
......................d........................................................
```
