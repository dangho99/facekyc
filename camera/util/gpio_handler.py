import os
import time


# TODO: Define input gate
# 488: pin16 PY.04
# 462: pin12 PT.05  
# 447: pin11 PR.04
# 453: pin7  PS.04

# TODO: Define output gate
# 499: pin26 PZ.07 
# 498: pin24 PZ.06
# 485: pin22 PY.01
# 487: pin18 PY.03

gate_gpio = {
    'input':  [(488, 'PY.04'), (462, 'PT.05'), (447, 'PR.04'), (453, 'PS.04')],
    'output': [(499, 'PZ.07'), (498, 'PZ.06'), (485, 'PY.01'), (487, 'PY.03')]
}


def init_gpio():
    # Config memory
    os.system("devmem2 0x0243D050 w 0x0a") 
    os.system("devmem2 0x0243D010 w 0x0a")
    os.system("devmem2 0x0243D008 w 0x0a")
    os.system("devmem2 0x0243D018 w 0x0a")

    # Setup output
    for pin in gate_gpio["output"]:
        os.system("echo {} > /sys/class/gpio/export".format(pin[0]))
        os.system("echo out > /sys/class/gpio/{}/direction".format(pin[1]))

    # Setup input
    for pin in gate_gpio["input"]:
        os.system("echo {} > /sys/class/gpio/export".format(pin[0]))
        os.system("echo in > /sys/class/gpio/{}/direction".format(pin[1]))
    

def write_gpio(idx, value):
    if idx is None:
        return
    os.system("echo {} > /sys/class/gpio/{}/value".format(value, gate_gpio["output"][idx][1]))


def open_gate(idx):
    if idx is None:
        return    
    write_gpio(idx, 1)
    time.sleep(0.25)
    write_gpio(idx, 0)
    time.sleep(0.25)
