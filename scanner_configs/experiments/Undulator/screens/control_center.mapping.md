# HTU Control Center: label-to-device mapping

The evidence behind `control_center.yaml`, one row per control on the LabVIEW
screenshot, grouped and ordered as on the screen (reading order: left to right,
then down, as the group's `columns` lay them out). **For the maintainer to check.**
Corrections go into the screen file (and this table) directly.

## How it was made

- **The source**: `GEECS-BELLA/GEECS-BELLA-GUIs`, `GUI_HTU_Control_Center/GUI_HTU_Control_Center.vi`.
  The VI's zlib blocks were inflated and their strings read (nothing was run).
  Every bound control carries a description string `Variable::N`, where `GUIdevice N`
  names the device; the label precedes it in the front-panel heap. The `.lvproj` and
  `.aliases` name no devices (the latter holds only the host's address).
- **Cross-checks**: the configs repo's scan variables (`scan_devices/scan_variables.yaml`),
  action plans (`action_library/actions.yaml`) and `aux_configs/visa_plunger_lookup.yaml`.
  A variable name is the VI's spelling, except where the action library or the DB spells
  it otherwise (PV names are case-folded anyway).
- **The GEECS DB** (checked afterwards, read only, 2026-10-29): every binding's device,
  variable, alias and the experiment's enablement. Its aliases settled the GAIA sides
  (the first guess had all six amp flippers on the wrong side), the vacuum channels, the
  jet timing and the Visa plunger order; two devices it does not have (Grating Cam,
  Blade Height) are TODOs now; one is disabled (ACave Current).
- **PV names**: `geecs_core.pv_naming.pv_name("Undulator", device, variable)`, the CA
  gateway's readback name. A setpoint binds the readback PV; its write (to `:SP`) goes
  through the module once it writes gateway PVs, and is disabled until then.
- **Confidence**: *high*: the VI string and the label agree, often with an alias or plan;
  *medium*: the device and variable are the VI's, but which control or which side is
  inferred; *low*: a guess the maintainer must confirm; *none*: not bound (a TODO).
- **Dropped**: the EXIT button (the browser tab is the window); struck-through labels
  (in LabVIEW, "device off": a process fact, no meaning here).
- **Not drawn** (in the source, not visible on the screenshot), among others: eight
  `Energy (nJ)` indicators on `U_VacuumGauge AI_mean.Channel 1`, `pockelcellA`/`pockelcellB`
  (U_GaiaSVEReader), `Jet timing (s)` (U_DG645_ShotControl `Delay.Ch C`), a second
  `Amplitude Jet trigger` on U_MRC_TimingBox `Amplitude.Ch AB`, `fire::10`, the hexapod's
  `Step size` controls, the state booleans (`Jet probe stage tck`, `Wedge enable`,
  `Phosphor enable`, `Fire Continues Allowed`), the LED pairs' hidden labels `GSN`/`GSS`,
  and the devices U_PIFinalSteering and U_SSR_2, which no visible control binds.
- **Layout changes** (the format has no spacer): in **Jet timing** LabVIEW stacks Pressure
  and Set opening time as full rows above a row of three buttons (Jet Trigger, Jet Enable,
  Purge) with their indicators (Amplitude, Opening time, auto purge) beneath; here the
  group has 2 columns, so Pressure sits beside Set opening time and each button sits beside
  its indicator. In **Misc area** the in/out note moves after the last row. The
  **Emitspoiler** and **Aline3** buttons, under the Valve Control box in LabVIEW, end it here.
- **Tones**: the LabVIEW colours as kit tokens: blue → `trace-2`, magenta → `trace-1`,
  green → `trace-3`, cyan → `muted`, salmon → `accent`, yellow → `trace-4`,
  lavender → `slate` (in the bella theme `accent` and `trace-1` are the same red).

## Counts

| Widgets | Writes to DB devices (disabled in this slice) | Readouts | Annotations | Images | Not bound (TODO) |
|---|---|---|---|---|---|
| 107 | 83 | 12 | 10 | 2 | 5 |

Annotations include the 5 not-bound controls. TODO: MRC Trigger (GAIA control), Grating Cam (Filters), Blade Height (Jet Stages), Jet Trigger (Jet timing), Jet Enable (Jet timing).

## Also to check

- **Emit spoiler on `U_PLC` DO.Ch9** (rows 65, 78): the DB aliases that channel *ALine2*.
  Check on the hardware which actuator Ch9 drives before its write is enabled.
- **The two plunger dialogs**: which dialog guards Emitspoiler and which guards Aline3
  (each warns about the other, consistent with Ch8/Ch9 being the colliding pair).
- **Grating Cam's wheel and Blade Height's stage**: the VI's devices are not in the DB;
  name the devices that replaced them.
- **ACave Current**: `U_ACaveMagSpecPS` is disabled in the experiment; re-enable it for
  the gateway to serve it.
- **Vacuum calibration**: the VI shows pressure = 10^(V−6); a gateway derived channel
  would carry it (the screen never computes), so the screen shows the raw voltage.
- **`Amplitude.Ch CD::10` objects** sit beside the constants in the Jet Trigger and MRC
  cases and before the four dialog cases (both Gaia shutters, Emitspoiler, Aline3). The
  DB gives `Amplitude.Ch CD` no alias. They read as copied labels, not writes; if they
  are writes, those six controls are multi-step and become TODOs (a screen does not compute).

## The controls

### GAIA control

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | North shutters | annotation | — | — | VI: free label on the panel |
| 2 | South shutters | annotation | — | — | VI: free label on the panel |
| 3 | Gaia stop | flipper | U_148_PLC · `DO.Ch1` → `undulator:u_148_plc:do_ch1`; in/out lamps `undulator:u_148_plc:di_ch1`, `undulator:u_148_plc:di_ch2` | high | VI: label → `DO.Ch1::37`; DB alias *Gaia Stop North*; lamps DI.Ch1/2 by the DO.Ch k ↔ DI.Ch 2k−1 (in), 2k (out) rule, which the action library confirms for DO.Ch1, Ch2, Ch9; insert_gaia_stops sets DO.Ch1+Ch2, checks DI.Ch1+Ch3 (in) |
| 4 | Gaia stop | flipper | U_148_PLC · `DO.Ch2` → `undulator:u_148_plc:do_ch2`; in/out lamps `undulator:u_148_plc:di_ch3`, `undulator:u_148_plc:di_ch4` | high | VI: label → `DO.Ch2::37`; DB alias *Gaia Stop South*; lamps DI.Ch3/4 by the DO.Ch k ↔ DI.Ch 2k−1 (in), 2k (out) rule, which the action library confirms for DO.Ch1, Ch2, Ch9 |
| 5 | Amp2 | flipper | U_148_PLC · `DO.Ch8` → `undulator:u_148_plc:do_ch8`; in/out lamps `undulator:u_148_plc:di_ch15`, `undulator:u_148_plc:di_ch16` | high | VI: label → `DO.Ch8::37`; DB alias *Gaia Amp2 North*; lamps DI.Ch15/16 by the DO.Ch k ↔ DI.Ch 2k−1 (in), 2k (out) rule, which the action library confirms for DO.Ch1, Ch2, Ch9 |
| 6 | Amp2 | flipper | U_148_PLC · `DO.Ch3` → `undulator:u_148_plc:do_ch3`; in/out lamps `undulator:u_148_plc:di_ch5`, `undulator:u_148_plc:di_ch6` | high | VI: label → `DO.Ch3::37`; DB alias *Gaia Amp2 South*; lamps DI.Ch5/6 by the DO.Ch k ↔ DI.Ch 2k−1 (in), 2k (out) rule, which the action library confirms for DO.Ch1, Ch2, Ch9 |
| 7 | Amp3 | flipper | U_148_PLC · `DO.Ch7` → `undulator:u_148_plc:do_ch7`; in/out lamps `undulator:u_148_plc:di_ch13`, `undulator:u_148_plc:di_ch14` | high | VI: label → `DO.Ch7::37`; DB alias *Gaia Amp3 North*; lamps DI.Ch13/14 by the DO.Ch k ↔ DI.Ch 2k−1 (in), 2k (out) rule, which the action library confirms for DO.Ch1, Ch2, Ch9 |
| 8 | Amp3 | flipper | U_148_PLC · `DO.Ch4` → `undulator:u_148_plc:do_ch4`; in/out lamps `undulator:u_148_plc:di_ch7`, `undulator:u_148_plc:di_ch8` | high | VI: label → `DO.Ch4::37`; DB alias *Gaia Amp3 South*; lamps DI.Ch7/8 by the DO.Ch k ↔ DI.Ch 2k−1 (in), 2k (out) rule, which the action library confirms for DO.Ch1, Ch2, Ch9 |
| 9 | Amp4 | flipper | U_148_PLC · `DO.Ch6` → `undulator:u_148_plc:do_ch6`; in/out lamps `undulator:u_148_plc:di_ch11`, `undulator:u_148_plc:di_ch12` | high | VI: label → `DO.Ch6::37`; DB alias *Gaia Amp4 North*; lamps DI.Ch11/12 by the DO.Ch k ↔ DI.Ch 2k−1 (in), 2k (out) rule, which the action library confirms for DO.Ch1, Ch2, Ch9 |
| 10 | Amp4 | flipper | U_148_PLC · `DO.Ch5` → `undulator:u_148_plc:do_ch5`; in/out lamps `undulator:u_148_plc:di_ch9`, `undulator:u_148_plc:di_ch10` | high | VI: label → `DO.Ch5::37`; DB alias *Gaia Amp4 South*; lamps DI.Ch9/10 by the DO.Ch k ↔ DI.Ch 2k−1 (in), 2k (out) rule, which the action library confirms for DO.Ch1, Ch2, Ch9 |
| 11 | MRC Trigger | annotation | **TODO**: none chosen | none | VI: the button has no variable; its event case writes `Amplitude.Ch AB::30` (U_MRC_TimingBox) with the values the VI chooses for on/off. A screen does not compute: bind a two-state role (or an action plan) once one exists |
| 12 | Gaia lamp timing | setpoint | U_1HzShiftedBox · `delay.Channel_C` → `undulator:u_1hzshiftedbox:delay_channel_c` | high | VI: label → `delay.Channel_C::18`; scan alias `Gaia Lamp timing`; DB alias *gaia lamp timing* |
| 13 | Gaia internal shutter A | toggle | U_GaiaSVEReader · `InternalShutterA` → `undulator:u_gaiasvereader:internalshuttera`; confirm: “Are you sure?” | high | VI: the event case writes `internalshuttera::29` after an "Are you sure" dialog; the action library spells it `InternalShutterA` (1 open, 0 closed) |
| 14 | Gaia internal shutter B | toggle | U_GaiaSVEReader · `InternalShutterB` → `undulator:u_gaiasvereader:internalshutterb`; confirm: “Are you sure?” | high | as shutter A: `internalshutterb::29`, action library `InternalShutterB` |
| 15 | Internal Shutter A | readout | U_GaiaSVEReader · `InternalShutterA` → `undulator:u_gaiasvereader:internalshuttera` | medium | VI: a string indicator whose closed/open/unknown word UpdateShutterStatus computes from `internalshuttera::29` (and possibly `pockelcella::29`); the screen shows the variable's own value |
| 16 | Internal Shutter B | readout | U_GaiaSVEReader · `InternalShutterB` → `undulator:u_gaiasvereader:internalshutterb` | medium | as shutter A (`internalshutterb::29`, `PockelCellB::29`) |

### 148 TRA motors

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 17 | Tube In X | setpoint | U_TRAServer01 · `Position.Axis 1` → `undulator:u_traserver01:position_axis_1` | high | VI: `Position.Axis 1::3` |
| 18 | Tube In Y | setpoint | U_TRAServer01 · `Position.Axis 2` → `undulator:u_traserver01:position_axis_2` | high | VI: `Position.Axis 2::3` |
| 19 | Comp In X | setpoint | U_TRAServer01 · `Position.Axis 3` → `undulator:u_traserver01:position_axis_3` | high | VI: `Position.Axis 3::3` |
| 20 | Comp In Y | setpoint | U_TRAServer01 · `Position.Axis 4` → `undulator:u_traserver01:position_axis_4` | high | VI: `Position.Axis 4::3` |
| 21 | DM Surf. X | setpoint | U_TRAServer03 · `Position.Axis 5` → `undulator:u_traserver03:position_axis_5` | high | VI: `Position.Axis 5::16`; alias `grating_angle_w_DMsurf_TRA` moves the same axis |
| 22 | DM Surf. Y | setpoint | U_TRAServer03 · `Position.Axis 6` → `undulator:u_traserver03:position_axis_6` | high | VI: `Position.Axis 6::16` |
| 23 | BCave In X | setpoint | U_TRAServer03 · `Position.Axis 1` → `undulator:u_traserver03:position_axis_1` | high | VI: `Position.Axis 1::16` |
| 24 | BCave In Y | setpoint | U_TRAServer03 · `Position.Axis 2` → `undulator:u_traserver03:position_axis_2` | high | VI: `Position.Axis 2::16` |
| 25 | OAP1 In X | setpoint | U_TRAServer03 · `Position.Axis 3` → `undulator:u_traserver03:position_axis_3` | high | VI: `Position.Axis 3::16` |
| 26 | OAP1 In Y | setpoint | U_TRAServer03 · `Position.Axis 4` → `undulator:u_traserver03:position_axis_4` | high | VI: `Position.Axis 4::16` |

### Extra Flippers

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 27 | Amp4 dump | flipper | U_148_PLC · `DO.Ch9` → `undulator:u_148_plc:do_ch9`; in/out lamps `undulator:u_148_plc:di_ch17`, `undulator:u_148_plc:di_ch18` | high | VI: `DO.Ch9::37`; Amp4_DUMP_HP / Amp4_SEND_HP_TO_TARGET set DO.Ch9 and check DI.Ch17 / DI.Ch18 |
| 28 | Iris | flipper | U_148_PLC · `DO.Ch12` → `undulator:u_148_plc:do_ch12`; in/out lamps `undulator:u_148_plc:di_ch23`, `undulator:u_148_plc:di_ch24` | medium | VI: `DO.Ch12::37`; lamps DI.Ch23/24 by the 2k−1/2k rule (the only unclaimed DI pair) |

### Filters

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 29 | Grating Cam | annotation | **TODO**: device not in the DB | none | VI: `pos.Channel0::19` on `U_FilterWheel_02`, which the GEECS DB does not have; of the experiment's enabled FilterWheels devices (U_GhostFilters, U_HASO_Filters, U_LowPowerGhostWFSFilter, U_MI_CoarseFilters, U_MI_FineFilters, U_ProbeFilters) only U_LowPowerGhostWFSFilter is bound nowhere on this screen: name the wheel; struck through in the screenshot |
| 30 | OAPin2 | toggle | U_PLC · `DO.Ch1` → `undulator:u_plc:do_ch1` | high | VI: `DO.Ch1::22` |
| 31 | Ghost pulsed | setpoint | U_GhostFilters · `pos.Channel0` → `undulator:u_ghostfilters:pos_channel0` | high | VI: `pos.Channel0::5` |
| 32 | Probe | setpoint | U_ProbeFilters · `pos.Channel0` → `undulator:u_probefilters:pos_channel0` | high | VI: `pos.Channel0::9` |
| 33 | HASO | setpoint | U_HASO_Filters · `pos.Channel0` → `undulator:u_haso_filters:pos_channel0` | high | VI: `pos.Channel0::14` |

### B-Cave Alignment

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 34 | OAP In 2 X | setpoint | U_ESP302_01 · `Position.Axis 1` → `undulator:u_esp302_01:position_axis_1` | high | VI: `Position.Axis 1::38` |
| 35 | OAP In 2 Y | setpoint | U_ESP302_01 · `Position.Axis 2` → `undulator:u_esp302_01:position_axis_2` | high | VI: `Position.Axis 2::38` |
| 36 | TC In Stage | setpoint | U_TCAlignStages · `Position.Ch2` → `undulator:u_tcalignstages:position_ch2` | high | VI: `Position.Ch2::36` |
| 37 | Beamline In X | setpoint | U_ESP302_02 · `Position.Axis 2` → `undulator:u_esp302_02:position_axis_2` | high | VI: `Position.Axis 2::39`; a laser x-offset pseudo alias pairs it with Beamline Out X |
| 38 | Beamline In Y | setpoint | U_ESP302_02 · `Position.Axis 3` → `undulator:u_esp302_02:position_axis_3` | high | VI: `Position.Axis 3::39`; pseudo alias `ERROR_Laser_angle_offset_y` pairs it with Beamline Out Y |
| 39 | TC Out Stage | setpoint | U_TCAlignStages · `Position.Ch1` → `undulator:u_tcalignstages:position_ch1` | high | VI: `Position.Ch1::36` |
| 40 | Beamline Out X | setpoint | U_ESP302_01 · `Position.Axis 3` → `undulator:u_esp302_01:position_axis_3` | high | VI: `Position.Axis 3::38`; alias `Beamline Out x` |
| 41 | Beamline Out Y | setpoint | U_ESP302_02 · `Position.Axis 1` → `undulator:u_esp302_02:position_axis_1` | high | VI: `Position.Axis 1::39` |

### Mode Imager

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 42 | Coarse Filters | setpoint | U_MI_CoarseFilters · `pos.Channel0` → `undulator:u_mi_coarsefilters:pos_channel0` | high | VI: `pos.Channel0::15` |
| 43 | Fine Filters | setpoint | U_MI_FineFilters · `pos.Channel0` → `undulator:u_mi_finefilters:pos_channel0` | high | VI: `pos.Channel0::28` |
| 44 | Position | setpoint | U_ModeImagerESP · `Position.Axis 1` → `undulator:u_modeimageresp:position_axis_1` | high | VI: `Position.Axis 1::6`; alias `Mode Imager Stage` |

### Compressor

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 45 | Separation | setpoint | U_CompAerotech · `Position.Axis1` → `undulator:u_compaerotech:position_axis1` | high | VI: `Position.Axis1::11`; alias `Grating Separation (um)`; struck through in the screenshot (device off then; no meaning here) |
| 46 | Angle 1 | readout | U_CompAerotech · `Position.Axis2` → `undulator:u_compaerotech:position_axis2` | medium | VI: `Position.Axis2::11`, drawn greyed (an indicator); struck through in the screenshot (device off then; no meaning here) |
| 47 | Angle 2 | readout | U_CompAerotech · `Position.Axis3` → `undulator:u_compaerotech:position_axis3` | medium | VI: `Position.Axis3::11`, drawn greyed (an indicator); struck through in the screenshot (device off then; no meaning here) |
| 48 | Compressor | image | `compressor.png` | — | the panel's picture, cropped from the screenshot |

### Hexapod

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 49 | x | setpoint | U_Hexapod · `xpos` → `undulator:u_hexapod:xpos` | high | VI: `xpos::17`; alias `Hexapod X` |
| 50 | u | setpoint | U_Hexapod · `uangle` → `undulator:u_hexapod:uangle` | high | VI: `uangle::17`; alias `Hexapod Angle U` |
| 51 | y | setpoint | U_Hexapod · `ypos` → `undulator:u_hexapod:ypos` | high | VI: `ypos::17`; alias `Hexapod Y` |
| 52 | v | setpoint | U_Hexapod · `vangle` → `undulator:u_hexapod:vangle` | high | VI: `vangle::17`; alias `Hexapod Angle V` |
| 53 | z | setpoint | U_Hexapod · `zpos` → `undulator:u_hexapod:zpos` | high | VI: `zpos::17`; alias `Hexapod Z` |
| 54 | w | setpoint | U_Hexapod · `wangle` → `undulator:u_hexapod:wangle` | high | VI: `wangle::17`; alias `Hexapod Angle W` |
| 55 | "+x" is laser propagation direction / "+y" is toward parking lot / "+z" is up / PMQ out at y=-22.0, in at ~17.5 | annotation | — | — | VI: free label; the action library's pmq_INSERT / pmq_REMOVE use y = 17.95 / −22 |
| 56 | Hexapod | image | `hexapod.png` | — | the panel's picture, cropped from the screenshot |

### Valve Control

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 57 | Beam Dump | toggle | U_PLC · `DO.Ch5` → `undulator:u_plc:do_ch5`; confirm: “Shutter the laser before switching.” | high | VI: `DO.Ch5::22`; inside the "shutter laser before switching" box |
| 58 | TC phos | toggle | U_PLC · `DO.Ch11` → `undulator:u_plc:do_ch11`; confirm: “Shutter the laser before switching.” | high | VI: `DO.Ch11::22`; inside the box |
| 59 | Slit | toggle | U_PLC · `DO.Ch2` → `undulator:u_plc:do_ch2`; confirm: “Shutter the laser before switching.” | high | VI: `DO.Ch2::22`; inside the box |
| 60 | MI Wedge | toggle | U_PLC · `DO.Ch3` → `undulator:u_plc:do_ch3`; confirm: “Shutter the laser before switching.” | high | VI: `DO.Ch3::22`; inside the box |
| 61 | DC Phos | toggle | U_PLC · `DO.Ch7` → `undulator:u_plc:do_ch7` | high | VI: `DO.Ch7::22` |
| 62 | CTR | toggle | U_PLC · `DO.Ch10` → `undulator:u_plc:do_ch10` | high | VI: `DO.Ch10::22` |
| 63 | Phos1 | toggle | U_PLC · `DO.Ch4` → `undulator:u_plc:do_ch4` | high | VI: `DO.Ch4::22` |
| 64 | Aline1 | toggle | U_PLC · `DO.Ch18` → `undulator:u_plc:do_ch18` | high | VI: `DO.Ch18::22` |
| 65 | emit spoiler | readout | U_PLC · `DO.Ch9` → `undulator:u_plc:do_ch9` | low | VI: `DO.Ch9::22`, drawn greyed (an indicator); the guarded write is the Emitspoiler button below; the DB aliases U_PLC `DO.Ch9` *ALine2*, not emit spoiler: the alias is stale or the spoiler is not on Ch9; check on the hardware before its write is enabled |
| 66 | Aline 3 | readout | U_PLC · `DO.Ch8` → `undulator:u_plc:do_ch8` | high | VI: `DO.Ch8::22`, drawn greyed (an indicator); DB alias *Aline3*; the guarded write is the Aline3 button below |
| 67 | Visa1 | toggle | U_VisaPlungers · `DigitalOutput.Channel 7` → `undulator:u_visaplungers:digitaloutput_channel_7` | high | VI: `DigitalOutput.Channel 7::25` (the order is reversed); `aux_configs/visa_plunger_lookup.yaml` agrees, and so does the DB alias *VisaPlunger1* |
| 68 | Visa2 | toggle | U_VisaPlungers · `DigitalOutput.Channel 6` → `undulator:u_visaplungers:digitaloutput_channel_6` | high | VI: `DigitalOutput.Channel 6::25` (the order is reversed); `aux_configs/visa_plunger_lookup.yaml` agrees, and so does the DB alias *VisaPlunger2* |
| 69 | Visa3 | toggle | U_VisaPlungers · `DigitalOutput.Channel 5` → `undulator:u_visaplungers:digitaloutput_channel_5` | high | VI: `DigitalOutput.Channel 5::25` (the order is reversed); `aux_configs/visa_plunger_lookup.yaml` agrees, and so does the DB alias *VisaPlunger3* |
| 70 | Visa4 | toggle | U_VisaPlungers · `DigitalOutput.Channel 4` → `undulator:u_visaplungers:digitaloutput_channel_4` | high | VI: `DigitalOutput.Channel 4::25` (the order is reversed); `aux_configs/visa_plunger_lookup.yaml` agrees, and so does the DB alias *VisaPlunger4* |
| 71 | Visa5 | toggle | U_VisaPlungers · `DigitalOutput.Channel 3` → `undulator:u_visaplungers:digitaloutput_channel_3` | high | VI: `DigitalOutput.Channel 3::25`; `visa_plunger_lookup.yaml` agrees, and so does the DB alias *VisaPlunger5* |
| 72 | Visa6 | toggle | U_VisaPlungers · `DigitalOutput.Channel 2` → `undulator:u_visaplungers:digitaloutput_channel_2` | high | VI: `DigitalOutput.Channel 2::25`; `visa_plunger_lookup.yaml` agrees, and so does the DB alias *VisaPlunger6* |
| 73 | Visa7 | toggle | U_VisaPlungers · `DigitalOutput.Channel 1` → `undulator:u_visaplungers:digitaloutput_channel_1` | high | VI: `DigitalOutput.Channel 1::25`; `visa_plunger_lookup.yaml` agrees, and so does the DB alias *VisaPlunger7* |
| 74 | Visa8 | toggle | U_VisaPlungers · `DigitalOutput.Channel 0` → `undulator:u_visaplungers:digitaloutput_channel_0` | high | VI: `DigitalOutput.Channel 0::25`; `visa_plunger_lookup.yaml` agrees, and so does the DB alias *VisaPlunger8* |
| 75 | Visa9 | toggle | U_PLC · `DO.Ch19` → `undulator:u_plc:do_ch19` | high | VI: `DO.Ch19::22`; `visa_plunger_lookup.yaml` agrees |
| 76 | XUV valve | toggle | U_PLC · `DO.Ch20` → `undulator:u_plc:do_ch20` | high | VI: `DO.Ch20::22` |
| 77 | UV spec mirror | toggle | U_PLC · `DO.Ch21` → `undulator:u_plc:do_ch21` | high | VI: `DO.Ch21::22` |
| 78 | Emitspoiler | toggle | U_PLC · `DO.Ch9` → `undulator:u_plc:do_ch9`; confirm: “Are you sure? Have you verified Aline3 is out?” | low | VI: the big button under the group (no variable of its own); its event case writes `DO.Ch9::22` after the dialog "Are you sure? Have you verified Aline3 is out?" (which dialog guards which button is read from the string order and the collision sense: check); the DB aliases U_PLC `DO.Ch9` *ALine2*, not emit spoiler: the alias is stale or the spoiler is not on Ch9; check on the hardware before its write is enabled |
| 79 | Aline3 | toggle | U_PLC · `DO.Ch8` → `undulator:u_plc:do_ch8`; confirm: “Are you sure? Have you verified emit spoiler is out?” | medium | VI: the big button under the group; writes `DO.Ch8::22` after "Are you sure? Have you verified emit spoiler is out?"; DB alias *Aline3* (check, as Emitspoiler) |

### Jet Stages

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 80 | Jet_X | setpoint | U_ESP_JetXYZ · `Position.Axis 1` → `undulator:u_esp_jetxyz:position_axis_1` | high | VI: `Position.Axis 1::7`; alias `JetX (mm)` |
| 81 | Jet_Y | setpoint | U_ESP_JetXYZ · `Position.Axis 2` → `undulator:u_esp_jetxyz:position_axis_2` | high | VI: `Position.Axis 2::7`; alias `JetY (mm)` |
| 82 | Jet_Z | setpoint | U_ESP_JetXYZ · `Position.Axis 3` → `undulator:u_esp_jetxyz:position_axis_3` | high | VI: `Position.Axis 3::7`; alias `JetZ (mm)` |
| 83 | Jet Blade | setpoint | U_ModeImagerESP · `Position.Axis 2` → `undulator:u_modeimageresp:position_axis_2` | high | VI: `Position.Axis 2::6`; alias `Jet Blade` |
| 84 | Blade Height | annotation | **TODO**: device not in the DB | none | VI: `Position.Axis 111::13` on `U_BCavePicoServer`, which the GEECS DB does not have; `Position.Axis 111` is the PicoPadServer type's axis naming (111 = pad 1 axis 1), and the one device of that type left is in another experiment, disabled: name the device; struck through in the screenshot |
| 85 | "+x" moves toward parking lot / "+y" moves down / "+z" moves upstream / "+" moves jet blade out of jet / "+" blade height moves away from jet | annotation | — | — | VI: free label on the panel |

### Jet timing

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 86 | Pressure Control Voltage (V) | setpoint | U_HP_Daq · `AnalogOutput.Channel 1` → `undulator:u_hp_daq:analogoutput_channel_1` | high | VI: `AnalogOutput.Channel 1::8`; alias `Gas Pressure` |
| 87 | Set opening time (s) | setpoint | U_DG645_ShotControl · `Delay.Ch B` → `undulator:u_dg645_shotcontrol:delay_ch_b` | high | VI: the visible control has no variable; state CheckJetOpeningTime handles it; the only `Delay.Ch B::10` strings are the `Opening time (s)` indicator's (an `OPening time` copy among them), and CheckJetOpeningTime's diagram writes that `Delay.Ch B::10`; alias `jet opening time` targets Delay.Ch B; DB alias *Jet_Opening_Duration* |
| 88 | Jet Trigger | annotation | **TODO**: none chosen | none | VI: no variable; CheckJetTriggerAmp / the event case write `Amplitude.Ch AB::10` with values the VI chooses (constants 0.5 and 4.0 in the case; the scan-mode configs use the same). A screen does not compute: a two-state role or an action plan |
| 89 | Amplitude Jet trigger | readout | U_DG645_ShotControl · `Amplitude.Ch AB` → `undulator:u_dg645_shotcontrol:amplitude_ch_ab` | high | VI: label → `Amplitude.Ch AB::10`, drawn as an indicator; HTU-LaserOFF-ScanMode sets it; DB alias *Jet_Trigger_Amplitude* (0.5–5 V). A twin with the same caption on `Amplitude.Ch AB::30` (U_MRC_TimingBox) is in the heap too: its strings neighbour MRC Trigger's; not on the screenshot |
| 90 | Jet Enable | annotation | **TODO**: none chosen | none | VI: no variable near the button and none in its event case's strings; not traceable from the source |
| 91 | Opening time (s) | readout | U_DG645_ShotControl · `Delay.Ch B` → `undulator:u_dg645_shotcontrol:delay_ch_b` | high | VI: label → `Delay.Ch B::10`, drawn as an indicator ("2m" = 2 ms); DB alias *Jet_Opening_Duration* |
| 92 | Purge | toggle | U_PLC · `DO.Ch6` → `undulator:u_plc:do_ch6` | medium | VI: the visible `Purge` button has no variable; its event case writes a hidden control `purge` → `DO.Ch6::22`; state CheckPurgeValve |
| 93 | auto purge | toggle | U_PLC · `SoftwareVars.Ch1` → `undulator:u_plc:softwarevars_ch1` | medium | VI: the visible `auto purge` button has no variable; its event case writes a hidden control labelled `Autopurge` → `SoftwareVars.Ch1::22` |

### Misc area

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 94 | Probe delay | setpoint | U_ModeImagerESP · `Position.Axis 3` → `undulator:u_modeimageresp:position_axis_3` | high | VI: `Position.Axis 3::6` |
| 95 | Phasics focus | setpoint | U_Zaber · `Position.Ch1` → `undulator:u_zaber:position_ch1` | medium | VI: `Position.Ch1::26`; the scan alias calls the same axis `haso stage` |
| 96 | Ghost focus | setpoint | U_Zaber · `Position.Ch2` → `undulator:u_zaber:position_ch2` | high | VI: `Position.Ch2::26`; alias `Ghost Focus` |
| 97 | Ghost filter | setpoint | U_Zaber · `Position.Ch3` → `undulator:u_zaber:position_ch3` | high | VI: `Position.Ch3::26` |
| 98 | Probe cam Stage | setpoint | U_ProbeCamStage · `Position` → `undulator:u_probecamstage:position` | high | VI: `Position::20`; alias `probe cam stage` |
| 99 | Probe cam offset | setpoint | U_ProbeCamStage · `Offset` → `undulator:u_probecamstage:offset` | high | VI: `Offset::20` |
| 100 | "in" at position 0.0 / "out" at position 75.0 | annotation | — | — | VI: free label under Ghost filter (moved after the last row here) |

### Vacuum

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 101 | BCavePressure | readout | U_VacuumGauge · `AI_mean.Channel 0` → `undulator:u_vacuumgauge:ai_mean_channel_0` | high | VI: `AI_mean.Channel 0::27`; DB alias *B-cave*. The VI shows pressure = 10^(V−6) (`pressure calibration.vi`); the screen shows the raw voltage |
| 102 | ACavePressure | readout | U_VacuumGauge · `AI_mean.Channel 1` → `undulator:u_vacuumgauge:ai_mean_channel_1` | high | VI: `AI_mean.Channel 1::27`; DB alias *A-Cave*; the raw voltage, as BCavePressure |

### Mag Specs

| # | Label | Kind | Binding (device · variable → PV) | Confidence | Evidence |
|---|---|---|---|---|---|
| 103 | BCave Current | setpoint | U_BCaveMagSpecPS · `Current_Limit.Ch1` → `undulator:u_bcavemagspecps:current_limit_ch1` | high | VI: `Current_Limit.Ch1::33`; alias `BCaveMagSepecCurrent` |
| 104 | ACave Current | setpoint | U_ACaveMagSpecPS · `Current` → `undulator:u_acavemagspecps:current` | high | VI: `Current::34`; struck through in the screenshot (device off then; no meaning here); the device is disabled in the experiment (`expt_device.enabled = no`), so the gateway does not serve it and it reads `unreachable` until it is re-enabled |
| 105 | BCave Hall probe | readout | U_BCaveHallProbe · `RawField` → `undulator:u_bcavehallprobe:rawfield` | high | VI: `Rawfield::31`, drawn greyed; the DB spells it `RawField` (the PV is case-folded) |
| 106 | ACave Hall probe | readout | U_ACaveHallProbe · `RawField` → `undulator:u_acavehallprobe:rawfield` | high | VI: `Rawfield::32`, drawn greyed; the DB spells it `RawField` (the PV is case-folded) |
| 107 | BCave Trim Current | setpoint | U_EMQTripletBipolar · `Current_Limit.Ch4` → `undulator:u_emqtripletbipolar:current_limit_ch4` | high | VI: `Current_Limit.Ch4::35` |
