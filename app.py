from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime


app = Flask(__name__,template_folder='template')
app.secret_key = "super_secret_key"

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'cliente'
        )
    """)
    
    # Tabla de productos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL,
            categoria TEXT,
            imagen TEXT,
            stock INTEGER NOT NULL
        )
    """)
    
    # Tabla de órdenes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ordenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            producto_id INTEGER,
            cantidad INTEGER,
            total REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# Ruta principal (Página de Inicio)
@app.route('/')
def index():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    conn.close()
    return render_template("index.html", productos=productos)

# Ruta para mostrar detalles de un producto
@app.route('/producto/<int:producto_id>')
def producto(producto_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    producto = cursor.fetchone()
    conn.close()
    return render_template("producto.html", producto=producto)

# Ruta para el carrito de compras
@app.route('/carrito')
def carrito():
    carrito = session.get("carrito", {})
    total = sum(item["cantidad"] * item["precio"] for item in carrito.values())
    return render_template("carrito.html", carrito=carrito, total=total)

# Ruta para agregar un producto al carrito
@app.route('/agregar_carrito/<int:producto_id>', methods=["POST"])
def agregar_carrito(producto_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    producto = cursor.fetchone()
    conn.close()

    if producto:
        carrito = session.get("carrito", {})
        if str(producto_id) in carrito:
            carrito[str(producto_id)]["cantidad"] += 1
        else:
            carrito[str(producto_id)] = {
                "nombre": producto[1],
                "precio": producto[3],
                "cantidad": 1
            }
        session["carrito"] = carrito
        flash("Producto agregado al carrito")
    return redirect(url_for("carrito"))

# Ruta para eliminar un producto del carrito
@app.route('/eliminar_carrito/<int:producto_id>')
def eliminar_carrito(producto_id):
    carrito = session.get("carrito", {})
    if str(producto_id) in carrito:
        del carrito[str(producto_id)]
        session["carrito"] = carrito
        flash("Producto eliminado del carrito")
    return redirect(url_for("carrito"))

# Ruta para procesar la compra
@app.route('/checkout')
def checkout():
    carrito = session.get("carrito", {})
    total = sum(item["cantidad"] * item["precio"] for item in carrito.values())

    # Guardar orden en la base de datos
    if "user_id" in session:  # Verificar si hay un usuario logueado
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        for producto_id, item in carrito.items():
            cursor.execute("""
                INSERT INTO ordenes (user_id, producto_id, cantidad, total)
                VALUES (?, ?, ?, ?)
            """, (session["user_id"], producto_id, item["cantidad"], total))
        conn.commit()
        conn.close()
        session["carrito"] = {}
        flash("Compra realizada con éxito")
    else:
        flash("Debes iniciar sesión para completar la compra")
    return redirect(url_for("index"))

# Ruta para el inicio de sesión
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[3]
            flash("Inicio de sesión exitoso")
            return redirect(url_for("index"))
        else:
            flash("Credenciales incorrectas")
    return render_template("login.html")

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada con éxito")
    return redirect(url_for("index"))

# Inicializar la base de datos y ejecutar la aplicación
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
