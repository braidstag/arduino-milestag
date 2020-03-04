import React from 'react';
import styled from 'styled-components';

const Container = styled.div`
    display: grid;
`;

const Logo = styled.img`
    height: 100px
    margin: auto 0 auto auto
`;

const TagLine = styled.span`
    margin: auto auto auto 0
    grid-column-start: 2
`;

function Header(props) {
    return <Container><Logo src='laserTriangle.jpg' /><TagLine>MeshTag</TagLine></Container>;
}

export default Header