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

---

# ITEM 15: Gary's voice with Dia (voice pass 4)

Chatterbox hit a ceiling on Gary: it read the disfluencies ("uh", "..."), but never *performed*
them, and it couldn't laugh or clear its throat. Gary's final voice comes from **Dia**.

| Tool | Role | License |
|---|---|---|
| [Dia-1.6B](https://huggingface.co/nari-labs/Dia-1.6B-0626) (`nari-labs/Dia-1.6B-0626`, Nari Labs), via Hugging Face `transformers` | Dialogue text-to-speech with nonverbal sounds | Apache-2.0 |

### Why it sounds more human

Dia was trained on conversation, not audiobook narration:
- **Nonverbal cues** written in parentheses are performed: `(laughs)`, `(clears throat)`,
  `(sighs)`, `(coughs)`.
- **"uh", "..." and restarts** come out as real hesitation instead of being read stiffly.
- It isn't imitating a reference narrator, so it invents its own loose, casual delivery.

### How Gary's voice was found

1. Gary's opening lines were written as a script with a speaker tag and cues:
   ```
   [S1] Okay, is it... yep. (clears throat) Good morning! Uh, Gary Lindqvist, Coulee Commercial Realty.
   And this is the Brenner Mutual building. Four floors, forty thousand square feet, and, uh... (laughs) folks, it's priced to move.
   ```
2. Generated with `guidance_scale=3.0, temperature=1.8, top_p=0.90, top_k=45` (the high
   temperature keeps the delivery loose) on seeds 1 and 2. **Every seed is a different person.**
   Seed 2 was picked by ear ("perfect for a realtor"). That 10-second take is
   `out/tts_ref/gary_dia.wav`, and it is used as-is for the lobby opening (`L01`).

### Keeping the same voice on every line (`film/voice_dia.py`)

Each new line is generated as a *continuation* of the picked take: Dia gets the take's audio and
its exact transcript, followed by the new line, and only the new audio is kept:

```python
inp = proc(text=[f"[S1] {prompt_transcript} [S1] {new_line}"], audio=[prompt_audio_44k],
           padding=True, return_tensors="pt")
plen = proc.get_audio_prompt_len(inp["decoder_attention_mask"])
out = model.generate(**inp, max_new_tokens=..., guidance_scale=3.0, temperature=1.8, top_p=0.90, top_k=45)
proc.save_audio(proc.batch_decode(out, audio_prompt_len=plen), "line.wav")
```

Then, as in pass 3: Whisper checks the words (cues in parentheses are ignored), up to 3 takes per
line with the best kept (overlong takes, where it rambles, are penalized), the camcorder SoX chain
from `film/voice.py`, and `loudnorm` levelling. Lines that need a laugh or a hesitation get a
Dia-only rewrite in `item15/script.py` (`DIA`).

### The voice drifts, so check it

Continuing from a voice prompt is not a lock: about half of the first pass came out sounding like a
slightly different man. Since nobody can listen to 38 lines on every run, every take is also scored
with a **speaker encoder** (Chatterbox's `VoiceEncoder`, `film/spk_sim.py`): cosine similarity of
the take to the picked Gary take. Calibrated on Gary: clips of the same voice score about 0.95 (3 s)
or 0.85 (1.2 s); a different Dia voice scores about 0.70 (3 s) or 0.62 (1.2 s).

- **Long lines (2.5 s or more) that drifted** are voice-converted onto the Gary take with
  `ChatterboxVC` (`film/vc_to.py`). That keeps Dia's delivery, laughs and timing and pulls the
  timbre back (B01 went from 0.56 to 0.85, C03 from 0.71 to 0.90). The words are re-checked
  with Whisper afterwards.
- **Short lines** come out garbled from voice conversion ("Even comes with a TV" turned into
  "...for the tule"), so they are re-rolled with new seeds until the voice matches (≥ 0.75).
- **Temperature**: 1.8 found the voice; for continuations 1.4 holds it a little better.
  At 1.0 Dia produced silence.

### Tips

- Keep each generation to about 5–20 s of speech. Longer and it rushes; one or two words alone
  come out garbled (the voice prompt helps here, since the model has context).
- Generate several seeds and pick the voice by ear. Metrics picked a worse voice once already.
- CPU: about 1–4 minutes per line. With an NVIDIA GPU, seconds.

### Reproducing

```bash
python3 -m venv /home/user/tts/dia
/home/user/tts/dia/bin/pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
/home/user/tts/dia/bin/pip install transformers soundfile descript-audio-codec faster-whisper num2words librosa
FILM=item15 /home/user/tts/dia/bin/python film/voice_dia.py      # or pass line ids
FILM=item15 python3 film/build.py
```

The shared helpers (Whisper word scoring, word stretch, camcorder treatment, levelling) live in
`film/vo_common.py`, used by both `voice3.py` and `voice_dia.py`.

### Asking another AI to do this

> Use the open-source Dia TTS model (nari-labs/Dia-1.6B-0626) through Hugging Face transformers.
> Write the lines with [S1] tags and nonverbal cues like (laughs), (clears throat), "uh" and "...".
> Use temperature 1.8, guidance_scale 3.0, top_p 0.9, top_k 45. Generate several seeds so I can
> pick a voice by ear, then use the picked take plus its transcript as an audio prompt so every
> later line keeps that voice. Check each line with Whisper.
