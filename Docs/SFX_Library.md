# SFX Library — Safar Pahad Parivar

All sounds are built by `Source/sfx/sfx_gen.py` — identical on every PC, so they are **not stored in git**.
Build or rebuild them with `.\Tools\make_sfx.ps1` (first run ≈10 min incl. a one-time ~850 MB download of recorded strings) → `<kit>\SFX\`.
48 kHz / 24-bit stereo WAV.

Three styles:
- **Strings** (folders 13–15 and `Strings_` stings) — real recorded orchestra: violin / viola / cello sections, solo violin, contrabass,
  harp, timpani, gong, cymbal swells, Nepalese bells. Warm and emotional, built in D major / D pentatonic so the sounds fit together.
  Recordings: *VSCO-2 Community Edition* by Versilian Studios (CC0 public domain — free for YouTube, no credit required).
- **Grand** (folders 09–12 and `Grand_` stings) — deep, cinematic synth: sub-bass, taiko/dhol, braams, gongs, ransingha horn with valley echo, drones.
- **Light** (folders 01–08) — playful UI sounds, ticks, pops, marimba, plus nature beds and phone sounds.

- **vNN** = variations of the same idea, so repeated moments don't sound identical.
- **LOOP_Ns** = seamless loop (the end joins the start) → use **SFX - Loop Fill (In to Out)** for any length.
- Levels: one-shots peak −3 dBFS (title kits −5 to −8 so they sit under the VO); beds ~−24 dB RMS.
- **Title Kits** (01, 09, 13) are timed to the SPP titles — **SFX - Auto Sound for Titles** places them (choose Strings / Grand / Light / Mix).
- Listen: `Docs/SPP_SFX_Strings_Demo.mp3`, `Docs/SPP_SFX_Grand_Demo.mp3`, `Docs/SPP_SFX_Demo_Reel.mp3`.


## 01 Title Kits

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

## 02 UI

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Pop` | 6 | 0.5 s | Soft pop for items appearing (info-card rows, labels) |
| `SPP_Tick_Soft` | 5 | 0.2 s | Very quiet tick (caption words, small UI changes) |
| `SPP_Click_Mouse` | 3 | 0.1 s | Mouse click (subscribe button on the end card) |
| `SPP_Notification_Bell` | 3 | 2.2 s | Bell 'ding' (subscribe / notification) |
| `SPP_Chime_Arrival` | 5 | 1.7 s | Two-note marimba chime (a stop / place appears) |
| `SPP_Shimmer` | 4 | 2.2 s | Sparkle for reveals (snow, logo, weather icon) |
| `SPP_Swipe` | 5 | 0.2 s | Short UI swipe (text sliding in) |

## 03 Motion

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

## 04 Dial & Mechanics

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

## 05 Map & Travel

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

## 06 Bells & Brand

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Temple_Bell` | 3 | 10.2 s | Mandir ghanta - long bronze bell (spiritual / arrival moments) |
| `SPP_Hand_Bell_Ringing` | 3 | 3.7 s | Small ghanti rung a few times (aarti, temple visit) |
| `SPP_Wind_Chime` | 3 | 5.4 s | Gentle wind chime (calm scenic moments) |
| `SPP_Intro_Sting` | 3 | 6.0 s | Logo sound timed to the SPP intro (put at the intro's first frame) |
| `SPP_EndCard_Sting` | 3 | 3.8 s | End-card sound timed to the SPP end card (first frame) |
| `SPP_Grand_Intro_Sting` | 3 | 8.5 s | GRAND logo sound for the SPP intro (drone rise, dots, bell, braam/horn on the name) |
| `SPP_Grand_EndCard_Sting` | 3 | 8.2 s | GRAND end-card sound (deep swell, bowl, warm low notes) |
| `SPP_Strings_Intro_Sting` | 3 | 8.7 s | STRINGS logo sound for the SPP intro (tremolo while the logo draws, harp dots, bell for the sun, full strings on the name) |
| `SPP_Strings_EndCard_Sting` | 3 | 6.3 s | STRINGS end card: harp, pizz for the boxes, warm chord |

## 07 Nature Beds

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Mountain_Wind` | 3 | loop 30.0 s | Mountain wind: calm / gusty / high-altitude whistle |
| `SPP_Prayer_Flags` | 2 | loop 30.0 s | Wind with prayer flags fluttering |
| `SPP_Mountain_Stream` | 3 | loop 30.0 s | Mountain stream / river |
| `SPP_Light_Rain` | 2 | loop 30.0 s | Light rain |
| `SPP_Night_Crickets` | 2 | loop 30.0 s | Night crickets (camp, village at night) |

