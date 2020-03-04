const mockGame = { json: () => Promise.resolve({ "started": true, "gameEndTime": Date.now() + 19 * 60 * 1000, "targetTeamCount": 2, "gameTime": 20 * 60 })};

export { mockGame }