"""Dry, frame-synchronized sound design. No music bed or third-party recordings."""
from pathlib import Path
import wave
import numpy as np

RATE, FPS, DURATION = 48000, 60, 9
CUTS = [
    (0, 'tomato'), (10, 'lemon'), (20, 'avocado'), (30, 'strawberry'),
    (40, 'shiitake'), (50, 'orange'), (59, 'broccoli'), (68, 'cherry'),
    (77, 'garlic'), (86, 'red-cabbage'), (95, 'mango'), (104, 'ginger'),
    (113, 'egg'), (122, 'basil'), (131, 'cheese'), (140, 'pear'),
    (149, 'salmon'), (158, 'passion-fruit'), (167, 'tofu'),
    (176, 'coconut'), (185, 'bok-choy'), (194, 'radish'), (203, 'lemon'),
]
ZOOM_START, ZOOM_END, END_CARD = 185/FPS, 372/FPS, 426/FPS


def compose(destination):
    rng = np.random.default_rng(520)
    mix = np.zeros((RATE*DURATION, 2), dtype=np.float64)

    def add(signal, start, gain=1, pan=0):
        offset = round(start*RATE)
        count = min(len(signal), len(mix)-offset)
        if count <= 0:
            return
        mix[offset:offset+count, 0] += signal[:count]*gain*np.sqrt((1-pan)/2)
        mix[offset:offset+count, 1] += signal[:count]*gain*np.sqrt((1+pan)/2)

    def time(duration):
        return np.arange(round(duration*RATE))/RATE

    def tap(start, index, gain=.25):
        t = time(.09)
        noise = rng.normal(0, 1, len(t))
        body = np.convolve(noise, np.ones(9)/9, mode='same')
        attack = np.minimum(t/.0007, 1)
        shell = np.sin(2*np.pi*(380+(index%4)*90)*t)*np.exp(-t*115)
        click = noise*np.exp(-t*500)*.12
        signal = (body*np.exp(-t*100)*.8 + shell*.7 + click)*attack
        add(signal, start, gain, [-.10,.08,0,.12][index%4])

    for i,(frame,_) in enumerate(CUTS):
        tap(frame/FPS, i, .32 if i<3 else .24)

    length = ZOOM_END-ZOOM_START
    t = time(length)
    noise = rng.normal(0, 1, len(t))
    air = np.convolve(noise, np.ones(12)/12, mode='same')
    envelope = np.sin(np.pi*t/length)**2.2
    add(air*envelope, ZOOM_START, .16)
    for start,gain in [(0,.18),(ZOOM_END,.22),(END_CARD,.19)]:
        t = time(.25)
        phase = 2*np.pi*(48*t + 45*.028*(1-np.exp(-t/.028)))
        signal = np.sin(phase)*np.exp(-t*23)*np.minimum(t/.002,1)
        add(signal,start,gain)
    tap(END_CARD, 0, .19)
    dry=mix.copy()
    for seconds,gain in [(.027,.11),(.053,.055)]:
        delay=round(seconds*RATE)
        mix[delay:]+=dry[:-delay,::-1]*gain
    mix=np.tanh(mix*1.3)
    mix *= .75/max(np.max(np.abs(mix)),1e-9)
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(destination),'wb') as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes((mix*32767).astype('<i2').tobytes())
    return {'sample_rate':RATE,'seconds':DURATION,'channels':2,
            'peak_dbfs_before_mastering':float(20*np.log10(np.max(np.abs(mix)))),
            'cut_frames':[frame for frame,_ in CUTS]}


if __name__=='__main__':
    print(compose(Path(__file__).parent/'output'/'soundtrack.wav'))
