#!/bin/bash
source pcds_conda
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
python "$SCRIPT_DIR/snd_run_calc.py"
