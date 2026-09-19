#!/bin/bash

source /cds/group/pcds/pyps/conda/dev_conda

# Run from this script's own directory so the local (dev) copies of
# snd_gui.py / scan_theta.py / *.ui are used.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Anchor for PyDMShellCommand buttons (expanded by PyDM as $SND_DIR); makes the
# screens' shell-command buttons work regardless of where this folder lives.
export SND_DIR="$SCRIPT_DIR"

pydm "$SCRIPT_DIR/snd_monitoring.ui" &
python "$SCRIPT_DIR/snd_gui.py" &
