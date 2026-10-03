# -*- coding: utf-8 -*-
"""
PROGRAMACIÓN LINEAL — Ventana del programa
    Método Simplex · Método de la Gran M · Método de las Dos Fases

Ejecución: doble clic sobre este archivo, o bien   py ProgramacionLineal.pyw

tkinter se usa para la ventana y matplotlib para dibujar las tablas.
Todos los cálculos están en motor.py, sin librerías.

Uso:
  1. Elegir el método, Maximizar/Minimizar, número de variables y restricciones.
  2. Presionar "Crear tabla" y escribir los coeficientes (3, -2.5 o 3/4).
  3. Presionar "Resolver": abajo aparecen las iteraciones y el resultado.

=============================================================================
  ÍNDICE PARA EXPONER  (copiar la etiqueta y buscarla con Ctrl+F)
=============================================================================
    #VENTANA-01  __init__()          Menú de métodos, Max/Min, tamaño del problema
    #VENTANA-02  crear_casillas()    Casillas de la función Z y de las restricciones
    #VENTANA-03  resolver()          Lee las casillas y llama al motor (motor.py)
    #VENTANA-04  dibujar_tabla()     Dibuja cada tabla con matplotlib y colores

  Los métodos (#SIMPLEX-01, #GRAN_M-01, #DOS_FASES-01...) están en motor.py.
=============================================================================
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
from io import BytesIO

from matplotlib.figure import Figure

import motor

# Colores de las tablas
ENCABEZADO = "#2F3E66"      # fila de títulos
COLUMNA = "#DCE8FF"         # columna de la variable que entra
RENGLON = "#FFE9C7"         # renglón de la variable que sale
PIVOTE = "#F4A62A"          # elemento pivote
RENGLON_Z = "#EEF0F4"       # renglón Z (o W)


class App(tk.Tk):

    # =========================================================================
    #   #VENTANA-01   __init__() — menú de métodos y datos del problema
    #
    #   Variables:
    #     self.metodo   -> método elegido: 'simplex', 'gran_m' o 'dos_fases'
    #     self.sentido  -> 'max' (maximizar) o 'min' (minimizar)
    #     self.n        -> número de variables de decisión (x1 ... xn)
    #     self.m        -> número de restricciones (R1 ... Rm)
    #     menu          -> recuadro con las opciones del método
    #     clave         -> nombre interno del método (el que usa motor.py)
    #     nombre        -> texto que ve el usuario en el menú
    #     conf          -> fila con Max/Min, variables, restricciones y "Crear tabla"
    #     self.marco    -> recuadro donde van las casillas del problema
    #     self.texto    -> área donde se muestran las iteraciones y el resultado
    #     self.lienzos  -> imágenes de las tablas (se guardan para que no las borre
    #                      el recolector de basura de Python)
    # =========================================================================
    def __init__(self):
        super().__init__()
        self.title("Programación Lineal - Simplex, Gran M y Dos Fases")
        self.metodo = tk.StringVar(value="simplex")
        self.sentido = tk.StringVar(value="max")
        self.n = tk.IntVar(value=2)         # número de variables
        self.m = tk.IntVar(value=3)         # número de restricciones

        # ---- Menú de métodos (la clave es el nombre que usa motor.resolver)
        menu = tk.LabelFrame(self, text="Método", padx=5, pady=5)
        menu.pack(fill="x", padx=10, pady=5)
        for clave, nombre in [("simplex", "Simplex"), ("gran_m", "Gran M"),
                              ("dos_fases", "Dos Fases")]:
            tk.Radiobutton(menu, text=nombre, variable=self.metodo,
                           value=clave).pack(side="left", padx=5)

        # ---- Tipo de problema y tamaño
        conf = tk.Frame(self)
        conf.pack(fill="x", padx=10)
        tk.Radiobutton(conf, text="Maximizar", variable=self.sentido, value="max").pack(side="left")
        tk.Radiobutton(conf, text="Minimizar", variable=self.sentido, value="min").pack(side="left")
        tk.Label(conf, text="   Variables:").pack(side="left")
        tk.Spinbox(conf, from_=1, to=10, width=3, textvariable=self.n,
                   state="readonly").pack(side="left")
        tk.Label(conf, text="   Restricciones:").pack(side="left")
        tk.Spinbox(conf, from_=1, to=10, width=3, textvariable=self.m,
                   state="readonly").pack(side="left")
        tk.Button(conf, text="Crear tabla", command=self.crear_casillas).pack(side="left", padx=10)

        # ---- Casillas del problema (se llenan en crear_casillas)
        self.marco = tk.LabelFrame(self, text="Problema", padx=5, pady=5)
        self.marco.pack(fill="x", padx=10, pady=5)

        tk.Button(self, text="Resolver", width=15, command=self.resolver).pack(pady=5)

        # ---- Área donde se muestran las iteraciones (texto + tablas)
        self.texto = scrolledtext.ScrolledText(self, width=110, height=30, font=("Segoe UI", 10))
        self.texto.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.texto.tag_configure("titulo", font=("Segoe UI", 11, "bold"))
        self.lienzos = []                   # imágenes de las tablas (referencias vivas)

        self.crear_casillas()

    def casilla(self, fila, columna):
        """Crea una casilla de texto para un número en la posición indicada."""
        e = tk.Entry(self.marco, width=7, justify="center")
        e.grid(row=fila, column=columna, padx=2, pady=2)
        return e

    # =========================================================================
    #   #VENTANA-02   crear_casillas() — casillas de Z y de las restricciones
    #
    #   Variables:
    #     n, m         -> número de variables y de restricciones elegidos
    #     j            -> número de variable (x1, x2, ...)
    #     i            -> número de restricción (R1, R2, ...)
    #     fila         -> renglón de la ventana donde va la restricción i
    #     self.c       -> casillas de los coeficientes de Z
    #     self.a       -> casillas de los coeficientes de cada restricción
    #     coefs        -> casillas de los coeficientes de UNA restricción
    #     signo        -> signo elegido para la restricción ('<=', '>=' o '=')
    #     self.signos  -> signos de todas las restricciones
    #     self.b       -> casillas del lado derecho de cada restricción
    #     casilla      -> una caja de texto donde se escribe un número
    # =========================================================================
    def crear_casillas(self):
        """Dibuja las casillas:   Z = [ ]x1 + [ ]x2   y   R1: [ ]x1 + [ ]x2 [<=] [ ]."""
        for w in self.marco.winfo_children():
            w.destroy()
        n, m = self.n.get(), self.m.get()

        # Función objetivo
        tk.Label(self.marco, text="Z =").grid(row=0, column=0)
        self.c = []
        for j in range(n):
            self.c.append(self.casilla(0, 1 + 2 * j))
            tk.Label(self.marco, text="x%d" % (j + 1)).grid(row=0, column=2 + 2 * j)

        # Restricciones: coeficientes, signo y lado derecho
        self.a, self.signos, self.b = [], [], []
        for i in range(m):
            fila = i + 1
            tk.Label(self.marco, text="R%d:" % (i + 1)).grid(row=fila, column=0)
            coefs = []
            for j in range(n):
                coefs.append(self.casilla(fila, 1 + 2 * j))
                tk.Label(self.marco, text="x%d" % (j + 1)).grid(row=fila, column=2 + 2 * j)
            signo = tk.StringVar(value="<=")
            tk.OptionMenu(self.marco, signo, "<=", ">=", "=").grid(row=fila, column=1 + 2 * n)
            self.a.append(coefs)
            self.signos.append(signo)
            self.b.append(self.casilla(fila, 2 + 2 * n))

    @staticmethod
    def leer(casilla):
        """Lee una casilla como Fraccion (vacía = 0)."""
        texto = casilla.get().strip()
        return motor.leer_numero(texto) if texto else motor.Fraccion(0)

    # =========================================================================
    #   #VENTANA-03   resolver() — lee el problema y llama al motor
    #
    #   Variables:
    #     c        -> coeficientes de Z ya convertidos a fracción
    #     restr    -> restricciones: lista de (coeficientes, signo, lado derecho)
    #     coefs    -> casillas de los coeficientes de una restricción
    #     signo    -> signo de esa restricción
    #     b        -> casilla del lado derecho de esa restricción
    #     prob     -> problema completo que se manda a motor.resolver()
    #     paso     -> cada cosa que devuelve el motor: un texto o una tabla (dict)
    #     titulo   -> True si el texto es un título (se escribe en negritas)
    # =========================================================================
    def resolver(self):
        """Lee el problema de las casillas, lo resuelve con motor.py y muestra el texto."""
        try:
            c = [self.leer(e) for e in self.c]
            restr = [([self.leer(e) for e in coefs], signo.get(), self.leer(b))
                     for coefs, signo, b in zip(self.a, self.signos, self.b)]
        except ValueError:
            messagebox.showerror("Error", "Solo se permiten números: enteros (4), "
                                          "decimales (2.5) o fracciones (3/4).")
            return
        prob = {"sentido": self.sentido.get(), "c": c, "restr": restr}

        # Borrar la solución anterior (al borrar el texto también se borran sus imágenes).
        self.texto.config(state="normal")
        self.texto.delete("1.0", "end")
        self.lienzos = []

        # Aquí se ejecuta el método elegido (en motor.py: #RESOLVER).
        # El motor devuelve textos y tablas: los textos se escriben y las tablas se dibujan.
        for paso in motor.resolver(self.metodo.get(), prob):
            if isinstance(paso, dict):
                self.dibujar_tabla(paso)
            else:
                titulo = paso.lstrip().startswith(("---", "===", "RESULTADO", "Tabla óptima"))
                self.texto.insert("end", paso + "\n", "titulo" if titulo else "")
        self.texto.config(state="disabled")     # solo lectura

    # =========================================================================
    #   #VENTANA-04   dibujar_tabla() — tabla simplex con matplotlib
    #
    #   Variables:
    #     foto        -> datos de la tabla que manda el motor (foto_tabla)
    #     encabezado  -> títulos de las columnas: Base, x1, x2, ..., LD, Cociente
    #     celdas      -> valores de cada renglón (como texto)
    #     renglon, q  -> un renglón y su cociente (se agrega al final)
    #     anchos      -> ancho de cada columna según su texto más largo
    #     fig         -> la figura de matplotlib
    #     ax          -> el área de dibujo dentro de la figura
    #     tabla       -> la tabla de matplotlib
    #     col         -> columna de la variable que ENTRA (se pinta azul)
    #     fila        -> renglón de la variable que SALE (se pinta naranja)
    #     ultimo      -> renglón Z (o W), se pinta gris
    #     r, c        -> renglón y columna de cada celda
    #     celda       -> una celda de la tabla
    #     buffer      -> la figura ya dibujada, en memoria, como PNG
    #     imagen      -> el PNG convertido a imagen de Tk (lo que se inserta)
    # =========================================================================
    def dibujar_tabla(self, foto):
        """Dibuja una tabla simplex con matplotlib y la inserta como imagen (PNG) en el
        área de resultados: así no queda un widget vivo que haya que redibujar en cada
        scroll, que es lo que causaba el movimiento trabado."""
        # Encabezado: "Base", luego x1, x2, s1, e2, a2... (foto["nombres"], ya
        # armados en motor.py) y al final la columna "LD".
        encabezado = ["Base"] + foto["nombres"] + ["LD"]
        # Cada renglón de la tabla: nombre de la básica + sus valores; el
        # último valor de cada lista (foto["valores"]) es siempre el LD,
        # por eso queda alineado bajo la columna "LD" del encabezado.
        celdas = [[b] + v for b, v in zip(foto["base"], foto["valores"])]
        if foto["cocientes"]:
            encabezado.append("Cociente")
            for renglon, q in zip(celdas, foto["cocientes"] + [""]):
                renglon.append(q)

        # Tamaño de la figura según el texto más largo de cada columna.
        anchos = [max(len(r[k]) for r in [encabezado] + celdas) + 4
                  for k in range(len(encabezado))]
        fig = Figure(figsize=(sum(anchos) * 0.08, 0.3 * (len(celdas) + 1)), dpi=100)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        tabla = ax.table(cellText=celdas, colLabels=encabezado, cellLoc="center",
                         colWidths=[a / sum(anchos) for a in anchos], bbox=[0, 0, 1, 1])
        tabla.auto_set_font_size(False)
        tabla.set_fontsize(10)

        # Colores. En la tabla de matplotlib el renglón 0 son los títulos,
        # por eso la columna/renglón del motor se recorren +1.
        col = foto["col"] + 1 if foto["col"] is not None else None
        fila = foto["fila"] + 1 if foto["fila"] is not None else None
        ultimo = len(celdas)                                # renglón Z
        for (r, c), celda in tabla.get_celld().items():
            celda.set_edgecolor("#C8CDD8")
            if r == 0:
                celda.set_facecolor(ENCABEZADO)
                celda.get_text().set_color("white")
                celda.get_text().set_fontweight("bold")
            elif r == fila and c == col:
                celda.set_facecolor(PIVOTE)
                celda.get_text().set_fontweight("bold")
            elif r == fila:
                celda.set_facecolor(RENGLON)
            elif c == col:
                celda.set_facecolor(COLUMNA)
            elif r == ultimo:
                celda.set_facecolor(RENGLON_Z)
            if c == 0 and r > 0:
                celda.get_text().set_fontweight("bold")     # columna Base

        # Convertir la figura a PNG e insertarla como imagen dentro del área de texto.
        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        imagen = tk.PhotoImage(data=buffer.getvalue())
        self.texto.image_create("end", image=imagen)
        self.texto.insert("end", "\n")
        self.lienzos.append(imagen)             # referencia viva (si no, Tk la borra)


if __name__ == "__main__":
    App().mainloop()
