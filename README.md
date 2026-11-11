# We Are Human — Browser Multiplayer PvE Prototype

This is an original, experimental browser-based third-person zombie survival prototype. It is **not** a hosted service or a copy of Dead Frontier 2's copyrighted graphics.

## Run locally

Install Python 3.10+ and run:

```bash
pip install -r requirements.txt
python server.py
```

Open http://localhost:8080 on your PC. Friends on the same Wi-Fi can connect to `http://YOUR_LOCAL_IP:8080`. For internet multiplayer, deploy this folder to a Python-compatible web host with WebSocket support and HTTPS, or configure secure reverse proxy and firewall rules. The server listens on port 8080 by default (`PORT` environment variable overrides).

## Controls

WASD movement, Shift sprint, mouse aim, click shoot, E loot, H medkit, Enter chat, Escape unlock mouse.

## Features

- Browser 3D graphics via Three.js loaded from CDN (requires internet for rendering)
- Dedicated Python multiplayer WebSocket server
- Server-authoritative zombie health and player-vs-zombie damage
- No PvP or friendly fire
- Two zombie-free outposts (players-only safe zones)
- Loot pickups, ammo, medkits, cash, zombie respawns, chat
- Secret `westonmerk` reward restricted to username `Moose1354` in this prototype

## Important limitations

- **Unverified build**: source code has not been tested in a real browser here.
- Accounts and money are **not persistent** across server restarts; no database or authentication is included.
- Username is not authenticated. Anyone can impersonate `Moose1354`; **do not use the secret reward on a public server until account authentication and admin permissions are implemented**.
- The city is procedurally assembled from simple 3D geometry; building interiors, advanced shaders, trading, detailed art, and inventory UI are future work.
- No permanent hosted server is provisioned by this ZIP.
