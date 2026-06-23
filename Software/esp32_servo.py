import machine
import time
import sys

SERVO_PINS = [25, 14, 19, 33, 23]
PWM_FREQ   = 50      
DUTY_MIN   = 40        
DUTY_MAX   = 115       

servos = []
for pin_num in SERVO_PINS:
    pwm = machine.PWM(machine.Pin(pin_num), freq=PWM_FREQ)
    servos.append(pwm)

uart = machine.UART(0, baudrate=115200)


def angle_to_duty(angle):
    angle = max(0, min(180, angle))
    return int(DUTY_MIN + (angle / 180.0) * (DUTY_MAX - DUTY_MIN))


def set_servo(index, angle):
    servos[index].duty(angle_to_duty(angle))


def center_all():
    for i in range(len(servos)):
        set_servo(i, 90)


def smooth_move(targets, steps=5, delay_ms=10):
    current = [90] * 5  
    for step in range(1, steps + 1):
        for i in range(5):
            interp = int(current[i] + (targets[i] - current[i]) * step / steps)
            set_servo(i, interp)
        time.sleep_ms(delay_ms)



center_all()
print("ESP32 Bionic Arm ready. Waiting for packets…")


buf = b""

while True:
    if uart.any():
        buf += uart.read(uart.any())


        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            line = line.strip()

            if not line.startswith(b"A"):
                continue

            try:
                parts  = line[1:].decode().split(",")
                if len(parts) != 5:
                    continue
                angles = [int(p) for p in parts]

                # Safety clamp
                angles = [max(0, min(180, a)) for a in angles]

                for i, angle in enumerate(angles):
                    set_servo(i, angle)

            except (ValueError, UnicodeDecodeError):
                pass 

    time.sleep_ms(5)
