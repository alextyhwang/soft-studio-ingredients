"""Deterministic, resolution-independent launch film; 520 real assets, no video model.

python motion/render.py --stills
python motion/render.py --draft
python motion/render.py
"""
import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import random
import subprocess
import time

import imageio_ffmpeg
import numpy as np
from PIL import Image as PILImage, ImageDraw, ImageFont
import skia

from soundtrack import compose, FLIPS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'motion'/'output'
OUT.mkdir(parents=True, exist_ok=True)
W, H, SECONDS = 1080, 1350, 16
BG, INK, GRAY = '#f7f7f7', '#191919', '#858585'
CATALOG = json.loads((ROOT/'metadata/ingredients.json').read_text())['items']
ITEMS = {item['id']: item for item in CATALOG}
TYPEFACE = skia.Typeface.MakeFromFile('C:/Windows/Fonts/segoeui.ttf')
MEDIUM = skia.Typeface.MakeFromFile('C:/Windows/Fonts/seguisb.ttf') or TYPEFACE
SAMPLE = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


def clamp(t):
    return min(1, max(0, t))


def lerp(a, b, t):
    return a + (b-a)*t


def bezier(t, x1, y1, x2, y2):
    t = clamp(t)
    lo, hi = 0., 1.
    for _ in range(15):
        u = (lo+hi)/2
        x = 3*(1-u)**2*u*x1 + 3*(1-u)*u*u*x2 + u**3
        if x < t:
            lo = u
        else:
            hi = u
    return 3*(1-u)**2*u*y1 + 3*(1-u)*u*u*y2 + u**3


def ease(t):
    return bezier(t, .23, 1, .32, 1)


def travel(t):
    return bezier(t, .77, 0, .175, 1)


def reveal(t, start, length=.5):
    return ease((t-start)/length)


def color(hexcode, alpha=1):
    s = hexcode.lstrip('#')
    return skia.ColorSetARGB(round(clamp(alpha)*255), int(s[:2],16), int(s[2:4],16), int(s[4:],16))


def paint(hexcode=INK, alpha=1):
    return skia.Paint(Color=color(hexcode, alpha), AntiAlias=True)


def rr(c, x, y, w, h, r, fill='#ffffff', alpha=1, shadow=False, border=False):
    rect = skia.Rect.MakeXYWH(x, y, w, h)
    if shadow:
        p = paint('#000000', .055*alpha)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, 20))
        c.drawRoundRect(skia.Rect.MakeXYWH(x, y+12, w, h), r, r, p)
    c.drawRoundRect(rect, r, r, paint(fill, alpha))
    if border:
        p = paint('#000000', .045*alpha)
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(1)
        c.drawRoundRect(rect, r, r, p)


@lru_cache(maxsize=100)
def font(size, medium=False):
    f = skia.Font(MEDIUM if medium else TYPEFACE, size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def text(c, value, x, y, size=32, fill=INK, alpha=1, align='left', tracking=0, medium=False):
    if alpha <= .002:
        return
    f = font(size, medium)
    width = f.measureText(value) + tracking*max(0, len(value)-1)
    if align == 'center':
        x -= width/2
    elif align == 'right':
        x -= width
    p = paint(fill, alpha)
    if tracking:
        for char in value:
            c.drawString(char, x, y, f, p)
            x += f.measureText(char) + tracking
    else:
        c.drawString(value, x, y, f, p)


def chip(c, value, cx, y, width=None, size=22, alpha=1, fill='#ffffff'):
    width = width or font(size).measureText(value) + 46
    rr(c, cx-width/2, y, width, 58, 29, fill, alpha)
    text(c, value, cx, y+37, size, '#626262', alpha, 'center')


@lru_cache(maxsize=530)
def asset(id):
    image = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(str(ROOT/ITEMS[id]['webp']['path'])))
    if image is None:
        raise ValueError(id)
    return image.withDefaultMipmaps()


def food(c, id, cx, cy, size, angle=0, alpha=1, sx=1):
    if alpha < .002:
        return
    c.save()
    c.translate(cx, cy)
    c.rotate(angle)
    c.scale(sx, 1)
    p = paint('#ffffff', alpha)
    c.drawImageRect(asset(id), skia.Rect.MakeXYWH(-size/2, -size/2, size, size), SAMPLE, p)
    c.restore()


