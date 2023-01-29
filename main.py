import configuracion,wifi,temperatura, utime, ure, usocket, errno
tiempo_ACS_OFF= utime.time()#Puntero de tiempo para tiempo que no se usa acs
time_valvula= utime.time()#Puntero de tiempo para cierre de valvulas
estado_valvula=1# 1>>Radiador+Sanitaria, 0>>Sanitaria solo
periodo_valvula_on=8#tiempo que se mantiene el rele de valvula en marcha
auto_ACS_OFF = False#puntero que marca si acs se apagara automaticamente tras no usarse durante un tiempo desde tiempo_ACS_OFF
tiempo_ACS_MAX = 600
bloqueo_encendido = False#puntero para control de termostato
bloqueo_apagado=False#punterro para control de termostato
temperaturas_anteriores = None# backup de temperaturas para determinar si las temperaturas cambiaron
configuracion.convertir()
quita_saltos=ure.compile('\n')
caleok = False #puntero para determinar si la temperatura del radiador es adecuada
saniok = False #puntero para determinar si la temperatura de agua sanitaria es adecuada
modo_calefaccion=False
modo_ACS=False
modo_Auto=True
quemador_activado=False  
valor_pwm=0
minimo_radiador=configuracion.minimo_radiador
maximo_radiador=configuracion.maximo_radiador
minimo_ACS=configuracion.minimo_ACS
temperatura_demandada=22
diferencia_maxima=configuracion.diferencia_maxima
import Salidas
Salidas.abre_valvula_acs()
valvulas_on=True#Puntero que define si algun rele de valvula esta activado
IP_dispositivo,ipserver=wifi.main() 
def estadoSocket(socket):
    ssocket= str(socket)
    salida=ure.match("<socket state=(\-?\d+) timeout=(\-?\d+) incoming=(\-?\d+) off=(\-?\d+)>",ssocket)
    if salida:
#         print(f'state={salida.group(1)}')
#         print(f'timeout={salida.group(2)}')
#         print(f'incoming={salida.group(3)}')
#         print(f'off={salida.group(4)}')
        return salida.group(1)
    

def conectar(direccion):
    try:
        conexion=usocket.socket()
        conexion.connect(direccion)
        intermedia=f'INICIO/{str(modo_ACS)}_{str(modo_calefaccion)}_{str(auto_ACS_OFF)}_{temperatura_demandada}\n'
        conexion.send (bytes(intermedia,"UTF-8"))

        conexion.settimeout(5)
    except OSError as exc:
        utime.sleep(2)
        if exc.errno !=errno.ECONNABORTED:
            pass
        else:
            pass 
    return conexion
dir_server=usocket.getaddrinfo(ipserver, 10000)[0][-1]

temperaturas=temperatura.toma_datos(dir_server)




def procesa_comando(linea):

    global tiempo_ACS_MAX
    global auto_ACS_OFF
    global tiempo_ACS_OFF
    global valvulas_on
    global time_valvula
    global temperatura_demandada
    global modo_Auto
    global modo_calefaccion
    global modo_ACS
    salida= ure.match("(\w+)#(\w+)",linea)
    if str(salida) =='<match num=3>':

        comando=salida.group(1)
        valor=salida.group(2)

    else:
        comando=None
        valor=None

    if comando == b'sani_auto':
        if valor == b'on':auto_ACS_OFF = True
        if valor == b'off':auto_ACS_OFF = False
    if comando == b'tiempo_off':
        tiempo_ACS_MAX = int(valor)*60
        
    if comando == b'valor_ventilador':
        a=round(int(valor)*1024/100)
        Salidas.ventilador.duty(a)
    if comando == b'sw_caldera':
        if valor == b'True':
            Salidas.enciende_caldera() 
        else:
            Salidas.apaga_caldera()
    if comando == b'ventilador_auto':
        if valor == b'true':
            modo_Auto=True
        else:
            modo_Auto=False
    if comando== b'sw_radiador':
        if valor== b'True':
            Salidas.abre_valvula_calefaccion()
        else:
            Salidas.abre_valvula_acs() 
        valvulas_on=True
        time_valvula=utime.time()
        
    if comando== b'sw_acs':
        if valor== b'True':
            Salidas.abre_valvula_acs()
        else:
            Salidas.abre_valvula_calefaccion()
        valvulas_on=True
        time_valvula=utime.time()
    if comando==b'temp_requerida':
        temperatura_demandada=round(float(valor))
    if comando==b'ACS':
        if  valor ==b'True':
            modo_ACS= True
        else:
            modo_ACS= False 
    if comando==b'calefaccion':
        if valor==b'True':
            modo_calefaccion= True
        else:
            modo_calefaccion=False
            
            
            


