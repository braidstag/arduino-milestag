
typedef struct shot {
  byte playerId;
  byte teamId;
  byte damage;
} shot;


typedef struct logicFunctions {
  //given the teamId and plaayerId, decide whether to consider processing the shot. return true if we should continue processing.
  boolean (*preRecieveShot)(byte, byte);
  
  //receive the shot
  void (*recieveShot)(shot *);
} logicFunctions;

