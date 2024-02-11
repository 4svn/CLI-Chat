import socket, json, binascii, os, threading, time

def main(client_address, mensaje_Codificado):
   global datos_clientes
   if client_address not in lista_ips:
      asignarToken(client_address, mensaje_Codificado)
      lista_ips.append(client_address)
   else:
      mensaje_decodificado = json.loads(mensaje_Codificado.decode('utf-8'))
      mensaje = mensaje_decodificado.get('mensaje', '')
      token_decodificado = mensaje_decodificado.get('token', '')
      timestamp = mensaje_decodificado.get('time', '')
      usuarioBan = mensaje_decodificado.get('usuario', '')
      tiempoBan = mensaje_decodificado.get('tiempo', '')

      if (tokenVerificado(token_decodificado)):
         admin = datos_clientes[token_decodificado]['admin']
         if admin is True:
            manejarMensajeAdmin(client_address, mensaje, usuarioBan, tiempoBan, timestamp, token_decodificado)
         else:
            manejarMensajeNormal(client_address, mensaje, timestamp, token_decodificado)
      else:
         print('Token invalido')

def manejarMensajeAdmin(client_address, mensaje, usuarioBan, tiempoBan, timestamp, token_decodificado):
   if mensaje=='ips':
      enviarIPs(client_address)
   elif mensaje=='ban':
      expulsarUsuario(usuarioBan, tiempoBan)
   else:
      manejarMensajeNormal(client_address, mensaje, timestamp, token_decodificado)

def tokenVerificado(token_decodificado):
   return token_decodificado in datos_clientes
         
def manejarMensajeNormal(client_address, mensaje, timestamp, token_decodificado):
   global datos_clientes
   nombre = datos_clientes[token_decodificado]['nombre']    
   if not esBaneado(nombre):
      datos = {'time': timestamp, 'nombre': nombre, 'mensaje': mensaje}
      datos_codificados = json.dumps(datos).encode('utf-8')
      enviarMensaje(datos_codificados)

def notificarBan(mensaje, client_address):
   data = {'nombre': 'ban', 'mensaje': mensaje}
   datos_codificados = json.dumps(data).encode('utf-8')
   SERVIDOR.sendto(datos_codificados, client_address)

def esBaneado(nombre):
   global usuarios_expulsados
   print(usuarios_expulsados)
   if nombre in usuarios_expulsados:
      tiempo_actual = time.time_ns()
      tiempo_expiracion = usuarios_expulsados[nombre]
      if not isinstance(tiempo_expiracion, str):
         if tiempo_actual < tiempo_expiracion:
               tiempo_restante_ban = ((tiempo_expiracion - tiempo_actual) / (60 * 10**9))
               notificarBan(f'No puedes enviar mensajes estás baneado por {str(tiempo_restante_ban)[:4]}', client_address)
               return True
         else:
            del usuarios_expulsados[nombre]
            return False
      else:
         notificarBan('Tienes ban permanente', client_address)
         return True
   else:
      return False

def enviarMensaje(mensaje_Codificado):
   global SERVIDOR, lista_ips
   for client_address in lista_ips:
      SERVIDOR.sendto(mensaje_Codificado, client_address)

def asignarToken(client_address, mensaje_Codificado):
   global datos_clientes
   mensaje_decodificado = json.loads(mensaje_Codificado.decode('utf-8'))
   password = mensaje_decodificado.get('password', '')
   nombre = mensaje_decodificado.get('nombre', '')
   admin_user = esAdmin(password)
   token = binascii.hexlify(os.urandom(10)).decode()
   datos_clientes[token] = {'direccion': client_address, 'nombre': nombre, 'password': password, 'admin': admin_user}
   enviarToken(client_address, token, admin_user)

def esAdmin(password):
   global ADMIN_PASSWORD
   if password == ADMIN_PASSWORD:
      return True
   else:
      return False

def enviarToken(client_address, token, admin_user):
   global SERVIDOR
   datos = {'token': token, 'admin': admin_user}
   datos_codificados = json.dumps(datos).encode('utf-8')
   SERVIDOR.sendto(datos_codificados, client_address)

def enviarIPs(client_address):
   global SERVIDOR, lista_ips
   ips={}
   contador=1
   for ip in lista_ips:
      ips[f'cliente_{contador}'] = ip
      contador += 1
   ips_codificadas = json.dumps(ips).encode('utf-8')
   SERVIDOR.sendto(ips_codificadas, client_address)

def guardarDatosUsuarios():
   global datos_clientes
   with open("Clientes.json", "w") as archivo:
      json.dump(datos_clientes, archivo)

def cargarDatosUsuarios():
   global datos_clientes
   print(datos_clientes)
   with open("Clientes.json", "r") as archivo:
      nuevos_datos = json.load(archivo)    
   datos_clientes.update(nuevos_datos)
   print(datos_clientes)

def comandosServidor():
   while True:
      print('''/cargar: Cargar datos de Clientes.json
/guardar: Guardar datos de clientes en un documento''')
      comando = input('>>')
      if comando=='/cargar':
         cargarDatosUsuarios()
      elif comando=='/guardar':
         guardarDatosUsuarios()
      else:
         print('Comando no es válido')

def usuarioValido(usuario):
   for _, datos in datos_clientes.items():
      nombre = datos['nombre'] 
      if usuario == nombre:
         return True
   return False

def expulsarUsuario(usuarioBan, tiempoBan):
   global datos_clientes
   if usuarioValido(usuarioBan):
      if tiempoBan.isdigit():
         tiempo_actual = time.time_ns()
         tiempo_expiracion = tiempo_actual + (int(tiempoBan)* 60 * 10**9)
         usuarios_expulsados[usuarioBan] = tiempo_expiracion
         print(f'El usuario {usuarioBan} es baneado por {tiempoBan} min')
      else:
         usuarios_expulsados[usuarioBan] = tiempoBan
         print(f'El usuario {usuarioBan} es baneado permanentemente')
   else:
      print('El usuario solicitado no existe en el sistema')

#Definir el tipo de servidor que quremos IPv4, y UDP
SERVIDOR = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVIDOR.bind(('localhost',9000))

datos_clientes={}
lista_ips=[]
usuarios_expulsados = {}
ADMIN_PASSWORD = "admin"

comandosServidor = threading.Thread(target=comandosServidor)
comandosServidor.start()

# En TCP, el servidor acepta una conexión con un cliente, y luego
# mantiene esa conexión abierta para recibir y enviar datos a través de ella.
# En UDP, cada paquete que recibe el servidor puede provenir de un cliente diferente,
# por lo que el servidor no mantiene una conexión continua con cada cliente.


# En TCP, el método 'recv()' se utiliza para recibir datos de un socket.
# Este método bloquea el programa hasta que se recibe algún dato o hasta que se agota el tiempo de espera.
# En UDP, el método 'recvfrom()' se utiliza en su lugar, ya que UDP es un protocolo sin conexión y
# cada paquete puede provenir de una dirección diferente. 'recvfrom()' devuelve el mensaje recibido
# así como la dirección del remitente.

while True: 
   mensaje_Codificado, client_address = SERVIDOR.recvfrom(1024)
   main(client_address, mensaje_Codificado)