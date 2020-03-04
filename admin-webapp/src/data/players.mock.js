const mockPlayers = { json: () => Promise.resolve({"players": [
    {"playerId": 1, "teamId": 1, "health": 5, "parameters": {"player.maxHealth": {"currentValue": 100, "effects": [], "baseValue": 100}, "gun.damage": {"currentValue": 2, "effects": [], "baseValue": 2}}, "ammo": 100},
    {"playerId": 1, "teamId": 2, "health": 5, "parameters": {"player.maxHealth": {"currentValue": 100, "effects": [], "baseValue": 100}, "gun.damage": {"currentValue": 2, "effects": [], "baseValue": 2}}, "ammo": 100},
    {"playerId": 3, "teamId": 1, "health": 55, "parameters": {"player.maxHealth": {"currentValue": 100, "effects": [], "baseValue": 100}, "gun.damage": {"currentValue": 2, "effects": [], "baseValue": 2}}, "ammo": 80},
]})};

export { mockPlayers }