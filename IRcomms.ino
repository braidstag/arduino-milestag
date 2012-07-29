//The IR communication components.
//
// Hacked together by Andrew Shirley

// Code which was either 'copypasta'ed or used as inspiration at some point:
//
// http://www.arduino.cc/cgi-bin/yabb2/YaBB.pl?num=1240843250 Copyright (C) Timo Herva aka 'mettapera', 2009
// http://tthheessiiss.wordpress.com/2009/08/05/dirt-cheap-wireless/ 

// TODO: the protocol says LSB first, i.e. you can't just shift and add (you have to use (oldValue shifted appropriately AND 1)).
//      use another CTC timer to tell when to set the ir up or down (not to be confused with the carrier frequency!)

//NB. as these are quite time sensitive enableing this often breaks it :-(
//#define DEBUG_SEND 1
//#define DEBUG_RECV 1


// pin numbers (9 is used for a Carrier wave and so isn't available)
byte pin_infrared = 8;
byte pin_ir_feedback = 13;
byte pin_ir_reciever = 12;
//byte pin_ir_reciever_port = PORTB;
byte pin_ir_reciever_bit = 0;

// some timings
long headerDuration = 2400;
long intervalDuration = 600;
long oneDuration = 1200;
long zeroDuration = 600;

byte timingTolerance = 100;

////////////////////////
// IR Writing variables
//byte volume_up = 0x24;//B0100100
unsigned long  simple_shot = 0x3101;

unsigned long writeBuffer = 0;
byte writeBits = 0;
unsigned long writeUpTime = 0;
unsigned long writeDownTime = 0;
unsigned long writeLastChangeTime = 0;

////////////////////////
// IR reading variables
unsigned long readBuffer = 0;
byte bitsRead = 0;

byte oldPinValue = 0;

//the micros for the point at which the IR went high
unsigned long readRiseTime = 0;

//the micros for the point at which the IR went low
unsigned long readFallTime = 0;

////////////////////////
// IR reading functions

//read the IR receiver and if applicable add to the readBuffer. This will return 1 if the transmission appears to be complete. Subsequent reads will return 0.
int signal_recieve() {
  byte pinValue = bitRead(PORTB, pin_ir_reciever_bit);
  if (!oldPinValue && pinValue) {
    //IR rising edge
    //TODO: should we check that we have been low for an appropriate amount of time?
    readRiseTime = micros();
    oldPinValue = HIGH;
#ifdef DEBUG_RECV
    Serial.print("\\ @");
    Serial.println(readRiseTime);
#endif
    //there is always more to be read if the IR is high.
    return 0;
  }
  else if (oldPinValue && !pinValue) {
    //IR falling edge
    readFallTime = micros();
    unsigned long duration = readFallTime - readRiseTime;

    if (within_tolerance(duration, headerDuration, timingTolerance)) {
      //we are within tolerance of 2400 us - a restart
      readBuffer = 0;
      bitsRead = 0;
    }
    else if (within_tolerance(duration, oneDuration, timingTolerance)) {
      //we are within tolerance of 1200 us - a one
      readBuffer = (readBuffer << 1) + 1;
      bitsRead++;
    }
    else if (within_tolerance(duration, zeroDuration, timingTolerance)) {
      //we are within tolerance of 600 us - a zero
      readBuffer = readBuffer << 1;
      bitsRead++;
    }
    else {
#ifdef DEBUG_RECV
      Serial.print("/ @");
      Serial.print(readFallTime);
      Serial.print("  ");
      Serial.println(duration);
#endif
    }

    oldPinValue = LOW;
    //wait to see if there is more to be read
    return 0;
  }
  else if (oldPinValue) {
    //IR continues to be high
    //there is always more to be read if the IR is high.
    return 0;
  }
  else /*if (!oldPinValue)*/ {
    //IR continues to be low
    //if we have been low for more than interval + tolerance (twice for extra leniency) we can assume the transmission has finished and try to read it.
    if (!readFallTime) {
      //we aren't waiting for an interval, all quiet on the IR front.
      return 0;
    }
    else if (micros() - readFallTime > intervalDuration + timingTolerance * 2) {
      readFallTime = 0; //cache this result
      return 1;
    }
    else {
      //still low, waiting for the interval
      return 0;
    }
  }
}

boolean within_tolerance(unsigned long value, unsigned long target, byte tolerance) {
  long remainder = value - target;
  return remainder < tolerance && remainder > -tolerance;
}

////////////////////////
// IR writing functions

void start_command(unsigned long command) {
  if (writeUpTime || writeDownTime) {
    //already writing - this is an error
    //Serial.println("tried to start a command when we are already sending");
    return;
  }
#ifdef DEBUG_SEND
  Serial.print("sending ");
  Serial.println(command, BIN);
#endif

  writeBuffer = reverse(command, 16);
  writeBits = 16;
  
  //write header
  ir_up();
#ifdef DEBUG_SEND
  Serial.println("  \\");
#endif
  writeDownTime = headerDuration;
}

void signal_send() {
  unsigned long elapsed = micros() - writeLastChangeTime;
  
  if (writeDownTime && writeDownTime <= elapsed) {
#ifdef DEBUG_SEND
    Serial.print("  /");
    Serial.print(elapsed);
    Serial.print(" - ");
    Serial.println(writeDownTime, DEC);
#endif
    ir_down();
    writeDownTime = 0;
    
    if (writeBits) {
      //not done yet
      writeUpTime = intervalDuration;
    }
  }
  else if (writeUpTime && writeUpTime <= elapsed) {
#ifdef DEBUG_SEND
    Serial.print("  \\");
    Serial.print(elapsed);
    Serial.print(" - ");
    Serial.println(writeUpTime, DEC);
#endif
    ir_up();
    writeUpTime = 0;
    
    if (writeBuffer & B1) {
      //write a one
      writeDownTime = oneDuration;
    }
    else {
      //write a zero
      writeDownTime = zeroDuration;
    }
    
    writeBuffer = writeBuffer >> 1;
    writeBits--;
  }
}

void ir_up() {
  digitalWrite(pin_infrared, HIGH);
  digitalWrite(pin_ir_feedback, HIGH);
  writeLastChangeTime = micros();
}

void ir_down() {
  digitalWrite(pin_infrared, LOW);
  digitalWrite(pin_ir_feedback, LOW);
  writeLastChangeTime = micros();
}

/*
 * Reverse the num least significant bits.
 */
unsigned long reverse(unsigned long in, int num) {
  unsigned long out = 0;
  for (int i = 0; i < num; i++) {
    out = out << 1;
    out = out | (in & 1); //take the lsb from in to out
    in = in >> 1;
  }
  
  return out;
}
