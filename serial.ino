char serialReadBuffer[64];
byte serialReadBufferOffset = 0;

void checkSerial() {
  int byteRead = Serial.read();
  
  if (byteRead == -1) {
    serialRead = false;
  }
  else {
    serialRead = true;
    
    serialReadBuffer[serialReadBufferOffset] = byteRead;
    serialReadBufferOffset++;
    
    if (serialReadBufferOffset >= 64) {
      serialReadBufferOffset = 0;
      //TODO: report that we have overrun our serial read buffer
    }
  }
  
  //if this is a \n, check the whole message
  if (byteRead == '\n') {
    byte numBytesRead = serialReadBufferOffset - 1; //we don't count the \n
    if (numBytesRead == 0) {
      //too little to be interesting
    }
//single character debugging commands
    else if (numBytesRead == 1 && serialReadBuffer[0] == 'f') {
      mt_fireShot();
    }
    else if (numBytesRead == 1 && serialReadBuffer[0] == 'b') {
      checkBattery();
    }
    else if (numBytesRead == 1 && serialReadBuffer[0] == 's') {
      shutdown();
    }
//commands from the real client
    else if (numBytesRead == 1 && serialReadBuffer[0] == 'c') {
      clientConnected = true;
      serialQueue("c\n");
    }
    else if (numBytesRead == 1 && serialReadBuffer[0] == 'd') {
      clientConnected = false;
      serialQueue("d\n");
    }
    else if (numBytesRead > 4 && strncmp("Fire", serialReadBuffer, 4) == 0) {
      //Fire
      byte teamId, playerId, dmg;
      sscanf(serialReadBuffer, "Fire(%hhd,%hhd,%hhd)", &teamId, &playerId, &dmg);
      mt_fireShot(teamId, playerId, dmg);
    }
    else if (numBytesRead > 12 && strncmp("BatteryCheck", serialReadBuffer, 12) == 0) {
      checkBattery();
    }
    else if (numBytesRead > 8 && strncmp("Shutdown", serialReadBuffer, 8) == 0) {
      shutdown();
    }
//temporary crap code for team select
    else if (numBytesRead > 3 && strncmp("red", serialReadBuffer, 3) == 0) {
      preConnectedTeamId = 1;
    }
    else if (numBytesRead > 5 && strncmp("green", serialReadBuffer, 5) == 0) {
      preConnectedTeamId = 2;
    }
    else if (numBytesRead > 4 && strncmp("blue", serialReadBuffer, 4) == 0) {
      preConnectedTeamId = 3;
    }
    else if (numBytesRead > 6 && strncmp("yellow", serialReadBuffer, 6) == 0) {
      preConnectedTeamId = 4;
    }
    else if (numBytesRead > 6 && strncmp("purple", serialReadBuffer, 6) == 0) {
      preConnectedTeamId = 5;
    }
    else if (numBytesRead > 4 && strncmp("cyan", serialReadBuffer, 4) == 0) {
      preConnectedTeamId = 6;
    }
    else if (numBytesRead > 5 && strncmp("white", serialReadBuffer, 5) == 0) {
      preConnectedTeamId = 7;
    }
    
    //reset the buffer
    serialReadBufferOffset = 0;
  }
}

#define serialWriteBufferSize 64
//the circle buffer
char serialWriteBuffer[serialWriteBufferSize];
//an offset from serialWriteBuffer ptr to the byte we next need to write in the circle buffer
byte writeOffset = 0;
//an offset from serialWriteBuffer ptr to the byte we next need to read from the circle buffer
byte readOffset = 0;

void serialQueue(const char *str) {
  //copy this byte-by-byte into the circle buffer
  int offset = 0;
  while (*(str + offset)) {
    if (writeOffset + 1 == readOffset || (writeOffset + 1 == serialWriteBufferSize && readOffset == 0)) {
      //we have already written as many bytes as we are allowed to write. 
      //As we are trying to write another byte, we have an issue. 
      //replace the previous byte with an "X" and abandon anything else in this queue request
      if (writeOffset == 0) {
        *(serialWriteBuffer + serialWriteBufferSize - 1) = 'X';
      }
      else {
        *(serialWriteBuffer + writeOffset - 1) = 'X';
      }

      return;
    }
    *(serialWriteBuffer + writeOffset) = *(str + offset);
    writeOffset++;
    if (writeOffset == serialWriteBufferSize) {
      //we have gone off the end of the buffer
      writeOffset = 0;
    }
    
    offset++;
  }
}

void serialQueue(double d) {
  char* out = (char*) malloc(32);
  snprintf(out, 32, "%.2f", d);
  serialQueue(out);
  free(out);
}

void serialQueue(int i) {
  char* out = (char*) malloc(11);
  snprintf(out, 11, "%d", i);
  serialQueue(out);
  free(out);
}

void writeSerialChar() {
  if (writeOffset == readOffset) {
    //nothng to be read form the circle buffer (to be written to the serial line)
    serialWritten = false;
    return;
  }

  Serial.print(*(serialWriteBuffer + readOffset));
  readOffset++;
  if (readOffset == serialWriteBufferSize) {
    //we have gone off the end of the buffer
    readOffset = 0;
  }
  serialWritten = true;
}
