import datetime
import json
import pickle
from flask import Flask, session, redirect, url_for, render_template
from custom_exceptions import OutOfStockError

# Clase base Persona
class Persona():
    def __init__(self, nombre, apellido, correo):
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo

    def info_persona(self):
        return f"Nombre: {self.nombre}\nApellido: {self.apellido}\nCorreo: {self.correo}"

# Subclase Cliente, heredada de Persona
class Cliente(Persona):
    def __init__(self, nombre, apellido, correo, idcliente, saldo=0, convenio="Sin convenio"):
        super().__init__(nombre, apellido, correo)
        self.idcliente = idcliente
        self.saldo = saldo
        self.convenio = convenio
        self.compras = []  # Lista para almacenar las compras del cliente
        self.carrito = CarritoCompras()  # Carrito de compras para el cliente

    def info_cliente(self):
        return f"{super().info_persona()}\nID: {self.idcliente}\nSaldo: {self.saldo}\nConvenio: {self.convenio}"

    def depositar_saldo(self, monto):
        self.saldo += monto
        return self.saldo
    
    def agregar_al_carrito(self, producto):
        self.carrito.agregar_producto(producto)

    def eliminar_del_carrito(self, producto):
        self.carrito.eliminar_producto(producto)

    def ver_carrito(self):
        for producto in self.carrito.productos:
            print(producto.info_producto())

    def cambiar_producto(self, producto_entrante, producto_saliente):
        diferencia = producto_saliente.valor_neto - producto_entrante.valor_neto
        if self.obtener_saldo() < diferencia:
            return "Saldo insuficiente"
        else:
            self.depositar_saldo(-diferencia)
            producto_entrante.stock += 1
            producto_saliente.stock -= 1
            return "Producto cambiado con éxito"

    def devolver(self, producto_devuelto, buen_estado=True):
        if buen_estado:
            producto_devuelto.stock += 1
            self.depositar_saldo(producto_devuelto.valor_neto)
            return "Devolución exitosa"
        else:
            return "No se puede devolver un artículo en mal estado"
        
    def valor_promedio_compras(self):
        compras = [producto.valor_neto for producto in self.compras]
        try:
            promedio = sum(compras) / len(compras)
            return promedio
        except ZeroDivisionError:
            return 0  # Si el cliente no tiene compras, se devuelve 0 como valor promedio

# Carrito de compras
class CarritoCompras():
    def __init__(self):
        self.productos = []

    def agregar_producto(self, producto):
        self.productos.append(producto)

    def eliminar_producto(self, producto):
        if producto in self.productos:
            self.productos.remove(producto)

    def calcular_total(self):
        total = sum(producto.valor_neto for producto in self.productos)
        return total
    
class OutOfStockError(Exception):
    pass

# Función para obtener cliente por su ID
def obtener_cliente_por_id(id_cliente):
    for cliente in clientes:
        if cliente.idcliente == id_cliente:
            return cliente
    return None  # Retornar None si no se encuentra ningún cliente con el ID dado

# Función para obtener producto por su SKU
def obtener_producto_por_sku(sku):
    try:
        with open('productos.json', 'r') as file:
            productos = json.load(file)
            for producto in productos:
                if producto['sku'] == sku:
                    return producto
    except FileNotFoundError:
        print("El archivo de productos no se encontró.")
    
    return None  # Retorna None si el producto con el SKU dado no se encuentra en el archivo JSON

