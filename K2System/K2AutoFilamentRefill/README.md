# K2 Auto Filament Refill

Automatically refills from the next available slot at the start of a print. 

## Setup

Add `cfs_slot_helper.py` to `/usr/share/klipper/klippy/extras`
Add `[cfs_slot_helper]` to `printer.cfg`
Add 
```
BOX_ENABLE_AUTO_REFILL ENABLE=1
CFS_PREPARE_SLOTS
```
to START_PRINT macro