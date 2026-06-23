"""
esp32_servo.py  –  ESP32 side (MicroPython)
Reads angle packets from the PC over UART/USB and moves 5 servos.

Pin mapping from schematic (Image 2):
    M1 (Thumb)   → GPIO 25
    M2 (Index)   → GPIO 14
    M3 (Middle)  → GPIO 19
    M4 (Ring)    → GPIO 33
    M5 (Pinky)   → GPIO 23

Flash MicroPython onto your ESP32, then upload this file as main.py.
The built-in machine.PWM handles servo control – no extra library needed.

Packet format expected from PC:
    A<thumb>,<index>,<middle>,<ring>,<pinky>\n
    Example: A90,45,120,60,180\n
"""

import machine
import time
import sys

# ── Pin assignments (from schematic) ─────────────────────────────────────────
SERVO_PINS = [25, 14, 19, 33, 23]   # Thumb, Index, Middle, Ring, Pinky

# ── Servo PWM constants ───────────────────────────────────────────────────────
PWM_FREQ   = 50        # 50 Hz standard for servos
DUTY_MIN   = 40        # ~0.5 ms pulse  → 0°   (out of 1023)
DUTY_MAX   = 115       # ~2.5 ms pulse  → 180° (out of 1023)
# Fine-tune these per your servo if endpoints feel off.
# Duty = (pulse_ms / 20ms) * 1023
# 0.5ms → 40, 1.5ms → 77, 2.5ms → 115  (approx)

# ── Setup ────────────────────────────────────────────────────────────────────
servos = []
for pin_num in SERVO_PINS:
    pwm = machine.PWM(machine.Pin(pin_num), freq=PWM_FREQ)
    servos.append(pwm)

uart = machine.UART(0, baudrate=115200)   # UART0 = USB serial on most boards


def angle_to_duty(angle):
    """Map 0-180° to PWM duty cycle (0-1023 scale used by MicroPython)."""
    angle = max(0, min(180, angle))
    return int(DUTY_MIN + (angle / 180.0) * (DUTY_MAX - DUTY_MIN))


def set_servo(index, angle):
    servos[index].duty(angle_to_duty(angle))


def center_all():
    for i in range(len(servos)):
        set_servo(i, 90)


def smooth_move(targets, steps=5, delay_ms=10):
    """
    Optionally smooth movement over several intermediate steps.
    targets: list of 5 angles
    """
    current = [90] * 5    # assume last known; for true smoothing keep state
    for step in range(1, steps + 1):
        for i in range(5):
            interp = int(current[i] + (targets[i] - current[i]) * step / steps)
            set_servo(i, interp)
        time.sleep_ms(delay_ms)


# ── Boot: center all servos ───────────────────────────────────────────────────
center_all()
print("ESP32 Bionic Arm ready. Waiting for packets…")

# ── Main loop ────────────────────────────────────────────────────────────────
buf = b""

while True:
    if uart.any():
        buf += uart.read(uart.any())

        # Process all complete lines in the buffer
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
                pass   # malformed packet – skip silently

    time.sleep_ms(5)
