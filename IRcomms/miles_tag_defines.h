
#define SYSTEM_MESSAGE                      B000

#define SYSTEM_MESSAGE_MASK                 0x1f00 // i.e. 5 least significant bits of the most significant byte
#define SYSTEM_MESSAGE_SHIFT                8

#define SYSTEM_MESSAGE_ADD_HEALTH           B00001
#define SYSTEM_MESSAGE_ADD_ROUNDS           B00010
#define SYSTEM_MESSAGE_ADD_CLIPS            B00011
#define SYSTEM_MESSAGE_ADD_RPG_ROUNDS       B00100

#define SYSTEM_MESSAGE_EXTN_INIT            B00101 //An extension to the spec, sent by a gun initialising to confirm it works / has been acknowledged

#define SYSTEM_MESSAGE_GOD_GUN              B01001

#define SYSTEM_MESSAGE_SCORE_DATA_HEADER    B10000
#define SYSTEM_MESSAGE_SCORE_REQUEST        B10001

#define SYSTEM_MESSAGE_SET_TEAM_ID          B10110
#define SYSTEM_MESSAGE_SET_PLAYER_ID        B10111

#define GOD_GUN_KILL_PLAYER                 0x00
#define GOD_GUN_PAUSE_PLAYER                0x01

#define GOD_GUN_START_GAME                  0x03
#define GOD_GUN_RESPAWN_PLAYER              0x04
#define GOD_GUN_INIT_PLAYER                 0x05
#define GOD_GUN_FULL_AMMO                   0x06
#define GOD_GUN_END_PLAYER                  0x07

#define UNLIMITED_CLIPS                     255
#define UNLIMITED_AMMO                      255


#define MT1_TEAM_MASK                       0xe000 // i.e. 3 most significant bits
#define MT1_TEAM_OFFSET                     13 // i.e. 3 most significant bits
#define MT1_PLAYER_MASK                     0x1f00 // i.e. 5 least significant bits of the most significant byte
#define MT1_PLAYER_OFFSET                   8 // i.e. 5 least significant bits of the most significant byte

#define MT1_DAMAGE_RESURRECT_OPPONENT       -1


