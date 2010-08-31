
typedef struct shot {
  byte playerId;
  byte teamId;
  byte damage;
} shot;


typedef struct logicFunctions {
  void (*recieveShot)(shot *);
  int foo;
} logicFunctions;

