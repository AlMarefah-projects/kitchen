import cv2
import numpy as np
import requests
import json
import time
import multiprocessing
from datetime import datetime, timezone, timedelta
from ultralytics import YOLO


# =========================
# Load Configuration
# =========================
def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)


CONFIG = load_config()

SERVER_URL = CONFIG["data_send_url"]
HEARTBEAT_URL = CONFIG["heartbeat_url"]
SECRET_KEY = CONFIG["X-Secret-Key"]

MODEL_PATH = CONFIG["model"]
CAMERAS = CONFIG["streams"]

CHECK_INTERVAL = CONFIG["inference_interval"]
HEARTBEAT_INTERVAL = CONFIG["heartbeat_interval"]

FRAME_WIDTH = CONFIG["frame_width"]
FRAME_HEIGHT = CONFIG["frame_height"]

SEND_WIDTH = CONFIG["frame_send_width"]
SEND_HEIGHT = CONFIG["frame_send_height"]

JPEG_QUALITY = CONFIG["frame_send_jpeg_quality"]

DRAW = CONFIG["draw"]
SHOW = CONFIG["show"]
SEND_DATA = CONFIG["send_data"]


# =========================
# Classes
# =========================
all_classes = [
    'hat', 'no_hat', 'mask', 'no_mask', 'gloves', 'no_gloves',
    'food_uncover', 'pilgrim', 'no_pilgrim', 'waste', 'incorrect_mask', 'food_processing'
]

VIOLATION_IDS = [1, 3, 5, 6, 8, 9, 10]


# =========================
# Time Helper
# =========================
def get_next_check_time():
    now = datetime.now(timezone.utc)
    return now + timedelta(seconds=CHECK_INTERVAL)


# =========================
# Send Data
# =========================
def send_violations(violations, start_time, end_time, timestamp, frame, camera_sn):
    headers = {"X-Secret-Key": SECRET_KEY}

    data = {
        "sn": camera_sn,
        "violation_list": json.dumps(violations),
        "start_time": start_time,
        "end_time": end_time,
        "timestamp": timestamp,
        "violation": bool(violations)
    }

    frame = cv2.resize(frame, (SEND_WIDTH, SEND_HEIGHT))

    _, img_encoded = cv2.imencode(
        '.jpg',
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    )

    files = {'image': ('violation.jpg', img_encoded.tobytes(), 'image/jpeg')}

    try:
        response = requests.post(
            SERVER_URL,
            headers=headers,
            data=data,
            files=files,
            timeout=30
        )

        if response.status_code in [200, 201]:
            print(f"[{camera_sn}] ✓ Data sent")
        else:
            print(f"[{camera_sn}] ✗ Failed: {response.status_code}")

    except Exception as e:
        print(f"[{camera_sn}] ✗ Send error: {e}")


# =========================
# Heartbeat
# =========================
def send_heartbeat(camera_sn):
    try:
        requests.post(
            HEARTBEAT_URL,
            headers={"X-Secret-Key": SECRET_KEY},
            json={"sn": camera_sn},
            timeout=5
        )
        print(f"[{camera_sn}] ♥ Heartbeat")
    except:
        print(f"[{camera_sn}] ✗ Heartbeat failed")


# =========================
# Camera Process
# =========================
def process_camera(camera):
    camera_sn = camera["sn"]
    rtsp_url = camera["video_source"]

    print(f"[{camera_sn}] Starting...")

    try:
        model = YOLO(MODEL_PATH, task='detect')
        print(f"[{camera_sn}] ✓ Model loaded")
    except Exception as e:
        print(f"[{camera_sn}] ✗ Model error: {e}")
        return

    cap = None
    next_check = get_next_check_time()
    last_heartbeat = time.time()

    while True:
        try:
            # Connect camera
            if cap is None or not cap.isOpened():
                print(f"[{camera_sn}] Connecting...")
                cap = cv2.VideoCapture(rtsp_url)

                if not cap.isOpened():
                    print(f"[{camera_sn}] ✗ Connection failed")
                    time.sleep(5)
                    continue

                print(f"[{camera_sn}] ✓ Connected")

            # Heartbeat
            if time.time() - last_heartbeat > HEARTBEAT_INTERVAL:
                send_heartbeat(camera_sn)
                last_heartbeat = time.time()

            # Wait until next inference
            now = datetime.now(timezone.utc)
            if now < next_check:
                time.sleep(0.5)
                continue

            ret, frame = cap.read()

            if not ret:
                print(f"[{camera_sn}] ✗ Frame read failed")
                cap.release()
                cap = None
                next_check = get_next_check_time()
                continue

            # Resize for inference
            frame_resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            # Inference
            start_inf = time.time()
            results = model.predict(
                frame_resized,
                imgsz=FRAME_WIDTH,
                conf=0.3,
                iou=CONFIG["iou_threshold"],
                verbose=False
            )
            print(f"[{camera_sn}] Inference: {(time.time()-start_inf)*1000:.1f} ms")

            detections = []
            if results and results[0].boxes:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                classes = results[0].boxes.cls.cpu().numpy().astype(int)
                confs = results[0].boxes.conf.cpu().numpy()

                for box, cls_id, conf in zip(boxes, classes, confs):
                    detections.append((box.astype(int), cls_id, float(conf)))

            violations = []
            processed_frame = frame.copy()

            for box, class_id, conf in detections:
                if class_id >= len(all_classes):
                    continue

                class_name = all_classes[class_id]
                x1, y1, x2, y2 = box

                is_violation = class_id in VIOLATION_IDS

                if is_violation and class_name not in violations:
                    violations.append(class_name)

                if DRAW:
                    color = (0, 0, 255) if is_violation else (0, 255, 0)
                    cv2.rectangle(processed_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        processed_frame,
                        f"{class_name} {conf:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        2
                    )

            print(f"[{camera_sn}] Violations: {violations if violations else 'None'}")

            # Time window
            period_start = next_check - timedelta(seconds=CHECK_INTERVAL)
            period_end = next_check

            start_time = period_start.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_time = period_end.strftime("%Y-%m-%dT%H:%M:%SZ")
            timestamp = end_time

            # Send
            if SEND_DATA:
                send_violations(
                    violations,
                    start_time,
                    end_time,
                    timestamp,
                    processed_frame,
                    camera_sn
                )

            # Show
            if SHOW:
                cv2.imshow(camera_sn, processed_frame)
                cv2.waitKey(1)

            next_check = get_next_check_time()

        except Exception as e:
            print(f"[{camera_sn}] ✗ Error: {e}")
            time.sleep(3)

    if cap:
        cap.release()


# =========================
# Main
# =========================
def main():
    print("\n" + "=" * 60)
    print("KITCHEN VIOLATION SYSTEM (CONFIG-DRIVEN)")
    print("=" * 60)

    print(f"Model: {MODEL_PATH}")
    print(f"Cameras: {len(CAMERAS)}")
    print(f"Inference interval: {CHECK_INTERVAL}s")

    processes = []

    for camera in CAMERAS:
        p = multiprocessing.Process(
            target=process_camera,
            args=(camera,)
        )
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\nStopping...")
        for p in processes:
            p.terminate()
            p.join()


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()
