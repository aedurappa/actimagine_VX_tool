"""Minimal 16-bit PCM WAV read/write, matching the subset of scipy.io.wavfile's
interface this project actually uses (read -> (samplerate, np.int16 array),
write(path, samplerate, np.int16 array)). Uses only the standard library
`wave` module -- avoids a scipy dependency (and the packaging headaches that
come with bundling it into a standalone exe) for what is otherwise a single
small feature.
"""
import wave
import numpy as np


def read(path):
    with wave.open(path, 'rb') as w:
        n_channels = w.getnchannels()
        sampwidth = w.getsampwidth()
        samplerate = w.getframerate()
        n_frames = w.getnframes()
        raw = w.readframes(n_frames)
    if sampwidth != 2:
        raise RuntimeError('only 16-bit PCM wav files are supported')
    data = np.frombuffer(raw, dtype=np.int16)
    if n_channels > 1:
        data = data.reshape(-1, n_channels)
    return samplerate, data


def write(path, samplerate, data):
    data = np.asarray(data, dtype=np.int16)
    n_channels = data.shape[1] if data.ndim > 1 else 1
    with wave.open(path, 'wb') as w:
        w.setnchannels(n_channels)
        w.setsampwidth(2)
        w.setframerate(samplerate)
        w.writeframes(data.tobytes())
