import re
import sqlite3


class GestorDB:
    def __init__(self, db_path: str, tabla: str, campos: list, campo_id: str = "id"):
        identificadores = [tabla, campo_id, *campos]
        if not all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", c) for c in identificadores):
            raise ValueError("Los nombres de tablas y columnas no son válidos.")
        self.tabla = tabla
        self.campos = campos
        self.campo_id = campo_id
        self.conn = sqlite3.connect(db_path)
        self._crear_tabla()

    def _crear_tabla(self):
        columnas_sql = ", ".join(f"{campo} TEXT" for campo in self.campos)
        query = (
            f"CREATE TABLE IF NOT EXISTS {self.tabla} ("
            f"{self.campo_id} INTEGER PRIMARY KEY AUTOINCREMENT, "
            f"{columnas_sql})"
        )
        self.conn.execute(query)
        self.conn.commit()

    def crear(self, datos: dict) -> int:
        columnas = ", ".join(self.campos)
        placeholders = ", ".join("?" for _ in self.campos)
        valores = [datos[campo] for campo in self.campos]
        query = f"INSERT INTO {self.tabla} ({columnas}) VALUES ({placeholders})"
        with self.conn:
            cursor = self.conn.execute(query, valores)
        return cursor.lastrowid

    def leer_todos(self) -> list:
        columnas = ", ".join([self.campo_id] + self.campos)
        query = f"SELECT {columnas} FROM {self.tabla} ORDER BY {self.campo_id}"
        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def actualizar(self, id_registro, datos: dict) -> None:
        set_clause = ", ".join(f"{campo} = ?" for campo in self.campos)
        valores = [datos[campo] for campo in self.campos] + [id_registro]
        query = f"UPDATE {self.tabla} SET {set_clause} WHERE {self.campo_id} = ?"
        with self.conn:
            self.conn.execute(query, valores)

    def eliminar(self, id_registro) -> None:
        query = f"DELETE FROM {self.tabla} WHERE {self.campo_id} = ?"
        with self.conn:
            self.conn.execute(query, (id_registro,))

    def existe_valor(self, campo: str, valor: str, excluir_id=None) -> bool:
        if campo not in self.campos:
            raise ValueError("El campo no pertenece a esta tabla.")
        query = f"SELECT 1 FROM {self.tabla} WHERE {campo} = ?"
        parametros = [valor]
        if excluir_id is not None:
            query += f" AND {self.campo_id} != ?"
            parametros.append(excluir_id)
        return self.conn.execute(query, parametros).fetchone() is not None

    def cerrar(self) -> None:
        self.conn.close()
