# Imported original triangle instrument

Run `TacticalSoul.cmd play examples/imported-melody/mod.json` from the root.
The original8000Hz triangle.wav imports into the verified boot-melody voice;
four notes play once, then stop. The40-sample loop has200Hz base pitch.
See [WAV contracts/native evidence](../../docs/MUSIC-SAMPLES.md).
The waveform is original framework-authored MIT content. Stereo/16-bit WAVs,
other playback slots and broader gameplay lifecycle remain unsupported.

`project.json` composes the same melody from `music.json`, fingerprinting
triangle.wav. Build/play accept either the project or the flat manifest;
both produce identical ROM bytes and ledger.
