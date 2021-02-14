#ifndef IRCOMMS_H
#define IRCOMMS_H

#include <Arduino.h>

//TODO: split this properly into module headers

//////////////////
// functions used by multiple modules.
void ir_up();
void ir_down();
void muzzleflash_up(unsigned int flashteam);
void muzzleflash_down();
void torch_up(unsigned int flashteam);
void torch_down();
void timeDebug();
void finished_signal_decode();

void mt_fireShot();
void mt_fireShot(byte teamId, byte playerId, byte dmg);
void mt_fireInit();
void mt_parseIRMessage(unsigned long recvBuffer, int bitsRead);
void checkBattery();
void shutdown();

void screen_setup();
void screen_addScrollingData(const char newLine[]);

void serialQueue_s(const char *str);
void serialQueue_d(double d);
void serialQueue_i(int i);
void writeSerialChar();
void checkSerial();

int signal_recieve();
void start_command(unsigned long command, byte myTeamId);
void signal_send();

unsigned long addParityBit(unsigned long in);
bool isEvenParity(unsigned long buf);

//////////////////
//global variables
extern boolean serialRead;
extern boolean serialWritten;
extern boolean clientConnected;
extern int preConnectedTeamId;
extern boolean initModeActive;
extern int batterytestmode;
extern unsigned long readBuffer;
extern int bitsRead;

#endif // IRCOMMS_H
