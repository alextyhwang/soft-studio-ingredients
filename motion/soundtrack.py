"""Original stereo score and frame-synchronized effects. No sampled recordings."""
from pathlib import Path
import wave
import numpy as np

RATE = 48000
DURATION = 16
FLIPS = [2.80, 3.20, 3.55, 3.85, 4.12, 4.36, 4.58, 4.78,
         4.97, 5.15, 5.32, 5.49, 5.66, 5.83, 6.00, 6.17]


def compose(destination):
    rng = np.random.default_rng(520)
    dry = np.zeros((RATE * DURATION, 2), dtype=np.float64)
    atmosphere = np.zeros_like(dry)

    def add(signal, start, gain=1, pan=0, bus=dry):
        offset = int(start * RATE)
        length = min(len(signal), len(bus) - offset)
        if length <= 0:
            return
        stereo = np.column_stack((signal[:length] * np.sqrt((1 - pan) / 2),
                                  signal[:length] * np.sqrt((1 + pan) / 2)))
        bus[offset:offset + length] += gain * stereo

    def time(duration):
        return np.arange(round(duration * RATE)) / RATE

    def freq(note):
        return 440 * 2 ** ((note - 69) / 12)

    def pluck(note, start, gain=.12, pan=0, duration=1.1):
        t = time(duration)
        f = freq(note)
        envelope = (1 - np.exp(-t * 480)) * np.exp(-t * 6)
        signal = (np.sin(2 * np.pi * f * t + .8 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 12))
                  + .15 * np.sin(2 * np.pi * f * 3 * t)) * envelope
        add(signal, start, gain, pan, atmosphere)

    # A restrained Cmaj9 / Am9 / Fmaj9 / G6 progression, four seconds per chord.
    chords = [[48, 55, 59, 62, 64], [45, 52, 55, 59, 60],
              [41, 48, 52, 55, 57], [43, 50, 55, 57, 59]]
    for bar, notes in enumerate(chords):
        t = time(4.6)
        pad = np.zeros_like(t)
        for index, note in enumerate(notes):
            f = freq(note + 12)
            pad += (np.sin(2*np.pi*f*t) + .3*np.sin(2*np.pi*f*1.003*t + index)) / len(notes)
        envelope = np.minimum(1, t / .7) * np.clip((4.6 - t) / 1.2, 0, 1)
        add(pad * envelope, bar * 4, .11, (-1)**bar * .25, atmosphere)

    notes = [72, 76, 79, 83, 74, 79, 76, 72]
    for i in range(24):
        pluck(notes[i % len(notes)] + (0 if i < 16 else -2), .25 + i * .5,
              .075 if i < 12 else .058, np.sin(i * 1.7) * .55)

    # Round, low-volume percussion. The last four seconds are left open for the title.
    for beat in range(2, 25):
        start = beat * .5
        if beat % 2 == 0:
            t = time(.28)
            phase = 2*np.pi*(48*t + (105-48)*.025*(1-np.exp(-t/.025)))
            add(np.sin(phase) * np.exp(-t*18) * np.minimum(t/.003, 1), start, .19)
        else:
            t = time(.12)
            noise = rng.normal(0, 1, len(t))
            soft = np.convolve(noise, np.ones(7)/7, mode='same')
            add(soft*np.exp(-t*38)*np.minimum(t/.002, 1), start, .055, .16)
        for step in range(2):
            t = time(.055)
            n = rng.normal(0, 1, len(t))
            high = n - np.convolve(n, np.ones(9)/9, mode='same')
            add(high*np.exp(-t*100)*np.minimum(t/.0015, 1), start + step*.25, .012, (-1)**beat*.3)

    # Small glass/wood taps exactly on entrances and the centers of the flips.
    events = [.38, .64, .90] + [v+.065 for v in FLIPS] + [10.05, 12.48, 13.04]
    for i, start in enumerate(events):
        t = time(.18)
        f = [1100, 1320, 1650, 980][i % 4]
        click = (np.sin(2*np.pi*f*t) + .28*np.sin(2*np.pi*f*2.13*t))
        click *= np.exp(-t*65) * np.minimum(t/.001, 1)
        add(click, start, .11 if i < 3 else .08, np.sin(i)*.35)

    # A brushed, airy reverse swell that resolves with the full-grid reveal.
    for start, duration, gain in [(6.40, 3.65, .055), (12.18, .7, .035)]:
        t = time(duration)
        n = rng.normal(0, 1, len(t))
        brushed = np.convolve(n, np.ones(28)/28, mode='same')
        envelope = np.sin(np.pi * t / duration) ** 1.8
        add(brushed*envelope, start, gain, -.15, atmosphere)

    for note, offset in [(72, 0), (76, .05), (79, .10), (86, .16)]:
        pluck(note, 10.05+offset, .10, (note-79)/20, 2.4)
    for note, offset in [(60, 0), (67, .08), (72, .16), (76, .24)]:
        pluck(note, 12.5+offset, .10, (note-68)/20, 3.4)

    # Stereo early reflections, then a short diffuse tail.
    reverberant = atmosphere.copy()
    for delay, gain in [(.071, .22), (.113, .17), (.197, .13), (.311, .10), (.457, .06)]:
        n = round(delay * RATE)
        reverberant[n:] += atmosphere[:-n, ::-1] * gain
    mix = dry + reverberant
    timeline = np.arange(len(mix)) / RATE
    mix *= (np.minimum(timeline/.04, 1) * np.clip((DURATION-timeline)/.65, 0, 1))[:, None]
    mix = np.tanh(mix * 1.5)
    peak = np.max(np.abs(mix))
    mix *= .78 / max(peak, 1e-8)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destination), 'wb') as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes((mix * 32767).astype('<i2').tobytes())
    return {'sample_rate': RATE, 'seconds': DURATION, 'channels': 2,
            'peak_dbfs_before_mastering': float(20*np.log10(np.max(np.abs(mix))))}


if __name__ == '__main__':
    print(compose(Path(__file__).parent/'output'/'soundtrack.wav'))