# n= 0
# for key, value in temperaturas.items():
#     n = n + 1




configuracion.limpia_memoria(True) 
conexion=conectar(dir_server)


configuracion.limpia_memoria(True)
# ------------------------------------INICIO BUCLE PROGRAMA---------------------------------------------------------------
while True:#comprobacion de reles de valvula para que paren una vez la valvula termino de abrir (8 seg)
    if valvulas_on and utime.time()-8 > time_valvula:
        Salidas.cierra_valvulas()
        valvulas_on=False
#Procesamos los posibles comandos llegados desde el mando        
    if estadoSocket(conexion) != '3':# '3' es estado conectado
        utime.sleep(1)
        conexion=conectar(dir_server)     
    try:
        entrada=conexion.readline()
        if entrada != b'':
            intermedia=ure.sub(quita_saltos,'',entrada)
            if intermedia:procesa_comando(intermedia)
    except OSError as exc:
        pass

    resultado=(temperatura.lee_tmp(temperatura.escanea()))

#     n=0
#     for key, value in resultado.items():
# 
#         n=n+1

    try:
        if estadoSocket(conexion) == '3' and temperaturas_anteriores != resultado:
            conexion.send(bytes('sondas/'+str(resultado.get('Ambiente'))+','+str(resultado.get('Radiador'))+','+str(resultado.get('ACS'))+' \n',"UTF-8"))
            temperaturas_anteriores = resultado
    except OSError as exc:
        pass
    configuracion.limpia_memoria(True) 
    puntero_caldera= False    
    if modo_calefaccion:
 
        if temperatura_demandada > round(resultado.get('Ambiente')):
            if bloqueo_apagado:
                temperatura_demandada+=1
                bloqueo_apagado=False
            bloqueo_encendido=True
            puntero_caldera=True
            if estado_valvula == 0 and valvulas_on == False:
                Salidas.abre_valvula_calefaccion()
                estado_valvula=1
                valvulas_on= True
#             valor_pwm = Salidas.calcula_pwm(resultado.get('Ambiente'),resultado.get('Radiador'),temperatura_demandada,minimo_radiador,maximo_radiador,diferencia_maxima)
#             if valor_pwm > 0 and valor_pwm <= 200: valor_pwm = 200 #salta de 0 a 200 (aprox. un 20%)
#             Salidas.ventilador.duty(valor_pwm)
#             valor_pwm_send = round(valor_pwm *100/1023)
#             if estadoSocket(conexion) == '3':
#                 conexion.send(bytes('valor_pwm/'+str(valor_pwm_send)+'\n',"UTF-8"))
        else:
            if estado_valvula == 1 and valvulas_on == False:
                Salidas.abre_valvula_acs()
                estado_valvula=0
                valvulas_on= True
            if bloqueo_encendido:
                temperatura_demandada-=1
                bloqueo_encendido= False
                bloqueo_apagado =True
       
        if estadoSocket(conexion) == '3' and caleok != round(resultado.get('Radiador'))> minimo_radiador:   
            if round(resultado.get('Radiador'))> minimo_radiador:
                conexion.send(bytes('Calefaccion_OK/True\n',"UTF-8"))
                
            else:
                conexion.send(bytes('Calefaccion_OK/False\n',"UTF-8"))
            caleok = round(resultado.get('Radiador'))> minimo_radiador    
#     else:
#         Salidas.ventilador.duty(0)  

                    
            
            
                 
    if modo_ACS:
        if estadoSocket(conexion) == '3'and caleok != round(resultado.get('ACS'))> minimo_ACS:
            try:
                if round(resultado.get('ACS'))> minimo_ACS:
                    conexion.send(bytes('ACS_OK/True\n',"UTF-8"))
                else:
                    conexion.send(bytes('ACS_OK/False\n',"UTF-8"))
                
            except OSError as exc:
                pass
        if auto_ACS_OFF and tiempo_ACS_OFF + tiempo_ACS_MAX < utime.time():
                    conexion.send(bytes('ACS_OK/Apagado\n',"UTF-8"))
                    modo_ACS=False
        if Salidas.caudal_ACS.value()==1:
            tiempo_ACS_OFF=utime.time()
        puntero_caldera=True
    if puntero_caldera:
        Salidas.enciende_caldera()
        quemador_activado=True
        if estadoSocket(conexion) == '3':
            try:
                conexion.send(bytes('quemador_activado/True\n',"UTF-8"))
            except OSError as exc:
                pass
    else:
        Salidas.apaga_caldera()
        quemador_activado=False
        try:
            if estadoSocket(conexion) == '3':
                conexion.send(bytes('quemador_activado/False\n',"UTF-8"))
        except OSError as exc:
            print(exc)
            
# fin programa