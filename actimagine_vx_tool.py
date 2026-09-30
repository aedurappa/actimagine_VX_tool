"""
ActImagine VX Encoder/Decoder Tool
Version 1.0
Copyright (C) 2026 aedurappa

Unpack/repack .vx video files (Actimagine codec, used by some Nintendo DS
games) to/from a folder of PNG frames + a WAV audio track.

Usage:
  - Drag a .vx file onto this program (or the built .exe) to unpack it into
    a folder of frame0001.png, frame0002.png, ... + properties.json (+
    fullaudio.wav if the video has audio) next to it.
  - Drag an unpacked folder (one containing properties.json) onto this
    program to repack it back into a new .vx file next to the folder. Any
    *.wav file placed in that folder is used as the audio track
    automatically (fullaudio.wav preferred if present, otherwise the first
    *.wav found).
  - Run with no argument to get a simple picker window for either action.

Based on the ActImagine video codec library by Charles Van Eeckhout
(https://github.com/CharlesVanEeckhout/actimagine), licensed under the GNU
General Public License v3.0. This program is likewise licensed under the
GPL-3.0 -- see LICENSE. Modifications from the original library (2026):
  - package/vframe_encoder_strategies/common/predict_inter.py: fixed a
    missing-argument crash in the four-step motion search, a uint8
    overflow in the DC-offset error calculation, and a DC-offset mismatch
    between the encoder's prediction and the decoder's reconstruction that
    caused severe visual drift/corruption a few dozen frames into any
    inter-predicted video.
  - package/vframe_encoder_strategies/simple_interpredict.py (new): a
    zero-motion DC+residual inter-prediction encoder strategy built on top
    of the library's own (previously unused) predict_inter primitives --
    roughly 2.5x smaller output than the library's original all-keyframe
    strategy, with no visible quality loss.
  - This file (new): a single consolidated entry point combining unpack and
    repack, with drag-and-drop/file-picker support and automatic audio-file
    detection, for building a standalone executable.

This program is distributed WITHOUT ANY WARRANTY, without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
"""
import os
import sys
import glob
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from package.actimagine import ActImagine
from package.vframe_encoder_strategies import SimpleInterPredict, SimpleKeyframeOnly
from package.aframe_encoder_strategies import SimplePulseExtend

VERSION = "1.0"


def log(msg):
    print(msg, flush=True)


def unpack_vx(vx_path):
    vx_path = os.path.abspath(vx_path)
    base = os.path.splitext(os.path.basename(vx_path))[0]
    out_folder = os.path.join(os.path.dirname(vx_path), f"{base}_unpacked")
    os.makedirs(out_folder, exist_ok=True)

    log(f"Unpacking: {vx_path}")
    with open(vx_path, 'rb') as f:
        data = f.read()

    act = ActImagine()
    for i, _ in enumerate(act.load_vx(data)):
        if (i + 1) % 50 == 0:
            log(f"  decoded frame {i+1}/{act.frames_qty}...")
    for i, _ in enumerate(act.export_vxfolder(out_folder)):
        pass
    log(f"Done: {act.frames_qty} frames, {act.frame_width}x{act.frame_height}px, "
        f"{act.frame_rate}fps, {act.audio_streams_qty} audio stream(s)")
    log(f"-> {out_folder}")
    return out_folder


def find_audio_file(folder):
    preferred = os.path.join(folder, 'fullaudio.wav')
    if os.path.isfile(preferred):
        return preferred
    wavs = sorted(glob.glob(os.path.join(folder, '*.wav')))
    return wavs[0] if wavs else None


def repack_vx(folder, output_path=None, use_interpredict=True):
    folder = os.path.abspath(folder)
    if not os.path.isfile(os.path.join(folder, 'properties.json')):
        raise SystemExit(f"Not an unpacked vx folder (no properties.json): {folder}")

    if output_path is None:
        base = os.path.basename(folder.rstrip('\\/'))
        if base.endswith('_unpacked'):
            base = base[:-len('_unpacked')]
        elif base.startswith('temp_'):
            base = base[len('temp_'):]
        output_path = os.path.join(os.path.dirname(folder), f"{base}_repacked.vx")
    output_path = os.path.abspath(output_path)

    audio_path = find_audio_file(folder)
    if audio_path:
        log(f"Audio track detected: {audio_path}")
    else:
        log("No audio file found in folder -- output will be silent.")

    act = ActImagine()
    log(f"Importing: {folder}")
    for i, _ in enumerate(act.import_vxfolder(folder)):
        if (i + 1) % 50 == 0:
            log(f"  read frame {i+1}...")
    log(f"Imported: {act.frames_qty} frames, {act.frame_width}x{act.frame_height}px, "
        f"{act.frame_rate}fps, {act.audio_streams_qty} audio stream(s)")

    vframe_strategy = SimpleInterPredict() if use_interpredict else SimpleKeyframeOnly()
    aframe_strategy = SimplePulseExtend()
    aframe_strategy.init_audio_extradata(act.audio_extradata)
    for i, avframe in enumerate(act.avframes):
        avframe.encode(avframe.vframe.plane_buffers, vframe_strategy, aframe_strategy)
        if (i + 1) % 50 == 0:
            log(f"  encoded frame {i+1}/{act.frames_qty}...")
    log("Encoding complete")

    data_new = act.save_vx()
    with open(output_path, 'wb') as f:
        f.write(bytes(data_new))
    log(f"Done: {len(data_new)/1024/1024:.2f} MB")
    log(f"-> {output_path}")
    return output_path


def process_path(path):
    path = path.strip('"')
    if os.path.isdir(path):
        repack_vx(path)
    elif os.path.isfile(path) and path.lower().endswith('.vx'):
        unpack_vx(path)
    else:
        raise SystemExit(f"Don't know what to do with: {path}\n"
                          "(expected a .vx file to unpack, or an unpacked folder to repack)")


def run_picker_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.title(f"ActImagine VX Tool v{VERSION}")
    root.geometry("360x150")
    root.resizable(False, False)

    def do_unpack():
        path = filedialog.askopenfilename(title="Select a .vx file to unpack",
                                           filetypes=[("VX video", "*.vx"), ("All files", "*.*")])
        if not path:
            return
        try:
            out = unpack_vx(path)
            messagebox.showinfo("Done", f"Unpacked to:\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def do_repack():
        path = filedialog.askdirectory(title="Select an unpacked vx folder to repack")
        if not path:
            return
        try:
            out = repack_vx(path)
            messagebox.showinfo("Done", f"Repacked to:\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Label(root, text=f"ActImagine VX Tool v{VERSION}", font=("Segoe UI", 11, "bold")).pack(pady=(14, 4))
    tk.Label(root, text="Or just drag a .vx file / unpacked folder\nonto this program's icon.",
              fg="#555555", justify="center").pack(pady=(0, 10))
    tk.Button(root, text="Unpack .vx file...", width=28, command=do_unpack).pack(pady=4)
    tk.Button(root, text="Repack folder...", width=28, command=do_repack).pack(pady=4)

    root.mainloop()


def main():
    args = sys.argv[1:]
    if not args:
        run_picker_gui()
        return

    for path in args:
        process_path(path)

    if os.name == 'nt' and sys.stdout.isatty() is False:
        # launched by drag-and-drop (no console kept open by the shell) --
        # pause so the user can read the output before the window closes.
        try:
            input("\nPress Enter to close...")
        except EOFError:
            pass


if __name__ == '__main__':
    main()