def line(c, x1, y1, x2, y2, alpha=1, fill=INK, width=2):
    p = paint(fill, alpha)
    p.setStrokeWidth(width)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    c.drawLine(x1,y1,x2,y2,p)


def arrow(c, cx, cy, alpha=1, fill=INK, size=20):
    line(c,cx,cy-size*.55,cx,cy+size*.55,alpha,fill,2.7)
    line(c,cx-size*.43,cy+size*.1,cx,cy+size*.55,alpha,fill,2.7)
    line(c,cx+size*.43,cy+size*.1,cx,cy+size*.55,alpha,fill,2.7)


def mark(c, x, y, size=58, alpha=1):
    rr(c,x,y,size,size,size/2,alpha=alpha)
    for dx in [-1,1]:
        for dy in [-1,1]:
            c.drawCircle(x+size/2+dx*size*.098,y+size/2+dy*size*.098,size*.039,paint(INK,alpha))


# Interleave all 20 categories so the final grid reads as a colorful collection.
grid_ids = [CATALOG[group*26+within]['id'] for within in range(26) for group in range(20)]
random.Random(520).shuffle(grid_ids)
FOCUS = 9*26+12
for index, id in [(FOCUS-1,'bok-choy'),(FOCUS,'lemon'),(FOCUS+1,'strawberry')]:
    other = grid_ids.index(id)
    grid_ids[other],grid_ids[index] = grid_ids[index],grid_ids[other]
assert len(grid_ids) == len(set(grid_ids)) == 520


