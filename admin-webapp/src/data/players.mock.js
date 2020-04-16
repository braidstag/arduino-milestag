const mockPlayers = {
    json: () => Promise.resolve({
        "players": [
            {
                "playerId": 1,
                "teamId": 1,
                "health": 5,
                "ammo": 100,
                "parameters": {
                    "player.maxHealth": { "currentValue": 100, "effects": [], "baseValue": 100 },
                    "gun.damage": { "currentValue": 2, "effects": [], "baseValue": 2 }
                },
                "stats": {
                    "shotsFired": 10,
                    "hitsReceived": 0,
                    "hitsGiven": 5,
                    "deaths": 0,
                    "kills": 1,
                },
            },
            {
                "playerId": 1,
                "teamId": 2,
                "health": 5,
                "ammo": 100,
                "parameters": {
                    "player.maxHealth": { "currentValue": 100, "effects": [], "baseValue": 100 },
                    "gun.damage": { "currentValue": 2, "effects": [], "baseValue": 2 }
                },
                "stats": {
                    "shotsFired": 10,
                    "hitsReceived": 50,
                    "hitsGiven": 1,
                    "deaths": 5,
                    "kills": 0,
                },
            },
            {
                "playerId": 3,
                "teamId": 1,
                "health": 55,
                "ammo": 80,
                "parameters": {
                    "player.maxHealth": { "currentValue": 100, "effects": [], "baseValue": 100 },
                    "gun.damage": { "currentValue": 2, "effects": [], "baseValue": 2 }
                },
                "stats": {
                    "shotsFired": 20,
                    "hitsReceived": 5,
                    "hitsGiven": 10,
                    "deaths": 1,
                    "kills": 5,
                },
            },
        ]
    })
};

export { mockPlayers }