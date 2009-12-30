
#include </home/afaucher/dev/mt/miles_tag_gun_state.pde>
#include </home/afaucher/dev/mt/miles_tag_defines.pde>
#include <util/parity.h>

void
mt_setup()
{
    TeamID = 0;
    PlayerID = 0;
    Life = 100;
    Armor = 100;
    
    Gun_ClipSize = 10;
    Gun_Clips = 255;
    
    
    Ammo = Gun_ClipSize;
    AmmoRemaining = Gun_Clips * Gun_ClipSize;
    
    FriendlyFire = false;
}

void
mt_parseIRMessage(unsigned long recvBuffer)
{
    if (!parity_even_bit(recvBuffer)) {
        Serial.println("Corrupt\n");
        return;
    }
    
    recvBuffer >> 1;
    
    byte recv_TeamID = (recvBuffer >> TEAM_SHIFT) & TEAM_MASK;
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
                break;
        }
    } else {
        byte recv_PlayerID = (recvBuffer >> PLAYER_SHIFT) & PLAYER_MASK;
        if (FriendlyFire && (TeamID == recv_TeamID)) {
            return;
        }
        
        byte recv_PlayerWeaponHit = DataByte2;
        switch (recv_PlayerWeaponHit) {
            case 0:
                Life = 100;
                break;
            case 1 ... 100:
            {
                if (Armor) {
                    byte ArmorDeflect = min(Armor,recv_PlayerWeaponHit);
                    Armor -= ArmorDeflect;
                    Life -= ArmorDeflect / 4;
                    recv_PlayerWeaponHit -= ArmorDeflect;
                }
                Life = max(0,recv_PlayerWeaponHit);
                break;
            }
            //No 'Base' Mode
            /*case 101 ... 200:
            {
                recv_PlayerWeaponHit -= 100;
            }*/
            default:
                Serial.println("Unknown Message");
                break;
        }
    }
}
