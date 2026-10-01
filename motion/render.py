"""Minimal nine-second launch edit. Deterministic 60 fps frames and original sound."""
import argparse
from bisect import bisect_right
from functools import lru_cache
import json
import math
from pathlib import Path
import random
import subprocess
import time

import imageio_ffmpeg
from PIL import Image as PILImage, ImageDraw, ImageFont
import skia
from soundtrack import compose, CUTS, DURATION, FPS, ZOOM_START, ZOOM_END, END_CARD, ZOOM_SWAPS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'motion'/'output'
OUT.mkdir(parents=True,exist_ok=True)
W,H,SECONDS=1080,1350,DURATION
BG,INK,GRAY='#f7f7f7','#191919','#747474'
CATALOG=json.loads((ROOT/'metadata/ingredients.json').read_text())['items']
ITEMS={item['id']:item for item in CATALOG}
TYPEFACE=skia.Typeface.MakeFromFile('C:/Windows/Fonts/segoeui.ttf')
SAMPLE=skia.SamplingOptions(skia.FilterMode.kLinear,skia.MipmapMode.kLinear)
CUT_TIMES=[frame/FPS for frame,_ in CUTS]
FEATURED={id for _,id in CUTS}
assert all(id in ITEMS for id in FEATURED)


def clamp(t):
    return min(1,max(0,t))


def lerp(a,b,t):
    return a+(b-a)*t


def travel(t):
    """easeInOutSine: https://easings.net/#easeInOutSine.

    A smooth camera acceleration, instead of a steep UI transition curve.
    """
    t=clamp(t)
    return (1-math.cos(math.pi*t))/2


def color(value):
    s=value.lstrip('#')
    return skia.ColorSetARGB(255,int(s[:2],16),int(s[2:4],16),int(s[4:],16))


def paint(value=INK):
    return skia.Paint(Color=color(value),AntiAlias=True)


@lru_cache(maxsize=12)
def font(size):
    f=skia.Font(TYPEFACE,size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def text(c,value,x,y,size,fill=INK,tracking=0):
    f=font(size)
    x-=(f.measureText(value)+tracking*max(0,len(value)-1))/2
    p=paint(fill)
    for char in value:
        c.drawString(char,x,y,f,p)
        x+=f.measureText(char)+tracking


@lru_cache(maxsize=600)
def asset(id,large=False):
    item=ITEMS[id]
    original=ROOT/'.release'/item['png']['path']
    path=original if large and original.exists() else ROOT/item['webp']['path']
    image=skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(str(path)))
    if image is None:
        raise ValueError(f'Cannot decode {id}')
    # Only draw-time bounds change. The source images remain untouched.
    with PILImage.open(path) as bitmap:
        bounds=bitmap.getchannel('A').point(lambda a:255 if a>12 else 0).getbbox()
    if bounds is None:
        raise ValueError(f'Empty image: {id}')
    x,y,right,bottom=bounds
    padding=max(2,round(max(right-x,bottom-y)*.014))
    x,y=max(0,x-padding),max(0,y-padding)
    right,bottom=min(image.width(),right+padding),min(image.height(),bottom+padding)
    return image.withDefaultMipmaps(),skia.Rect.MakeLTRB(x,y,right,bottom)


def food(c,id,cx,cy,size,large=False):
    image,source=asset(id,large)
    ratio=size/max(source.width(),source.height())
    width,height=source.width()*ratio,source.height()*ratio
    destination=skia.Rect.MakeXYWH(cx-width/2,cy-height/2,width,height)
    c.drawImageRect(image,source,destination,SAMPLE)


# Every ingredient appears once; the array matches the portrait frame.
COLS,ROWS,CELL=20,26,120
grid_ids=[item['id'] for item in CATALOG]
random.Random(520).shuffle(grid_ids)
FOCUS=12*COLS+9
other=grid_ids.index('lemon')
grid_ids[other],grid_ids[FOCUS]=grid_ids[FOCUS],grid_ids[other]
assert len(grid_ids)==len(set(grid_ids))==COLS*ROWS==520
FOCUS_COL,FOCUS_ROW=FOCUS%COLS,FOCUS//COLS
FOCUS_X,FOCUS_Y=(FOCUS_COL+.5)*CELL,(FOCUS_ROW+.5)*CELL
HERO_SIZE=740
FINAL_ZOOM=940/(COLS*CELL)


def build_grid_states():
    """Use real pair exchanges, retaining all 520 distinct assets at every step."""
    state=grid_ids.copy()
    states=[]
    for frame,row,col,ingredient in ZOOM_SWAPS:
        index=(FOCUS_ROW+row)*COLS+FOCUS_COL+col
        target=ingredient or grid_ids[index]
        partner=state.index(target)
        state[index],state[partner]=state[partner],state[index]
        states.append(tuple(state))
    return states


GRID_STATES=build_grid_states()
GRID_SWAP_TIMES=[event[0]/FPS for event in ZOOM_SWAPS]


def grid_ingredients(t):
    index=bisect_right(GRID_SWAP_TIMES,t+1e-7)-1
    return GRID_STATES[index] if index>=0 else grid_ids


def camera(t):
    progress=travel((t-ZOOM_START)/(ZOOM_END-ZOOM_START))
    zoom=math.exp(lerp(math.log(HERO_SIZE/80),math.log(FINAL_ZOOM),progress))
    fx=lerp(FOCUS_X,COLS*CELL/2,progress)
    fy=lerp(FOCUS_Y,ROWS*CELL/2,progress)
    return zoom,fx,fy


