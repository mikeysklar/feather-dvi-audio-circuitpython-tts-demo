# Moonshine Klatt speech through supervisor.runtime.audio.
# Klatt renders at 22050 Hz and DVI audio is 48 kHz only, so a Resampler sits between them.
import gc
import time

import audiomixer
import audiospeed
import supervisor

import adafruit_moonshine_klatt as speech

fmt = dict(channel_count=1, bits_per_sample=16, samples_signed=True)
out = audiomixer.Mixer(voice_count=1, buffer_size=2048, sample_rate=48000, **fmt)
supervisor.runtime.audio.play(out)
inner = audiomixer.Mixer(voice_count=1, buffer_size=1024, sample_rate=22050, **fmt)
out.voice[0].play(audiospeed.Resampler(inner), loop=True)

tts = speech.TTS(inner.voice[0])
print("free", gc.mem_free())

while True:
    for voice in tts.voices:
        tts.voice = voice
        start = time.monotonic()
        tts.say(f"Hello from Circuit Python. This is the {voice} voice.")
        print(f"{voice}: {time.monotonic() - start:.2f} s")
        time.sleep(1)
    time.sleep(3)
