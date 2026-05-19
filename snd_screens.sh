#!/bin/bash                                                                                             

source /cds/group/pcds/pyps/conda/dev_conda
cd /reg/g/pcds/epics-dev/screens/pydm/xcs/snd_screens

pydm /reg/g/pcds/epics-dev/screens/pydm/xcs/snd_screens/snd_monitoring.ui &
python /reg/g/pcds/epics-dev/screens/pydm/xcs/snd_screens/snd_gui.py &
