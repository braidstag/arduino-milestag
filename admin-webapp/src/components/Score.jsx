import React from 'react';
import styled from 'styled-components';

const ListContainer = styled.div`
    display: grid;
    grid-template-columns: auto;
`;

const SideBySideContainer = styled.div`
    display: grid;
    grid-template-columns: auto auto;
`;

const TeamHeader = styled.div`
    grid-column-start: span 1;
    background: grey;
`;

const PlayerContainer = styled.div`
    grid-column-start: span 1;
`;

const braidArrays = (arrays, undefinedMapping = () => undefined) => {
    const braided = [];
    for (let i = 0; i < Math.max(...arrays.map(a => a.length)); i++) {
        arrays.forEach((array, j) => {
            if (array[i] === undefined) {
                if (undefinedMapping) {
                    braided.push(undefinedMapping(i, j));
                }
            } else {
                braided.push(array[i]);
            }
        });
    }
    return braided;
};

/**
 * Convert a typical player map {teamId: { playerId: playerObj}} to a flattened array.
 * The array will be of players, one from each team then another from each team, undefined will be used for teams with missing players.
 */
const playersToBraidedArray = (players) =>
    braidArrays(Object.values(players), (i, j) => ({playerId: i+1, teamId: j+1}))

function Score(props) {
    const playersByTeam = {}
    props.players.forEach(p => {if (!playersByTeam[p.teamId]) {playersByTeam[p.teamId] = []}; playersByTeam[p.teamId].push(p)})
    Object.values(playersByTeam).forEach(pl => {pl.sort((a, b) => a.playerId > b.playerId)})

    if (Object.keys(playersByTeam).length === 2) {
        //2 teams, show side-by side
        const braidedPlayers = playersToBraidedArray(playersByTeam)

        //team Headers
        const teamsMarkup = Object.keys(playersByTeam).map(teamId => {
            return <TeamHeader key={teamId}>{teamId} - {props.teamPoints[teamId] || 0}</TeamHeader>;
        })

        //player details
        const playersMarkup = braidedPlayers.map(p => {
            const key = `${p.teamId}:${p.playerId}`;
            return p.health !== undefined ? <PlayerContainer key={key}>{p.playerId}. Score: {p.stats.kills} Health: {p.health}/{p.parameters['player.maxHealth'].currentValue}</PlayerContainer> : <PlayerContainer key={key}/>
        })

        return <SideBySideContainer>{teamsMarkup}{playersMarkup}</SideBySideContainer>;
    } else {
        //not 2 teams, show in a list

        const teamsMarkup = Object.keys(playersByTeam).map(teamId => {
            const playersMarkup = playersByTeam[teamId].map(p =>
                <PlayerContainer key={`${p.teamId}:${p.playerId}`}>{p.playerId}. Score: {p.stats.kills} Health: {p.health}/{p.parameters['player.maxHealth'].currentValue}</PlayerContainer>
            )
            return <React.Fragment key={teamId}><TeamHeader>{teamId} - {props.teamPoints[teamId] || 0}</TeamHeader>{playersMarkup}</React.Fragment>;
        })
        return <ListContainer>{teamsMarkup}</ListContainer>;
    }


}

export default Score