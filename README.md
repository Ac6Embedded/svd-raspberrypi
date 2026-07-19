# svd-raspberrypi

CMSIS SVD files for Raspberry Pi microcontrollers (RP2040, RP2350), pulled straight from the official pico-sdk repository. Files are unmodified copies (provenance: pristine).

## Coverage

| Family | Files |
|--------|-------|
| RP2040 | 1 |
| RP2350 | 1 |

Total: 2 files, about 7.7 MiB.

## Sources

Fetched 2026-07-19 from raspberrypi/pico-sdk, branch master, commit `98a542c1a62fb549ffb5d66a3e5892b06276b670`.

- https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/src/rp2040/hardware_regs/RP2040.svd
- https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/src/rp2350/hardware_regs/RP2350.svd
- https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/LICENSE.TXT

## LICENSE AND REDISTRIBUTION STATUS

The pico-sdk LICENSE.TXT (copied to `LICENSES/pico-sdk-LICENSE.TXT`) is BSD-3-Clause. It starts with "Copyright 2020 (c) 2020 Raspberry Pi (Trading) Ltd." and states: "Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met", followed by the three standard BSD clauses (retain the copyright notice, reproduce it in binary distributions, no endorsement using the copyright holder's name).

Redistribution of these SVD files is permitted. This repo keeps the copyright notice and full license text in `LICENSES/`, which satisfies clause 1.

## Refresh

    python fetch.py

The script downloads both SVDs and the license from pico-sdk master, validates each SVD (well-formed XML, root element `device`), places them under `<Family>/`, and rewrites `manifest.json` with the current master commit sha.

The fetch is incremental: it first compares the upstream master commit sha against `manifest.json` and downloads files only when something changed. A GitHub Action (`.github/workflows/check-updates.yml`) runs it weekly on Monday at 06:00 UTC and commits any updates.

## Provenance legend

- pristine: byte-for-byte copy of the upstream file. All files here are pristine.
- patched, community, converted: not used in this repo.

## Known gaps

- RP2350 ships one combined SVD in pico-sdk. There are no separate files for the package or memory variants (RP2350A/B, RP2354A/B); the single RP2350.svd covers them.
- No SVD exists for the RP1 I/O controller or older non-microcontroller Raspberry Pi chips.