@lru_cache(maxsize=1)
def atlas():
    surface = skia.Surface.MakeRasterN32Premul(2600,2000)
    c=surface.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    for i,id in enumerate(grid_ids):
        x,y=(i%26)*100,(i//26)*100
        rr(c,x+4,y+4,92,92,18,'#ffffff',border=True)
        food(c,id,x+50,y+50,78)
    return surface.makeImageSnapshot().withDefaultMipmaps()


sets = [
    ['cucumber','tomato','cheese'],
    ['lemon','avocado','strawberry'],
    ['broccoli','carrot','red-cabbage'],
    ['cherry','shiitake','bread'],
    ['basil','honey','milk'],
    ['fig','egg','salmon'],
    ['mango','tofu','garlic'],
    ['cinnamon','lime','walnut'],
    ['corn','onion','blueberry'],
    ['pear','butter','chickpeas'],
    ['ginger','coconut','radish'],
    ['potato','peach','cashew'],
    ['spinach','yogurt','raspberry'],
    ['papaya','rosemary','pistachio'],
    ['cauliflower','oats','kiwi'],
    ['orange','almond','chocolate'],
    ['bok-choy','lemon','strawberry'],
]
# Resolve a few common singular/plural aliases against the released catalog.
aliases = {'egg':'eggs', 'walnut':'walnuts', 'blueberry':'blueberries', 'cashew':'cashews',
           'raspberry':'raspberries','pistachio':'pistachios','almond':'almonds',
           'chickpeas':'chickpea','chocolate':'dark-chocolate'}
for trio in sets:
    for i,id in enumerate(trio):
        if id not in ITEMS and aliases.get(id) in ITEMS:
            trio[i] = aliases[id]
        if trio[i] not in ITEMS:
            raise ValueError(f'Unknown featured ingredient: {trio[i]}')


def swap_state(t, slot):
    index, sx, tilt = 0, 1., 0.
    for i,start in enumerate(FLIPS):
        local=(t-start-slot*.025)/.13
        if local < 0:
            break
        if local >= 1:
            index=i+1
            continue
        q=travel(local)
        index=i if q<.5 else i+1
        sx=max(.045,abs(math.cos(math.pi*q)))
        tilt=math.sin(math.pi*q)*2*(-1 if slot%2 else 1)
        break
    return sets[index][slot],sx,tilt,index


def scene(c,t):
    c.clear(color(BG))
    # The film begins with ingredients already present, then resolves into place.
    intro_out=1-reveal(t,2.35,.35)
    trio_out=1-reveal(t,6.35,.35)
    if t<6.72:
        title_in=.22+.78*reveal(t,0,.62)
        if intro_out>.001:
            chip(c,'A little of everything.',540,216,alpha=title_in*intro_out)
            text(c,'Good ingredients.',540,351+18*(1-title_in),76,alpha=title_in*intro_out,align='center',tracking=-2.8)
            text(c,'For your next idea.',540,441+18*(1-title_in),76,GRAY,title_in*intro_out,'center',-2.8)
        flip_title=reveal(t,2.55,.4)*(1-reveal(t,6.1,.3))
        text(c,'Pick a favorite.',540,306+18*(1-reveal(t,2.55,.4)),76,alpha=flip_title,align='center',tracking=-2.7)
        text(c,'Then find a few more.',540,392,61,GRAY,flip_title,'center',-2)
        settle=travel((t-2.30)/.45)
        starts=[(222,689,-11),(550,832,5),(851,643,10)]
        for slot,(ix,iy,angle) in enumerate(starts):
            entrance=.22+.78*reveal(t,-.08+slot*.17,.62)
            id,sx,tilt,_=swap_state(t,slot)
            target=220+slot*320
            cx=lerp(ix,target,settle)
            morph=reveal(t,6.18,.20)
            cy=lerp(iy,lerp(718,699,morph),settle)+24*(1-entrance)
            size=lerp(340,lerp(278,249.6,morph),settle)*(1-.045*(1-entrance))
            ca=settle*trio_out
            if ca>.001:
                c.save()
                c.translate(cx,cy)
                c.scale(sx,1)
                card_h=lerp(362,294.4,morph)
                card_y=lerp(-169,-147.2,morph)
                rr(c,-149,card_y,298,card_h,lerp(50,57.6,morph),alpha=ca,shadow=True)
                c.restore()
            food(c,id,cx,cy-lerp(0,19*(1-morph),settle),size,lerp(angle,tilt,settle),entrance*trio_out,sx)
            label=ITEMS[id]['name']
            if settle>.001:
                text(c,label,cx,cy+150,25,INK,settle*trio_out*(1-morph)*min(1,sx*2),'center',-.4)
        small_alpha=reveal(t,1.2,.4)*intro_out
        chip(c,'Transparent backgrounds',376,1086,alpha=small_alpha)
        chip(c,'PNG + WebP',736,1086,alpha=small_alpha)
        if t>2.55:
            a=reveal(t,2.6,.4)*(1-reveal(t,6.12,.25))
            chip(c,'20 categories. One consistent style.',540,1056,alpha=a)
            for i in range(3):
                c.drawCircle(524+i*16,1160,3,paint(INK,a*(1 if i==int(t*2)%3 else .18)))

    # Continuous camera pullback. All 520 unique ingredients are in the atlas.
    if t>=6.35:
        q=travel((t-6.60)/3.50)
        zoom=math.exp(lerp(math.log(3.2),math.log(.363),q))
        focusx=lerp(1250,1300,q)
        focusy=lerp(950,1000,q)
        cy=lerp(699,719,q)
        final=reveal(t,12.15,.85)
        zoom*=lerp(1,1.04,final)
        alpha=reveal(t,6.35,.35)*lerp(1,.22,final)
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(32,342,1016,754))
        c.translate(540,cy)
        c.scale(zoom,zoom)
        c.translate(-focusx,-focusy)
        p=paint('#ffffff',alpha)
        c.drawImage(atlas(),0,0,SAMPLE,p)
        c.restore()
        # Pale masks soften the camera's entry and leave the final atlas entirely visible.
        head_in=reveal(t,6.70,.6)*(1-final)
        text(c,'A whole creative pantry.',540,258,64,alpha=head_in*(1-reveal(t,9.70,.32)),align='center',tracking=-2)
        count_in=reveal(t,9.82,.46)*(1-final)
        text(c,'520 ingredients.',540,257,79,alpha=count_in,align='center',tracking=-3)
        text(c,'Every one included.',540,309,28,'#696969',count_in,'center',-.4)
        free_in=reveal(t,10.12,.55)*(1-final)
        text(c,'All free.',540,1215+22*(1-reveal(t,10.12,.55)),100,alpha=free_in,align='center',tracking=-4)
        text(c,'CC BY 4.0 · Attribution required',540,1270,23,'#696969',free_in,'center')

    # White composer-style end card, echoing the actual landing page.
    end=reveal(t,12.15,.85)
    if end>.001:
        c.save()
        c.translate(0,36*(1-end))
        rr(c,113,365,854,650,66,alpha=end,shadow=True)
        chip(c,'SOFT STUDIO INGREDIENTS',540,415,alpha=end,fill='#f7f7f7',size=19)
        text(c,'All 520.',540,603,123,alpha=end,align='center',tracking=-5.5)
        text(c,'All free.',540,746,123,GRAY,end,'center',-5.5)
        text(c,'For personal + commercial projects.',540,827,29,'#696969',end,'center',-.3)
        chip(c,'PNG + WebP',438,879,width=200,alpha=end,fill='#f7f7f7')
        chip(c,'Transparent',656,879,width=200,alpha=end,fill='#f7f7f7')
        c.restore()
        cta=reveal(t,12.80,.55)
        rr(c,216,1080+18*(1-cta),648,102,51,alpha=cta)
        text(c,'Get the collection',259,1143+18*(1-cta),32,alpha=cta,tracking=-.7)
        rr(c,776,1093+18*(1-cta),76,76,38,INK,cta)
        arrow(c,814,1131+18*(1-cta),cta,'#ffffff',28)
        text(c,'soft-studio-ingredients.vercel.app',540,1235,27,INK,cta,'center',-.4)
        text(c,'CC BY 4.0 · Credit Alex Wang',540,1282,21,'#696969',cta,'center')

    # Persistent, quiet branding above the film's action.
    brand=1
    mark(c,62,59,62,brand)
    text(c,'Soft Studio',141,102,32,alpha=brand,tracking=-.9,medium=True)
    if t<6.35:
        completed=sum(start<=t for start in FLIPS)
        badge=f'{min(520,3+completed*3):03d} / 520'
    elif t<10.1:
        q=travel((t-6.6)/3.5)
        badge=f'{round(lerp(51,520,q)):03d} / 520'
    else:
        badge='520 / 520'
    chip(c,badge,904,62,width=184,size=25,alpha=brand)


