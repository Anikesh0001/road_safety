import os, cv2, json, numpy as np
from PIL import Image

def ensure_dir(path): os.makedirs(path, exist_ok=True)
def write_json(path, obj): open(path,"w").write(json.dumps(obj,indent=2))
def read_json(path): return json.load(open(path))
def resize_keep_aspect(img, width=None, height=None):
    h,w = img.shape[:2]; r = width/w if width else height/h
    return cv2.resize(img, (int(w*r), int(h*r)))
def draw_detections(img, dets, color=(0,255,0)):
    o=img.copy()
    for d in dets:
        x1,y1,x2,y2=map(int,d["xyxy"])
        cv2.rectangle(o,(x1,y1),(x2,y2),color,2)
        cv2.putText(o,f"{d['label']}:{d['conf']:.2f}",(x1,y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX,0.5,color,1)
    return o
def save_side_by_side(i1,i2,out):
    if isinstance(i1,np.ndarray): i1=Image.fromarray(cv2.cvtColor(i1,cv2.COLOR_BGR2RGB))
    if isinstance(i2,np.ndarray): i2=Image.fromarray(cv2.cvtColor(i2,cv2.COLOR_BGR2RGB))
    w,h=i1.size; new=Image.new("RGB",(w*2,h)); new.paste(i1,(0,0)); new.paste(i2,(w,0)); new.save(out)
