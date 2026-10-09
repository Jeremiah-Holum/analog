# Voice prompts (Dia-1.6B)

Takes picked by ear, kept here so they survive the build machine. To use one, give Dia the audio
plus its exact transcript, then the new line (see `film/VOICE.md`, "Keeping the same voice").

| File | Who | Dia seed | Notes |
|---|---|---|---|
| `gary.wav` | Gary Lindqvist, ITEM 15 | 2 | "Absolutely amazing... perfect for a realtor." |
| `paul.wav` | Paul Voss, caller in ITEM 20 | 8 (no prompt) | "Is this... Young man. You need to get back in that elevator, and you need to go home." |
| `denny.wav` | next voice (Denny Szabo, ITEM 20) | 1 | Picked for the next film. |

Both were generated (temperature 1.8, guidance 3.0, top_p 0.90, top_k 45) from this transcript:

```
[S1] Okay, is it... yep. (clears throat) Good morning! Uh, Gary Lindqvist, Coulee Commercial Realty.
And this is the Brenner Mutual building. Four floors, forty thousand square feet, and, uh... (laughs) folks, it's priced to move.
```
