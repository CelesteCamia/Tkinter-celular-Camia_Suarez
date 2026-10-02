import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk


class CRUDGenericoGUI(tk.Frame):
    def __init__(self, parent, titulo: str, campos: list, gestor_db, validador):
        super().__init__(parent)
        self.titulo = titulo
        self.campos = campos
        self.gestor_db = gestor_db
        self.validador = validador

        self.entries = {}
        self.id_seleccionado = None

        self._construir_formulario()
        self._construir_botones()
        self._construir_tabla()
        self._cargar_datos()

    def _construir_formulario(self):
        frame_form = tk.LabelFrame(self, text=f"Datos de {self.titulo}")
        frame_form.pack(fill="x", padx=10, pady=10)

        for columna in range(2):
            frame_form.columnconfigure(columna, weight=1, uniform="campos")

        for indice, campo in enumerate(self.campos):
            fila, columna = divmod(indice, 2)
            grupo = tk.Frame(frame_form)
            grupo.grid(row=fila, column=columna, sticky="ew", padx=10, pady=6)
            grupo.columnconfigure(0, weight=1)
            tk.Label(grupo, text=f"{campo['label']}:").grid(
                row=0, column=0, sticky="w"
            )
            if campo.get("tipo") == "opciones":
                entrada = ttk.Combobox(
                    grupo, values=campo["opciones"], state="readonly"
                )
            else:
                entrada = tk.Entry(grupo)
            entrada.grid(row=1, column=0, sticky="ew", pady=(3, 0))
            self.entries[campo["key"]] = entrada

    def _construir_botones(self):
        frame_botones = tk.Frame(self)
        frame_botones.pack(fill="x", padx=10, pady=5)

        botones = [
            ("Crear", self.crear_registro),
            ("Actualizar", self.actualizar_registro),
            ("Eliminar", self.eliminar_registro),
            ("Limpiar", self.limpiar_formulario),
        ]
        for texto, comando in botones:
            tk.Button(frame_botones, text=texto, width=12, command=comando).pack(
                side="left", padx=5
            )

    def _construir_tabla(self):
        contenedor = tk.Frame(self)
        contenedor.pack(fill="both", expand=True, padx=10, pady=10)
        contenedor.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)
        encabezados = {"id": "ID", **{c["key"]: c["label"] for c in self.campos}}
        self.tabla = ttk.Treeview(
            contenedor, columns=list(encabezados), show="headings", height=8,
            selectmode="browse"
        )
        for clave, titulo in encabezados.items():
            self.tabla.heading(clave, text=titulo)
            self.tabla.column(clave, width=100, minwidth=60, anchor="center")
        vertical = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla.yview)
        horizontal = ttk.Scrollbar(contenedor, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.tabla.bind("<<TreeviewSelect>>", self._seleccionar_fila)

    def _cargar_datos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        try:
            registros = self.gestor_db.leer_todos()
        except sqlite3.Error:
            messagebox.showerror("Error", "No se pudieron cargar los registros.")
            return
        for registro in registros:
            self.tabla.insert("", "end", values=registro)

    def _seleccionar_fila(self, event):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        valores = self.tabla.item(seleccion[0], "values")
        self.id_seleccionado = valores[0]
        for i, campo in enumerate(self.campos, start=1):
            entrada = self.entries[campo["key"]]
            if isinstance(entrada, ttk.Combobox):
                entrada.set(valores[i])
            else:
                entrada.delete(0, tk.END)
                entrada.insert(0, valores[i])

    def _obtener_datos_formulario(self) -> dict:
        return {key: entry.get().strip() for key, entry in self.entries.items()}

    def _validar_campos(self, datos: dict, excluir_id=None) -> bool:
        try:
            self.validador(self.campos, datos, self.gestor_db, excluir_id)
        except ValueError as error:
            messagebox.showerror("Error de validación", str(error))
            return False
        except sqlite3.Error:
            messagebox.showerror("Error", "No se pudo verificar el DNI en la base de datos.")
            return False
        return True

    def _guardar_registro(self, actualizar=False):
        datos = self._obtener_datos_formulario()
        seleccion = self.id_seleccionado
        excluir_id = seleccion if actualizar else None
        if not self._validar_campos(datos, excluir_id):
            return
        try:
            if actualizar:
                self.gestor_db.actualizar(seleccion, datos)
            else:
                self.gestor_db.crear(datos)
        except sqlite3.Error:
            messagebox.showerror("Error", "No se pudo guardar el registro. Revisá que la base esté disponible.")
            return
        self._cargar_datos()
        self.limpiar_formulario()
        accion = "actualizado" if actualizar else "creado"
        messagebox.showinfo("Éxito", f"{self.titulo} {accion} correctamente.")

    def crear_registro(self):
        self._guardar_registro()

    def actualizar_registro(self):
        if self.id_seleccionado is None:
            messagebox.showwarning(
                "Selección requerida",
                "Debe seleccionar un registro de la tabla antes de actualizar.",
            )
            return
        self._guardar_registro(actualizar=True)

    def eliminar_registro(self):
        if self.id_seleccionado is None:
            messagebox.showwarning(
                "Selección requerida",
                "Debe seleccionar un registro de la tabla antes de eliminar.",
            )
            return
        if not messagebox.askyesno("Confirmar eliminación", "¿Querés eliminar el registro seleccionado?"):
            return
        try:
            self.gestor_db.eliminar(self.id_seleccionado)
        except sqlite3.Error:
            messagebox.showerror("Error", "No se pudo eliminar el registro.")
            return
        self._cargar_datos()
        self.limpiar_formulario()
        messagebox.showinfo("Éxito", f"{self.titulo} eliminado correctamente.")

    def limpiar_formulario(self):
        for entry in self.entries.values():
            if isinstance(entry, ttk.Combobox):
                entry.set("")
            else:
                entry.delete(0, tk.END)
        self.id_seleccionado = None
        seleccion = self.tabla.selection()
        if seleccion:
            self.tabla.selection_remove(seleccion)
