import React from 'react';
import styled from 'styled-components';
import { NavLink } from 'react-router-dom'

const Container = styled.div`
    display: grid;
    grid-template-columns: 9em 9em;
    justify-content: center;
`;

const Page = styled(NavLink)`
    margin: 0px 5px;
    padding: 0 1em;

    border-radius: 20px 20px 0 0;
    border: solid black 1px;

    text-align: center;
`;

function Navigation(props) {
    return <Container><Page to='/'>Game Admin</Page><Page to='/score'>Scores</Page></Container>;
}

export default Navigation