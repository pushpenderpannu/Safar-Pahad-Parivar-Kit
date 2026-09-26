# SFX Library — Safar Pahad Parivar

All sounds are generated from code (`Source/sfx/sfx_gen.py`) — identical on every PC, so they are **not stored in git**.
Build or rebuild them with `.\Tools\make_sfx.ps1` (≈1 min, ~300 MB) → `<kit>\SFX\`.  48 kHz / 24-bit stereo WAV.

- **vNN** = variations of the same idea, so repeated moments don't sound identical.
- **LOOP_Ns** = seamless loop (the end joins the start) → use **SFX - Loop Fill (In to Out)** for any length.
- Levels: one-shots peak −3 dBFS (title kits −6 to −8 so they sit under the VO); beds are ~−24 dB RMS.
- **01 Title Kits** are timed to the SPP titles — **SFX - Auto Sound for Titles** places them for you.


## Title Kits

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_InfoCard_In` | 4 | 2.7 s | SPP Info Card: slide-in, rows, rolling numbers, settle (clip start) |
| `SPP_Title_Out` | 4 | 0.9 s | Any SPP title leaving (0.6 s before its end) |
| `SPP_Altitude_In_1_5s` | 2 | 3.3 s | SPP Altitude Counter with Count Duration 1.5 s: box in, counter rolls, lands |
| `SPP_Altitude_In_2_0s` | 2 | 3.9 s | SPP Altitude Counter with Count Duration 2.0 s: box in, counter rolls, lands |
| `SPP_Altitude_In_2_5s` | 2 | 4.4 s | SPP Altitude Counter with Count Duration 2.5 s: box in, counter rolls, lands |
| `SPP_Altitude_In_3_0s` | 2 | 4.9 s | SPP Altitude Counter with Count Duration 3.0 s: box in, counter rolls, lands |
| `SPP_Altitude_In_4_0s` | 2 | 5.9 s | SPP Altitude Counter with Count Duration 4.0 s: box in, counter rolls, lands |
| `SPP_Altitude_In_5_0s` | 2 | 6.9 s | SPP Altitude Counter with Count Duration 5.0 s: box in, counter rolls, lands |
| `SPP_Altitude_In_6_0s` | 2 | 7.9 s | SPP Altitude Counter with Count Duration 6.0 s: box in, counter rolls, lands |
| `SPP_PeakCallout_In` | 4 | 2.0 s | SPP Peak Callout: marker ping, line draws, label + height |
| `SPP_PopupTitle_In` | 4 | 2.2 s | SPP Pop-up Title: soft hit, text swipe, sparkle |
| `SPP_Credits_In` | 3 | 3.7 s | SPP Credits: soft swell, heading chime, gentle line ticks |
| `SPP_RouteMap_Open` | 3 | 1.6 s | SPP Route Map start: map unfolds + title |
| `SPP_Caption_Word` | 4 | 0.1 s | Barely-there tick per caption word (optional) |

## UI

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Pop` | 6 | 0.5 s | Soft pop for items appearing (info-card rows, labels) |
| `SPP_Tick_Soft` | 5 | 0.2 s | Very quiet tick (caption words, small UI changes) |
| `SPP_Click_Mouse` | 3 | 0.1 s | Mouse click (subscribe button on the end card) |
| `SPP_Notification_Bell` | 3 | 2.2 s | Bell 'ding' (subscribe / notification) |
| `SPP_Chime_Arrival` | 5 | 1.7 s | Two-note marimba chime (a stop / place appears) |
| `SPP_Shimmer` | 4 | 2.2 s | Sparkle for reveals (snow, logo, weather icon) |
| `SPP_Swipe` | 5 | 0.2 s | Short UI swipe (text sliding in) |

## Motion

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Whoosh_Short_In` | 4 | 1.1 s | Short whoosh, builds into the moment |
| `SPP_Whoosh_Short_Out` | 4 | 1.0 s | Short whoosh, leaves from the moment |
| `SPP_Whoosh_Medium_In` | 4 | 1.5 s | Medium whoosh, builds into the moment |
| `SPP_Whoosh_Medium_Out` | 4 | 1.2 s | Medium whoosh, leaves from the moment |
| `SPP_Whoosh_Long_In` | 4 | 2.0 s | Long whoosh, builds into the moment |
| `SPP_Whoosh_Long_Out` | 4 | 1.7 s | Long whoosh, leaves from the moment |
| `SPP_Swish_Pan` | 4 | 0.3 s | Fast left-right swish (whip pans, quick cuts) |
| `SPP_Riser_2s` | 3 | 3.3 s | 2-second riser that peaks at the end (cut on the peak) |
| `SPP_Riser_4s` | 3 | 5.3 s | 4-second riser that peaks at the end (cut on the peak) |
| `SPP_Riser_6s` | 3 | 7.3 s | 6-second riser that peaks at the end (cut on the peak) |
| `SPP_Reverse_Swell` | 3 | 1.6 s | Reverse-cymbal style swell into a title (1.5 s) |
| `SPP_Impact_Soft` | 4 | 3.7 s | Warm soft impact for a title / logo landing |
| `SPP_Boom_Cinematic` | 2 | 6.4 s | Deep cinematic boom (use sparingly - chapter starts) |

