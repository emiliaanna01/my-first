import sys,glob,os
from PIL import Image,ImageDraw
d,out,cols=sys.argv[1],sys.argv[2],int(sys.argv[3])
fs=sorted(glob.glob(d+"/f*.png"),key=lambda p:int(os.path.basename(p)[1:-4]))
w,h=360,640
for k in range(0,len(fs),10):
    part=fs[k:k+10]; rows=(len(part)+cols-1)//cols
    S=Image.new("RGB",(cols*w,rows*(h+30)),"#222"); D=ImageDraw.Draw(S)
    for i,p in enumerate(part):
        x,y=(i%cols)*w,(i//cols)*(h+30)
        S.paste(Image.open(p).convert("RGB").resize((w,h)),(x,y+30)); D.text((x+6,y+8),f"{int(os.path.basename(p)[1:-4])/30:.1f}s",fill="white")
    S.save(f"{out}{k//10}.png")
