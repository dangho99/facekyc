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

GPIO.setwarnings(False)
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


def clean_gpio():
    GPIO.cleanup()


def open_gate(idx):
    if idx is None:
        return
    GPIO.output(gate_gpio['output'][idx], GPIO.HIGH)
    time.sleep(0.25)
    GPIO.output(gate_gpio['output'][idx], GPIO.LOW)
    time.sleep(0.25)


def get_gate(idx):
    if idx is None:
        return
    return GPIO.input(gate_gpio['input'][idx])
