# Math
import numpy as np
# Constants
phi = (1 + 5**0.5)/2
# Displays
from scipy.io import wavfile
import librosa
from IPython.display import Audio, display
import pyaudio
# key input
from pynput import keyboard


class Instrument:
    """Instrument emulator class."""
    def __init__(self, harmonics=[1], amps=None, attack=0.1, release=0.6, sample_rate=44100, chunk_size=512):
        # Instrument sound constants
        self.harmonics = np.array(harmonics)
        if amps is None:
            self.amps = np.ones(len(harmonics))
        else:
            self.amps = amps

        assert(len(amps) == len(harmonics), "size of amps does not match freqs or harmonics")
        self.attack = attack
        self.n_attack_samples = attack*sample_rate
        if self.n_attack_samples == 0:
            self.n_attack_samples = 1

        self.release = release
        self.n_release_samples = release*sample_rate
        if self.n_release_samples == 0:
            self.n_attack_samples = 1

        # Audio constants
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size

        # Sound emulation auxiliary variables
        self.time_offset = 0
        self.buffer_time_lapse = chunk_size/sample_rate
        self.time_chunk = np.linspace(0, self.buffer_time_lapse, chunk_size, endpoint=False)
        self.pressed_keys = {}
        self.releasing_keys = {}

        self.octave = 1


    class Note:
        # Note representation containing frequency and amplitude
        def __init__(self, fundamental, amp):
            self.fundamental = fundamental
            self.amp = amp

        def __repr__(self):
            return f"Note({self.fundamental}, {self.amp})"

    def _init_stream(self):
        # Initialize the Stream object
        self.stream = pyaudio.PyAudio().open(
            rate=self.sample_rate,
            channels=1,
            format=pyaudio.paFloat32,
            output=True,
            frames_per_buffer=self.chunk_size
        )

    def _key_to_freq(self, in_key):
        if in_key == 'z':
            self.octave /= 2
        elif in_key == 'x':
            self.octave *= 2
        elif in_key == 'a':
            return 261.63
        elif in_key == 'w':
            return 277.18
        elif in_key == 's':
            return 293.66
        elif in_key == 'e':
            return 311.13
        elif in_key == 'd':
            return 329.63
        elif in_key == 'f':
            return 349.23
        elif in_key == 't':
            return 369.99
        elif in_key == 'g':
            return 392.00
        elif in_key == 'y':
            return 415.30
        elif in_key == 'h':
            return 440.00
        elif in_key == 'u':
            return 466.16
        elif in_key == 'j':
            return 493.88
        elif in_key == 'k':
            return 523.25
        elif in_key == 'o':
            return 554.37
        elif in_key == 'l':
            return 587.33
        elif in_key == 'p':
            return 622.25
        elif in_key == 'ñ':
            return 659.25

    def _generate_sound_chunk(self, fundamental):
        chunk = np.zeros(self.chunk_size)
        times = self.time_chunk + self.time_offset
        for f, a in zip(fundamental*self.harmonics, self.amps):
            chunk += a*np.sin(2*np.pi*f*times)

        return chunk

    def _generate_pressed_sound(self):
        chunk = np.zeros(self.chunk_size)
        for key in list(self.pressed_keys):
            try:
                note = self.pressed_keys[key]
                key_chunk = self._generate_sound_chunk(note.fundamental)
                if note.amp < 1:
                    amp_end = note.amp + self.chunk_size/self.n_attack_samples
                    attack_envelope = np.linspace(note.amp, amp_end, self.chunk_size, endpoint=False)
                    key_chunk = np.multiply(key_chunk, attack_envelope)
                    note.amp = amp_end
                    if note.amp >= 1:
                        note.amp = 1

                chunk += key_chunk
            except KeyError: # sometimes key is deleted or not properly added when pressed
                pass

        return chunk

    def _generate_releasing_sound(self):
        chunk = np.zeros(self.chunk_size)
        for key in list(self.releasing_keys):
            try:
                note = self.releasing_keys[key]
                if note.amp > 0:
                    key_chunk = self._generate_sound_chunk(note.fundamental)
                    amp_end = note.amp - self.chunk_size/self.n_attack_samples
                    attack_envelope = np.linspace(note.amp, amp_end, self.chunk_size, endpoint=False)
                    key_chunk = np.multiply(key_chunk, attack_envelope)
                    note.amp = amp_end
                    chunk += key_chunk
                else:
                    del self.releasing_keys[key]

            except KeyError: # sometimes key is deleted or not properly added when pressed
                pass

        return chunk

    def key_press(self, in_key):
        fundamental = self.octave*self._key_to_freq(in_key)
        if fundamental:
            self.pressed_keys[in_key] = self.Note(fundamental=fundamental, amp=0)

    def key_release(self, in_key):
        fundamental = self._key_to_freq(in_key)
        if fundamental:
            self.releasing_keys[in_key] = self.Note(fundamental=self.pressed_keys[in_key].fundamental, amp=self.pressed_keys[in_key].amp)
            del self.pressed_keys[in_key]

    def emit_sound(self):
        self._init_stream()
        try:
            while True:
                if (not self.pressed_keys) and (not self.releasing_keys):
                    # no key is being played of released
                    self.time_offset = 0
                else:
                    chunk = np.zeros(self.chunk_size)
                    chunk += self._generate_pressed_sound() + self._generate_releasing_sound()
                    self.time_offset += self.buffer_time_lapse
                    if self.time_offset > 360: # Restart offset
                        self.time_offset = 0

                    self.stream.write(chunk.astype(np.float32).tobytes())

        except KeyboardInterrupt as err:
            self.stream.close()

##########################################

if __name__ == "__main__":

    # Declare instrument Fibonizer2
    nf2 = 8
    harmonics = [phi**k for k in range(0,nf2)]
    amps = np.power(np.reciprocal(harmonics),1)

    Fibonizer2 = Instrument(harmonics=harmonics, amps=amps)

    pressed = set() # set holding pressed keys so that holding one down does not trigger on_press multiple times.

    # Init key listening
    def on_press(key):
        if key not in pressed:
            pressed.add(key)
            try:
                Fibonizer2.key_press(key.char)
            except:
                try:
                    if key.name == 'ctrl':
                        return False
                except:
                    pass

    def on_release(key):
        pressed.discard(key)
        try:
            Fibonizer2.key_release(key.char)
        except:
            pass

    # Collect events until released
    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release)
    listener.start()

    # start playing
    print('ready to play')
    Fibonizer2.emit_sound()
