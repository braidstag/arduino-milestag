//milestag protocol 1 documented at http://www.lasertagparts.com/mtformat.htm
//milestag protocol 2 documented at http://www.lasertagparts.com/mtformat-2.htm
// we currently only implement MT1 as MT2 seems incomplete.

#include <stdlib.h>
#include <stdarg.h>
#include <Arduino.h>
#include <HardwareSerial.h>
#include "miles_tag_defines.h"
#include "IRComms.h"

void mt_parseIRMessage(unsigned long recvBuffer, int bitsRead) {
    if (!isEvenParity(recvBuffer)) {
        serialQueue_s("C\n");
        return;
    }

    //trim the 17th bit (parity) off to make things neater
    recvBuffer = recvBuffer >> 1;

    byte recv_TeamID = (recvBuffer & MT1_TEAM_MASK) >> MT1_TEAM_OFFSET;
    byte DataByte2 = recvBuffer & 0xff;

    if (recv_TeamID == SYSTEM_MESSAGE) {
        byte recv_SystemMessage = (recvBuffer & SYSTEM_MESSAGE_MASK) >> SYSTEM_MESSAGE_SHIFT;

        switch (recv_SystemMessage) {
            case SYSTEM_MESSAGE_SET_TEAM_ID:
                serialQueue("Shot(SetTeam(%u))\n", DataByte2);
                break;
            case SYSTEM_MESSAGE_SET_PLAYER_ID:
                serialQueue("Shot(SetPlayer(%u))\n", DataByte2);
                break;
            case SYSTEM_MESSAGE_ADD_HEALTH:
                serialQueue("Shot(AddHealth(%u))\n", DataByte2);
                break;
            case SYSTEM_MESSAGE_ADD_CLIPS:
            {
                serialQueue("Shot(AddClips(%u))\n", DataByte2);
                break;
            }
            case SYSTEM_MESSAGE_GOD_GUN:
            {
                byte recv_GodGun = DataByte2;
                switch (recv_GodGun) {
                    case GOD_GUN_KILL_PLAYER:
                        serialQueue_s("Shot(Killed())\n");
                        break;
                    case GOD_GUN_FULL_AMMO:
                        serialQueue_s("FA\n");
                        break;
                    case GOD_GUN_RESPAWN_PLAYER:
                        serialQueue_s("Shot(ReSpawn())\n");
                        break;
                    case GOD_GUN_PAUSE_PLAYER:
                    case GOD_GUN_START_GAME:
                    case GOD_GUN_INIT_PLAYER:
                    case GOD_GUN_END_PLAYER:
                    default:
                        serialQueue_s("Shot(UnknownGGM)\n");
                        break;
                }

                break;
            }
            case SYSTEM_MESSAGE_ADD_ROUNDS:
                serialQueue("Shot(AddRounds(%u))\n", DataByte2);
                break;
            case SYSTEM_MESSAGE_EXTN_INIT:
                serialQueue_s("InitHit\n");
                break;
            case SYSTEM_MESSAGE_ADD_RPG_ROUNDS:
            case SYSTEM_MESSAGE_SCORE_DATA_HEADER:
            case SYSTEM_MESSAGE_SCORE_REQUEST:
            default:
                serialQueue("Shot(UnknownSM(%lu, %d))\n", recvBuffer, bitsRead);
                break;
        }
    } else {
        byte recv_PlayerID = (recvBuffer & MT1_PLAYER_MASK) >> MT1_PLAYER_OFFSET;
        signed char damage = 0;

        byte recv_PlayerWeaponHit = DataByte2;
        switch (recv_PlayerWeaponHit) {
            case 0:
            {
                damage = MT1_DAMAGE_RESURRECT_OPPONENT;
                break;
            }
            case 1 ... 100:
            {
                damage = recv_PlayerWeaponHit;
                break;
            }
            //No 'Base' Mode
            /*case 101 ... 200:
            {
                recv_PlayerWeaponHit -= 100;
                baseDamage = recv_PlayerWeaponHit;
            }
            case 255:
                baseDamage = MT1_DAMAGE_RESURRECT_ENEMY_BASE;
            */

            default:
                serialQueue_s("Shot(UnknownDmg)\n");
                break;
        }

        serialQueue("H%d,%d,%d\n", (int) recv_TeamID, (int) recv_PlayerID, (int) damage /*,(int) baseDamage*/);
    }
}


void mt_fireShot() {
  mt_fireShot(preConnectedTeamId, 1, 3);
}

void mt_fireShot(byte teamId, byte playerId, byte dmg) {
  unsigned long shot = (teamId << MT1_TEAM_OFFSET) | (playerId << MT1_PLAYER_OFFSET) | dmg;
  start_command(shot, teamId);
}

void mt_fireInit() {
    unsigned long shot = (SYSTEM_MESSAGE << MT1_TEAM_OFFSET) | (SYSTEM_MESSAGE_EXTN_INIT << SYSTEM_MESSAGE_SHIFT);
    start_command(shot, 7);
}
