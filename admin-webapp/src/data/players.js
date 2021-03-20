import { mockPlayers } from './players.mock.js'

const mock = false;

async function getPlayersData() {
    if (mock) {
        return mockPlayers;
    }
    const response = await fetch(`/players?fullInfo=true`);
    if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`Error getting players data: ${response.status}: ${errorBody}`);
    }
    return response;
}

async function initialisePlayer() {
    if (mock) {
        return
    }
    await fetch('/players:startInitialising', {
        method: 'POST',
    })
}

export default { getPlayersData, initialisePlayer }