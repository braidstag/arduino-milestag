#define altfire_pin 2
#define trigger_pin 3
#define torchred_pin 4
#define torchgreen_pin 5
#define torchblue_pin 6
#define laser_pin 7
#define pin_ir_reciever 8
#define pin_infrared 9
#define power_relay_pin 10
#define muzzlered_pin 11
#define muzzleblue_pin 12
#define muzzlegreen_pin 13
#define power_monitor_pin A0

// the setup function runs once when you press reset or power the board
void setup() {

    Serial.begin(115200);
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
}

// the loop function runs over and over again forever
void loop() {
  digitalWrite(muzzlered_pin, HIGH);              // turn the LED on
  Serial.print("Muzzle Red");
  delay(1000);                       // wait for a second
  digitalWrite(muzzlered_pin, LOW);
  delay(1000);                       // wait for a second

  digitalWrite(muzzlegreen_pin, HIGH);              // turn the LED on
  Serial.print("Muzzle Green");
  delay(1000);                       // wait for a second
  digitalWrite(muzzlegreen_pin, LOW);
  delay(1000);                       // wait for a second

  digitalWrite(muzzleblue_pin, HIGH);              // turn the LED on
  Serial.print("Muzzle blue");
  delay(1000);                       // wait for a second
  digitalWrite(muzzleblue_pin, LOW);
  delay(1000);                       // wait for a second
//Shoot board
  digitalWrite(torchred_pin, HIGH);              // turn the LED on
  Serial.print("Torch Red");
  delay(1000);                       // wait for a second
  digitalWrite(torchred_pin, LOW);
  delay(1000);                       // wait for a second

  digitalWrite(torchgreen_pin, HIGH);              // turn the LED on
  Serial.print("Torch Green");
  delay(1000);                       // wait for a second
  digitalWrite(torchgreen_pin, LOW);
  delay(1000);                       // wait for a second

  digitalWrite(torchblue_pin, HIGH);              // turn the LED on
  Serial.print("Torch blue");
  delay(1000);                       // wait for a second
  digitalWrite(torchblue_pin, LOW);
  delay(1000);                       // wait for a second


}
