import re
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from crud_gui import CRUDGenericoGUI
from db_manager import GestorDB

CAMPOS_CELULARES = [
    {"key": "marca", "label": "Marca", "tipo": "texto"},
    {"key": "precio", "label": "Precio", "tipo": "precio"},
    {"key": "stock", "label": "Stock", "tipo": "stock"},
]

CAMPOS_CLIENTES = [
    {"key": "nombre", "label": "Nombre", "tipo": "nombre"},
    {"key": "apellido", "label": "Apellido", "tipo": "nombre"},
    {"key": "dni", "label": "DNI", "tipo": "dni"},
    {"key": "email", "label": "Email", "tipo": "email"},
    {"key": "telefono", "label": "Teléfono", "tipo": "telefono"},
    {"key": "pago", "label": "Pago", "tipo": "opciones", "opciones": ("Efectivo", "Tarjeta")},
]


def validar_formulario(campos, datos, gestor_db, excluir_id=None):
    for campo in campos:
        clave = campo["key"]
        datos[clave] = datos[clave].strip()
        if not datos[clave]:
            raise ValueError(f"El campo {campo['label']} no puede quedar vacío.")

    for campo in campos:
        clave = campo["key"]
        valor = datos[clave]
        if clave in ("nombre", "apellido"):
            if not any(letra.isalpha() for letra in valor) or not all(
                letra.isalpha() or letra in " '-’" for letra in valor
            ):
                raise ValueError(f"{campo['label']}: ingresá letras, sin números.")
        elif clave == "precio":
            valor = valor.replace(",", ".")
            if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", valor) or not any(
                digito in "123456789" for digito in valor
            ):
                raise ValueError("Precio: ingresá un número mayor que cero, con hasta 2 decimales.")
            datos[clave] = valor
        elif clave == "stock":
            if not re.fullmatch(r"[0-9]+", valor):
                raise ValueError("Stock: ingresá un número entero mayor o igual a cero.")
        elif clave == "dni":
            if not re.fullmatch(r"[0-9]{7,8}", valor):
                raise ValueError("DNI: ingresá 7 u 8 números, sin puntos.")
            if gestor_db.existe_valor("dni", valor, excluir_id):
                raise ValueError("Ese DNI ya está registrado en otro cliente.")
        elif clave == "email":
            if not re.fullmatch(r"[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+", valor):
                raise ValueError("Email: ingresá un formato como nombre@dominio.com.")
        elif clave == "telefono":
            telefono = valor
            for separador in " ()-":
                telefono = telefono.replace(separador, "")
            if not re.fullmatch(r"\+?[0-9]{10,15}", telefono):
                raise ValueError("Teléfono: ingresá entre 10 y 15 números, con código de área.")
        elif clave == "pago":
            if valor not in campo["opciones"]:
                raise ValueError("Pago: seleccioná Efectivo o Tarjeta.")


def main():
    root = tk.Tk()
    root.title("Tkinter Camia Suarez Sistema (Celulares)")
    root.geometry("820x540")
    root.minsize(680, 480)
    ruta_db = Path(__file__).resolve().with_name("app.db")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    gestor_celulares = GestorDB(
        db_path=ruta_db,
        tabla="celulares",
        campos=[c["key"] for c in CAMPOS_CELULARES],
    )
    gestor_clientes = GestorDB(
        db_path=ruta_db,
        tabla="clientes",
        campos=[c["key"] for c in CAMPOS_CLIENTES],
    )

    tab_celulares = CRUDGenericoGUI(
        notebook, titulo="Celular", campos=CAMPOS_CELULARES,
        gestor_db=gestor_celulares, validador=validar_formulario
    )
    tab_clientes = CRUDGenericoGUI(
        notebook, titulo="Cliente", campos=CAMPOS_CLIENTES,
        gestor_db=gestor_clientes, validador=validar_formulario
    )

    notebook.add(tab_celulares, text="Celulares")
    notebook.add(tab_clientes, text="Clientes")

    try:
        root.mainloop()
    finally:
        gestor_celulares.cerrar()
        gestor_clientes.cerrar()


if __name__ == "__main__":
    main()
