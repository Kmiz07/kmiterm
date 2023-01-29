from machine import Pin
from machine import PWM
print('salidas')
caldera = Pin(13, Pin.OUT, value=0)
valvula_calefaccion=Pin(16, Pin.OUT, value=0)
valvula_acs=Pin(14,Pin.OUT, value=0)
ventilador = PWM(Pin(12), freq=20, duty=0)
caudal_ACS=Pin(15,Pin.IN)

def cierra_valvulas():
    valvula_calefaccion.value(0)
    valvula_acs.value(0)
def abre_valvula_calefaccion():

    valvula_acs.value(0)
    valvula_calefaccion.value(1)
    
def abre_valvula_acs():

    valvula_calefaccion.value(0)
    valvula_acs.value(1)
    
def enciende_caldera():
    caldera.value(1)
def apaga_caldera():
    caldera.value(0)
def calcula_pwm(ta,tr,td,tr_min,tr_max,t_dif):
    '''Calcula la velocidad del ventilador, teniendo en cuenta la temperatura ambiente, la temperatura del radiador y la temperatura programada.'''
    if ta>td:
        vpt=0
    elif (td-ta)>=t_dif:
        vpt=1023
    else:
        vpt=round(((td-ta)/t_dif)*1023)
    if tr<tr_min:
        vpr=0
    elif tr>=tr_max:
        vpr=1023
    else:
        vpr=round((tr-tr_min)*1023//(tr_max-tr_min))
    if vpt <= vpr:
        print(f'pwm={str(vpt)}')
        return vpt
    else:
        print(f'pwm={str(vpr)}')
        return vpr