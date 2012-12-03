char serialBuffer[64];

void checkSerial() {
  if (Serial.available() > 0) {
    byte bytesRead = Serial.readBytesUntil('\n', serialBuffer, 64);

    if (bytesRead == 0) {
      //too little to be interesting
    }
//single character debugging commands
    else if (bytesRead == 1 && serialBuffer[0] == 'f') {
      mt_fireShot();
    }
    else if (bytesRead == 1 && serialBuffer[0] == 'b') {
      checkBattery();
    }
    else if (bytesRead == 1 && serialBuffer[0] == 's') {
      shutdown();
    }
//commands from the real client
    else if (bytesRead > 4 && strncmp("Fire", serialBuffer, 4) == 0) {
      //Fire
      byte teamId, playerId, dmg;
      sscanf(serialBuffer, "Fire(%hhd,%hhd,%hhd)", &teamId, &playerId, &dmg);
      mt_fireShot(teamId, playerId, dmg);
    }
    else if (bytesRead > 13 && strncmp("ClientConnect", serialBuffer, 13) == 0) {
      clientConnected = true;
      Serial.println("c");
    }
    else if (bytesRead > 16 && strncmp("ClientDisconnect", serialBuffer, 16) == 0) {
      clientConnected = false;
      Serial.println("d");
    }
    else if (bytesRead > 12 && strncmp("BatteryCheck", serialBuffer, 12) == 0) {
      checkBattery();
    }
    else if (bytesRead > 8 && strncmp("Shutdown", serialBuffer, 8) == 0) {
      shutdown();
    }
//temporary crap code for team select
    else if (bytesRead > 3 && strncmp("red", serialBuffer, 3) == 0) {
      preConnectedTeamId = 1;
    }
    else if (bytesRead > 5 && strncmp("green", serialBuffer, 5) == 0) {
      preConnectedTeamId = 2;
    }
    else if (bytesRead > 4 && strncmp("blue", serialBuffer, 4) == 0) {
      preConnectedTeamId = 3;
    }
    else if (bytesRead > 6 && strncmp("yellow", serialBuffer, 6) == 0) {
      preConnectedTeamId = 4;
    }
    else if (bytesRead > 6 && strncmp("purple", serialBuffer, 6) == 0) {
      preConnectedTeamId = 5;
    }
    else if (bytesRead > 4 && strncmp("cyan", serialBuffer, 4) == 0) {
      preConnectedTeamId = 6;
    }
    else if (bytesRead > 5 && strncmp("white", serialBuffer, 5) == 0) {
      preConnectedTeamId = 7;
    }
  }
}

