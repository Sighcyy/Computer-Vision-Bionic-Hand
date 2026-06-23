"""
hand_tracker.py  –  PC side
Tracks hand landmarks with MediaPipe, maps finger curl to servo angles,
and streams them to the ESP32 over a serial (USB) connection.

Dependencies:
    pip install opencv-python mediapipe pyserial

Usage:
    python hand_tracker.py --port COM3        # Windows
    python hand_tracker.py --port /dev/ttyUSB0  # Linux / Mac
"""

import cv2
import mediapipe as mp
import serial
import time
import argparse
import math

# ── Config ──────────────────────────────────────────────────────────────────
BAUD_RATE    = 115200
SEND_HZ      = 30          # how often we push data (frames per second cap)
SERVO_MIN    = 0           # degrees
SERVO_MAX    = 180         # degrees

# Which finger maps to which servo index (M1-M5)
# Order: Thumb, Index, Middle, Ring, Pinky
FINGER_TO_SERVO = [0, 1, 2, 3, 4]   # M1=Thumb … M5=Pinky

# MediaPipe landmark indices for each finger's MCP and TIP
FINGER_LANDMARKS = [
    (mp.solutions.hands.HandLandmark.THUMB_CMC,  mp.solutions.hands.HandLandmark.THUMB_TIP),
    (mp.solutions.hands.HandLandmark.INDEX_FINGER_MCP,  mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP),
    (mp.solutions.hands.HandLandmark.MIDDLE_FINGER_MCP, mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP),
    (mp.solutions.hands.HandLandmark.RING_FINGER_MCP,   mp.solutions.hands.HandLandmark.RING_FINGER_TIP),
    (mp.solutions.hands.HandLandmark.PINKY_MCP,         mp.solutions.hands.HandLandmark.PINKY_TIP),
]

# Pip landmarks used to gauge curl depth
FINGER_PIP = [
    mp.solutions.hands.HandLandmark.THUMB_IP,
    mp.solutions.hands.HandLandmark.INDEX_FINGER_PIP,
    mp.solutions.hands.HandLandmark.MIDDLE_FINGER_PIP,
    mp.solutions.hands.HandLandmark.RING_FINGER_PIP,
    mp.solutions.hands.HandLandmark.PINKY_PIP,
]

# ── Helpers ──────────────────────────────────────────────────────────────────
def dist(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)


def finger_curl_angle(lm, mcp_id, pip_id, tip_id):
    """
    Returns an angle 0-180 representing how curled the finger is.
    0   = fully open / extended
    180 = fully closed / curled
    Uses the ratio of TIP-to-MCP distance vs PIP-to-MCP distance.
    """
    mcp = lm[mcp_id]
    pip = lm[pip_id]
    tip = lm[tip_id]

    mcp_to_tip = dist(mcp, tip)
    mcp_to_pip = dist(mcp, pip)

    if mcp_to_pip < 1e-6:
        return 90

    # When extended, tip is ~2x pip distance; when curled, closer to 1x
    ratio = mcp_to_tip / (2.0 * mcp_to_pip)
    ratio = max(0.0, min(1.0, ratio))        # clamp 0-1
    angle = int((1.0 - ratio) * SERVO_MAX)   # invert: curled = high angle
    return angle


def build_packet(angles):
    """Format: A<t>,<i>,<m>,<r>,<p>\n  (Thumb,Index,Middle,Ring,Pinky)"""
    return "A" + ",".join(str(a) for a in angles) + "\n"


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM3", help="Serial port for ESP32")
    parser.add_argument("--cam",  default=0,      type=int, help="Camera index")
    args = parser.parse_args()

    print(f"[INFO] Opening serial port {args.port} @ {BAUD_RATE} baud …")
    try:
        ser = serial.Serial(args.port, BAUD_RATE, timeout=1)
        time.sleep(2)   # let ESP32 reset
        print("[INFO] Serial connected.")
    except serial.SerialException as e:
        print(f"[ERROR] Cannot open port: {e}")
        return

    mp_hands  = mp.solutions.hands
    mp_draw   = mp.solutions.drawing_utils
    hands_det = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.6,
    )

    cap = cv2.VideoCapture(args.cam)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera.")
        return

    prev_time   = 0
    frame_delay = 1.0 / SEND_HZ

    print("[INFO] Running – press Q to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res   = hands_det.process(rgb)

        angles = [90, 90, 90, 90, 90]   # default: mid-position

        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark
            mp_draw.draw_landmarks(frame, res.multi_hand_landmarks[0],
                                   mp_hands.HAND_CONNECTIONS)

            for i, (mcp_id, tip_id) in enumerate(FINGER_LANDMARKS):
                pip_id = FINGER_PIP[i]
                angles[i] = finger_curl_angle(lm, mcp_id, pip_id, tip_id)

        # Display angles on frame
        labels = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        for i, (label, angle) in enumerate(zip(labels, angles)):
            cv2.putText(frame, f"{label}: {angle}°",
                        (10, 30 + i * 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Hand Tracker – Bionic Arm", frame)

        # Rate-limit serial writes
        now = time.time()
        if now - prev_time >= frame_delay:
            packet = build_packet(angles)
            try:
                ser.write(packet.encode())
            except serial.SerialException as e:
                print(f"[WARN] Serial write error: {e}")
            prev_time = now

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    ser.close()
    print("[INFO] Stopped.")


if __name__ == "__main__":
    main()
