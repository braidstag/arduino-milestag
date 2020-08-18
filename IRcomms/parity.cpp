#include <stdbool.h>

bool isEvenParity(unsigned long buf) {
  bool evenParityBit = false;
  for (unsigned int i = 0; i < sizeof(unsigned long) * 8; i++) {
    evenParityBit = evenParityBit ^ (buf & 1);
    buf = buf >> 1;
  }
  return !evenParityBit;
}

unsigned long addParityBit(unsigned long in) {
  if (!isEvenParity(in)) {
    return in | 0x00010000;
  }
  else {
    return in;
  }
}
