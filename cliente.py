import socket, threading, json, re
from datetime import datetime

def recibir_token(passwordAdmin, nombreUsuario):
    global admin, SOCKET, SERVIDOR
    data = {'nombre': nombreUsuario, 'password': passwordAdmin}
    encoded_data = json.dumps(data).encode('utf-8')
    SOCKET.sendto(encoded_data, SERVIDOR)

    data, _ = SOCKET.recvfrom(1024)
    datos_decodificados = json.loads(data.decode('utf-8'))
    soyAdmin = datos_decodificados.get('admin', '')
    if soyAdmin:
        admin = True
        print('Te has conectado al servidor como admin')
        print(ListaComandos)
    else:
        print('Te has conectado al servidor como usuario normal')
    return datos_decodificados.get('token', '')

def recibirMensajes():
    global SOCKET
    while True:
        try:
            data, _ = SOCKET.recvfrom(1024)
            datos_decodificados = json.loads(data.decode('utf-8'))
            timestamp = datos_decodificados.get('time', '')
            mensaje = datos_decodificados.get('mensaje', '')
            nombre = datos_decodificados.get('nombre', '')
            if nombre == 'ban':
                print(mensaje)
            elif datos_decodificados.get('cliente_1', ''):
                print(datos_decodificados)
            else:
                print(f"{timestamp} @{nombre} > {mensaje}")

        except json.JSONDecodeError:
            print("Error decoding JSON data")
        except Exception as e:
            print(f"Error: {e}")

def gestionarMensajes(token):
    global admin
    while True:
        timestamp = datetime.now().strftime("%m/%d %H:%M:%S")
        mensaje = input(" ")
        if admin:
            comandosAdmin(token, mensaje, timestamp)
        else:
            enviarMensaje(timestamp, token, mensaje)

def comandosAdmin(token, comando, timestamp):
    if comando == '/help':
        print(ListaComandos)
    elif comando == '/lista-ips':
        print('Solicitando lista IPs....')
        enviarMensaje('', token, 'ips')
    elif comando.startswith('/expulsar'):
        expulsarUsuario(token, comando)
    else:
        enviarMensaje(timestamp, token, comando)

def enviarMensaje(timestamp, token, mensaje):
    global SOCKET, SERVIDOR
    data = {'time': timestamp, 'token': token, 'mensaje': mensaje}
    encoded_data = json.dumps(data).encode('utf-8')
    SOCKET.sendto(encoded_data, SERVIDOR)

def expulsarUsuario(token, comando):
    global SOCKET, SERVIDOR
    print('Expulsando usuario....')
    match = re.match(r'/expulsar\s+(\w+)\s+(1|5|forever)', comando)
    if match:
        nombre_usuario = match.group(1)
        duracion = match.group(2)
        data = {'mensaje': 'ban', 'usuario': nombre_usuario, 'token': token, 'tiempo': duracion}
        encoded_data = json.dumps(data).encode('utf-8')
        SOCKET.sendto(encoded_data, SERVIDOR)
    else:
        print('Comando de expulsión no válido')

ListaComandos = '''
Comandos de Admin:
/help
/lista-ips
/expulsar [usuario] [duración]
    Duración:
    - 1: Expulsión por 1 minuto
    - 5: Expulsión por 5 minutos
    - forever: Expulsión permanente
'''

#El tipo de socket (IPv4 y UDP)
SOCKET= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SOCKET.bind(('0.0.0.0', 0))
# Cambio de TCP a UDP: En el protocolo UDP no hay una conexión establecida entre cliente y servidor como en TCP.
# Cada paquete enviado desde el cliente puede ir a un destino diferente, por lo que no hay un concepto de 'conexión'.
# Se usa un socket UDP para recibir y enviar paquetes, pero no se llama a métodos como 'accept()' o 'connect()'
# como en TCP.

# En UDP no hay un método 'accept()' ya que no se establecen conexiones como en TCP.
# En su lugar, el servidor simplemente recibe paquetes que llegan de los clientes, y cada paquete se procesa
# de forma independiente.

# En TCP, el método 'send()' se utiliza para enviar datos a través de un socket.
# En UDP, el método 'sendto()' se utiliza en su lugar. 'sendto()' permite especificar la dirección
# del destino junto con el mensaje que se va a enviar. A diferencia de TCP, en UDP no hay una conexión
# establecida, por lo que es necesario especificar la dirección del destinatario en cada envío de datos.


SERVIDOR = ('localhost',9000)
admin = False
nombreUsuario = input("Elije tu nombre en el chat: ")
passwordAdmin = input("Contraseña admin: ")

initial_token = recibir_token(passwordAdmin, nombreUsuario)

HiloEscritura = threading.Thread(target=gestionarMensajes, args=(initial_token,))
HiloEscritura.start()

HiloLectura = threading.Thread(target=recibirMensajes)
HiloLectura.start()