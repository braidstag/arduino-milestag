//A remote with an accelerometer for Sony IR protocol
//The sleep code is adapted from www.arduino.cc/playground/Learning/ArduinoSleepCode, (C) D. Cuartielles
//Other parts of this code are copyrighted by me. You can use this code freely, just  mention me in the
//copyright section.
//
//Original Copyright (C) Timo Herva aka 'mettapera', 2009
// hacked up by Andrew Shirley

//TODO: the protocol says LSB first, i.e. you can't just shift and add (you have to use (oldValue OR (1 shifted appropriately)).
//      use another CTC timer to tell when to set the ir up or down (not to be confused with the carrier frequency!)

//some pretty obvious pins
byte pin_infrared = 9; //don't chnage this one without changing the pwm freq setup!
byte pin_visible = 13;
byte pin_ir_reciever = 12;

//some sony timings
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
  byte pinValue = digitalRead(pin_ir_reciever);
  if (oldPinValue && !pinValue) {
    Serial.print("\\ @");
    Serial.println(micros());
    //IR rising edge (falling edge on this pin)
    readRiseTime = micros();
    oldPinValue = LOW;
  }
  else if (!oldPinValue && pinValue) {
    //IR falling edge (rising edge on this pin)
    unsigned long microsVal = micros();
    unsigned long duration = microsVal - readRiseTime;
    Serial.print("/ @");
    Serial.print(microsVal);
    Serial.print("  ");
    Serial.println(duration);

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
    if (within_tolerance(duration, zeroTime, timingTolerance)) {
      //we are within tollerance of 600 us - a zero
      readBuffer = readBuffer << 1;
      bitsRead++;
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
  Serial.println("  \\");
  writeDownTime = startTime;
}

void signal_send() {
  unsigned long elapsed = micros() - writeLastChangeTime;
  
  if (writeDownTime && writeDownTime < elapsed) {
    Serial.print("  /");
    Serial.print(elapsed);
    Serial.print(" - ");
    Serial.println(writeDownTime, DEC);
    ir_down();
    writeDownTime = 0;
    
    if (writeBits) {
      //not done yet
      writeUpTime = intervalTime;
    }
  }
  else if (writeUpTime && writeUpTime < elapsed) {
    Serial.print("  \\");
    Serial.print(elapsed);
    Serial.print(" - ");
    Serial.println(writeUpTime, DEC);
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
  analogWrite(pin_infrared, 255);
  digitalWrite(pin_visible, HIGH);
  writeLastChangeTime = micros();
}

void ir_down() {
  analogWrite(pin_infrared, 0);
  digitalWrite(pin_visible, LOW);
  writeLastChangeTime = micros();
}

////////////////////////
// general functions

//setting things ready  
void setup() {
  //set the pins
  pinMode(pin_infrared, OUTPUT);
  pinMode(pin_visible, OUTPUT);
  pinMode(pin_ir_reciever, INPUT);
  
  //set the carrier wave frequency. This only sets up pin 9 so don't change the pin_infrared config!
  TCCR1A = _BV(WGM01) | _BV(COM0A0); // | _BV(COM0B0); for another pin (10)
  TCCR1B = _BV(CS00);
  
  TIMSK1 = 0;
  TIFR1 = _BV(OCF1A);
  
  OCR1A = 13 - 1;
  //OCR1B = 13 - 1; for another pin (10)

  //debug  
  Serial.begin(9600); 
  Serial.println("jobbie - debug");
}


unsigned long time = micros();

void loop() {
  //command_decode(volume_up);
  //signal_send();
  
  if (micros() > time + 10000000) {
    time = micros();
    //Serial.print("starting ");
    //Serial.println(volume_up, BIN);
    start_command(volume_up);
  }
  signal_send();
  
//  signal_recieve();
  debug_signal();
}
/*
unsigned long cycletime = 4800;
unsigned long time2 = micros() + cycletime / 2;

void loop() {
  if (micros() > time + cycletime) {
    time = micros();
    ir_up();
    Serial.println("up");
  }
  if (micros() > time2 + cycletime) {
    time2 = micros();
    ir_down();
    Serial.println("down");
  }
}
*/













