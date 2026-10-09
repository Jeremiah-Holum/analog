# Running the pipeline on a GPU PC (Windows 11 + NVIDIA)

The cloud machine this was built on has 4 CPU cores and no GPU: a Dia voice line takes 3–10 minutes and
a 38-second shot takes over an hour. On an NVIDIA card both drop to seconds or minutes. These steps
reproduce the same Linux environment inside WSL2, so every path in the code works unchanged.

## 1. Check the card (PowerShell)

```powershell
nvidia-smi                      # driver 535 or newer; note the GPU name and VRAM (8 GB+ is plenty)
wsl --install -d Ubuntu-22.04   # skip if Ubuntu is already installed; reboot if it asks
```

## 2. Ubuntu (inside WSL)

```bash
nvidia-smi                      # must show the card here too (WSL gets the Windows driver; install no driver in Ubuntu)
sudo mkdir -p /home/user && sudo chown $USER /home/user      # the code expects /home/user/...
sudo apt update && sudo apt install -y git ffmpeg sox libsox-fmt-all fonts-dejavu python3-venv python3-pip \
    python3-numpy python3-pil libxi6 libxkbcommon0 libxrender1 libgl1 libsm6 xz-utils wget
```

Blender 4.0.2 (the version everything was made with):

```bash
cd /home/user
wget https://download.blender.org/release/Blender4.0/blender-4.0.2-linux-x64.tar.xz
tar xf blender-4.0.2-linux-x64.tar.xz
sudo ln -sf /home/user/blender-4.0.2-linux-x64/blender /usr/local/bin/blender
blender -b --python-expr "import bpy; p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='OPTIX'; p.get_devices(); print([d.name for d in p.devices])"
```

The last line should list the GPU. (If OptiX isn't available under WSL, `GPU=CUDA` below works too.)

## 3. The project

```bash
git clone https://github.com/jeremiah-holum/analog /home/user/analog
cd /home/user/analog && git checkout claude/friendly-tesla-f6rbrh
```

## 4. Voice environments

```bash
# Dia (voices) with CUDA PyTorch
python3 -m venv /home/user/tts/dia
/home/user/tts/dia/bin/pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
/home/user/tts/dia/bin/pip install transformers==5.17.0 soundfile descript-audio-codec faster-whisper num2words librosa
/home/user/tts/dia/bin/python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"

# Chatterbox (speaker check + voice conversion)
python3 -m venv /home/user/tts/cb
/home/user/tts/cb/bin/pip install chatterbox-tts==0.1.7 librosa
```

The scripts pick the GPU automatically when PyTorch sees one (`DEVICE=cpu` forces the CPU).
Whisper stays on the CPU on purpose: it's small, and it avoids a cuDNN install.

## 5. Make ITEM 20

```bash
cd /home/user/analog/film
# a) Irene's voice: audition a few seeds, LISTEN to them (they're in /home/user/tts/irene), pick an older woman
/home/user/tts/dia/bin/python dia_audition.py /home/user/tts/irene \
  "Is this... am I on? (clears throat) Young man. You need to get back in that elevator, and you need to go home." 1 2 3 4 5 6 7 8
cp /home/user/tts/irene/seedN.wav ../voices/irene.wav          # N = the one picked by ear

# b) every line (Denny, Irene, Gary), checked by Whisper and the speaker encoder
FILM=item20 /home/user/tts/dia/bin/python voice_dia.py

# c) renders on the GPU (stills + the three moving shots)
cd .. && GPU=1 FILM=item20 blender -b -P film/render.py -- \
  n_hall_a n_hall_b n_gary_a n_gary_b n_door_lit n_door_dark n_door_fig n_open n_approach n_count

# d) synth sounds, then the edit
FILM=item20 python3 item20/sounds.py
FILM=item20 python3 film/build.py           # -> out_item20/item20.mp4; watch for "runs past the cut" warnings

# e) phone + YouTube copies, then push
cd out_item20 && P=/tmp/p20
ffmpeg -y -i item20.mp4 -c:v libx264 -preset slow -b:v 330k -pass 1 -passlogfile $P -an -f mp4 /dev/null
ffmpeg -y -i item20.mp4 -c:v libx264 -preset slow -b:v 330k -pass 2 -passlogfile $P -c:a aac -b:a 96k -movflags +faststart item20_phone.mp4
ffmpeg -y -i item20.mp4 -vf "scale=1440:1080:flags=lanczos" -c:v libx264 -preset medium -b:v 2300k -pass 1 -passlogfile $P -an -f mp4 /dev/null
ffmpeg -y -i item20.mp4 -vf "scale=1440:1080:flags=lanczos" -c:v libx264 -preset medium -b:v 2300k -pass 2 -passlogfile $P -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart item20_youtube.mp4
cd .. && cp out_item20/item20_phone.mp4 renders/item20.mp4 && cp out_item20/item20_youtube.mp4 renders/item20_youtube.mp4
git add voices/irene.wav renders/item20*.mp4 && git commit -m "ITEM 20: rendered on the GPU PC" && git pull --no-rebase && git push
```

Keep the YouTube file under 100 MB (GitHub's limit); lower `2300k` if needed.
Shared sound effects ship in `assets/sfx`; voice prompts in `voices/`. Nothing else outside git is needed.