def current_ingredient(t):
    index=max(0,bisect_right(CUT_TIMES,t+1e-7)-1)
    return CUTS[index][1]


def grid(c,t):
    zoom,fx,fy=camera(t)
    c.save()
    c.translate(W/2,H/2)
    c.scale(zoom,zoom)
    c.translate(-fx,-fy)
    left,right=fx-W/(2*zoom)-90,fx+W/(2*zoom)+90
    top,bottom=fy-H/(2*zoom)-90,fy+H/(2*zoom)+90
    for i,id in enumerate(grid_ingredients(t)):
        col,row=i%COLS,i//COLS
        cx,cy=(col+.5)*CELL,(row+.5)*CELL
        if left<cx<right and top<cy<bottom:
            # The final cuts happen inside the already-moving camera.
            if i==FOCUS and t<CUT_TIMES[-1]:
                id=current_ingredient(t)
            # Nearby ingredients retain original-resolution artwork as they enter.
            large=abs(col-FOCUS_COL)<=1 and abs(row-FOCUS_ROW)<=1
            food(c,id,cx,cy,80,large=large)
    c.restore()


def scene(c,t):
    c.clear(color(BG))
    if t<ZOOM_START:
        food(c,current_ingredient(t),W/2,H/2,HERO_SIZE,large=True)
    elif t<END_CARD:
        grid(c,t)
    else:
        # One message, hard cut. No animated titles or decorative controls.
        text(c,'520 ingredients.',W/2,588,83,tracking=-3)
        text(c,'Free.',W/2,778,156,tracking=-6)
        text(c,'Soft Studio',W/2,887,30,GRAY,tracking=-.5)
        text(c,'CC BY 4.0 · Attribution required',W/2,1263,23,GRAY)


def still(t,path,width=1080):
    surface=skia.Surface.MakeRasterN32Premul(width,round(width*H/W))
    c=surface.getCanvas()
    c.scale(width/W,width/W)
    scene(c,t)
    surface.makeImageSnapshot().save(str(path),skia.kPNG)


def storyboard():
    times=[0,.18,.35,3.60,3.94,4.18,4.52,6.50,8.0]
    board=PILImage.new('RGB',(1080,3*496),'#eaeaea')
    draw=ImageDraw.Draw(board)
    for i,t in enumerate(times):
        path=OUT/f'v4-frame-{t:.2f}.png'
        still(t,path,360)
        x,y=(i%3)*360,(i//3)*496
        with PILImage.open(path) as frame:
            board.paste(frame,(x,y))
        draw.text((x+14,y+460),f'{t:04.2f}s',fill='#333333',
                  font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',19))
    board.save(OUT/'storyboard.jpg',quality=95)
    still(0,OUT/'poster.png')
    (OUT/'grid-manifest.json').write_text(json.dumps({
        'count':520,'columns':COLS,'rows':ROWS,'ids':list(GRID_STATES[-1])},indent=2))
    print(f'Storyboard: {OUT / "storyboard.jpg"}',flush=True)


def render(draft=False):
    width,height,fps=(540,676,30) if draft else (1080,1350,FPS)
    audio=OUT/'soundtrack.wav'
    report=compose(audio)
    path=OUT/('soft-studio-draft.mp4' if draft else 'soft-studio-launch-x.mp4')
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    command=[ffmpeg,'-hide_banner','-y','-f','rawvideo','-pix_fmt','bgra','-s',f'{width}x{height}',
             '-r',str(fps),'-i','pipe:0','-i',str(audio),'-map','0:v','-map','1:a',
             '-vf','scale=in_range=pc:out_range=tv:out_color_matrix=bt709',
             '-c:v','libx264','-preset','fast' if draft else 'slow','-crf','22' if draft else '18',
             '-maxrate','12M','-bufsize','24M','-pix_fmt','yuv420p','-profile:v','high',
             '-g',str(fps*2),'-c:a','aac','-b:a','192k','-ar','48000',
             '-af','loudnorm=I=-18:TP=-1.5:LRA=7','-movflags','+faststart',
             '-x264-params','colorprim=bt709:transfer=bt709:colormatrix=bt709',
             '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
             '-t',str(SECONDS),str(path)]
    surface=skia.Surface.MakeRasterN32Premul(width,height)
    c=surface.getCanvas()
    start=time.perf_counter()
    with (OUT/('encode-draft.log' if draft else 'encode.log')).open('w') as log:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
        try:
            for frame in range(fps*SECONDS):
                c.save()
                c.scale(width/W,height/H)
                scene(c,frame/fps)
                c.restore()
                pixels=surface.makeImageSnapshot().toarray(colorType=skia.ColorType.kBGRA_8888_ColorType)
                process.stdin.write(pixels.tobytes())
                if frame%fps==0:
                    print(f'{frame//fps:02d}s / {SECONDS}s rendered ({time.perf_counter()-start:.1f}s elapsed)',flush=True)
        finally:
            process.stdin.close()
        code=process.wait()
        if code:
            raise RuntimeError(f'Encoder exited {code}; see {log.name}')
    report.update({'revision':4,'path':str(path),'width':width,'height':height,'fps':fps,
                   'frames':fps*SECONDS,'bytes':path.stat().st_size,'unique_grid_images':520,
                   'render_seconds':round(time.perf_counter()-start,2)})
    (OUT/('draft-report.json' if draft else 'render-report.json')).write_text(json.dumps(report,indent=2))
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--stills',action='store_true')
    parser.add_argument('--draft',action='store_true')
    args=parser.parse_args()
    storyboard()
    if not args.stills:
        render(args.draft)
