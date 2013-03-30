//#define DEBUG_DECODE 1
#define DEBUG_MAIN_LOOP 1

void decode_signal() {
#ifdef DEBUG_DECODE
  Serial.print("==");
  Serial.println(readBuffer, BIN);
  Serial.println(readBuffer, HEX);
#endif
}

//setting things ready
void setup() {
  //set the pins
  pinMode(pin_infrared, OUTPUT);
  pinMode(pin_ir_reciever, INPUT);
  pinMode(power_relay_pin, OUTPUT);
  pinMode(laser_pin, OUTPUT);
  pinMode(trigger_pin, INPUT);
  pinMode(altfire_pin, INPUT);
  pinMode(power_monitor_pin, INPUT);
  pinMode(muzzlered_pin, OUTPUT);
  pinMode(muzzlegreen_pin, OUTPUT);
  pinMode(muzzleblue_pin, OUTPUT);
  pinMode(torchred_pin, OUTPUT);
  pinMode(torchgreen_pin, OUTPUT);
  pinMode(torchblue_pin, OUTPUT);

  digitalWrite(power_relay_pin, HIGH);

  // see http://www.atmel.com/dyn/resources/prod_documents/doc8161.pdf for more details (page 136 onwards)
  //set the carrier wave frequency. This only sets up pin 9.
  TCCR1A = _BV(COM1A0); // | _BV(COM1B0); for another pin (10)
  TCCR1B = _BV(WGM12) | _BV(CS10);
  
  TIMSK1 = 0; //no interupts
  TIFR1 = _BV(OCF1A) | _BV(OCF1A); //clear Output Compare Match Flags (by setting them :-P )
  unsigned long desired_freq = 38000;
  OCR1A = 10000000/desired_freq - 1; // see page 126 of datasheet for this equation
  //OCR1B = 10000000/desired_freq - 1; for another pin (10)

  ir_down();

  //debug  
  Serial.begin(115200);
}

boolean clientConnected = false;
int preConnectedTeamId = 7; //our teamId - only used before a proper client connects.

void loop() {
#ifdef DEBUG_MAIN_LOOP
  timeDebug();
#endif
  checkTrigger();
  checkAltfire();
  signal_send();
  if (signal_recieve()) {
    decode_signal();
    mt_parseIRMessage(readBuffer);
    finished_signal_decode();
  }

  checkSerial();
  writeSerialChar();
#ifdef DEBUG_MAIN_LOOP
  timeDebug();
#endif
}

boolean oldTrigger = false;
long lastTriggerCheck = 0;

void checkTrigger() {
  //only check the trigger every millisecond as a crude de-bounce.
  if (micros() > lastTriggerCheck + 1000) {
    boolean trigger = digitalRead(trigger_pin);
    if (trigger && trigger != oldTrigger) {
      //if we are still debugging and the pi hasn't connected, just send a shot with fixed team/player/damage
      if (clientConnected) {
        serialQueue("T\n");
      }
      else {
        mt_fireShot();
      }

      oldTrigger = trigger;    
    }
    if (!trigger && trigger != oldTrigger) {
      if (clientConnected) {
        serialQueue("t\n");
      }

      oldTrigger = trigger;    
    }
    lastTriggerCheck = micros();
  }
}

void checkAltfire() {
  boolean altfire = digitalRead(altfire_pin);

  if (altfire) {
   	torch_up(preConnectedTeamId);
  } else {
    torch_down();
  }
}

void checkBattery() {
  serialQueue("B");
  serialQueue(analogRead(power_monitor_pin) * 5 / 1023.0);
  serialQueue("/n");
}

void shutdown() {
  delay(50000);
  digitalWrite(power_relay_pin, LOW);
}
