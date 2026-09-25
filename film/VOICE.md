# How the voices in THE THIRD FLOOR were made

Every spoken line in the film is synthetic. There were no human voice actors in the
production. This file covers what was used, how the lines were made to sound like a real,
frightened night guard recorded on a 1994 camcorder, and what didn't work along the way.

## Tools

| Tool | Role | License |
|---|---|---|
| [Chatterbox](https://github.com/resemble-ai/chatterbox) 0.1.7 (Resemble AI) | Text-to-speech with zero-shot voice cloning and an "exaggeration" (emotion) control; also its voice converter (`ChatterboxVC`) | MIT |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper), `small.en` model | Speech recognition, used to check every take and to find word timings | MIT |
| [librosa](https://librosa.org) 0.11 (pYIN pitch tracker) | Pitch and loudness measurements used to reject unnatural takes | ISC |
| [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) via kokoro-onnx | Reference voice for the facilities memo (`bm_george`) | Apache-2.0 |
| SoX, FFmpeg | Camcorder-mic treatment, per-word time stretch, loudness levelling | GPL/LGPL |

Everything runs on CPU in about 30–50 minutes for the whole script.

## Source voices

- **Dale (every line except the yell):** about 20 s of **LibriTTS-R** test-clean speaker **8455**
  ([mythicinfinity/libritts_r](https://huggingface.co/datasets/mythicinfinity/libritts_r)).
  These are LibriVox volunteer audiobook narrations, restored to 24 kHz. Five deep male narrators
  were auditioned reading the same line, and #8455 was picked by ear.
  *License: CC BY 4.0. Credit: LibriTTS-R (Koizumi et al., 2023), derived from LibriTTS / LibriVox.*
- **The yell ("Hey! Hey! This floor's closed!"):** performed from real shouted speech by
  **RAVDESS Actor 21** (strong-intensity "angry" and "fearful" takes), then voice-converted into Dale.
  *License: CC BY-NC-SA 4.0 ([Livingstone & Russo, 2018](https://zenodo.org/records/1188976)).*
  **Because of this one line, the film as it stands is for non-commercial use.** Replace line
  `F02` (for example with a real recording) before any commercial release.
- **The facilities memo:** Chatterbox cloned from a Kokoro `bm_george` reference, low exaggeration,
  then pitched down and run through an old-tape filter.

## The pipeline (`film/voice3.py`)

For each line in `film/script.py`:

1. **One reference voice, low emotion.** Every Dale line is cloned from the same reference with
   Chatterbox exaggeration at 0.40–0.45. The fear comes from the writing and the processing, not
   from the model overacting.
2. **Up to 4 takes, scored automatically.** Each take is scored on two things:
   - **Words:** Whisper transcribes it, and the transcript is compared with the script. Filler
     words ("uh", "um") and immediate repeats ("I, I") are ignored, because Whisper tends to tidy
     them away. Takes that drop or garble words lose.
   - **Prosody:** librosa's pYIN tracks the pitch. A take is penalized if it swings too widely
     (sing-song), jumps around frame to frame, or ends a statement on a rising pitch (the
     "let's go see the lights?" problem).
   The best take is kept. Most lines pass on the first try.
3. **Drawn-out words.** A word marked with `~` in the script (`"This would be~... ten."`) is found
   with Whisper word timestamps, and only that word is slowed down by 1.9× (SoX `tempo -s`, a
   speech-aware time stretch). The TTS model can't do "beeee..." on its own.
4. **The yell** is generated with the RAVDESS shouting reference at high exaggeration, then passed
   through `ChatterboxVC` so it sounds like Dale.
5. **Door counts** are two continuous takes (Tape 1: 301–309, Tape 2: 301–314), not one
   sentence per number, so they sound like one person counting under his breath. Each take is
   cut at the silences between numbers, every chunk is checked with Whisper, and each number is
   placed at the moment the camera reads that door's plaque.
6. **Camcorder treatment** (SoX, per style in `film/voice.py`): band-limited like a cheap mic
   (about 160 Hz–5 kHz), compressed, with a little room reverb. The yell also gets overdrive and a
   bigger hallway reverb, the way a shout clips a camcorder mic.
7. **Loudness levelling** (FFmpeg `loudnorm`, narrow loudness range), so lines don't fade in and
   out. Calm lines sit at −20 LUFS, scared lines at −21, whispers at −24 and the yell at −15.

In the edit (`film/build.py`), no line is allowed to start before the previous one has finished,
and everything is mixed under tape hiss, fluorescent buzz and room tone.

### The writing matters as much as the model

The script is written to be *spoken*: false starts ("I, uh, I called Pruitt. About the… about the
man."), trailing off, restarts ("That's not… that's not right."), and drawn-out hesitations. The
stumbling increases through the film. Tape 1 is mostly clean; by Tape 4 he trips over nearly every
sentence.

## What didn't work (and why)

| Attempt | Problem |
|---|---|
| **Piper** (`en_US-joe-medium`) | Fast, but flat and obviously robotic. |
| **Chatterbox cloned from a Kokoro voice** | It inherited the AI voice's polished audiobook sound. |
| **Chatterbox cloned from RAVDESS actors** (separate calm/scared/yell references) | The actors only say two short sentences each ("Kids are talking by the door"). With so little variety in the reference, and emotion turned up, the accent drifted and he sounded like a non-native speaker. It got worse as the lines got more emotional. |
| **High exaggeration for scared lines** | Cartoonish delivery ("ItsS Not FiNE!"), and the voice changed character between lines. |
| **A tremolo effect on whispered lines** | Made the voice audibly pulse in and out. Removed. |
| **One separate sentence per door number** | Each number had its own full-stop intonation, so the counting sounded disconnected. |
| **Synthetic "breathing"** (filtered noise) | Sounded like "whoo-shhh", not breath. Removed. |

## Reproducing

```bash
# one-time: Chatterbox + Whisper + librosa in a venv
python3 -m venv /home/user/tts/cb
/home/user/tts/cb/bin/pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
/home/user/tts/cb/bin/pip install chatterbox-tts faster-whisper num2words librosa

# reference voices: out/tts_ref/dale.wav (LibriTTS-R 8455), dale_yell.wav (RAVDESS 21), memo.wav
/home/user/tts/kk/bin/python film/voice_ref.py      # builds the RAVDESS and Kokoro references

# voice everything (or pass line ids, e.g. X03 F02 COUNT2), then rebuild the film
/home/user/tts/cb/bin/python film/voice3.py
python3 film/build.py
```

`film/voice.py` (Piper) and `film/voice2.py` (the earlier Chatterbox passes) are kept for
reference. `voice.py` still holds the per-style SoX chains that `voice3.py` uses.
