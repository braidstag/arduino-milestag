const mockGame = { json: () => Promise.resolve({ "started": true, "gameEndTime": Date.now() + 19 * 60 * 1000, "targetTeamCount": 2, "gameTime": 20 * 60, "teamPoints": { "1": 2, "2": 5} })};

export { mockGame }