## 08 Phone

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

## 09 Grand Title Kits

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Grand_InfoCard_In` | 4 | 6.2 s | GRAND Info Card: deep whoosh, low tom, warm rows, heavy counter, soft boom |
| `SPP_Grand_Title_Out` | 4 | 2.2 s | GRAND title leaving: deep air + sub tail |
| `SPP_Grand_Altitude_In_1_5s` | 3 | 7.2 s | GRAND Altitude Counter (1.5 s count): rising drone, heavy counter, landing hit |
| `SPP_Grand_Altitude_In_2_0s` | 3 | 7.4 s | GRAND Altitude Counter (2.0 s count): rising drone, heavy counter, landing hit |
| `SPP_Grand_Altitude_In_2_5s` | 3 | 8.2 s | GRAND Altitude Counter (2.5 s count): rising drone, heavy counter, landing hit |
| `SPP_Grand_Altitude_In_3_0s` | 3 | 8.7 s | GRAND Altitude Counter (3.0 s count): rising drone, heavy counter, landing hit |
| `SPP_Grand_Altitude_In_4_0s` | 3 | 9.7 s | GRAND Altitude Counter (4.0 s count): rising drone, heavy counter, landing hit |
| `SPP_Grand_Altitude_In_5_0s` | 3 | 10.9 s | GRAND Altitude Counter (5.0 s count): rising drone, heavy counter, landing hit |
| `SPP_Grand_Altitude_In_6_0s` | 3 | 11.7 s | GRAND Altitude Counter (6.0 s count): rising drone, heavy counter, landing hit |
| `SPP_Grand_PeakCallout_In` | 4 | 6.9 s | GRAND Peak Callout: deep bell, low sweep along the line, soft drum on the label |
| `SPP_Grand_PopupTitle_In` | 5 | 6.8 s | GRAND chapter title: braam / taiko+boom / ransingha horn / gong swell / echo hit |
| `SPP_Grand_Credits_In` | 3 | 8.7 s | GRAND credits: slow drone swell with a singing bowl |
| `SPP_Grand_RouteMap_Open` | 3 | 4.0 s | GRAND route map start: deep whoosh, drum, map paper, drone swell |
| `SPP_Grand_Stop_Hit` | 5 | 4.4 s | GRAND route stop: low drum + deep bell (instead of pin pop) |
| `SPP_Grand_Journey_Pulse` | 3 | loop 10.0 s | GRAND loop under the route drawing: slow drum pulse on a low drone |

## 10 Grand Impacts & Swells

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Grand_Braam` | 5 | 7.9 s | Low brass braam (big reveals, a massive peak on screen) |
| `SPP_Grand_Taiko_Hit` | 5 | 3.9 s | Big taiko-style drum hit |
| `SPP_Grand_Sub_Boom` | 4 | 7.7 s | Deep sub boom (cut to a wide mountain shot) |
| `SPP_Grand_Echo_Boom` | 3 | 6.8 s | Boom that echoes across the valley |
| `SPP_Grand_Whoosh_In` | 4 | 4.1 s | Deep, slow whoosh into a moment (1.5-3 s) |
| `SPP_Grand_Whoosh_Out` | 4 | 3.2 s | Deep whoosh leaving |
| `SPP_Grand_Riser_Hit` | 3 | 10.3 s | Low riser that lands on a big hit (hit at 4.0 s) |
| `SPP_Grand_Reverse_Swell` | 3 | 2.5 s | Deep reverse swell (lands at the end, 2.5 s) |

## 11 Grand Bells & Horns

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Grand_Gong` | 3 | 13.6 s | Big gong / tam-tam swell (10 s) |
| `SPP_Grand_Temple_Bell_Deep` | 3 | 13.2 s | Very deep mandir bell (10 s tail) |
| `SPP_Grand_Singing_Bowl` | 3 | 12.7 s | Singing bowl, long and calm (monastery, sunrise) |
| `SPP_Grand_Ransingha_Call` | 4 | 6.3 s | Himalayan copper horn call with valley echo (Kumaoni ransingha style) |

## 12 Grand Drones & Drums

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Grand_Drone` | 4 | loop 30.0 s | Cinematic low drone bed: warm D / hopeful Dmaj9 / dark / airy fifths |
| `SPP_Grand_Dhol_Pulse` | 3 | loop 10.7 s | Slow dhol-damau style drum pattern (journey, festival, procession) |
| `SPP_Grand_Heavy_Gears` | 3 | loop 10.0 s | Heavy, slow mechanism loop (big dial turning) |
| `SPP_Grand_Mountain_Air` | 3 | loop 30.0 s | Vast mountain air: deep wind with a low sub presence |

