# Type something in the serial console; it shows on the DVI screen and is spoken
# through the DVI cable with PicoTTS. Needs a board with PSRAM and board.DVI_AUDIO.
import sys
import time

import audiomixer
import audiospeed
import board
import displayio
import supervisor
import terminalio
from adafruit_display_text import bitmap_label, wrap_text_to_pixels

import adafruit_picotts as speech

# Audio: PicoTTS renders at 16 kHz, DVI audio is 48 kHz, a Resampler joins them.
fmt = dict(channel_count=1, bits_per_sample=16, samples_signed=True)
out = audiomixer.Mixer(voice_count=1, buffer_size=4096, sample_rate=48000, **fmt)
board.DVI_AUDIO.play(out)
inner = audiomixer.Mixer(voice_count=1, buffer_size=4096, sample_rate=16000, **fmt)
out.voice[0].play(audiospeed.Resampler(inner), loop=True)
tts = speech.TTS(inner.voice[0])
tts.volume = 0.5  # default 1.0 sounded over-amplified

# Screen: a small rainbow bitmap scaled up 10x, animated by rotating its palette.
display = supervisor.runtime.display
W, H = display.width, display.height
STEPS = 32


def hue(i):
    h = i * 6 / STEPS
    x = int(255 * (1 - abs(h % 2 - 1)))
    return [(255, x, 0), (x, 255, 0), (0, 255, x), (0, x, 255), (x, 0, 255), (255, 0, x)][
        int(h) % 6
    ]


colors = [(r << 16) | (g << 8) | b for r, g, b in (hue(i) for i in range(STEPS))]
palette = displayio.Palette(STEPS)
bg = displayio.Bitmap(W // 10, H // 10, STEPS)
for y in range(bg.height):
    for x in range(bg.width):
        bg[x, y] = (x + y) % STEPS
background = displayio.Group(scale=10)
background.append(displayio.TileGrid(bg, pixel_shader=palette))

title = bitmap_label.Label(
    terminalio.FONT, text="Type something to say", color=0xFFFFFF,
    background_color=0x000000, padding_left=6, padding_right=6, padding_top=3,
    padding_bottom=3, anchor_point=(0.5, 0), anchored_position=(W // 2, 8),
)
said = bitmap_label.Label(
    terminalio.FONT, text=" ", color=0xFFFF00, background_color=0x000000, scale=2,
    padding_left=8, padding_right=8, padding_top=6, padding_bottom=6,
    anchor_point=(0.5, 0.5), anchored_position=(W // 2, H // 2), line_spacing=1.0,
)

root = displayio.Group()
root.append(background)
root.append(title)
root.append(said)
display.root_group = root


def show(text):
    lines = wrap_text_to_pixels(text, W // 2 - 24, terminalio.FONT)
    said.text = "\n".join(lines[-6:]) or " "


def prompt():
    print("\nType something to say: ", end="")


shift = 0
next_frame = 0
typed = ""
show("Hello!")
tts.say("Hello! Type something and I will say it.", wait=False)
prompt()

while True:
    tts.update()
    now = time.monotonic()
    # Animate only when quiet: a full-screen redraw mid-speech can starve the audio.
    if not tts.speaking and now >= next_frame:
        next_frame = now + 0.08
        shift = (shift + 1) % STEPS
        for i in range(STEPS):
            palette[i] = colors[(i + shift) % STEPS]

    if supervisor.runtime.serial_bytes_available:
        ch = sys.stdin.read(1)
        if ch in "\r\n":
            if typed.strip():
                print()
                show(typed)
                tts.say(typed, wait=False)
                typed = ""
                prompt()
        elif ch in "\x08\x7f":
            if typed:
                typed = typed[:-1]
                print("\b \b", end="")
                show(typed + "_")
        elif ch >= " ":
            typed += ch
            print(ch, end="")
            show(typed + "_")
