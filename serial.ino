char serialBuffer[64];

void checkSerial() {
  if (Serial.available() > 0) {
    byte bytesRead = Serial.readBytesUntil('\n', serialBuffer, 64);

    if (bytesRead == 0) {
      //too little to be interesting
    }
    else if (bytesRead == 1) {
      //single character, probably a debugging command
      switch (serialBuffer[0]) {
        case 'f':
          mt_fireShot();
          break;
        case 'b':
          checkBattery();
          break;
        case 's':
          shutdown();
          break;
      }
    }
    else {
      if (strncmp("Fire", serialBuffer, 4) == 0) {
        //Fire
        byte teamId, playerId, dmg;
        sscanf(serialBuffer, "Fire(%hhd,%hhd,%hhd)", &teamId, &playerId, &dmg);
        mt_fireShot(teamId, playerId, dmg);
      }
      else if (strncmp("ClientConnect", serialBuffer, 13) == 0) {
        clientConnected = true;
      }
      else if (strncmp("BatteryCheck", serialBuffer, 12) == 0) {
        checkBattery();
      }
      else if (strncmp("Shutdown", serialBuffer, 8) == 0) {
        shutdown();
      }
    }
  }
}

