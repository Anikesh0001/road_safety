# src/detect_multiclass.py
"""
Multi-class detection pipeline:
 - YOLO object detection (signs, cones, barriers, poles, benches, studs)
 - Pothole/crack segmentation (use your best.pt or other)
 - Lane & shoulder heuristics (lane_and_shoulder.py)
Outputs:
 - results/multi_base.json  (per-frame detections)
 - writes overlays to frames/*_multi.jpg for visualization
"""

import os, json, argparse
from ultralytics import YOLO
import cv2
import numpy as np
from tqdm import tqdm
from src.utils import ensure_dir
from src.lane_and_shoulder import detect_lane_markings, detect_shoulder_issues

# ----- CONFIG -----
# YOLO detection model for general objects (signs, cones, barriers). Default uses ultralytics hub yolov8n; you can point to custom weights.
OBJ_MODEL = "yolov8n.pt"   # leave as is if you want Auto-download COCO weights (detects many objects). Replace with custom weights path if available.
SEG_MODEL = "best.pt"      # your pothole/crack segmentation model (local). If not present, segmentation fallback uses bbox detections.
CONF_THR = 0.25
TEMPORAL_WINDOW = 5   # for simple smoothing

# map COCO classes of interest -> our infra classes (if using coco)
COCO_MAP = {
    # some COCO classes that are useful
    "traffic light": "sign_or_signal",
    "stop sign": "road_sign",
    "bench": "roadside_furniture",
    "fire hydrant": "roadside_object",
    "chair": "roadside_furniture",
    "person": "vru",
    "bicycle": "vru",
    "car": "vehicle",
    "truck": "vehicle",
    "motorcycle": "vehicle"
}
# You can extend COCO_MAP if using custom model

def load_model(path):
    print("Loading model:", path)
    return YOLO(path)


def process_frames(frames_folder, out_json, overlay_out_folder, obj_model_path=OBJ_MODEL, seg_model_path=SEG_MODEL, conf=CONF_THR):
    ensure_dir(overlay_out_folder)
    ensure_dir(os.path.dirname(out_json) or ".")

    obj_model = load_model(obj_model_path)
    seg_model = None
    try:
        seg_model = load_model(seg_model_path)
    except Exception:
        print("⚠ segmentation model not loaded; continuing without masks")

    results_all = {}
    frame_files = sorted([f for f in os.listdir(frames_folder) if f.lower().endswith((".jpg",".png"))])
    for fname in tqdm(frame_files):
        path = os.path.join(frames_folder, fname)
        frame = cv2.imread(path)
        if frame is None: 
            continue
        h,w = frame.shape[:2]
        det_entry = {"objects": [], "pavement": {}, "lane": {}, "shoulder": {}}

        # YOLO object detection
        res = obj_model(path, conf=conf)[0]
        if len(res.boxes) > 0:
            for i,box in enumerate(res.boxes):
                cls_id = int(box.cls[0])
                conf_v = float(box.conf[0])
                label = obj_model.names.get(cls_id, str(cls_id))
                x1,y1,x2,y2 = map(int, box.xyxy[0].tolist())
                det_entry["objects"].append({
                    "label": label, "conf": round(conf_v,3), "bbox":[x1,y1,x2,y2]
                })
                # draw box on overlay
                cv2.rectangle(frame, (x1,y1),(x2,y2),(0,255,0),2)
                cv2.putText(frame, f"{label} {conf_v:.2f}", (x1,y1-6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,255,0),1)

        # segmentation for pavement (pothole/crack) if available
        if seg_model is not None:
            seg_res = seg_model(path, conf=conf)[0]
            # segmentation framework: results.masks
            if seg_res.masks is not None:
                masks = []
                total_area = 0
                for i,mask in enumerate(seg_res.masks.data):
                    mask_np = mask.cpu().numpy()
                    mask_resized = cv2.resize((mask_np*255).astype("uint8"), (w,h), interpolation=cv2.INTER_NEAREST)
                    area = int((mask_resized>127).sum())
                    total_area += area
                    masks.append({"area": int(area)})
                    # overlay
                    color_mask = np.zeros_like(frame)
                    color_mask[:,:,2] = mask_resized
                    frame = cv2.addWeighted(frame, 0.7, color_mask, 0.3, 0)
                det_entry["pavement"]["mask_count"] = len(masks)
                det_entry["pavement"]["total_mask_area"] = int(total_area)
            else:
                # fallback: use boxes from seg_res.boxes if no masks
                det_entry["pavement"]["mask_count"] = len(seg_res.boxes)
                det_entry["pavement"]["total_mask_area"] = 0
        else:
            det_entry["pavement"]["mask_count"] = 0
            det_entry["pavement"]["total_mask_area"] = 0

        # lane marking analysis
        lane_info = detect_lane_markings(frame)
        det_entry["lane"] = {"line_count": lane_info["line_count"], "faded_score": lane_info["faded_score"]}
        # shoulder analysis
        sh_info = detect_shoulder_issues(frame)
        det_entry["shoulder"] = {"shoulder_present": sh_info["shoulder_present"], "erosion_score": sh_info["erosion_score"]}

        # save overlay image
        overlay_path = os.path.join(overlay_out_folder, f"{os.path.splitext(fname)[0]}_multi.jpg")
        cv2.imwrite(overlay_path, frame)

        results_all[fname] = det_entry

    # save json
    json.dump(results_all, open(out_json, "w"), indent=2)
    print("Saved:", out_json)
    return results_all


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", required=True, help="frames folder")
    parser.add_argument("--out", default="results/multi_detections.json")
    parser.add_argument("--overlays", default="frames/overlays_multi")
    parser.add_argument("--obj_model", default=OBJ_MODEL)
    parser.add_argument("--seg_model", default=SEG_MODEL)
    parser.add_argument("--conf", type=float, default=CONF_THR)
    args = parser.parse_args()

    process_frames(args.frames, args.out, args.overlays, args.obj_model, args.seg_model, args.conf)
