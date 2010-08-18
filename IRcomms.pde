//The IR communication components.
//
// Hacked together by Andrew Shirley

// Code which was either 'copypasta'ed or used as inspiration at some point:
//
// http://www.arduino.cc/cgi-bin/yabb2/YaBB.pl?num=1240843250 Copyright (C) Timo Herva aka 'mettapera', 2009
// http://tthheessiiss.wordpress.com/2009/08/05/dirt-cheap-wireless/ 

// TODO: the protocol says LSB first, i.e. you can't just shift and add (you have to use (oldValue OR (1 shifted appropriately)).
//      use another CTC timer to tell when to set the ir up or down (not to be confused with the carrier frequency!)

#define DEBUG_SEND 1

#undef DEBUG_RECV


// pin numbers
byte pin_infrared = 8;
byte pin_visible = 13;
byte pin_ir_reciever = 12;
//byte pin_ir_reciever_port = PORTB;
byte pin_ir_reciever_bit = 0;

// some timings
long startTime = 2400;
long intervalTime = 600;
long oneTime = 1200;
long zeroTime = 600;

byte timingTolerance = 200;

////////////////////////
// IR Writing variables
//byte volume_up = 0x24;//B0100100
byte volume_up = B0001100;

byte writeBuffer = 0;
byte writeBits = 0;
unsigned long writeUpTime = 0;
unsigned long writeDownTime = 0;
unsigned long writeLastChangeTime = 0;

////////////////////////
// IR reading variables
byte readBuffer = 0;
byte bitsRead = 0;
byte oldBitsRead = 0;

byte oldPinValue = 1;

//the micros for the point at which the IR went high (the pin went low)
unsigned long readRiseTime;


////////////////////////
// IR reading functions
void signal_recieve() {
  byte pinValue = bitRead(PORTB, pin_ir_reciever_bit);
  if (oldPinValue && !pinValue) {
#ifdef DEBUG_RECV
    Serial.print("\\ @");
    Serial.println(micros());
#endif
    //IR rising edge (falling edge on this pin)
    readRiseTime = micros();
    oldPinValue = LOW;
  }
  else if (!oldPinValue && pinValue) {
    //IR falling edge (rising edge on this pin)
    unsigned long microsVal = micros();
    unsigned long duration = microsVal - readRiseTime;

    if (within_tolerance(duration, startTime, timingTolerance)) {
      //we are within tollerance of 2400 us - a restart
      readBuffer = 0;
      bitsRead = 0;
    }
    else if (within_tolerance(duration, oneTime, timingTolerance)) {
      //we are within tollerance of 1200 us - a one
      readBuffer = (readBuffer << 1) + 1;
      bitsRead++;
    }
    else if (within_tolerance(duration, zeroTime, timingTolerance)) {
      //we are within tollerance of 600 us - a zero
      readBuffer = readBuffer << 1;
      bitsRead++;
    }
    else {
#ifdef DEBUG_RECV
      Serial.print("/ @");
      Serial.print(microsVal);
      Serial.print("  ");
      Serial.println(duration);
#endif
    }

    oldPinValue = HIGH;
  }
}

boolean within_tolerance(unsigned long value, unsigned long target, byte tolerance) {
  long remainder = value - target;
  return remainder < tolerance && remainder > -tolerance;
}

void debug_signal() {
  if (bitsRead != oldBitsRead) {
    if (bitsRead == 0) {
      Serial.println("====");
    }
    
    oldBitsRead = bitsRead;
    Serial.print("==");
    Serial.println(readBuffer, BIN);
  }
}

////////////////////////
// IR writing functions

void start_command(byte command) {
  if (writeUpTime || writeDownTime) {
    //already writing - this is an error
    Serial.println("tried to start a command when we are already sending");
    return;
  }
  
  writeBuffer = command;
  writeBits = 8;
  
  //write header
  ir_up();
#ifdef DEBUG_SEND
  Serial.println("  \\");
#endif
  writeDownTime = startTime;
}

void signal_send() {
  unsigned long elapsed = micros() - writeLastChangeTime;
  
  if (writeDownTime && writeDownTime < elapsed) {
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
      writeUpTime = intervalTime;
    }
  }
  else if (writeUpTime && writeUpTime < elapsed) {
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
      writeDownTime = oneTime;
    }
    else {
      //write a zero
      writeDownTime = zeroTime;
    }
    
    writeBuffer = writeBuffer >> 1;
    writeBits --;
  }
}

void ir_up() {
  digitalWrite(pin_infrared, HIGH);
  digitalWrite(pin_visible, HIGH);
  writeLastChangeTime = micros();
}

void ir_down() {
  digitalWrite(pin_infrared, LOW);
  digitalWrite(pin_visible, LOW);
  writeLastChangeTime = micros();
}

////////////////////////
// general functions

//setting things ready  
void setup() {
  //set the pins
  pinMode(pin_infrared, OUTPUT);
  pinMode(9, OUTPUT);
  pinMode(pin_visible, OUTPUT);
  pinMode(pin_ir_reciever, INPUT);
  
  // see http://www.atmel.com/dyn/resources/prod_documents/doc8161.pdf for more details (page 136 onwards)
  //set the carrier wave frequency. This only sets up pin 9.
  TCCR1A = _BV(COM1A0); // | _BV(COM1B0); for another pin (10)
  TCCR1B = _BV(WGM12) | _BV(CS10);
  
  TIMSK1 = 0; //no interupts
  TIFR1 = _BV(OCF1A) | _BV(OCF1A); //clear Output Compare Match Flags (by setting them :-P )
  unsigned long desired_freq = 40000;
  OCR1A = 10000000/desired_freq - 1; // see page 126 of datasheet for this equation
  //OCR1B = 10000000/desired_freq - 1; for another pin (10)

  ir_down();

  //debug  
  Serial.begin(9600); 
  Serial.println("jobbie - debug");
}


unsigned long time = micros();

void loop() {
  //command_decode(volume_up);
  //signal_send();
  
  if (micros() > time + 1000000) {
    time = micros();
    //Serial.print("starting ");
    //Serial.println(volume_up, BIN);
    start_command(volume_up);
  }
  signal_send();
  
  signal_recieve();
  debug_signal();
}
