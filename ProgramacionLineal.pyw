# -*- coding: utf-8 -*-
"""
PROGRAMACIÓN LINEAL — Interfaz gráfica
    Método Simplex · Método de la Gran M · Método de las Dos Fases

Ejecución: doble clic sobre este archivo, o bien   py ProgramacionLineal.pyw

tkinter (incluido con Python) se usa ÚNICAMENTE para dibujar la ventana.
Todos los cálculos se hacen a mano en motor.py, sin librerías.
"""

import tkinter as tk
from tkinter import ttk

import motor


# =====================================================================
#   ESTILO
# =====================================================================

FONDO = "#F3F5FA"
LATERAL = "#141B34"
LATERAL_ACTIVO = "#222B4D"
LATERAL_TEXTO = "#E6E9F5"
LATERAL_TENUE = "#8089AB"
ACENTO = "#5B5BF0"
ACENTO_OSCURO = "#4545D8"
ACENTO_SUAVE = "#ECECFE"
TARJETA = "#FFFFFF"
BORDE = "#E2E6EF"
TEXTO = "#0F172A"
TENUE = "#64748B"
SUAVE = "#F6F8FC"
CABECERA = "#F0F3F9"
VERDE = "#0E9F6E"
VERDE_SUAVE = "#E5F6EF"
ROJO = "#DC3C44"
ROJO_SUAVE = "#FDECEC"
AMBAR = "#C26A06"
AMBAR_SUAVE = "#FEF3E2"
COL_PIVOTE = "#EDEEFF"
FIL_PIVOTE = "#FFF4E3"

F = "Segoe UI"
FS = "Segoe UI Semibold"
MONO = "Consolas"

METODOS = [
    ("simplex", "Método Simplex", "Forma canónica (≤)",
     "Para problemas en forma canónica: restricciones ≤ con lado derecho no negativo. "
     "El origen es la primera solución básica factible."),
    ("gran_m", "Método de la Gran M", "Artificiales penalizadas",
     "Para restricciones ≥ o =: se agregan variables artificiales penalizadas en la "
     "función objetivo con una constante M muy grande."),
    ("dos_fases", "Método de las Dos Fases", "Fase 1 + Fase 2",
     "La Fase 1 minimiza la suma de las artificiales para hallar una solución básica "
     "factible; la Fase 2 optimiza la función objetivo original."),
]

EJEMPLOS = {
    "simplex": ("max", ["3", "5"],
                [(["1", "0"], "<=", "4"), (["0", "2"], "<=", "12"), (["3", "2"], "<=", "18")]),
    "gran_m": ("min", ["0.4", "0.5"],
               [(["0.3", "0.1"], "<=", "2.7"), (["0.5", "0.5"], "=", "6"),
                (["0.6", "0.4"], ">=", "6")]),
    "dos_fases": ("min", ["0.4", "0.5"],
                  [(["0.3", "0.1"], "<=", "2.7"), (["0.5", "0.5"], "=", "6"),
                   (["0.6", "0.4"], ">=", "6")]),
}

MAX_CARACTERES = 12
DIGITOS = "0123456789"

SIGNOS = ["<=", ">=", "="]
SIMBOLO = {"<=": "≤", ">=": "≥", "=": "="}
SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def bonito(texto):
    """x1 -> x₁ (subíndices) y '-' -> '−' (signo menos tipográfico)."""
    res = []
    en_variable = False
    for ch in texto:
        if ch.isdigit() and en_variable:
            res.append(ch.translate(SUB))
            continue
        en_variable = ch.isalpha()
        res.append("−" if ch == "-" else ch)
    return "".join(res)


# =====================================================================
#   VALIDACIÓN DE LAS CASILLAS
# =====================================================================

def numero_parcial(texto):
    """True si el texto es un número o el comienzo de uno.

    Se usa mientras el usuario escribe: permite '', '-', '3.', '3/' (aún
    incompletos) pero bloquea letras, espacios y cualquier otro símbolo.
    Formato: [signo] dígitos [. dígitos] [ / dígitos [. dígitos] ]
    """
    if len(texto) > MAX_CARACTERES:
        return False
    if texto[:1] in ("+", "-"):
        texto = texto[1:]
    partes = texto.split("/")
    if len(partes) > 2:
        return False
    for parte in partes:
        if parte.count(".") > 1:
            return False
        for ch in parte:
            if ch not in DIGITOS and ch != ".":
                return False
    return True


def revisar_numero(texto):
    """Validación final de una casilla. Devuelve (Fraccion, None) o (None, error)."""
    t = texto.strip()
    if t == "":
        return motor.Fraccion(0), None
    if not numero_parcial(t):
        return None, "solo se permiten números"

    def tiene_digito(s):
        for ch in s:
            if ch in DIGITOS:
                return True
        return False

    if "/" in t:
        numerador, denominador = t.split("/")
        if not tiene_digito(numerador) or not tiene_digito(denominador):
            return None, "fracción incompleta (ejemplo: 3/4)"
        if motor.leer_numero(denominador) == 0:
            return None, "el denominador no puede ser 0"
    elif not tiene_digito(t):
        return None, "número incompleto"
    return motor.leer_numero(t), None


# =====================================================================
#   COMPONENTES
# =====================================================================

class Boton(tk.Label):
    ESTILOS = {
        "primario": (ACENTO, "#FFFFFF", ACENTO_OSCURO, ACENTO),
        "secundario": (TARJETA, TEXTO, SUAVE, BORDE),
        "suave": (ACENTO_SUAVE, ACENTO, "#E0E0FD", ACENTO_SUAVE),
    }

    def __init__(self, master, texto, comando, estilo="primario"):
        bg, fg, hover, borde = self.ESTILOS[estilo]
        super().__init__(master, text=texto, bg=bg, fg=fg, font=(FS, 10), padx=18, pady=8,
                         cursor="hand2", highlightthickness=1, highlightbackground=borde,
                         highlightcolor=borde)
        self._bg, self._hover = bg, hover
        self.bind("<Enter>", lambda e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg))
        self.bind("<Button-1>", lambda e: comando())


class Segmentado(tk.Frame):
    """Control segmentado (tipo pestañas) de opciones excluyentes."""

    def __init__(self, master, opciones, valor, comando=None, fondo="#E8EBF3"):
        super().__init__(master, bg=fondo, padx=3, pady=3)
        self.fondo = fondo
        self.valor = valor
        self.comando = comando
        self.etiquetas = {}
        for clave, texto in opciones:
            et = tk.Label(self, text=texto, font=(FS, 10), padx=16, pady=5, cursor="hand2")
            et.pack(side="left")
            et.bind("<Button-1>", lambda e, c=clave: self.seleccionar(c))
            self.etiquetas[clave] = et
        self.refrescar()

    def seleccionar(self, clave):
        self.valor = clave
        self.refrescar()
        if self.comando:
            self.comando(clave)

    def refrescar(self):
        for clave, et in self.etiquetas.items():
            if clave == self.valor:
                et.config(bg=TARJETA, fg=TEXTO)
            else:
                et.config(bg=self.fondo, fg=TENUE)


