
import machine, onewire, ds18x20, time, ubinascii,configuracion,usocket

from machine import Pin
sensor = ds18x20.DS18X20(onewire.OneWire(machine.Pin(2)))
# nombres_sondas=['Ambiente','Radiador','Deposito']
def emparejar_sondas(conexion):
    
    sondas_T={'Ambiente':b'',
              'Radiador':b'',
              'ACS':b''} 
    flash=Pin(0, Pin.IN)
#     n=0
    for key in sondas_T:
        print(f'Inserta sensor {key} y pulsa flash')
        conexion.send (bytes(f'ALERTA/Inserta sensor {key} y pulsa flash\n',"UTF-8"))
#         n=n+1
        while True:
            if flash.value() == 0:
                roms = escanea()
                for rom in roms:
                    if rom != b'':
                        if not ubinascii.hexlify(rom) in sondas_T.values():
                            sondas_T.update({key:ubinascii.hexlify(rom)})
                    else:
                        print(f'error en {key}')
                print(f'{key} guardado.') 
                break
        time.sleep(1)
    conexion.send (bytes('Configuracion terminada!!!!!',"UTF-8"))
    configuracion.unir('sondas_T',str(sondas_T))
    
    print('Configuracion terminada')
    configuracion.convertir()  
    sondas_T= None
def escanea():
    roms = sensor.scan()
    return roms

def lee_tmp(roms):
    temperatura= configuracion.sondas_T.copy()
    sensor.convert_temp()
    time.sleep_ms(750)
    for rom in roms:
        rm_hex = ubinascii.hexlify(rom)
        for key, value in temperatura.items():
            if value == rm_hex:
                temperatura.update({key:round(sensor.read_temp(rom),1)})
                print(rm_hex +'('+key+')'+' Temperatura medida: '+ str(sensor.read_temp(rom)))
    return temperatura 
        
def verifica_sondas(roms):
    print("Verificando sondas.......")
    verificacion_ok = True
    if not hasattr(configuracion, 'sondas_T'): configuracion.convertir()
    if not hasattr(configuracion, 'sondas_T'):verificacion_ok = False 
    if len(roms) != 3:
        verificacion_ok = False
        print('roms!=3')
    else: 
        for rm in roms:
            rm_hex = ubinascii.hexlify(rm)
            if not rm_hex in configuracion.sondas_T.values():
                print(str(rm_hex)+' no esta')
                for key,value in sondas_T.items():
                    if value == rm_hex:
                        print('fallo en sonda'+ str(key))
                            
                verificacion_ok = False
    print(verificacion_ok)

    return verificacion_ok

        

    
        
def toma_datos(conexion):
    
    try:
        if verifica_sondas(escanea()):
            return lee_tmp(escanea())
        else:
            print('Fallo en verificacion de sondas')

            emparejar_sondas(conexion)

            return configuracion.sondas_T 
        
    except OSError as exc:
        print('No hay sondas de temperatura conectadas' + str(exc))
        emparejar_sondas(conexion)