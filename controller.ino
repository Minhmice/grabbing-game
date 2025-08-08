const int player1_joy_x_pin = A0;
const int player1_joy_y_pin = A1;
const int player1_joy_rotate_pin = A2;
const int player1_ready_btn_pin = 2;
const int player1_grab_btn_pin = 4;

const int player2_joy_x_pin = A3;
const int player2_joy_y_pin = A4;
const int player2_joy_rotate_pin = A5;
const int player2_ready_btn_pin = 3;
const int player2_grab_btn_pin = 5;

bool player1_ready_state = false;
bool player1_grab_state = false;
bool player2_ready_state = false;
bool player2_grab_state = false;

unsigned long last_send_time = 0;
const int send_interval = 20;

void setup() {
  Serial.begin(115200);

  pinMode(player1_ready_btn_pin, INPUT_PULLUP);
  pinMode(player1_grab_btn_pin, INPUT_PULLUP);
  pinMode(player2_ready_btn_pin, INPUT_PULLUP);
  pinMode(player2_grab_btn_pin, INPUT_PULLUP);
}

void loop() {
  if (millis() - last_send_time >= send_interval) {
    last_send_time = millis();

    int player1_joy_x = analogRead(player1_joy_x_pin);
    int player1_joy_y = analogRead(player1_joy_y_pin);
    int player1_joy_rotate = analogRead(player1_joy_rotate_pin);

    int player2_joy_x = analogRead(player2_joy_x_pin);
    int player2_joy_y = analogRead(player2_joy_y_pin);
    int player2_joy_rotate = analogRead(player2_joy_rotate_pin);

    player1_ready_state = !digitalRead(player1_ready_btn_pin);
    player1_grab_state = !digitalRead(player1_grab_btn_pin);
    player2_ready_state = !digitalRead(player2_ready_btn_pin);
    player2_grab_state = !digitalRead(player2_grab_btn_pin);

    Serial.print(player1_joy_x);
    Serial.print(",");
    Serial.print(player1_joy_y);
    Serial.print(",");
    Serial.print(player1_joy_rotate);
    Serial.print(",");
    
    Serial.print(player2_joy_x);
    Serial.print(",");
    Serial.print(player2_joy_y);
    Serial.print(",");
    Serial.print(player2_joy_rotate);
    Serial.print(",");
    
    Serial.print(player1_ready_state);
    Serial.print(",");
    Serial.print(player1_grab_state);
    Serial.print(",");
    Serial.print(player2_ready_state);
    Serial.print(",");
    Serial.println(player2_grab_state);
  }
}