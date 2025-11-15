# src/lane_and_shoulder.py
import cv2
import numpy as np

def detect_lane_markings(frame, debug=False):
    """
    Returns a dict:
      { 'line_count': int, 'faded_score': 0..1 (higher = more faded), 'mask': np.array }
    Approach:
      - convert to gray, apply CLAHE to normalize illumination
      - use Canny + HoughLinesP to detect line segments
      - estimate fadedness by comparing intensity under lines vs expected brightness
    """
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # illumination normalization
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    norm = clahe.apply(gray)

    # edge detection
    edges = cv2.Canny(norm, 50, 150, apertureSize=3)

    # Hough
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=int(w*0.05), maxLineGap=20)
    line_count = 0 if lines is None else len(lines)

    # Faded score heuristic:
    # sample brightness inside narrow band along lines (if any). If average is low -> faded
    faded_score = 0.0
    if lines is not None:
        samples = []
        for x1,y1,x2,y2 in lines[:,0]:
            mx = int((x1+x2)/2)
            my = int((y1+y2)/2)
            r = max(2, int(min(w,h)*0.01))
            # clamp
            y0 = max(0, my-r); y1b = min(h, my+r)
            x0 = max(0, mx-r); x1b = min(w, mx+r)
            patch = norm[y0:y1b, x0:x1b]
            if patch.size>0:
                samples.append(patch.mean()/255.0)
        if samples:
            mean_brightness = np.mean(samples)
            # if bright (>=0.6) => not faded, else faded
            faded_score = max(0.0, 1.0 - mean_brightness)

    # Build mask for visualization
    mask = np.zeros((h,w), dtype=np.uint8)
    if lines is not None:
        for x1,y1,x2,y2 in lines[:,0]:
            cv2.line(mask, (x1,y1), (x2,y2), 255, 4)

    return {"line_count": line_count, "faded_score": round(float(faded_score),3), "mask": mask, "edges": edges}


def detect_shoulder_issues(frame, debug=False):
    """
    Detects shoulder presence/erosion by analyzing left/right margins brightness & texture.
    Returns dict:
      { 'shoulder_present': bool, 'erosion_score': 0..1 }
    Heuristic:
      - compute edge density and mean brightness near margins (bottom-left/right)
      - if edge density is high in shoulder zone -> erosion
    """
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # define ROI near bottom corners (20% width, 20% height)
    margin_w = int(w*0.2)
    margin_h = int(h*0.2)
    left_roi = gray[h-margin_h:h, 0:margin_w]
    right_roi = gray[h-margin_h:h, w-margin_w:w]

    def analyze_roi(roi):
        if roi.size==0:
            return {"edge_density":0.0, "mean_brightness":0.0}
        edges = cv2.Canny(roi, 50, 150)
        edge_density = edges.mean()
        mean_brightness = roi.mean()/255.0
        return {"edge_density": float(edge_density), "mean_brightness": float(mean_brightness)}

    L = analyze_roi(left_roi)
    R = analyze_roi(right_roi)

    # heuristics: high edge density and low brightness -> erosion/damage
    erosion_score = max(L["edge_density"], R["edge_density"])
    erosion_score = min(1.0, erosion_score*3.0)  # scale into 0..1
    shoulder_present = (L["mean_brightness"]>0.15 or R["mean_brightness"]>0.15)

    return {"shoulder_present": bool(shoulder_present), "erosion_score": round(float(erosion_score),3), "left":L, "right":R}