class Contador(tk.Frame):
    """Selector numérico  [−] 3 [+]."""

    def __init__(self, master, valor, minimo, maximo, comando):
        super().__init__(master, bg=TARJETA, highlightthickness=1, highlightbackground=BORDE)
        self.valor, self.minimo, self.maximo, self.comando = valor, minimo, maximo, comando
        menos = tk.Label(self, text="−", font=(FS, 12), bg=TARJETA, fg=ACENTO, width=3,
                         cursor="hand2")
        self.etiqueta = tk.Label(self, text=str(valor), font=(FS, 11), bg=TARJETA, fg=TEXTO,
                                 width=3)
        mas = tk.Label(self, text="+", font=(FS, 12), bg=TARJETA, fg=ACENTO, width=3,
                       cursor="hand2")
        menos.pack(side="left", ipady=2)
        self.etiqueta.pack(side="left")
        mas.pack(side="left", ipady=2)
        for b, d in ((menos, -1), (mas, 1)):
            b.bind("<Button-1>", lambda e, d=d: self.cambiar(d))
            b.bind("<Enter>", lambda e, b=b: b.config(bg=ACENTO_SUAVE))
            b.bind("<Leave>", lambda e, b=b: b.config(bg=TARJETA))

    def cambiar(self, d):
        nuevo = self.valor + d
        if self.minimo <= nuevo <= self.maximo:
            self.fijar(nuevo)
            self.comando(nuevo)

    def fijar(self, v):
        self.valor = v
        self.etiqueta.config(text=str(v))


class Desplazable(tk.Frame):
    """Marco con barras de desplazamiento vertical y horizontal."""

    def __init__(self, master, fondo):
        super().__init__(master, bg=fondo)
        self.canvas = tk.Canvas(self, bg=fondo, highlightthickness=0, bd=0,
                                yscrollincrement=20, xscrollincrement=20)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.interior = tk.Frame(self.canvas, bg=fondo)
        self._ventana = self.canvas.create_window(0, 0, window=self.interior, anchor="nw")
        self.interior.bind("<Configure>", self._ajustar)
        self.canvas.bind("<Configure>", self._ajustar)

    def _ajustar(self, _=None):
        ancho = max(self.interior.winfo_reqwidth(), self.canvas.winfo_width())
        alto = max(self.interior.winfo_reqheight(), self.canvas.winfo_height())
        self.canvas.itemconfigure(self._ventana, width=ancho)
        self.canvas.configure(scrollregion=(0, 0, ancho, alto))

    def desplazar(self, pasos, horizontal=False):
        if horizontal:
            if self.canvas.xview() != (0.0, 1.0):
                self.canvas.xview_scroll(pasos, "units")
        elif self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(pasos, "units")

    def arriba(self):
        self.canvas.yview_moveto(0)
        self.canvas.xview_moveto(0)

    def abajo(self):
        self.update_idletasks()
        self.canvas.yview_moveto(1)


