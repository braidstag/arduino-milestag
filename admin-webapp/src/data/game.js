import { mockGame } from './game.mock.js'

const mock = false;

async function getGameData() {
    if (mock) {
        return mockGame
    }
    const response = await fetch(`/game`);
    if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`Error getting game data: ${response.status}: ${errorBody}`);
    }
    return response;
}

async function patchGame (bodyData) {
  const response = await fetch(`/game`, {
        method: 'PATCH',
        body: JSON.stringify(bodyData),
        mode: 'cors',
        headers: {
            'Content-Type': 'application/json',
        },
        redirect: 'follow',
    });
    if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`Error setting gameTime: ${response.status}: ${errorBody}`);
    }
}


export default { getGameData, patchGame }