def still(t,path,width=1080):
    height=round(width*H/W)
    surface=skia.Surface.MakeRasterN32Premul(width,height)
    c=surface.getCanvas()
    c.scale(width/W,width/W)
    scene(c,t)
    surface.makeImageSnapshot().save(str(path),skia.kPNG)


def storyboard():
    times=[1.8,3.05,4.55,6.55,7.7,8.2,9.2,10.8,14.0]
    board=PILImage.new('RGB',(1080,3*496),'#eaeaea')
    draw=ImageDraw.Draw(board)
    for i,t in enumerate(times):
        path=OUT/f'frame-{t:.2f}.png'
        still(t,path,360)
        thumb=PILImage.open(path)
        x,y=(i%3)*360,(i//3)*496
        board.paste(thumb,(x,y))
        draw.text((x+14,y+460),f'{t:04.1f}s',fill='#333333',font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',19))
    board.save(OUT/'storyboard.jpg',quality=95)
    still(1.8,OUT/'poster.png')
    (OUT/'grid-manifest.json').write_text(json.dumps({'count':520,'columns':26,'rows':20,'ids':grid_ids},indent=2))
    print(f'Storyboard: {OUT / "storyboard.jpg"}',flush=True)


def render(draft=False):
    width,height,fps=(540,676,30) if draft else (1080,1350,60)
    audio=OUT/'soundtrack.wav'
    report=compose(audio)
    path=OUT/('soft-studio-draft.mp4' if draft else 'soft-studio-launch-x.mp4')
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    command=[ffmpeg,'-hide_banner','-y','-f','rawvideo','-pix_fmt','bgra','-s',f'{width}x{height}',
             '-r',str(fps),'-i','pipe:0','-i',str(audio),'-map','0:v','-map','1:a',
             '-c:v','libx264','-preset','fast' if draft else 'slow','-crf','22' if draft else '18',
             '-maxrate','12M','-bufsize','24M','-pix_fmt','yuv420p','-profile:v','high',
             '-g',str(fps*2),'-c:a','aac','-b:a','192k','-ar','48000',
             '-af','loudnorm=I=-16:TP=-1.2:LRA=7','-movflags','+faststart',
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
    report.update({'path':str(path),'width':width,'height':height,'fps':fps,
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
