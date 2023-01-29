
import configuracion,network,utime,ure,usocket,uos

def crea_buffer(conexion):
    valores=configuracion.lee()
    with open("buffer.dat",'w')as archivo:
        archivo.write('<html>\r\n<head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\r\n</head>\r\n<body>\r\n<form action="configura.html" method="post">\r\n<ul>')
        for k in valores: 
            archivo.write('\r\n<li>\r\n')
            archivo.write('<label for="' + k + '">'+ k +':</label>')
            archivo.write('<input type="text" id="' + k +'" name="' + k + '" value="' + valores[k] + '" size="120">\r\n<li/>')
        archivo.write('<li class="button">\r\n<button type="submit">Actualizar</button></li>')
        archivo.write('\r\n<ul/><form/>\r\n</body>\r\n</html>')
    conexion.send('HTTP/1.1 200 OK\r\nContent-Type: text/html \r\nContent-Lengh: ' +str(uos.stat('buffer.dat')[6]) +' \r\nConnection: keep-alive\r\n\r\n')
    with open('buffer.dat','r')as archivo:
        for linea in archivo:
            conexion.send(linea)
            utime.sleep_ms(50)
    linea=None
    archivo=None
    configuracion.limpia_memoria()
def main():
   
#conectamos a wifi segun configuracion en datos.dat
#     crea_buffer()
#     print('wifi')
    configuracion.convertir()
    wlan = network.WLAN(network.STA_IF)
    aplan = network.WLAN(network.AP_IF)
    aplan.active(False)
    wlan.active(True)
    if configuracion.forzar == True:
        wlan.ifconfig(configuracion.ST_CONF)
    tiempo = utime.time()
    wlan.connect(configuracion.ST_SSID,configuracion.ST_PASSW)
    while not wlan.isconnected():            
        if utime.time()-15>tiempo:
            print('creando AP')
            break           
    if wlan.isconnected():
        msg_inicio= "conectado como ST en: "+ str(wlan.ifconfig()[0])
        print(wlan.ifconfig()[3])
        print(msg_inicio)
        configuracion.limpia_memoria()
        return str(wlan.ifconfig()[0]),str(wlan.ifconfig()[3])
        



#Cuando falla sta se crea un ap y se debe conectar en el y en un navegador enviar: [192.168.4.1/<SSID>,<PASSW>]
#el chip se reseteara con la nueva configuracion, y si no es correcta, volvera al ap de nuevo para reconfigurar.
    
    else:
        
        separa_por_lineas = ure.compile('[\r\n]')
        separa_por_espacios = ure.compile('\s')
        separa_por_and = ure.compile('&')
        cambia_comillas = ure.compile('%27')
        cambia_abre_corchete = ure.compile('%5B')
        cambia_cierra_corchete = ure.compile('%5D')
        cambia_abre_llaves=ure.compile('%7B')
        cambia_cierra_llaves=ure.compile('%7D')
        cambia_coma = ure.compile('%2C')
        cambia_dos_puntos = ure.compile('%3A')
        separa_k_v = ure.compile('=')
        elimina_mas=ure.compile('\+')
        
        
        tipo=[]
        motivo=[]

        wlan.active(False)
        aplan.active(True)
        aplan.ifconfig(configuracion.AP_CONF)                
        aplan.config(essid = configuracion.AP_SSID, password = configuracion.AP_PASSW)
        print("Conectado como AP en:",aplan.ifconfig())
        print(str(aplan))
        confserv = ("",80)
        serv_socket = usocket.socket()
        serv_socket.bind(confserv)
        serv_socket.listen(1)
        serv_socket.settimeout(None)
        print(str(serv_socket))
        while True:
            conn, addr = serv_socket.accept()
            print('datos recibidos:')
            recepcion=''
            datos=''
            datos = conn.readline()
            print('datos:'+str(datos))
            while datos != b'':
                recepcion += (datos.decode())
                datos = conn.readline()
                if datos == b'\r\n':
                    break
            if recepcion != '':
                lineas=separa_por_lineas.split(recepcion)
#                 print(lineas)
                nombres=separa_por_espacios.split(lineas[0])
                tipo=nombres[0]#'GET' o 'POST' 
                motivo=nombres[1]# '/' o 'configura.html'
            else:
                print('no llegaron datos validos')
            a=['GET','/']
            if tipo == 'GET' and motivo =='/inicio.html':
                crea_buffer(conn)
                    
                
                    
                conn.close()
            elif tipo == 'POST' and motivo =='/configura.html':
                for linea in lineas:
                    valores_linea = separa_por_espacios.split(linea)
                    nombre_dato = valores_linea[0]
                    if nombre_dato == 'Content-Length:':
                        longitud = int(valores_linea[1])
                datos = conn.read(longitud).decode()
#                 print(datos)
#         modifica respuestas para poder ingresarlas en el archivo de configuracion
                resultados = separa_por_and.split(datos)
                for resultado in resultados:
                    resultado_ok = cambia_comillas.sub("'",resultado)
                    resultado = cambia_abre_corchete.sub("[",resultado_ok)
                    resultado_ok = cambia_cierra_corchete.sub("]",resultado)
                    resultado = cambia_coma.sub(",",resultado_ok)
                    resultado_ok = cambia_dos_puntos.sub(":",resultado)
                    resultado=cambia_abre_llaves.sub("{",resultado_ok)
                    resultado_ok=cambia_cierra_llaves.sub("}",resultado)
                    resultado=elimina_mas.sub(" ",resultado_ok)
                    
                    k,v = separa_k_v.split(resultado)
                    configuracion.unir(k,v)
                    print(k,v)
                conn.send(b'HTTP/1.1 200 OK\r\nContent-Type: text/html \r\nConnection: close \r\n\r\n<html><body>Cambios realizados</body></html>\r\n\r\n')
                conn.close() 
                utime.sleep(5)
                break
            else:
                conn.send(b'HTTP/1.1 404 Not Found\r\nContent-Type: text/html \r\nConnection: close \r\n\r\n<html><body>Pagina no aceptada</body></html>\r\n\r\n')
                conn.close()
        print('saliendo y reiniciando')
        serv_socket.close()
#         return 'reiniciando.....'
        configuracion.reinicia() 
