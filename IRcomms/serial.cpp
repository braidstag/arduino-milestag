#include <Arduino.h>
#include <HardwareSerial.h>
#include "IRComms.h"

#define serialWriteBufferSize 64
//the circle buffer
char serialWriteBuffer[serialWriteBufferSize];
//an offset from serialWriteBuffer ptr to the byte we next need to write in the circle buffer
byte writeOffset = 0;
//an offset from serialWriteBuffer ptr to the byte we next need to read from the circle buffer
byte readOffset = 0;

//a second buffer to temporarily format strings into.
char formatBuffer[serialWriteBufferSize];

/*
 * Takes a format string and arguments (as per sprintf) and buffers it to be sent over serial.
 * If the resulting string is bigger than the statically allocated buffer, it will be truncated.
 */
void serialQueue(const char * fmt, ...) {
  va_list ap;
  va_start(ap, fmt);

  int targetSize = vsnprintf(formatBuffer, serialWriteBufferSize, fmt, ap);
  if (targetSize > serialWriteBufferSize) {
    //wanted to write more than we could. Set the last non-null byte to 'X' to indicate this.
    formatBuffer[serialWriteBufferSize - 2] = 'X';
  }
  serialQueue_s(formatBuffer);

  va_end (ap);
}

void serialQueue_s(const char *str) {
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

void serialQueue_d(double d) {
  snprintf(formatBuffer, serialWriteBufferSize, "%.2f", d);
  serialQueue_s(formatBuffer);
}

void serialQueue_i(int i) {
  snprintf(formatBuffer, serialWriteBufferSize, "%d", i);
  serialQueue_s(formatBuffer);
}

void writeSerialChar() {
  if (writeOffset == readOffset) {
    //nothing to be read form the circle buffer (to be written to the serial line)
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
      serialQueue_s("c\n");
    }
    else if (numBytesRead == 1 && serialReadBuffer[0] == 'd') {
      clientConnected = false;
      serialQueue_s("d\n");
    }
    else if (numBytesRead > 5 && strncmp("Fire(", serialReadBuffer, 5) == 0) {
      //Fire
      byte teamId, playerId, dmg;
      int r = sscanf(serialReadBuffer, "Fire(%hhu,%hhu,%hhu)", &teamId, &playerId, &dmg);
      if (r == 3) {
        mt_fireShot(teamId, playerId, dmg);
      } else {
        //This message didn't parse
        //TODO: report this.
      }
    }
    else if (numBytesRead == 12 && strncmp("BatteryCheck", serialReadBuffer, 12) == 0) {
      checkBattery();
    }
    else if (numBytesRead == 8 && strncmp("Shutdown", serialReadBuffer, 8) == 0) {
      shutdown();
    }
    else if (numBytesRead == 4 && strncmp("Init", serialReadBuffer, 4) == 0) {
      //Start init mode.
      initModeActive=true;
    }
    else if (numBytesRead == 6 && strncmp("NoInit", serialReadBuffer, 6) == 0) {
      //Stop init mode.
      initModeActive=false;
      muzzleflash_down();
      torch_down();
    }
    else if (numBytesRead == 8 && strncmp("FireInit", serialReadBuffer, 8) == 0) {
      //Fire init shot.
      mt_fireInit();
    }
//some more for battery testing
    else if (numBytesRead == 4 && strncmp("test", serialReadBuffer, 4) == 0) {
      batterytestmode = 1;
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
