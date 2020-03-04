import { mockPlayers } from './players.mock.js'

const mock = false;

async function getPlayersData() {
    if (mock) {
        return mockPlayers;
    }
    const response = await fetch(`http://localhost:${/*port || */8000}/players?fullInfo=true`);
    if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`Error getting players data: ${response.status}: ${errorBody}`);
    }
    return response;
}

export default { getPlayersData }