# =====================================================================
#   APLICACIÓN
# =====================================================================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Programación Lineal — Simplex · Gran M · Dos Fases")
        self.configure(bg=FONDO)
        ancho = min(1400, self.winfo_screenwidth() - 80)
        alto = min(880, self.winfo_screenheight() - 90)
        x = (self.winfo_screenwidth() - ancho) // 2
        y = max(10, (self.winfo_screenheight() - alto) // 2 - 20)
        self.geometry("%dx%d+%d+%d" % (ancho, alto, x, y))
        self.minsize(1020, 640)
        self._estilos()

        self.metodo = "simplex"
        self.sentido = "max"
        self.n, self.m = 2, 3
        self.c_vars, self.a_vars, self.signos, self.b_vars = [], [], [], []
        self.pagina = "plant"
        self.marcadas = set()       # casillas señaladas con error al resolver
        self._pista_id = None
        self._vcmd = (self.register(self._validar_tecla), "%P", "%W")

        self._lateral()
        self._principal()
        self.bind_all("<MouseWheel>", self._rueda)
        self.bind_all("<Shift-MouseWheel>", lambda e: self._rueda(e, True))
        self.bind("<Return>", lambda e: self.resolver() if self.pagina == "plant" else None)

        self.cambiar_metodo("simplex")
        self.cargar_ejemplo()

    # ----------------------------------------------------------- estilo
    def _estilos(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        for o in ("Vertical", "Horizontal"):
            st.configure(o + ".TScrollbar", gripcount=0, background="#CDD3E0",
                         darkcolor="#CDD3E0", lightcolor="#CDD3E0", troughcolor=FONDO,
                         bordercolor=FONDO, arrowcolor=TENUE, relief="flat", arrowsize=12)
            st.map(o + ".TScrollbar", background=[("active", "#AEB6C8")])

    def _rueda(self, e, horizontal=False):
        try:
            w = self.winfo_containing(e.x_root, e.y_root)
        except (KeyError, tk.TclError):
            return
        while w is not None and not isinstance(w, Desplazable):
            w = w.master
        if w is not None and e.delta:
            muescas = int(e.delta / 120) or (1 if e.delta > 0 else -1)
            w.desplazar(-muescas * 3, horizontal)

    # ---------------------------------------------------- barra lateral
    def _lateral(self):
        lat = tk.Frame(self, bg=LATERAL, width=270)
        lat.pack(side="left", fill="y")
        lat.pack_propagate(False)

        logo = tk.Frame(lat, bg=LATERAL)
        logo.pack(fill="x", padx=24, pady=(30, 30))
        cv = tk.Canvas(logo, width=44, height=44, bg=LATERAL, highlightthickness=0)
        cv.pack(side="left")
        r, x0, y0, x1, y1 = 11, 2, 2, 42, 42
        puntos = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
                  x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        cv.create_polygon(puntos, smooth=True, fill=ACENTO, outline="")
        cv.create_text(22, 22, text="Σ", fill="#FFFFFF", font=(FS, 17))
        txt = tk.Frame(logo, bg=LATERAL)
        txt.pack(side="left", padx=(12, 0))
        tk.Label(txt, text="Programación Lineal", bg=LATERAL, fg="#FFFFFF",
                 font=(FS, 13)).pack(anchor="w")
        tk.Label(txt, text="Métodos de optimización", bg=LATERAL, fg=LATERAL_TENUE,
                 font=(F, 9)).pack(anchor="w")

        tk.Label(lat, text="MÉTODOS", bg=LATERAL, fg=LATERAL_TENUE,
                 font=(FS, 8)).pack(anchor="w", padx=26, pady=(0, 8))

        self.items = {}
        for i, (clave, nombre, corto, _) in enumerate(METODOS):
            item = tk.Frame(lat, bg=LATERAL, cursor="hand2")
            item.pack(fill="x", padx=12, pady=2)
            barra = tk.Frame(item, bg=LATERAL, width=4)
            barra.pack(side="left", fill="y")
            num = tk.Label(item, text=str(i + 1), bg=LATERAL, fg=LATERAL_TENUE, width=3,
                           font=(FS, 11))
            num.pack(side="left", padx=(8, 4), pady=12)
            cuerpo = tk.Frame(item, bg=LATERAL)
            cuerpo.pack(side="left", fill="x", pady=10)
            t1 = tk.Label(cuerpo, text=nombre, bg=LATERAL, fg=LATERAL_TEXTO, font=(FS, 10))
            t1.pack(anchor="w")
            t2 = tk.Label(cuerpo, text=corto, bg=LATERAL, fg=LATERAL_TENUE, font=(F, 9))
            t2.pack(anchor="w")
            partes = (item, num, cuerpo, t1, t2)
            self.items[clave] = (partes, barra, num)
            for w in partes:
                w.bind("<Button-1>", lambda e, c=clave: self.cambiar_metodo(c))
                w.bind("<Enter>", lambda e, c=clave: self._hover_item(c, True))
                w.bind("<Leave>", lambda e, c=clave: self._hover_item(c, False))

        pie = tk.Frame(lat, bg=LATERAL)
        pie.pack(side="bottom", fill="x", padx=24, pady=24)
        tk.Frame(pie, bg="#2A3358", height=1).pack(fill="x", pady=(0, 14))
        tk.Label(pie, text="Aritmética exacta con fracciones.\nCálculos programados a mano,\n"
                           "sin librerías.", bg=LATERAL, fg=LATERAL_TENUE, font=(F, 9),
                 justify="left").pack(anchor="w")

    def _hover_item(self, clave, dentro):
        if clave == self.metodo:
            return
        partes, _, _ = self.items[clave]
        for w in partes:
            w.config(bg=LATERAL_ACTIVO if dentro else LATERAL)

    def _pintar_lateral(self):
        for clave, (partes, barra, num) in self.items.items():
            activo = clave == self.metodo
            for w in partes:
                w.config(bg=LATERAL_ACTIVO if activo else LATERAL)
            barra.config(bg=ACENTO if activo else LATERAL)
            num.config(fg="#FFFFFF" if activo else LATERAL_TENUE)

    # ------------------------------------------------- zona principal
    def _principal(self):
        pr = tk.Frame(self, bg=FONDO)
        pr.pack(side="left", fill="both", expand=True)

        cab = tk.Frame(pr, bg=FONDO)
        cab.pack(fill="x", padx=36, pady=(26, 14))
        izq = tk.Frame(cab, bg=FONDO)
        izq.pack(side="left", fill="x", expand=True)
        self.lbl_titulo = tk.Label(izq, text="", bg=FONDO, fg=TEXTO, font=(FS, 20))
        self.lbl_titulo.pack(anchor="w")
        self.lbl_desc = tk.Label(izq, text="", bg=FONDO, fg=TENUE, font=(F, 10),
                                 justify="left", wraplength=640)
        self.lbl_desc.pack(anchor="w", pady=(2, 0))
        self.pestanas = Segmentado(cab, [("plant", "1  Planteamiento"),
                                         ("sol", "2  Solución paso a paso")],
                                   "plant", self.ir_a)
        self.pestanas.pack(side="right", anchor="n", pady=(6, 0))

        cuerpo = tk.Frame(pr, bg=FONDO)
        cuerpo.pack(fill="both", expand=True)
        self.pag_plant = Desplazable(cuerpo, FONDO)
        self.pag_sol = Desplazable(cuerpo, FONDO)
        self._pagina_planteamiento()
        self._solucion_vacia()

    def ir_a(self, pagina):
        self.pagina = pagina
        self.pestanas.valor = pagina
        self.pestanas.refrescar()
        if pagina == "plant":
            self.pag_sol.pack_forget()
            self.pag_plant.pack(fill="both", expand=True)
        else:
            self.pag_plant.pack_forget()
            self.pag_sol.pack(fill="both", expand=True)

    def _fijar_metodo(self, clave):
        self.metodo = clave
        for c, nombre, _, desc in METODOS:
            if c == clave:
                self.lbl_titulo.config(text=nombre)
                self.lbl_desc.config(text=desc)
        self._pintar_lateral()

    def cambiar_metodo(self, clave):
        self._fijar_metodo(clave)
        self._solucion_vacia()
        self.ir_a("plant")

    # ------------------------------------------------ tarjetas genéricas
    def tarjeta(self, master, insignia=None, titulo=None, color=ACENTO, subtitulo=None,
                franja=None):
        exterior = tk.Frame(master, bg=BORDE)
        exterior.pack(fill="x", pady=(0, 16))
        if franja:
            tk.Frame(exterior, bg=franja, width=4).pack(side="left", fill="y")
        interior = tk.Frame(exterior, bg=TARJETA, padx=24, pady=20)
        interior.pack(side="left", fill="both", expand=True, padx=(0 if franja else 1, 1),
                      pady=1)
        if insignia or titulo:
            enc = tk.Frame(interior, bg=TARJETA)
            enc.pack(fill="x", pady=(0, 14))
            if insignia:
                bg_ins = {ACENTO: ACENTO_SUAVE, VERDE: VERDE_SUAVE, ROJO: ROJO_SUAVE,
                          AMBAR: AMBAR_SUAVE}.get(color, ACENTO_SUAVE)
                tk.Label(enc, text=insignia, bg=bg_ins, fg=color, font=(FS, 8),
                         padx=8, pady=2).pack(anchor="w", pady=(0, 6))
            if titulo:
                tk.Label(enc, text=titulo, bg=TARJETA, fg=TEXTO,
                         font=(FS, 14)).pack(anchor="w")
            if subtitulo:
                tk.Label(enc, text=subtitulo, bg=TARJETA, fg=TENUE, font=(F, 10),
                         justify="left", wraplength=900).pack(anchor="w", pady=(2, 0))
        return interior

    def seccion(self, master, texto):
        tk.Label(master, text=texto.upper(), bg=TARJETA, fg=TENUE,
                 font=(FS, 8)).pack(anchor="w", pady=(14, 8))

    def chip(self, master, clave, valor, bg=ACENTO_SUAVE, fg=ACENTO):
        f = tk.Frame(master, bg=bg, padx=12, pady=6)
        if clave:
            tk.Label(f, text=clave, bg=bg, fg=fg, font=(F, 9)).pack(side="left")
        tk.Label(f, text=bonito(valor), bg=bg, fg=fg,
                 font=(FS, 11)).pack(side="left", padx=(8 if clave else 0, 0))
        return f

    def caja_operaciones(self, master, ops, titulo="Operaciones de renglón (Gauss-Jordan)"):
        if not ops:
            return
        self.seccion(master, titulo)
        caja = tk.Frame(master, bg=SUAVE, padx=16, pady=12, highlightthickness=1,
                        highlightbackground=BORDE)
        caja.pack(anchor="w")
        for op in ops:
            tk.Label(caja, text=bonito(op), bg=SUAVE, fg=TEXTO, font=(MONO, 11),
                     anchor="w", justify="left").pack(anchor="w", pady=1)

    # ------------------------------------------------------ tabla simplex
    def tabla(self, master, foto):
        col_piv, fil_piv, razones = foto["col"], foto["fila"], foto["razones"]
        nombres = foto["nombres"]
        et = foto["etiqueta"]
        rejilla = tk.Frame(master, bg=BORDE, padx=1, pady=1)
        rejilla.pack(anchor="w")

        enc = ["Base", et] + nombres + ["LD"]
        if razones is not None:
            enc.append("Cociente")
        nc = len(nombres)

        def celda(fila, col, texto, bg=TARJETA, fg=TEXTO, fuente=(MONO, 11), arriba=0):
            tk.Label(rejilla, text=texto, bg=bg, fg=fg, font=fuente, padx=12,
                     pady=6).grid(row=fila, column=col, sticky="nsew",
                                  padx=(0, 1), pady=(arriba, 1))

        for k, texto in enumerate(enc):
            j = k - 2
            es_piv = col_piv is not None and j == col_piv
            celda(0, k, bonito(texto) + ("  ↓" if es_piv else ""),
                  bg=ACENTO if es_piv else CABECERA,
                  fg="#FFFFFF" if es_piv else TENUE, fuente=(FS, 10))

        # Renglones de las restricciones y, al final, el renglón Z (como en la libreta).
        filas = [(foto["base"][i], "0", f, i) for i, f in enumerate(foto["filas"])]
        filas.append((et, "1", foto["z"], None))

        for r, (base, uno, valores, i) in enumerate(filas, start=1):
            es_r0 = i is None
            sale = fil_piv is not None and i == fil_piv
            fondo_fila = "#FAFBFE" if es_r0 else TARJETA
            if sale:
                fondo_fila = FIL_PIVOTE
            # Línea más gruesa arriba del renglón Z para separarlo de las restricciones.
            arriba = 2 if es_r0 else 0

            def celda_fila(col, texto, **kw):
                celda(r, col, texto, arriba=arriba, **kw)

            celda_fila(0, bonito(base) + ("  ←" if sale else ""),
                       bg=fondo_fila, fg=AMBAR if sale else (ACENTO if not es_r0 else TEXTO),
                       fuente=(FS, 11))
            celda_fila(1, uno, bg=fondo_fila, fg=TENUE)
            for j, v in enumerate(valores):
                bg, fg, fuente = fondo_fila, TEXTO, (MONO, 11)
                if j == col_piv and j < nc:
                    bg = COL_PIVOTE
                    if sale:
                        bg, fg, fuente = ACENTO, "#FFFFFF", (MONO, 11, "bold")
                if j == nc:
                    fuente = (MONO, 11, "bold")
                if v == "0" and bg in (TARJETA, "#FAFBFE"):
                    fg = "#A7B0C2"
                celda_fila(2 + j, bonito(v), bg=bg, fg=fg, fuente=fuente)
            if razones is not None:
                if es_r0:
                    celda_fila(2 + len(valores), "", bg=fondo_fila)
                else:
                    txt = razones[i]
                    celda_fila(2 + len(valores), bonito(txt),
                          bg=AMBAR_SUAVE if sale else fondo_fila,
                          fg=AMBAR if sale else (TENUE if txt == "—" else TEXTO),
                          fuente=(MONO, 10, "bold") if sale else (MONO, 10))

    def resumen(self, master, res, titulo):
        self.seccion(master, titulo)
        fila = tk.Frame(master, bg=TARJETA)
        fila.pack(anchor="w", fill="x")
        for nombre, valor in res["basicas"]:
            self.chip(fila, None, "%s = %s" % (nombre, valor), bg=SUAVE,
                      fg=TEXTO).pack(side="left", padx=(0, 8), pady=2)
        self.chip(fila, None, "%s = %s" % (res["etiqueta"], res["valor"]), bg=ACENTO,
                  fg="#FFFFFF").pack(side="left", padx=(8, 0), pady=2)
        if res["no_basicas"]:
            tk.Label(master, text="Variables no básicas (valen 0):  " +
                     bonito(", ".join(res["no_basicas"])), bg=TARJETA, fg=TENUE,
                     font=(F, 9)).pack(anchor="w", pady=(8, 0))

    # ============================================= PÁGINA: PLANTEAMIENTO
    def _pagina_planteamiento(self):
        raiz = tk.Frame(self.pag_plant.interior, bg=FONDO, padx=36)
        raiz.pack(fill="both", expand=True, pady=(0, 30))

        conf = self.tarjeta(raiz, "CONFIGURACIÓN", "Tipo de problema")
        fila = tk.Frame(conf, bg=TARJETA)
        fila.pack(anchor="w")

        def grupo(texto):
            g = tk.Frame(fila, bg=TARJETA)
            g.pack(side="left", padx=(0, 40))
            tk.Label(g, text=texto, bg=TARJETA, fg=TENUE, font=(F, 9)).pack(anchor="w",
                                                                           pady=(0, 6))
            return g

        self.seg_sentido = Segmentado(grupo("Objetivo"),
                                      [("max", "Maximizar Z"), ("min", "Minimizar Z")],
                                      "max", self._cambiar_sentido)
        self.seg_sentido.pack(anchor="w")
        self.cont_n = Contador(grupo("Variables de decisión"), self.n, 1, 12,
                               self._cambiar_n)
        self.cont_n.pack(anchor="w")
        self.cont_m = Contador(grupo("Restricciones"), self.m, 1, 12, self._cambiar_m)
        self.cont_m.pack(anchor="w")

        modelo = self.tarjeta(raiz, "MODELO", "Función objetivo y restricciones",
                              subtitulo="Solo se aceptan números: enteros, decimales y "
                                        "fracciones (3, −2.5, 3/4); las casillas vacías "
                                        "cuentan como 0. Haz clic en el signo de una "
                                        "restricción para cambiarlo (≤, ≥, =).")
        self.marco_modelo = tk.Frame(modelo, bg=TARJETA)
        self.marco_modelo.pack(anchor="w")

        acciones = tk.Frame(raiz, bg=FONDO)
        acciones.pack(fill="x", pady=(4, 0))
        Boton(acciones, "Resolver  ▶", self.resolver).pack(side="left")
        Boton(acciones, "Cargar ejemplo", self.cargar_ejemplo,
              "secundario").pack(side="left", padx=(10, 0))
        Boton(acciones, "Limpiar", self.limpiar, "secundario").pack(side="left",
                                                                   padx=(10, 0))
        self.lbl_pista = tk.Label(acciones, text="", bg=FONDO, fg=AMBAR, font=(F, 10))
        self.lbl_pista.pack(side="left", padx=(18, 0))

        # Recuadro con la lista de errores encontrados al presionar Resolver.
        self.caja_errores = tk.Frame(raiz, bg=ROJO_SUAVE, padx=20, pady=14)

        self._construir_modelo()

    def _cambiar_sentido(self, v):
        self.sentido = v
        self.lbl_z.config(text="%s  Z  =" % ("Max" if v == "max" else "Min"))

    def _cambiar_n(self, v):
        self.n = v
        self._construir_modelo()

    def _cambiar_m(self, v):
        self.m = v
        self._construir_modelo()

    def _ajustar_listas(self):
        while len(self.c_vars) < self.n:
            self.c_vars.append(tk.StringVar())
        del self.c_vars[self.n:]
        while len(self.a_vars) < self.m:
            self.a_vars.append([])
            self.signos.append(tk.StringVar(value="<="))
            self.b_vars.append(tk.StringVar())
        del self.a_vars[self.m:], self.signos[self.m:], self.b_vars[self.m:]
        for fila in self.a_vars:
            while len(fila) < self.n:
                fila.append(tk.StringVar())
            del fila[self.n:]

    def _entrada(self, master, var, ancho=7):
        e = tk.Entry(master, textvariable=var, width=ancho, justify="center",
                     font=(MONO, 12), relief="flat", bg=SUAVE, fg=TEXTO,
                     insertbackground=ACENTO, highlightthickness=1,
                     highlightbackground=BORDE, highlightcolor=ACENTO,
                     validate="key", validatecommand=self._vcmd)
        e.bind("<comma>", self._coma)
        return e

    # ------------------------------------------------ validación al teclear
    @staticmethod
    def _pintar_casilla(ent, error):
        if error:
            ent.config(highlightbackground=ROJO, highlightcolor=ROJO, bg=ROJO_SUAVE)
        else:
            ent.config(highlightbackground=BORDE, highlightcolor=ACENTO, bg=SUAVE)

    def _validar_tecla(self, propuesto, widget):
        """Se ejecuta en cada tecla (o pegado): rechaza lo que no sea un número."""
        ent = self.nametowidget(widget)
        if numero_parcial(propuesto):
            self.marcadas.discard(ent)
            self._pintar_casilla(ent, False)
            return True
        self._pintar_casilla(ent, True)
        self.after(450, lambda: ent.winfo_exists() and
                   self._pintar_casilla(ent, ent in self.marcadas))
        if len(propuesto) > MAX_CARACTERES:
            self._pista("Máximo %d caracteres por casilla." % MAX_CARACTERES)
        else:
            self._pista("Solo se permiten números: enteros (4), decimales (2.5) "
                        "o fracciones (3/4).")
        return False

    def _coma(self, e):
        """La coma decimal se convierte en punto (2,5 -> 2.5)."""
        e.widget.insert("insert", ".")
        return "break"

    def _pista(self, texto):
        self.lbl_pista.config(text="●  " + bonito(texto))
        if self._pista_id:
            self.after_cancel(self._pista_id)
        self._pista_id = self.after(2800, lambda: self.lbl_pista.config(text=""))

    def _mostrar_errores(self, errores):
        caja = self.caja_errores
        for w in caja.winfo_children():
            w.destroy()
        if not errores:
            caja.pack_forget()
            return
        tk.Label(caja, text="No se puede resolver todavía: corrige lo siguiente",
                 bg=ROJO_SUAVE, fg=ROJO, font=(FS, 11)).pack(anchor="w", pady=(0, 6))
        limite = 8
        for texto in errores[:limite]:
            tk.Label(caja, text="•   " + bonito(texto), bg=ROJO_SUAVE, fg=TEXTO,
                     font=(F, 10), justify="left", wraplength=900).pack(anchor="w", pady=1)
        if len(errores) > limite:
            tk.Label(caja, text="… y %d error(es) más." % (len(errores) - limite),
                     bg=ROJO_SUAVE, fg=TENUE, font=(F, 10)).pack(anchor="w", pady=(2, 0))
        caja.pack(fill="x", pady=(16, 0))

    def _construir_modelo(self):
        self._ajustar_listas()
        self.marcadas = set()
        self._mostrar_errores([])
        g = self.marco_modelo
        for w in g.winfo_children():
            w.destroy()
        n = self.n
        self.ent_c, self.ent_a, self.ent_b = [], [], []

        def etiqueta_var(fila, j, ultimo):
            tk.Label(g, text=bonito("x%d" % (j + 1)) + ("   +" if not ultimo else ""),
                     bg=TARJETA, fg=TEXTO, font=(F, 12), anchor="w").grid(
                row=fila, column=2 + 2 * j, sticky="w", padx=(6, 10))

        self.lbl_z = tk.Label(g, text="", bg=TARJETA, fg=ACENTO, font=(FS, 12))
        self.lbl_z.grid(row=0, column=0, sticky="w", padx=(0, 18), pady=6)
        self._cambiar_sentido(self.sentido)
        for j in range(n):
            e = self._entrada(g, self.c_vars[j])
            e.grid(row=0, column=1 + 2 * j, ipady=5, pady=6)
            self.ent_c.append(e)
            etiqueta_var(0, j, j == n - 1)

        tk.Frame(g, bg=BORDE, height=1).grid(row=1, column=0, columnspan=2 * n + 4,
                                             sticky="ew", pady=(12, 4))
        tk.Label(g, text="Sujeto a", bg=TARJETA, fg=TENUE, font=(F, 9)).grid(
            row=2, column=0, sticky="w", pady=(4, 4))

        for i in range(self.m):
            r = 3 + i
            tk.Label(g, text="R%d" % (i + 1), bg=SUAVE, fg=TENUE, font=(FS, 9), padx=8,
                     pady=2).grid(row=r, column=0, sticky="w", pady=5)
            fila_e = []
            for j in range(n):
                e = self._entrada(g, self.a_vars[i][j])
                e.grid(row=r, column=1 + 2 * j, ipady=5, pady=5)
                fila_e.append(e)
                etiqueta_var(r, j, j == n - 1)
            self.ent_a.append(fila_e)
            signo = tk.Label(g, text=SIMBOLO[self.signos[i].get()], bg=ACENTO_SUAVE,
                             fg=ACENTO, font=(FS, 13), width=3, cursor="hand2")
            signo.grid(row=r, column=1 + 2 * n, padx=(4, 14), ipady=3)
            signo.bind("<Button-1>", lambda e, i=i, w=signo: self._ciclar_signo(i, w))
            eb = self._entrada(g, self.b_vars[i])
            eb.grid(row=r, column=2 + 2 * n, ipady=5, pady=5)
            self.ent_b.append(eb)

        x = ", ".join("x%d" % (j + 1) for j in range(n))
        tk.Label(g, text=bonito(x) + "  ≥  0", bg=TARJETA, fg=TENUE, font=(F, 11)).grid(
            row=3 + self.m, column=1, columnspan=2 * n + 2, sticky="w", pady=(10, 0))

    def _ciclar_signo(self, i, w):
        actual = self.signos[i].get()
        nuevo = SIGNOS[(SIGNOS.index(actual) + 1) % 3]
        self.signos[i].set(nuevo)
        w.config(text=SIMBOLO[nuevo])

    def cargar_ejemplo(self):
        sentido, c, restr = EJEMPLOS[self.metodo]
        self.n, self.m = len(c), len(restr)
        self.cont_n.fijar(self.n)
        self.cont_m.fijar(self.m)
        self.seg_sentido.seleccionar(sentido)
        self._ajustar_listas()
        for j, v in enumerate(c):
            self.c_vars[j].set(v)
        for i, (a, s, b) in enumerate(restr):
            for j, v in enumerate(a):
                self.a_vars[i][j].set(v)
            self.signos[i].set(s)
            self.b_vars[i].set(b)
        self._construir_modelo()

    def limpiar(self):
        for v in self.c_vars + self.b_vars:
            v.set("")
        for fila in self.a_vars:
            for v in fila:
                v.set("")
        for s in self.signos:
            s.set("<=")
        self._construir_modelo()
        self._solucion_vacia()

    def _leer_problema(self):
        """Valida todas las casillas y arma el problema. Devuelve None si hay errores."""
        errores = []
        self.marcadas = set()
        todas = list(self.ent_c)                     # en el orden en que se ven
        for fila, eb in zip(self.ent_a, self.ent_b):
            todas += fila + [eb]
        for ent in todas:
            self._pintar_casilla(ent, False)

        def marcar(entradas, mensaje):
            for ent in entradas:
                self.marcadas.add(ent)
                self._pintar_casilla(ent, True)
            errores.append(mensaje)

        def num(var, ent, lugar):
            valor, error = revisar_numero(var.get())
            if error:
                marcar([ent], "%s: %s." % (lugar, error))
                return None
            return valor

        # Función objetivo
        c = [num(self.c_vars[j], self.ent_c[j], "Z · coeficiente de x%d" % (j + 1))
             for j in range(self.n)]
        if all(v is not None and v == 0 for v in c):
            marcar(self.ent_c, "Función objetivo: todos los coeficientes son 0. Escribe al "
                               "menos un coeficiente distinto de 0.")

        # Restricciones
        restr = []
        for i in range(self.m):
            a = [num(self.a_vars[i][j], self.ent_a[i][j],
                     "R%d · coeficiente de x%d" % (i + 1, j + 1)) for j in range(self.n)]
            b = num(self.b_vars[i], self.ent_b[i], "R%d · lado derecho" % (i + 1))
            signo = self.signos[i].get()
            if all(v is not None and v == 0 for v in a):
                if b is not None:
                    se_cumple = ((signo == "<=" and not b < 0) or
                                 (signo == ">=" and not b > 0) or
                                 (signo == "=" and b == 0))
                    mensaje = ("R%d: todos los coeficientes son 0, así que la restricción "
                               % (i + 1))
                    if se_cumple:
                        mensaje += ("siempre se cumple y no aporta nada. Completa sus "
                                    "coeficientes o reduce el número de restricciones.")
                    else:
                        mensaje += ("nunca se puede cumplir (0 %s %s). Revisa sus "
                                    "coeficientes." % (SIMBOLO[signo], b))
                    marcar(self.ent_a[i], mensaje)
            restr.append((a, signo, b))

        if errores:
            self._mostrar_errores(errores)
            primera = next((e for e in todas if e in self.marcadas), None)
            if primera is not None:
                primera.focus_set()
            return None
        self._mostrar_errores([])
        return {"sentido": self.sentido, "c": c, "restr": restr}

    def resolver(self, metodo=None):
        if metodo:
            self._fijar_metodo(metodo)
        prob = self._leer_problema()
        if prob is None:
            return
        res = motor.resolver(self.metodo, prob)
        self._mostrar_solucion(res)
        self.ir_a("sol")
        self.pag_sol.arriba()

    # ================================================= PÁGINA: SOLUCIÓN
    def _limpiar_sol(self):
        for w in self.pag_sol.interior.winfo_children():
            w.destroy()
        raiz = tk.Frame(self.pag_sol.interior, bg=FONDO, padx=36)
        raiz.pack(fill="both", expand=True, pady=(0, 30))
        return raiz

    def _solucion_vacia(self):
        raiz = self._limpiar_sol()
        t = self.tarjeta(raiz)
        tk.Label(t, text="○", bg=TARJETA, fg="#C5CBDA", font=(F, 36)).pack(pady=(30, 4))
        tk.Label(t, text="Aún no hay una solución", bg=TARJETA, fg=TEXTO,
                 font=(FS, 14)).pack()
        tk.Label(t, text="Captura el problema en la pestaña Planteamiento y presiona "
                         "Resolver.", bg=TARJETA, fg=TENUE, font=(F, 10)).pack(pady=(4, 16))
        Boton(t, "Ir al planteamiento", lambda: self.ir_a("plant"), "suave").pack(
            pady=(0, 30))

    def _mostrar_solucion(self, res):
        raiz = self._limpiar_sol()
        resultado = res["resultado"]

        # Barra de resumen
        barra = tk.Frame(raiz, bg=FONDO)
        barra.pack(fill="x", pady=(0, 16))
        estados = {"optimo": ("✓  Solución óptima", VERDE, VERDE_SUAVE),
                   "infactible": ("✕  Sin solución factible", ROJO, ROJO_SUAVE),
                   "no_acotado": ("∞  No acotado", AMBAR, AMBAR_SUAVE),
                   "no_aplica": ("!  Método no aplicable", AMBAR, AMBAR_SUAVE),
                   "limite": ("!  Sin convergencia", AMBAR, AMBAR_SUAVE)}
        txt, fg, bg = estados[resultado["estado"]]
        tk.Label(barra, text=txt, bg=bg, fg=fg, font=(FS, 10), padx=12,
                 pady=5).pack(side="left")
        tk.Label(barra, text="%d iteración(es)" % res["iteraciones"], bg=FONDO, fg=TENUE,
                 font=(F, 10)).pack(side="left", padx=14)
        if resultado["estado"] == "optimo":
            tk.Label(barra, text=bonito("Z = " + resultado["z"]), bg=FONDO, fg=TEXTO,
                     font=(FS, 11)).pack(side="left")
        Boton(barra, "Ir al resultado  ↓", self.pag_sol.abajo, "suave").pack(side="right")
        Boton(barra, "Editar problema", lambda: self.ir_a("plant"),
              "secundario").pack(side="right", padx=(0, 10))

        for paso in res["pasos"]:
            getattr(self, "_paso_" + paso["tipo"])(raiz, paso)
        self._resultado(raiz, resultado)

    # ---- pasos
    def _paso_modelo(self, raiz, p):
        t = self.tarjeta(raiz, "PLANTEAMIENTO", "Modelo del problema")
        cols = tk.Frame(t, bg=TARJETA)
        cols.pack(anchor="w", fill="x")
        bloques = [("Problema original", p["original"])]
        if p["estandar"]:
            bloques.append((p["titulo_estandar"], p["estandar"]))
        for k, (titulo, m) in enumerate(bloques):
            caja = tk.Frame(cols, bg=SUAVE, padx=20, pady=16, highlightthickness=1,
                            highlightbackground=BORDE)
            caja.grid(row=0, column=k, sticky="nsew", padx=(0, 14))
            tk.Label(caja, text=titulo.upper(), bg=SUAVE, fg=TENUE,
                     font=(FS, 8)).pack(anchor="w", pady=(0, 10))
            tk.Label(caja, text=bonito(m["objetivo"]), bg=SUAVE, fg=ACENTO,
                     font=(MONO, 12, "bold")).pack(anchor="w")
            tk.Label(caja, text="Sujeto a:", bg=SUAVE, fg=TENUE, font=(F, 9)).pack(
                anchor="w", pady=(8, 2))
            for r in m["restricciones"]:
                tk.Label(caja, text="   " + bonito(r), bg=SUAVE, fg=TEXTO,
                         font=(MONO, 11)).pack(anchor="w")
            tk.Label(caja, text="   " + bonito(m["no_negatividad"]), bg=SUAVE, fg=TENUE,
                     font=(MONO, 11)).pack(anchor="w", pady=(4, 0))
        for nota in p["notas"]:
            tk.Label(t, text="●  " + bonito(nota), bg=TARJETA, fg=AMBAR, font=(F, 10),
                     justify="left", wraplength=900).pack(anchor="w", pady=(12, 0))

    def _paso_aviso(self, raiz, p):
        color = {"info": ACENTO, "exito": VERDE, "error": ROJO}.get(p["nivel"], ACENTO)
        t = self.tarjeta(raiz, None, p["titulo"], franja=color)
        for linea in p["lineas"]:
            tk.Label(t, text=bonito(linea), bg=TARJETA, fg=TEXTO, font=(F, 10),
                     justify="left", wraplength=900).pack(anchor="w", pady=2)
        self.caja_operaciones(t, p.get("operaciones"))

    def _paso_fase(self, raiz, p):
        b = tk.Frame(raiz, bg=LATERAL, padx=26, pady=18)
        b.pack(fill="x", pady=(8, 16))
        tk.Label(b, text="FASE %d" % p["numero"], bg=ACENTO, fg="#FFFFFF", font=(FS, 9),
                 padx=10, pady=3).pack(side="left", anchor="n", padx=(0, 18))
        txt = tk.Frame(b, bg=LATERAL)
        txt.pack(side="left", fill="x")
        tk.Label(txt, text=bonito(p["titulo"]), bg=LATERAL, fg="#FFFFFF",
                 font=(FS, 14)).pack(anchor="w")
        tk.Label(txt, text=p["descripcion"], bg=LATERAL, fg=LATERAL_TENUE,
                 font=(F, 10)).pack(anchor="w", pady=(2, 0))

    def _paso_preparacion(self, raiz, p):
        t = self.tarjeta(raiz, "PREPARACIÓN", p["titulo"])
        tk.Label(t, text=bonito(p["texto"]), bg=TARJETA, fg=TEXTO, font=(F, 10),
                 justify="left", wraplength=900).pack(anchor="w", pady=(0, 12))
        self.tabla(t, p["tabla"])
        self.caja_operaciones(t, p["operaciones"],
                              "Operaciones para anular los coeficientes en R0")

    def _paso_iteracion(self, raiz, p):
        fase = "FASE %d  ·  " % p["fase"] if p["fase"] else ""
        titulo = "Iteración %d" % p["numero"]
        t = self.tarjeta(raiz, fase + "ITERACIÓN %d" % p["numero"], titulo,
                         subtitulo="Tabla actual (antes de pivotear): se elige la variable "
                                   "que entra y la que sale.")

        chips = tk.Frame(t, bg=TARJETA)
        chips.pack(anchor="w", pady=(0, 12))
        self.chip(chips, "Entra", p["entra"], VERDE_SUAVE, VERDE).pack(side="left",
                                                                      padx=(0, 8))
        if p["sale"]:
            self.chip(chips, "Sale", p["sale"], AMBAR_SUAVE, AMBAR).pack(side="left",
                                                                        padx=(0, 8))
            self.chip(chips, "Pivote", p["pivote"]).pack(side="left")
        else:
            self.chip(chips, "Sale", "ninguna", ROJO_SUAVE, ROJO).pack(side="left")

        explica = ("Entra %s por tener el coeficiente %s del renglón 0 (%s)."
                   % (p["entra"], p["criterio"], p["coef_entra"]))
        if p["sale"]:
            explica += (" Sale %s por tener el menor cociente LD ÷ coeficiente (%s)."
                        % (p["sale"], p["cociente"]))
        tk.Label(t, text=bonito(explica), bg=TARJETA, fg=TENUE, font=(F, 10),
                 justify="left", wraplength=900).pack(anchor="w", pady=(0, 12))

        self.tabla(t, p["tabla"])

        if not p["sale"]:
            aviso = tk.Frame(t, bg=ROJO_SUAVE, padx=14, pady=10)
            aviso.pack(anchor="w", fill="x", pady=(14, 0))
            tk.Label(aviso, text=bonito("Ningún coeficiente de la columna %s es positivo: "
                                        "no hay variable que salga y %s puede crecer sin "
                                        "límite." % (p["entra"], p["entra"])),
                     bg=ROJO_SUAVE, fg=ROJO, font=(FS, 10), justify="left",
                     wraplength=880).pack(anchor="w")
            return

        self.caja_operaciones(t, p["operaciones"])
        self.resumen(t, p["resumen"], "Resultados de la iteración %d" % p["numero"])

    def _paso_optima(self, raiz, p):
        fase = " de la Fase %d" % p["fase"] if p["fase"] else ""
        t = self.tarjeta(raiz, "TABLA FINAL", "Tabla óptima" + fase, color=VERDE,
                         franja=VERDE)
        tk.Label(t, text=bonito(p["mensaje"]), bg=TARJETA, fg=VERDE, font=(FS, 10),
                 justify="left", wraplength=900).pack(anchor="w", pady=(0, 12))
        self.tabla(t, p["tabla"])
        self.resumen(t, p["resumen"], "Solución de esta tabla")

    # ---- resultado final
    def _resultado(self, raiz, r):
        est = r["estado"]
        if est == "optimo":
            t = self.tarjeta(raiz, "RESULTADO", "Solución óptima", color=VERDE,
                             franja=VERDE)
            fila = tk.Frame(t, bg=TARJETA)
            fila.pack(anchor="w", fill="x")
            zc = tk.Frame(fila, bg=VERDE_SUAVE, padx=28, pady=18)
            zc.pack(side="left", fill="y", padx=(0, 20))
            tk.Label(zc, text="Z %s" % ("máxima" if r["sentido"] == "max" else "mínima"),
                     bg=VERDE_SUAVE, fg=VERDE, font=(FS, 10)).pack(anchor="w")
            tk.Label(zc, text=bonito(r["z"]), bg=VERDE_SUAVE, fg=VERDE,
                     font=(FS, 30)).pack(anchor="w")
            dec = self._decimal(r["z"])
            if dec:
                tk.Label(zc, text="≈ " + dec, bg=VERDE_SUAVE, fg=VERDE,
                         font=(F, 10)).pack(anchor="w")

            der = tk.Frame(fila, bg=TARJETA)
            der.pack(side="left", fill="both", expand=True)
            self._mosaico(der, "Variables de decisión", r["variables"], True)
            if r["holguras"]:
                self._mosaico(der, "Holgura / exceso", r["holguras"], False)
            if r["multiples"]:
                nota = tk.Frame(t, bg=AMBAR_SUAVE, padx=14, pady=10)
                nota.pack(anchor="w", fill="x", pady=(16, 0))
                tk.Label(nota, text=bonito(
                    "Soluciones óptimas múltiples: la(s) variable(s) no básica(s) %s "
                    "tiene(n) coeficiente 0 en el renglón Z, así que existen otras "
                    "soluciones con el mismo valor de Z." % ", ".join(r["multiples"])),
                    bg=AMBAR_SUAVE, fg=AMBAR, font=(F, 10), justify="left",
                    wraplength=880).pack(anchor="w")
            return

        color = ROJO if est == "infactible" else AMBAR
        suave = ROJO_SUAVE if est == "infactible" else AMBAR_SUAVE
        icono = {"infactible": "✕", "no_acotado": "∞"}.get(est, "!")
        t = self.tarjeta(raiz, "RESULTADO", None, color=color, franja=color)
        fila = tk.Frame(t, bg=TARJETA)
        fila.pack(anchor="w", fill="x")
        cv = tk.Canvas(fila, width=56, height=56, bg=TARJETA, highlightthickness=0)
        cv.pack(side="left", anchor="n", padx=(0, 18))
        cv.create_oval(2, 2, 54, 54, fill=suave, outline="")
        cv.create_text(28, 28, text=icono, fill=color, font=(FS, 20))
        txt = tk.Frame(fila, bg=TARJETA)
        txt.pack(side="left", fill="x", expand=True)
        tk.Label(txt, text=r["titulo"], bg=TARJETA, fg=color, font=(FS, 16)).pack(anchor="w")
        tk.Label(txt, text=bonito(r["mensaje"]), bg=TARJETA, fg=TEXTO, font=(F, 10),
                 justify="left", wraplength=820).pack(anchor="w", pady=(4, 0))
        if est == "no_aplica":
            b = tk.Frame(txt, bg=TARJETA)
            b.pack(anchor="w", pady=(14, 0))
            Boton(b, "Resolver con la Gran M", lambda: self.resolver("gran_m")).pack(
                side="left")
            Boton(b, "Resolver con Dos Fases", lambda: self.resolver("dos_fases"),
                  "secundario").pack(side="left", padx=(10, 0))

    def _mosaico(self, master, titulo, pares, grande):
        tk.Label(master, text=titulo.upper(), bg=TARJETA, fg=TENUE,
                 font=(FS, 8)).pack(anchor="w", pady=(0 if grande else 12, 6))
        f = tk.Frame(master, bg=TARJETA)
        f.pack(anchor="w")
        for k, (nombre, valor) in enumerate(pares):
            c = tk.Frame(f, bg=SUAVE, padx=16, pady=8 if grande else 5,
                         highlightthickness=1, highlightbackground=BORDE)
            c.grid(row=k // 6, column=k % 6, padx=(0, 8), pady=(0, 8), sticky="w")
            tk.Label(c, text=bonito(nombre), bg=SUAVE, fg=TENUE,
                     font=(F, 10 if grande else 9)).pack(anchor="w")
            tk.Label(c, text=bonito(valor), bg=SUAVE, fg=TEXTO,
                     font=(FS, 16 if grande else 11)).pack(anchor="w")

    @staticmethod
    def _decimal(texto):
        """'21/4' -> '5.25' (división larga hecha a mano, 4 decimales)."""
        if "/" not in texto:
            return None
        a, b = texto.split("/")
        a, b = int(a), int(b)
        signo = "-" if a < 0 else ""
        a = abs(a)
        entero, resto = a // b, a % b
        dec = ""
        for _ in range(4):
            resto *= 10
            dec += str(resto // b)
            resto %= b
        dec = dec.rstrip("0") or "0"
        return bonito(signo + str(entero) + "." + dec)


if __name__ == "__main__":
    App().mainloop()
