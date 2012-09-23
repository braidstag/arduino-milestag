//milestag protocol 1 documented at http://www.lasertagparts.com/mtformat.htm
//milestag protocol 2 documented at http://www.lasertagparts.com/mtformat-2.htm
// we currently only implement MT1 as MT2 seems incomplete.

void serialPrint(int size, const char * fmt, ...) {
  char* out = (char*) malloc(size);
  va_list ap;
  va_start(ap, fmt);
  
  vsnprintf(out, size, fmt, ap);
  Serial.println(out);
  free(out);
  
  va_end (ap);
}

void mt_parseIRMessage(unsigned long recvBuffer) {
    if (!isEvenParity(recvBuffer)) {
        serialPrint(14, "Shot(Corrupt)");
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
                serialPrint(19, "Shot(SetTeam(%u))", DataByte2);
                break;
            case SYSTEM_MESSAGE_SET_PLAYER_ID:
                serialPrint(21, "Shot(SetPlayer(%u))", DataByte2);
                break;
            case SYSTEM_MESSAGE_ADD_HEALTH:
                serialPrint(21, "Shot(AddHealth(%u))", DataByte2);
                break;
            case SYSTEM_MESSAGE_ADD_CLIPS:
            {
                serialPrint(20, "Shot(AddClips(%u))", DataByte2);
                break;
            }
            case SYSTEM_MESSAGE_GOD_GUN:
            {
                byte recv_GodGun = DataByte2;
                switch (recv_GodGun) {
                    case GOD_GUN_KILL_PLAYER:
                        serialPrint(15, "Shot(Killed())");
                        break;
                    case GOD_GUN_FULL_AMMO:
                        serialPrint(17, "Shot(FullAmmo())");
                        break;
                    case GOD_GUN_RESPAWN_PLAYER:
                        serialPrint(15, "Shot(ReSpawn())");
                        break;
                    case GOD_GUN_PAUSE_PLAYER:
                    case GOD_GUN_START_GAME:
                    case GOD_GUN_INIT_PLAYER:
                    case GOD_GUN_END_PLAYER:
                    default:
                        serialPrint(17, "Shot(UnknownGGM)");
                        break;
                }
                
                break;
            }
            case SYSTEM_MESSAGE_ADD_ROUNDS:
                serialPrint(21, "Shot(AddRounds(%u))", DataByte2);
                break;
            case SYSTEM_MESSAGE_ADD_RPG_ROUNDS:
            case SYSTEM_MESSAGE_SCORE_DATA_HEADER:
            case SYSTEM_MESSAGE_SCORE_REQUEST:
            default:
                serialPrint(28, "Shot(UnknownSM(%lu))", recvBuffer);
                break;
        }
    } else {
        byte recv_PlayerID = (recvBuffer & MT1_PLAYER_MASK) >> MT1_PLAYER_OFFSET;
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
                serialPrint(17, "Shot(UnknownDmg)");
                break;
        }
        
        serialPrint(23, "Shot(Hit(%u,%u,%u))", recv_TeamID, recv_PlayerID, damage/*, baseDamage*/);
    }
}


void mt_fireShot() {
  mt_fireShot(1,1,3);
}

void mt_fireShot(byte teamId, byte playerId, byte dmg) {
  unsigned long shot = (teamId << MT1_TEAM_OFFSET) | (playerId << MT1_PLAYER_OFFSET) | dmg;
  start_command(shot);
}
