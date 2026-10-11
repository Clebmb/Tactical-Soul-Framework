"""Generate original pixel UFOs for the fixed native bats/clouds source page.

No host ROM or extracted art is read. Run in any working directory; output stays
beside this script. Palette index zero stays transparent.
"""
import json
from pathlib import Path

def artwork():
    width,height=128,32;pixels=[0]*(width*height)
    def dot(x,y,color):
        if 0<=x<width and 0<=y<height:pixels[y*width+x]=color
    def ufo(left,top,w,h,phase=0):
        for y in range(h):
            for x in range(w):
                # Elliptical saucer, bright canopy, and independent landing lights.
                nx=(2*x+1-w)/w;ny=(2*y+1-h)/h
                color=0
                if nx*nx+(ny*2)**2<0.85:color=1
                if abs(nx)<0.38 and -0.75<ny<-0.1:color=3
                if abs(ny)<0.14 and abs(nx)<0.95:color=2
                if y==h*3//4 and (x+phase)%4==0:color=4
                dot(left+x,top+y,color)
    for phase,x in enumerate((8,16,24)):ufo(x,0,8,16,phase)
    for y in (0,8):
        for phase,x in enumerate((32,40,48,56)):ufo(x,y,8,8,phase+y//8)
    ufo(0,16,32,16,0);ufo(32,16,32,16,1)
    ufo(64,0,64,16,0);ufo(64,16,64,16,1)
    return dict(width=width,height=height,pixels=pixels)

def main():
    folder=Path(__file__).resolve().parent/'modules'/'assets'
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'invaders.json').write_text(json.dumps(artwork(),separators=(',',':'))+'\n')
    colors=[[0,0,0],[96,248,248],[32,64,160],[248,248,248],[248,216,64]]+[[0,0,0]]*11
    (folder/'palette.json').write_text(json.dumps(colors,indent=2)+'\n')
    print('Generated original invaders.json and palette.json')

if __name__=='__main__':main()
