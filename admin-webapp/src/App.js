import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route } from 'react-router-dom'

import Admin from './components/Admin'
import Header from './components/Header'
import Navigation from './components/Navigation'
import Score from './components/Score'

import gameData from './data/game'
import playersData from './data/players'

const extractMessage = (error) => { return error.message; }

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(false);
  const [data, setData] = useState({});
  const [players, setPlayers] = useState([]);

  useEffect(() => {
    let isCancelled = false

    setIsLoading(true);

    gameData.getGameData()
    .then((response) => {
      if (!isCancelled) {
        return response.json()
      }
    })
    .then((newData) => {
      setData(newData);
      setError(null);
    })
    .then(() => playersData.getPlayersData())
    .then((response) => {
      if (!isCancelled) {
        return response.json()
      }
    })
    .then((playersData) => {
      setPlayers(playersData.players);
      setError(null);
      setIsLoading(false);
    })
    .catch((error) => {
      if (!isCancelled) {
        setError(error);
        setIsLoading(false);
      }
    });

    return () => {isCancelled = true};
  }, []);

  const saveGameTime = (newGameTime) => {
    gameData.patchGame({ gameTime: newGameTime })
    .then(() => {
      setData({...data, gameTime: newGameTime})
    });
  }

  const saveTargetTeamCount = (newTargetTeamCount) => {
    gameData.patchGame({ targetTeamCount: newTargetTeamCount })
    .then(() => {
      setData({...data, targetTeamCount: newTargetTeamCount})
    });
  }

  const startGame = () => {
    gameData.patchGame({ started: true })
    .then(() => {
      setData({...data, started: true})
    });
  }

  const stopGame = () => {
    gameData.patchGame({ started: false })
    .then(() => {
      setData({...data, started: false})
    });
  }

  const initialisePlayer = () => {
    playersData.initialisePlayer()
  }

  const body = (() => {
    if (isLoading) {
      return <div>Loading...</div>
    } else if (error) {
      return <div>{extractMessage(error)}</div>
    } else {
      return (
        <>
          <Route exact path="/" render={() => (
            <Admin
              game={data}
              saveGameTime={saveGameTime}
              saveTargetTeamCount={saveTargetTeamCount}
              startGame={startGame}
              stopGame={stopGame}
              initialisePlayer={initialisePlayer}
            />
          )} />
          <Route exact path="/score" render={() => (
            <Score
              players={players}
              teamPoints={data.teamPoints}
            />
          )} />
        </>
      );
    }
  })();

  return <Router><Header/><Navigation />{body}</Router>
}

export default App;
