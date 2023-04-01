import Jetson.GPIO as GPIO
import time

# Jetson Xavier NX pin datasheet: 
# https://people.eng.unimelb.edu.au/pbeuchat/asclinic/hardware/sbc_jetson_xavier_nx.html

# pin16 PY.04
# pin12 PT.05
# pin11 PR.04
# pin7  PS.04

# pin26 PZ.07
# pin24 PZ.06
# pin22 PY.01
# pin18 PY.03

gate_gpio = {
    'input': [16, 12, 11, 7],
    'output': [26, 24, 22, 18]
}


def init_gpio():
    # mode
    GPIO.setmode(GPIO.BOARD)

    # in-out
    GPIO.setup(gate_gpio['input'], GPIO.IN)
    GPIO.setup(gate_gpio['output'], GPIO.OUT)


def open_gate(idx):
    GPIO.output(gate_gpio['output'][idx], GPIO.HIGH)
    time.sleep(2.0)
    GPIO.output(gate_gpio['output'][idx], GPIO.HIGH)


def get_gate(idx):
    return GPIO.input(gate_gpio['input'][idx])