# Cargar cliente desde un archivo
def cargar_clientes():
    try:
        with open("clientes.json", "r") as f:
            data = json.load(f)
            clientes = []
            for cliente_data in data:
                cliente = Cliente(cliente_data['nombre'], cliente_data['apellido'], cliente_data['correo'], cliente_data['idcliente'], cliente_data['saldo'], cliente_data['convenio'])
                cliente.fecha_registro = datetime.datetime.strptime(cliente_data['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                clientes.append(cliente)
            return clientes
    except FileNotFoundError:
        return []

# Guardar clientes en un archivo
def guardar_clientes(clientes):
    with open("clientes.json", "w") as f:
        json.dump([cliente.__dict__ for cliente in clientes], f, indent=4)

# Variables globales
clientes = cargar_clientes()

# Ejemplo de uso
cliente1 = Cliente("Juan", "Pérez", "juan@example.com", "001", 1000, "VIP")
cliente2 = Cliente("María", "González", "maria@example.com", "002", 500)

# Agregar clientes a la lista de clientes
clientes.append(cliente1)
clientes.append(cliente2)

# Guardar clientes en el archivo JSON
guardar_clientes(clientes)

# Detalle Producto
class Producto():
    def __init__(self, sku, nombre, categoria, proveedor, stock, valor_neto, impuesto=1.19, descuento=0):
        self.sku = sku
        self.nombre = nombre
        self.categoria = categoria
        self.proveedor = proveedor
        self.stock = stock
        self.valor_neto = valor_neto
        self.descuento = descuento
        self.impuesto = impuesto

    # Convertir el objeto Producto a un diccionario
    def to_dict(self):
        return {
            'sku': self.sku,
            'nombre': self.nombre,
            'categoria': self.categoria,
            'proveedor': self.proveedor,
            'stock': self.stock,
            'valor_neto': self.valor_neto,
            'descuento': self.descuento,
            'impuesto': self.impuesto,
            'precio': self.precio_total
        }

    def guardar_productos(productos):
        with open('productos.json', 'w') as file:
            json.dump([p.to_dict() for p in productos], file, indent=4)

    def info_producto(self):
        return f"SKU: {self.sku}\nNombre: {self.nombre}\nCategoría: {self.categoria}\nProveedor: {self.proveedor}\nStock: {self.stock}\nValor neto: {self.valor_neto}\nImpuesto: {self.__impuesto}\nDescuento: {self.descuento}"

    def vender(self):
        if self.stock == 0:
            raise OutOfStockError(f"No hay stock disponible para el producto {self.nombre}")
        self.stock -= 1
        return "Producto vendido con éxito"

# Subclase Vendedor, heredada de Persona
class Vendedor(Persona):
    def __init__(self, nombre, apellido, correo, run, seccion, comision=0, turno_noche=False):
        super().__init__(nombre, apellido, correo)
        self.run = run
        self.seccion = seccion
        self.comision = comision
        self.turno_noche = turno_noche

    def info_vendedor(self):
        return f"{super().info_persona()}\nRUN: {self.run}\nSección: {self.seccion}\nComisión: {self.comision}\nTurno noche: {self.turno_noche}"

    def vender(self, producto, cliente):
        try:
            if not cliente.saldo >= producto.valor_neto:
                return "Saldo insuficiente"
            producto.vender()
            comision = producto.valor_neto * 0.005
            self.comision += comision
            cliente.depositar_saldo(-producto.valor_neto)
            return "Venta exitosa"
        except OutOfStockError as e:
            return str(e)

    def canje_comision(self, vendedor, producto):
        if not isinstance(vendedor, Vendedor):
            return "No es un vendedor"
        valor_producto = producto.valor_neto * 0.6
        if vendedor.__comision >= valor_producto:
            vendedor.__comision -= valor_producto
            self.__comision -= valor_producto
            producto.stock -= 1
            return "Canje exitoso"
        else:
            return "No se puede canjear"

# Clase Proveedor
class Proveedor():
    def __init__(self, rut, nombre_legal, razon_social, pais, tipo_persona):
        self.rut = rut
        self.nombre_legal = nombre_legal
        self.razon_social = razon_social
        self.pais = pais
        self.tipo_persona = tipo_persona

    def proveer(self, producto, stock_a_proveer):
        if producto.proveedor!= self:
            return "Producto no proveido por este proveedor"
        producto.stock += stock_a_proveer
        return "Stock exitosamente agregado"

# Clase Orden de compra
class OrdenCompra():
    def __init__(self, id_ordencompra, producto, despacho):
        self.id_ordencompra = id_ordencompra
        self.producto = producto
        self.despacho = despacho

    def calcular_total(self):
        if self.despacho:
            total = self.producto.valor_neto + 5000
        else:
            total = self.producto.valor_neto
        return total

# Reponer productos en Bodega
class Bodega():
    @staticmethod
    def reponer_stock(sucursal):
        for producto in sucursal.productos:
            if producto.stock < 50:
                print(f"Reponiendo productos en {sucursal.nombre}...")
                if Bodega.descontar_stock(producto):
                    sucursal.aumentar_stock(producto, 300)
                    print("Productos repuestos en la sucursal.")
                else:
                    print("No hay suficiente stock en la bodega para reponer.")
            else:
                print("Stock suficiente en la sucursal.")

    @staticmethod
    def descontar_stock(producto):
        if producto.stock >= 300:
            producto.stock -= 300
            return True
        else:
            return False

# Clase sucursal
class Sucursal():
    def __init__(self, nombre):
        self.nombre = nombre
        self.productos = []

    def aumentar_stock(self, producto, cantidad):
        producto.stock += cantidad

class ProductoSucursal():
    def __init__(self, producto, cantidad):
        self.producto = producto
        self.cantidad = cantidad
        
def cargar_proveedores():
    try:
        with open("info_proveedores.dat", "rb") as f:
            proveedores = pickle.load(f)
    except FileNotFoundError:
        proveedores = []
    return proveedores

def guardar_proveedores(proveedores):
    with open("info_proveedores.dat", "wb") as f:
        pickle.dump(proveedores, f)

# Carga inicial de datos de stock_productos.json
def cargar_stock_productos():
    try:
        with open('stock_productos.json', 'r') as file:
            stock_productos = json.load(file)
    except FileNotFoundError:
        stock_productos = []
    return stock_productos

# Carga inicial de datos de ventas_productos.json
def cargar_ventas_vendedores():
    try:
        with open('ventas_productos.json', 'r') as file:
            ventas_vendedores = json.load(file)
    except FileNotFoundError:
        ventas_vendedores = []
    return ventas_vendedores

# Variables globales
bodega = Bodega()
clientes = []
vendedores = []
proveedores = cargar_proveedores()
sucursal = Sucursal("Sucursal Principal")
stock_productos = cargar_stock_productos()
ventas_vendedores = cargar_ventas_vendedores()

# OPCIONES MENU
menu_base = ["Clientes", "Bodega", "Vendedores", "Proveedores", "Venta"]
menu_clientes = ["Listar", "Crear", "Editar", "Eliminar", "Salir"]
menu_bodega = ["Listar", "Crear", "Editar", "Eliminar", "Producto con más stock", "Buscar", "Salir"]
menu_vendedores = ["Listar", "Crear", "Editar", "Eliminar", "Salir"]
menu_proveedores = ["Listar", "Crear", "Editar", "Eliminar", "Salir"]
menu_ventas = ["Listar", "Realizar", "Salir"]

# Inicio app
print("Bienvenido a Te lo Vendo\n¿Qué desea hacer?")
# Mostrar menu base
while True:
    opcion = input("Seleccione una opción: ")
    for i, opcion in enumerate(menu_base):
        print(f"{i+1}. {opcion}")
    opcion_seleccionada = int(input("Ingrese una opción: "))

    # Opciones del menu base
    while opcion_seleccionada != 0:
        if opcion_seleccionada == 1:
            print("¿Qué desea hacer?")
            for i, opcion in enumerate(menu_clientes):
                print(f"{i+1}. {opcion}")
            opcion_seleccionada_menu = int(input("Ingrese una opción: "))
            
            # Opciones del menu clientes
            while opcion_seleccionada_menu != 0:
                if opcion_seleccionada_menu == 1:
                    if len(clientes) == 0:
                        print("No hay clientes registrados")
                        break
                    for cliente in clientes:
                        print(cliente.infoClientes())
                    opcion_seleccionada_menu = 0
                elif opcion_seleccionada_menu == 2:
                    idcliente = input("Ingrese el ID del cliente: ")
                    nombre = input("Ingrese el nombre del cliente: ")
                    apellido = input("Ingrese el apellido del cliente: ")
                    correo = input("Ingrese el correo del cliente: ")
                    fecha_registro = datetime.now()
                    saldo = int(input("Ingrese el saldo del cliente: "))
                    convenio = input("Ingrese el convenio del cliente: ")
                    cliente = Cliente(idcliente, nombre, apellido, correo, fecha_registro, saldo, convenio)
                    clientes.append(cliente)
                    print("Cliente agregado exitosamente")
                    opcion_seleccionada_menu = 0
                elif opcion_seleccionada_menu == 3:
                    # Opción para editar cliente
                    pass
                elif opcion_seleccionada_menu == 4:
                    # Opción para eliminar cliente
                    pass
                elif opcion_seleccionada_menu == 5:
                    break  # Salir al menu base
                else:
                    print("Opción no válida")
                    break