## Dial & Mechanics

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Dial_Tick` | 6 | 0.1 s | Single dial / counter tick |
| `SPP_Odometer_Roll_1_0s` | 3 | 1.5 s | Counter rolls and settles over 1.0 s (matches the titles' count-up) |
| `SPP_Odometer_Roll_1_5s` | 3 | 2.0 s | Counter rolls and settles over 1.5 s (matches the titles' count-up) |
| `SPP_Odometer_Roll_2_0s` | 3 | 2.5 s | Counter rolls and settles over 2.0 s (matches the titles' count-up) |
| `SPP_Odometer_Roll_2_5s` | 3 | 3.0 s | Counter rolls and settles over 2.5 s (matches the titles' count-up) |
| `SPP_Odometer_Roll_3_0s` | 3 | 3.5 s | Counter rolls and settles over 3.0 s (matches the titles' count-up) |
| `SPP_Odometer_Roll_4_0s` | 3 | 4.5 s | Counter rolls and settles over 4.0 s (matches the titles' count-up) |
| `SPP_Odometer_Roll_5_0s` | 3 | 5.5 s | Counter rolls and settles over 5.0 s (matches the titles' count-up) |
| `SPP_Odometer_Roll_6_0s` | 3 | 6.6 s | Counter rolls and settles over 6.0 s (matches the titles' count-up) |
| `SPP_Digit_Spin_Stop` | 4 | 1.2 s | Slot-machine digit spin landing (date/time digits) |
| `SPP_Gear_Rotate` | 4 | loop 10.0 s | Seamless gear / odometer turning loop |
| `SPP_Clock_Ticking` | 3 | loop 10.0 s | Clock tick-tock loop (1 Hz, time passing) |
| `SPP_Clock_Timelapse` | 3 | loop 10.0 s | Fast clock loop for time-lapses / running clock |
| `SPP_Ratchet` | 4 | 0.6 s | Short ratchet / crank (map pin set, dial lock) |

## Map & Travel

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Map_Unfold` | 4 | 1.6 s | Paper map unfolding (route map opens) |
| `SPP_Map_Fold` | 3 | 1.2 s | Paper map folding away |
| `SPP_Pen_Draw` | 3 | loop 10.0 s | Pencil drawing on paper loop (route line drawing) |
| `SPP_Dotted_Trail` | 3 | loop 10.0 s | Soft dotted-path taps loop (dotted route drawing) |
| `SPP_Pin_Drop` | 5 | 0.7 s | Map pin drops and bounces (a stop appears) |
| `SPP_Map_Zoom_In` | 3 | 1.7 s | Camera zooms into the map |
| `SPP_Map_Zoom_Out` | 3 | 1.4 s | Camera pulls back to the whole route |
| `SPP_Travel_Motion` | 3 | loop 10.0 s | Gentle moving-air bed while the route draws |
| `SPP_Camera_Shutter` | 3 | 0.3 s | Camera shutter (photo moments, freeze frames) |

## Bells & Brand

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Temple_Bell` | 3 | 10.2 s | Mandir ghanta - long bronze bell (spiritual / arrival moments) |
| `SPP_Hand_Bell_Ringing` | 3 | 3.7 s | Small ghanti rung a few times (aarti, temple visit) |
| `SPP_Wind_Chime` | 3 | 5.4 s | Gentle wind chime (calm scenic moments) |
| `SPP_Intro_Sting` | 3 | 6.0 s | Logo sound timed to the SPP intro (put at the intro's first frame) |
| `SPP_EndCard_Sting` | 3 | 3.8 s | End-card sound timed to the SPP end card (first frame) |

## Nature Beds

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Mountain_Wind` | 3 | loop 30.0 s | Mountain wind: calm / gusty / high-altitude whistle |
| `SPP_Prayer_Flags` | 2 | loop 30.0 s | Wind with prayer flags fluttering |
| `SPP_Mountain_Stream` | 3 | loop 30.0 s | Mountain stream / river |
| `SPP_Light_Rain` | 2 | loop 30.0 s | Light rain |
| `SPP_Night_Crickets` | 2 | loop 30.0 s | Night crickets (camp, village at night) |

## Phone

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Ringback_India` | 1 | loop 12.0 s | Indian ringback tone the caller hears (400 Hz, 0.4-0.2-0.4-2.0 s) |
| `SPP_Dial_Tone_India` | 1 | loop 6.0 s | Indian dial tone (continuous 400 Hz x 25 Hz) |
| `SPP_Busy_Tone_India` | 1 | loop 6.0 s | Indian busy tone (0.75 s on / off) |
| `SPP_Call_Ended_Beeps` | 2 | 1.6 s | Call disconnected beeps |
| `SPP_Keypad_Dialing` | 3 | 3.7 s | Dialing a 10-digit number on a keypad (DTMF tones) |
| `SPP_Ringtone` | 4 | loop 6.0 s | Original mobile ringtone melodies (marimba / bell) |
| `SPP_Vibrate` | 3 | loop 6.0 s | Phone vibrating on a table (loop) |
| `SPP_Pickup` | 3 | 0.7 s | Picking up the call (handset click, line opens) |
| `SPP_Hangup` | 3 | 0.3 s | Hanging up (click, line cuts) |
| `SPP_Message_Ping` | 4 | 0.9 s | Incoming message ping (original) |
| `SPP_Line_Noise` | 2 | loop 10.0 s | Phone line hiss / static bed under a phone voice |

**249 files, 78 sounds.**
