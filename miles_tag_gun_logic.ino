//milestag protocol 1 documented at http://www.lasertagparts.com/mtformat.htm
//milestag protocol 2 documented at http://www.lasertagparts.com/mtformat-2.htm
// we currently only implement MT1 as MT2 seems incomplete.

#include "miles_tag_structs.h"

//Player characteristics
byte TeamID;
byte PlayerID;
unsigned int STARTING_LIFE = 100;
unsigned int STARTING_ARMOR = 100;

//player stats
unsigned int Life; //[0,999]
byte Armor; //[0,200]

//Gun Characteristics
byte Gun_ClipSize; //[1,250], else UNLIMITED_AMMO
byte Gun_Clips; //[2,200], else UNLIMITED_CLIPS

//Gun Status
byte Ammo; //[0,ClipSize]
unsigned int AmmoRemaining;

//Does friendly fire hurt.
boolean FriendlyFire;

//ignore the shot if friendlyfire is off and this is a shot from our team.
boolean defaultPreReceiveShot(byte teamId, byte playerId) {
  return FriendlyFire || (TeamID != teamId);
}

void defaultReceiveShot(struct shot *receivedShot) {
  if (receivedShot->damage == MT1_DAMAGE_RESURRECT_OPPONENT) {
    Life = max(Life, STARTING_LIFE);
    Armor = max(Armor, STARTING_ARMOR);
  }
  else {
    if (Armor) {
      byte ArmorDeflect = min(Armor, receivedShot->damage);
      Armor -= ArmorDeflect;
      Life -= ArmorDeflect / 4;
      receivedShot->damage -= ArmorDeflect;
    }
    Life = max(0, Life - receivedShot->damage);
    
    if (Life == 0) {
      Serial.println("DEAD!");
    }
  }
}

logicFunctions gameLogic = {&defaultPreReceiveShot, &defaultReceiveShot};



void
mt_setup()
{
    TeamID = 0;
    PlayerID = 0;
    Life = STARTING_LIFE;
    Armor = STARTING_ARMOR;
    
    Gun_ClipSize = 10;
    Gun_Clips = 255;
    
    Ammo = Gun_ClipSize;
    AmmoRemaining = Gun_Clips * Gun_ClipSize;
    
    FriendlyFire = false;
}

void
mt_parseIRMessage(unsigned long recvBuffer)
{
    if (!isEvenParity(recvBuffer)) {
        Serial.println("Corrupt\n");
        return;
    }
    
    //trim the 17th bit (parity) off to make things neater
    recvBuffer = recvBuffer >> 1;

    byte recv_TeamID = (recvBuffer & MT1_TEAM_MASK) >> MT1_TEAM_OFFSET;
    byte DataByte2 = recvBuffer & 0xff;
    
    if (recv_TeamID == SYSTEM_MESSAGE) {
        byte recv_SystemMessage = (recvBuffer >> SYSTEM_MESSAGE_SHIFT) & SYSTEM_MESSAGE_MASK;
        
        switch (recv_SystemMessage) {
            case SYSTEM_MESSAGE_SET_TEAM_ID:
                TeamID = DataByte2;
                break;
            case SYSTEM_MESSAGE_SET_PLAYER_ID:
                PlayerID = DataByte2;
                break;
            case SYSTEM_MESSAGE_ADD_HEALTH:
                Life += DataByte2;
                break;
            case SYSTEM_MESSAGE_ADD_CLIPS:
            {
                if (Gun_Clips == UNLIMITED_CLIPS) break;
                AmmoRemaining = min(Gun_Clips * Gun_ClipSize, AmmoRemaining + (DataByte2 * Gun_ClipSize));
                break;
            }
            case SYSTEM_MESSAGE_GOD_GUN:
            {
                byte recv_GodGun = DataByte2;
                switch (recv_GodGun) {
                    case GOD_GUN_KILL_PLAYER:
                        Life = 0;
                        break;
                    case GOD_GUN_FULL_AMMO:
                        Ammo = Gun_ClipSize;
                        AmmoRemaining = Gun_Clips * Gun_ClipSize;
                        break;
                    case GOD_GUN_RESPAWN_PLAYER:
                        Life = 100;
                        break;
                    case GOD_GUN_PAUSE_PLAYER:
                    case GOD_GUN_START_GAME:
                    case GOD_GUN_INIT_PLAYER:
                    case GOD_GUN_END_PLAYER:
                    default:
                        Serial.println("Unknown GGM");
                        break;
                }
                
                break;
            }
            case SYSTEM_MESSAGE_ADD_ROUNDS:
                AmmoRemaining = min(Gun_Clips * Gun_ClipSize, AmmoRemaining + DataByte2);
                break;
            case SYSTEM_MESSAGE_ADD_RPG_ROUNDS:
            case SYSTEM_MESSAGE_SCORE_DATA_HEADER:
            case SYSTEM_MESSAGE_SCORE_REQUEST:
            default:
                Serial.println("Unknown SM");
                Serial.println(recvBuffer, HEX);
                break;
        }
    } else {
        byte recv_PlayerID = recvBuffer & MT1_PLAYER_MASK;

        if (!gameLogic.preRecieveShot(recv_TeamID, recv_PlayerID)) {
          Serial.println("ignoring shot");
          return;
        }

        signed char damage;
        
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
                Serial.println("Unknown Message");
                break;
        }
        
        shot currShot = {recv_PlayerID, recv_TeamID, damage/*, baseDamage*/};
        
        gameLogic.recieveShot(&currShot);
    }
}

