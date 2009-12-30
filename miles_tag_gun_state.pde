
byte TeamID;
byte PlayerID;

unsigned int Life; //[0,999]
byte Armor; //[0,200]

//Gun Characteristics
byte Gun_ClipSize; //[1,250], else UNL
byte Gun_Clips; //[2,200], else UNL

//Actual Status
byte Ammo; //[0,ClipSize]
unsigned int AmmoRemaining;

boolean FriendlyFire;
