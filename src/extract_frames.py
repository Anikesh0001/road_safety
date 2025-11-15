import cv2, os, argparse
from src.utils import ensure_dir
def extract(video,out,fps=1):
    ensure_dir(out); cap=cv2.VideoCapture(video)
    real_fps=cap.get(cv2.CAP_PROP_FPS) or 30
    step=max(int(real_fps/fps),1); i=saved=0
    while True:
        r,f=cap.read(); 
        if not r: break
        if i%step==0: cv2.imwrite(f"{out}/frame_{saved:05}.jpg",f); saved+=1
        i+=1
    cap.release(); print("Saved",saved,"frames in",out)
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("video"); p.add_argument("--out"); p.add_argument("--fps",type=int,default=1)
    a=p.parse_args(); extract(a.video,a.out,a.fps)