## 13 Strings Title Kits

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Strings_InfoCard_In` | 4 | 5.1 s | STRINGS Info Card: harp flourish, pizzicato rows, spiccato counter, violin settle |
| `SPP_Strings_Title_Out` | 4 | 3.8 s | STRINGS title leaving: soft falling harp / pizz |
| `SPP_Strings_Altitude_In_1_5s` | 3 | 7.2 s | STRINGS Altitude Counter (1.5 s): tremolo climbs with the count, spiccato counter, timpani + chord landing |
| `SPP_Strings_Altitude_In_2_0s` | 3 | 7.7 s | STRINGS Altitude Counter (2.0 s): tremolo climbs with the count, spiccato counter, timpani + chord landing |
| `SPP_Strings_Altitude_In_2_5s` | 3 | 8.0 s | STRINGS Altitude Counter (2.5 s): tremolo climbs with the count, spiccato counter, timpani + chord landing |
| `SPP_Strings_Altitude_In_3_0s` | 3 | 8.7 s | STRINGS Altitude Counter (3.0 s): tremolo climbs with the count, spiccato counter, timpani + chord landing |
| `SPP_Strings_Altitude_In_4_0s` | 3 | 9.7 s | STRINGS Altitude Counter (4.0 s): tremolo climbs with the count, spiccato counter, timpani + chord landing |
| `SPP_Strings_Altitude_In_5_0s` | 3 | 10.5 s | STRINGS Altitude Counter (5.0 s): tremolo climbs with the count, spiccato counter, timpani + chord landing |
| `SPP_Strings_Altitude_In_6_0s` | 3 | 11.7 s | STRINGS Altitude Counter (6.0 s): tremolo climbs with the count, spiccato counter, timpani + chord landing |
| `SPP_Strings_PeakCallout_In` | 4 | 4.0 s | STRINGS Peak Callout: harp rising to a high violin note, pizz on the label |
| `SPP_Strings_PopupTitle_In` | 5 | 5.0 s | STRINGS chapter title: swell+timpani / tremolo into stab / solo violin phrase / cello+gong / harp into chord |
| `SPP_Strings_Credits_In` | 3 | 8.1 s | STRINGS credits: warm string chord swell with harp |
| `SPP_Strings_RouteMap_Open` | 3 | 6.6 s | STRINGS route map start: cymbal swell, harp, low cello |
| `SPP_Strings_Stop_Hit` | 5 | 4.1 s | STRINGS route stop: pizzicato chord + Nepalese bell (+ soft timpani) |
| `SPP_Strings_Journey` | 3 | loop 10.0 s | STRINGS travel ostinato (spiccato violins + cello pizz, 96 bpm) - loops under the route drawing |

## 14 Strings Hits & Swells

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Strings_Swell` | 5 | 7.1 s | String-section swell (grows then fades) - scenic reveals |
| `SPP_Strings_Tremolo_Riser` | 3 | 7.3 s | Tremolo strings rising into a hit (hit at 4.0 s) |
| `SPP_Strings_Stab` | 4 | 3.7 s | Short full-strings stab with timpani |
| `SPP_Timpani_Hit` | 4 | 0.9 s | Real timpani hit |
| `SPP_Timpani_Roll` | 3 | 13.7 s | Real timpani roll (crescendo) |
| `SPP_Gong_Hit` | 4 | 29.4 s | Real orchestral gong |
| `SPP_Bass_Drum` | 4 | 1.6 s | Real orchestral bass drum hit |
| `SPP_Cymbal_Swell` | 3 | 15.0 s | Cymbal crescendo (real) - peaks at its end, cut on it |
| `SPP_Solo_Violin_Phrase` | 6 | 5.0 s | Short pahadi-flavoured solo violin phrases (emotional moments) |

## 15 Strings Beds & Bells

| Sound | Variations | Length | Use |
|---|---|---|---|
| `SPP_Strings_Pad` | 4 | loop 30.0 s | Sustained string bed: warm D / tender Bm / open G / hopeful A |
| `SPP_Cello_Drone` | 2 | loop 30.0 s | Low cello + contrabass drone (awe, vastness) |
| `SPP_Harp_Gliss` | 4 | 4.6 s | Harp glissando up / down (reveals, transitions) |
| `SPP_Nepalese_Bells` | 6 | 2.1 s | Real Nepalese bells (arrivals, monastery, sparkle) |
| `SPP_Pizzicato_Pop` | 6 | 1.1 s | Pizzicato 'pop' (organic replacement for UI pops) |

**480 files, 142 sounds.**
