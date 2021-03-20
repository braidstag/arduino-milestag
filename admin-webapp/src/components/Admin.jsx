import React from 'react';
import MuiSlider from '@material-ui/core/Slider';
import styled from 'styled-components';

const Slider = styled.span`
    grid-column-start: 2;
    grid-column-end: 3;
    grid-row-start: auto;
    grid-row-end: auto;
`;

const Container = styled.div`
    display: grid
    grid-template-columns: auto auto;
    padding: 0 150px;
`;

function Admin(props) {

    const twoSF = (inp) => { if (inp < 10) { return `0${inp}`} else { return `${inp}`} };
    const renderTime = (seconds) => `${twoSF(Math.floor(seconds / 60))}:${twoSF(seconds % 60)}`;

    const startStopButton = props.game.started ?
    (<button onClick={(event) => props.stopGame()}>Stop Game</button>) :
    (<button onClick={(event) => props.startGame()}>Start Game</button>)

    return (
        <Container>
            <div>{startStopButton}</div>

            {/* TODO: disable this button when not applicable */}
            <div><button onClick={() => props.initialisePlayer()}>Initialise Player</button></div>

            <Slider>
                <span>game Time</span>
                <MuiSlider
                    aria-label="gameTime"
                    onChangeCommitted={(event, value) => props.saveGameTime(value)}
                    value={props.game.gameTime}
                    valueLabelFormat={renderTime}
                    valueLabelDisplay="on"
                    step={10}
                    marks
                    min={60}
                    max={1800}
                    style={{
                        paddingTop: "56px" //11 for the normal padding and 45 for the value balloon
                    }}
                />
            </Slider>

            <Slider>
            <span>No. of Teams</span>
                <MuiSlider
                    aria-label="targetTeamCount"
                    onChangeCommitted={(event, value) => props.saveTargetTeamCount(value)}
                    value={props.game.targetTeamCount}
                    valueLabelDisplay="on"
                    step={1}
                    marks
                    min={1}
                    max={8}
                    style={{
                        paddingTop: "56px" //11 for the normal padding and 45 for the value balloon
                    }}
                />
            </Slider>
        </Container>
    );
}

export default Admin;