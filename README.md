## stpProxy

[![Docker Image CI](https://github.com/reworthrewards/speid/actions/workflows/docker-image.yml/badge.svg)](https://github.com/reworthrewards/speid/actions/workflows/docker-image.yml)
[![Test](https://github.com/reworthrewards/speid/actions/workflows/test.yml/badge.svg)](https://github.com/reworthrewards/speid/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/reworthrewards/speid/branch/main/graph/badge.svg?token=0BmgZw3rL6)](https://codecov.io/gh/reworthrewards/speid)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

**Este es un Fork de [cuenca-mx/speid](https://github.com/cuenca-mx/speid) (Gracias!).
Se realizan ajustes para mantener estas premisas:**

- Hacerlo agnóstico a la plataforma donde será desplegado (Se quita lo relacionado a Aptible y NewRelic)
- Hacerlo agnóstico al lenguaje de programación del backend con el que se comunique (Se usa Celery solo internamente)

Una forma robusta de comunicarse con STP, utilizando la librería 
[stpmex](https://pypi.org/project/stpmex/) para el manejo de transferencias eléctronicas. Hay dos puntos importantes:

- **Envío de transferencias** Enviar los datos de la transferencia a `PUT /registra`. 
`stpProxy` encola la petición e intentará enviarla hasta 5 veces en los primeros 30 segundos,
después lo intentará cada 20 minutos hasta que haya un total de 12 intentos.
Después de los 12 intentos la orden puede volver a ser enviada manualmente usando este comando:
```python
flask speid re-execute-transaction ${SPEID_ID}
```
Por otro lado, cuando la orden es enviada con éxito, se recibe la respuesta de STP en `POST /orden_events` 
para hacer el llamado al mismo endpoint en el backend y confirmar o cancelar la orden.

- **Recepción de transferencias** Las órdenes se reciben en `POST /ordenes` y hace un llamado
al backend con el mismo endpoint para poder recibir las órdenes, 
en caso de un error en el backend la orden se confirma pero se mantiene en la base de datos 
para poder ser reprocesada porteriormente. 

#### Backlog
- Recibir y enviar órdenes al backend por GRPC
- Módulo de cuentas
- Descargar de CEP

### Requerimientos

- Una cuenta de STP
- Python v3 o superior.
- Docker
- Sentry
- Un backend de donde recibir y enviar las órdenes

### Instalación

El archivo `env.template` contiene todos los parámetros necesarios para hacer funcionar el proxy,
es necesario completar los faltantes como las credenciales de STP, el DSN de Sentry o
la URL de MongoDB para realizar la conexión.

Después de esto, solo es necesario utilizar un gestor de contenedores para ejecutar 
la imagen de Docker incluida en el proyecto.

En caso de ser necesario ejectuarlo en una máquina local, poner en el archivo `.env` las variables correspondientes. Posteriormente,
utilizar el archivo `docker-compose` incluido que levanta todos los servicios necesarios.
``` bash
docker-compose up
```

### Test

Para ejecutar los test localmente, se puede utilizar la variable de ambiente `DATABASE_URI` 
por `mongomock://localhost:27017/db`:

```bash
cp env.template .env
make install-dev
make test
```

Sin embargo, eso implica tener las variables de entorno en el equipo de desarrollo 
utilizado, tammbién se puede realizar todo en Docker usando la variable de ambiente 
`DATABASE_URI` con `mongodb://db/db`:

```bash
cp env.template .env
make docker-test
```

También se puede ejecutar el servicio y dar una línea de comandos dentro del contenedor
para poder ejecutar instrucciones como el acceso a la base de datos, etc.

```bash
cp env.template .env
make docker-shell
```

Ambos comandos ejecutan todas las instancias necesarias para funcionar y las cierran
al terminar.


### Uso básico

#### Recibir una orden

Cuando se recibe una nueva orden SPEI, STP hace una llamada al 
servicio `/ordenes`. Se crea una transacción en la tabla `transactions`
y se asocia un evento tipo `create`. Posteriormente, se hace un POST al endpoint 
definido en la variable de ambiente `BACKEND_URL`. El servicio aguarda 15 segundos a 
obtener una respuesta la cual es almacenada en un nuevo Evento asociado a la 
Transacción y se responde a STP.

El cuerpo del mensaje enviado al backend es como sigue:
```python
{
'orden_id': 6440277,                              # Orden ID de STP 
'fecha_operacion': 20181008,                     
'institucion_ordenante': '072',                  # Código del banco definido por SPEI
'institucion_beneficiaria': '646',               # Código del banco definido por SPEI
'clave_rastreo': '7279MAP6201810060648658333', 
'monto': 1020,                                 # En centavos 
'nombre_ordenante': 'RICARDO SANCHEZ CASTILLO', 
'tipo_cuenta_ordenante': 40, 
'cuenta_ordenante': '072691004495711499', 
'rfc_curp_ordenante': 'SACR891125M47', 
'nombre_beneficiario': 'Matin Tamizi', 
'tipo_cuenta_beneficiario': 40, 
'cuenta_beneficiario': '646180157029907065', 
'rfc_curp_beneficiario': 'No capturado.', 
'concepto_pago': 'Test2', 
'referencia_numerica': 181006, 
'empresa': 'TU_EMPESA',
'speid_id': 'SPEID_ID'                        # Es un ID auto-generado y debe ser único para cada orden
}
```

#### Enviar una orden

Si el cliente quiere realizar una transferencia, entonces el backend hacer un `POST /registra`
con los siguientes campos obligatorios:

```python
{
    "nombre_beneficiario": "Nombre",
    "cuenta_beneficiario": "CLABE del beneficiario",
    "institucion_beneficiaria": "Código del banco en SPEI",
    "nombre_ordenante": "Nombre",
    "cuenta_ordenante": "CLABE del ordenante",
    "institucion_ordenante": "Código del banco en SPEI",
    "rfc_curp_ordenante": "RFC",
    "monto": 120, # Cantidad en centavos
    "concepto_pago": "Concepto"
}
```

Campos opcionales:

```python
{
    "speid_id": "ID generado por el backend para identificar la orden",
    "empresa": "Default: Aquella que fue ingresada en las credenciales de STP",
    "folio_origen": "",
    "clave_rastreo": "Default: CR{TIME}",
    "tipo_pago": 1, # Default: 1
    "tipo_cuenta_ordenante": "",
    "tipo_cuenta_beneficiario": 40, # Default: 40
    "rfc_curp_beneficiario": "Default: ND",
    "email_beneficiario": "",
    "tipo_cuenta_beneficiario2": "",
    "nombre_beneficiario2": "",
    "cuenta_beneficiario2": "",
    "rfc_curpBeneficiario2": "",
    "concepto_pago2": "",
    "clave_cat_usuario1": "",
    "clave_cat_usuario2": "",
    "clave_pago": "",
    "referencia_cobranza": "",
    "referencia_numerica": 0, # Default: Número aleatorio
    "tipo_operacion": "",
    "topologia": "Default: T",
    "usuario": "",
    "medio_entrega": 3, # Default: 3
    "prioridad": 1, #Default: 1
    "iva": "",
}
```

Posteriormente el backend recibirá un evento de cambio de estado en el endpoint `POST /orden_events`

```python
{
'speid_id': 'SOME_ID',
'orden_id': 'orden_id',
'estado': 'submitted'    # [sucess, failed]
}
```

El estado en el que puede responder STP para una transferencia son los siguientes:
1. `LIQUIDACION`: La transferencia fue exitosa.
2. `DEVOLUCION`: No fue posible realizar la transferencia. Este caso aplica 
para transferencias con destino a Instituciones participantes directos de SPEI.
3. `CANCELACION`: No fue posible realizar la transferencia. Este caso aplica 
para transferencias con destino a Instituciones que en su CLABE tengan el prefijo **646**, es decir, clientes de STP.

Cabe aclarar que el estado `LIQUIDACION` mapea a `succeeded`, mientras que
`DEVOLUCION` y `CANCELACION` mapean a `failed` para retornarse al backend.
