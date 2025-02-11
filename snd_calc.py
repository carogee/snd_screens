import numpy as np
import matplotlib.pyplot as plt
from ophyd import EpicsSignal
from pcdsdevices import analog_signals
from time import sleep

aio = analog_signals.Acromag(name = 'xcs_aio', prefix = 'XCS:USR')

def show_cc():
    aio.ao1_5.set(0)
    aio.ao1_4.set(5)
    print("SND CC only")

def show_delay():
    aio.ao1_5.set(5)
    aio.ao1_4.set(0)
    print("SND Delay only")

def show_both():
    aio.ao1_5.set(5)
    aio.ao1_4.set(5)
    print("SND Both open")



def snd_correlation(nshots=240,do_ch=6):
    " DCO is ch 6 IPM5 is ch 9"
    sndall=EpicsSignal('XCS:TT:01:SNDDIO.VALA')
    ipm5_vals=np.zeros(nshots)
    dd_vals=np.zeros(nshots) #ch15                                                                                                            
    do_vals=np.zeros(nshots) #ch9                                                                                                             
    cc_vals=np.zeros(nshots) #ch14                                                                                                            
    #Ch8, CC (Ch9), Ch10, Ch11, Ch12, Ch13, Ch14, Delay (Ch15), IPM4 Sum, IPM5 Sum.                                                           
    print('Collect {} shots'.format(nshots))
    show_cc();sleep(0.5)
    for i in range(nshots):
        snddata=sndall.get()
        dd_vals[i]=snddata[7,]
        cc_vals[i]=snddata[1,]
        do_vals[i]=snddata[do_ch,]
        sleep(0.005)
    do_ref=np.nanmean(do_vals)
    cc_ref=np.nanmean(cc_vals)
    coff_cc=cc_ref/do_ref
    print('coefficient CC : {:.2f}'.format(coff_cc))
    plt.figure()
    plt.subplot(2,2,1)
    plt.plot(do_vals,cc_vals,'.')
    plt.grid();
    plt.xlabel('DO signal');
    plt.ylabel('CC signal'); plt.title(f"CC only: Coefficient={coff_cc:.2f}")
    plt.legend()
    show_delay();sleep(0.5)
    dd_vals=np.zeros(nshots) #ch15                                                                                                            
    do_vals=np.zeros(nshots) #ch9                                                                                                             
    cc_vals=np.zeros(nshots) #ch14                                                                                                            
    for i in range(nshots):
        snddata=sndall.get()
        dd_vals[i]=snddata[7,]
        cc_vals[i]=snddata[1,]
        do_vals[i]=snddata[do_ch,]
        sleep(0.005)
    do_ref=np.nanmean(do_vals)
    dd_ref=np.nanmean(dd_vals)
    coff_dd=dd_ref/do_ref
    print('coefficient DD : {:.2f}'.format(coff_dd))
    plt.subplot(2,2,2)
    plt.plot(do_vals,dd_vals,'.')
    plt.grid();
    plt.xlabel('DO signal')
    plt.ylabel('DD signal')
    plt.title(f"DD only: Coefficient={coff_dd:.2f}")
    show_both()
    dd_vals=np.zeros(nshots) #ch15                                                                                                            
    do_vals=np.zeros(nshots) #ch9                                                                                                             
    cc_vals=np.zeros(nshots) #ch14                                                                          c                                  
    for i in range(nshots):
        snddata=sndall.get()
        dd_vals[i]=snddata[7,]*coff_dd
        cc_vals[i]=snddata[1,]*coff_cc
        do_vals[i]=snddata[do_ch,]
        sleep(0.005)
    ratios = 1+(dd_vals-cc_vals)/do_vals
    ratio = np.nanmean(ratios)
    print('Ratio [1+(Delay-ChannelCut)/Sum]: {:.2f}'.format(ratio))
    #return coff_cc, coff_dd, ratio
    plt.subplot(2,2,3)
    plt.plot(cc_vals,dd_vals,'.')
    plt.grid()
    plt.xlabel('CC signal')
    plt.ylabel('DD signal')
    plt.title("Both correlation")
    plt.subplot(2,2,4)
    plt.plot(do_vals,ratios,'.')
    plt.grid()
    plt.xlabel('Sum signal')
    plt.title(f"Ratio [1+(DD-CC)/Sum]: {ratio:.2f}")
    plt.ylabel('Ratios')
    plt.tight_layout()
    #plt.ion()
    plt.show()
    #return coff_cc, coff_dd, ratio

snd_correlation()
#coff_cc_value, coff_dd_value, ratio_value =snd_correlation(nshots=240,do_ch=6)
#print('coefficient CC : {:.2f}'.format(coff_cc_value))
#print('coefficient DD : {:.2f}'.format(coff_dd_value))
#print('Ratio [1+(Delay-ChannelCut)/Sum]: {:.2f}'.format(ratio_value))

