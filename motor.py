# -*- coding: utf-8 -*-
"""
MOTOR DE CÁLCULO — Programación Lineal
    Método Simplex, Método de la Gran M y Método de las Dos Fases.

Este archivo NO usa ninguna librería: la aritmética exacta con fracciones y
las expresiones con la M simbólica están programadas a mano.

La función principal es  resolver(metodo, problema), que devuelve la lista de
pasos (tablas, variables que entran/salen, operaciones de renglón, etc.) y el
resultado final, para que la interfaz gráfica los muestre.

Convenciones:
  - Renglón 0 (R0):  Z - c1x1 - c2x2 - ... = 0
  - Maximizar: entra la variable con el coeficiente MÁS NEGATIVO de R0;
               la tabla es óptima cuando todos son >= 0.
  - Minimizar: entra la variable con el coeficiente MÁS POSITIVO de R0;
               la tabla es óptima cuando todos son <= 0.
  - Sale la variable básica con el menor cociente  LD / coeficiente (> 0).
  - Variables: x (decisión), s (holgura), e (exceso), a (artificial).
"""


# =====================================================================
#   ARITMÉTICA DE FRACCIONES
# =====================================================================

def mcd(a, b):
    """Máximo común divisor por el algoritmo de Euclides."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


class Fraccion:
    """Número racional exacto  num/den  (den > 0, siempre simplificado)."""
    __slots__ = ("num", "den")

    def __init__(self, num=0, den=1):
        if den == 0:
            raise ZeroDivisionError("División entre cero")
        if den < 0:
            num, den = -num, -den
        g = mcd(num, den)
        if g > 1:
            num //= g
            den //= g
        self.num = num
        self.den = den

    @staticmethod
    def de(x):
        if isinstance(x, Fraccion):
            return x
        if isinstance(x, int):
            return Fraccion(x)
        raise TypeError("Tipo no soportado: %r" % (x,))

    def __add__(self, o):
        o = Fraccion.de(o)
        return Fraccion(self.num * o.den + o.num * self.den, self.den * o.den)

    def __neg__(self):
        return Fraccion(-self.num, self.den)

    def __sub__(self, o):
        return self + (-Fraccion.de(o))

    def __mul__(self, o):
        o = Fraccion.de(o)
        return Fraccion(self.num * o.num, self.den * o.den)

    def __truediv__(self, o):
        o = Fraccion.de(o)
        if o.num == 0:
            raise ZeroDivisionError("División entre cero")
        return Fraccion(self.num * o.den, self.den * o.num)

    def __abs__(self):
        return Fraccion(abs(self.num), self.den)

    def signo(self):
        return (self.num > 0) - (self.num < 0)

    def _cmp(self, o):
        return (self - Fraccion.de(o)).signo()

    def __eq__(self, o):
        o = Fraccion.de(o)
        return self.num == o.num and self.den == o.den

    def __lt__(self, o):
        return self._cmp(o) < 0

    def __gt__(self, o):
        return self._cmp(o) > 0

    def __str__(self):
        if self.den == 1:
            return str(self.num)
        return "%d/%d" % (self.num, self.den)


class ExprM:
    """Expresión  m*M + c,  con M un número 'muy grande' (Método de la Gran M).

    Para comparar manda primero el coeficiente de M y, si es igual, la
    constante.  En los demás métodos la parte m siempre vale 0.
    """
    __slots__ = ("m", "c")

    def __init__(self, m=0, c=0):
        self.m = Fraccion.de(m)
        self.c = Fraccion.de(c)

    @staticmethod
    def de(x):
        if isinstance(x, ExprM):
            return x
        return ExprM(0, Fraccion.de(x))

    def __add__(self, o):
        o = ExprM.de(o)
        return ExprM(self.m + o.m, self.c + o.c)

    def __neg__(self):
        return ExprM(-self.m, -self.c)

    def __sub__(self, o):
        return self + (-ExprM.de(o))

    def __mul__(self, k):
        """Producto por un escalar (Fraccion o entero)."""
        k = Fraccion.de(k)
        return ExprM(self.m * k, self.c * k)

    def es_cero(self):
        return self.m == 0 and self.c == 0

    def signo(self):
        if self.m != 0:
            return self.m.signo()
        return self.c.signo()

    def _cmp(self, o):
        return (self - ExprM.de(o)).signo()

    def __eq__(self, o):
        return self._cmp(o) == 0

    def __lt__(self, o):
        return self._cmp(o) < 0

    def __gt__(self, o):
        return self._cmp(o) > 0

    def __str__(self):
        if self.m == 0:
            return str(self.c)
        if self.m == 1:
            parte_m = "M"
        elif self.m == -1:
            parte_m = "-M"
        elif self.m.den == 1:
            parte_m = "%sM" % self.m
        else:
            parte_m = "(%s)M" % self.m
        if self.c == 0:
            return parte_m
        if self.c > 0:
            return "%s+%s" % (parte_m, self.c)
        return "%s-%s" % (parte_m, abs(self.c))


def leer_numero(texto):
    """Convierte '3', '-2.5', '3/4', '+.5' a Fraccion (sin usar float)."""
    t = texto.strip()
    if not t:
        raise ValueError("número vacío")
    if "/" in t:
        a, b = t.split("/", 1)
        den = leer_numero(b)
        if den == 0:
            raise ValueError("denominador cero")
        return leer_numero(a) / den
    signo = 1
    if t[0] in "+-":
        if t[0] == "-":
            signo = -1
        t = t[1:]
    if "." in t:
        entero, decimal = t.split(".", 1)
        digitos = entero + decimal
        if not digitos.isdigit():
            raise ValueError("número inválido")
        return Fraccion(signo * int(digitos), 10 ** len(decimal))
    if not t.isdigit():
        raise ValueError("número inválido")
    return Fraccion(signo * int(t))


# =====================================================================
#   TEXTO DE EXPRESIONES
# =====================================================================

def fmt_coef(coef):
    """Coeficiente dentro de un término: las fracciones van entre paréntesis."""
    if isinstance(coef, ExprM) and coef.m == 0:
        coef = coef.c
    if isinstance(coef, Fraccion) and coef.den != 1:
        return "(%s)" % coef
    if isinstance(coef, ExprM) and coef.c != 0:
        return "(%s)" % coef
    return str(coef)


def combinacion(coefs, nombres):
    """Construye un texto del tipo  3x1 - (1/2)x2 + s1."""
    texto = ""
    for coef, nombre in zip(coefs, nombres):
        if coef == 0:
            continue
        negativo = coef < 0
        valor = -coef if negativo else coef
        cuerpo = nombre if valor == 1 else fmt_coef(valor) + nombre
        if texto == "":
            texto = ("-" if negativo else "") + cuerpo
        else:
            texto += (" - " if negativo else " + ") + cuerpo
    return texto if texto else "0"


def _termino_operacion(f, renglon):
    """Texto ' - 2·R1', ' + (1/2)·R1' o ' - ((8/15)M-1/3)·R1' para R_i ← R_i - f·R_r."""
    if isinstance(f, ExprM) and f.m == 0:
        f = f.c
    if isinstance(f, Fraccion):
        signo = " + " if f < 0 else " - "
        valor = abs(f)
        return signo + ("" if valor == 1 else fmt_coef(valor) + "·") + renglon
    if f.c == 0:
        signo = " + " if f.m < 0 else " - "
        valor = -f if f.m < 0 else f
        return signo + fmt_coef(valor) + "·" + renglon
    return " - (%s)·%s" % (f, renglon)


# =====================================================================
#   TABLA SIMPLEX
# =====================================================================

class Tabla:
    def __init__(self, nombres, tipos, filas, z, base, sentido, etiqueta="Z"):
        self.nombres = nombres      # nombre de cada columna (variable)
        self.tipos = tipos          # 'x', 's', 'e' o 'a' por columna
        self.filas = filas          # renglones 1..m (Fraccion), el último = LD
        self.z = z                  # renglón 0 (ExprM), el último = valor de Z
        self.base = base            # índice de la variable básica de cada renglón
        self.sentido = sentido      # 'max' o 'min'
        self.etiqueta = etiqueta    # 'Z' o 'W'


def foto(t, col=None, fila=None, razones=None):
    """Copia en texto de la tabla, para mostrarla en pantalla."""
    return {
        "etiqueta": t.etiqueta,
        "nombres": list(t.nombres),
        "base": [t.nombres[b] for b in t.base],
        "z": [str(v) for v in t.z],
        "filas": [[str(v) for v in f] for f in t.filas],
        "col": col,
        "fila": fila,
        "razones": razones,
    }


def resumen(t):
    """Valores de la solución básica actual."""
    return {
        "basicas": [(t.nombres[b], str(t.filas[i][-1])) for i, b in enumerate(t.base)],
        "no_basicas": [t.nombres[j] for j in range(len(t.nombres)) if j not in t.base],
        "etiqueta": t.etiqueta,
        "valor": str(t.z[-1]),
    }


def elegir_entrante(t):
    """Columna que entra a la base, o None si la tabla ya es óptima."""
    mejor = None
    for j in range(len(t.nombres)):
        if j in t.base:
            continue
        v = t.z[j]
        if t.sentido == "max":
            if v < 0 and (mejor is None or v < t.z[mejor]):
                mejor = j
        else:
            if v > 0 and (mejor is None or v > t.z[mejor]):
                mejor = j
    return mejor


def elegir_saliente(t, col):
    """Prueba del cociente mínimo. Devuelve (renglón que sale o None, detalle)."""
    detalle = []
    mejor = None
    mejor_r = None
    for i, fila in enumerate(t.filas):
        a = fila[col]
        if a > 0:
            r = fila[-1] / a
            detalle.append((i, a, r))
            if (mejor is None or r < mejor_r
                    or (r == mejor_r and t.base[i] < t.base[mejor])):
                mejor, mejor_r = i, r
        else:
            detalle.append((i, a, None))
    return mejor, detalle


def hacer_cero_en_r0(t, i):
    """R0 ← R0 - (coef)·Ri  para anular el coeficiente de la básica del renglón i."""
    b = t.base[i]
    f = t.z[b]
    if f.es_cero():
        return None
    t.z = [a - f * v for a, v in zip(t.z, t.filas[i])]
    return "R0 ← R0" + _termino_operacion(f, "R%d" % (i + 1))


def pivotear(t, r, c):
    """Operaciones de Gauss-Jordan sobre el pivote (r, c). Devuelve su descripción."""
    ops = []
    piv = t.filas[r][c]
    t.filas[r] = [v / piv for v in t.filas[r]]
    if piv != 1:
        ops.append("R%d ← R%d ÷ %s" % (r + 1, r + 1, fmt_coef(piv)))
    else:
        ops.append("R%d ← R%d   (el pivote ya es 1)" % (r + 1, r + 1))
    for i in range(len(t.filas)):
        if i == r:
            continue
        f = t.filas[i][c]
        if f != 0:
            t.filas[i] = [a - f * b for a, b in zip(t.filas[i], t.filas[r])]
            ops.append("R%d ← R%d" % (i + 1, i + 1) + _termino_operacion(f, "R%d" % (r + 1)))
    f = t.z[c]
    if not f.es_cero():
        t.z = [a - f * b for a, b in zip(t.z, t.filas[r])]
        ops.append("R0 ← R0" + _termino_operacion(f, "R%d" % (r + 1)))
    t.base[r] = c
    return ops


def iterar(t, pasos, fase=None, max_iter=100):
    """Aplica el simplex hasta el óptimo. Devuelve (estado, iteraciones)."""
    it = 0
    criterio = "más negativo" if t.sentido == "max" else "más positivo"
    while True:
        col = elegir_entrante(t)
        if col is None:
            if t.sentido == "max":
                msg = ("Todos los coeficientes del renglón %s son ≥ 0, por lo tanto "
                       "la tabla es óptima." % t.etiqueta)
            else:
                msg = ("Todos los coeficientes del renglón %s son ≤ 0, por lo tanto "
                       "la tabla es óptima." % t.etiqueta)
            pasos.append({"tipo": "optima", "fase": fase, "tabla": foto(t),
                          "mensaje": msg, "resumen": resumen(t)})
            return "optimo", it
        if it >= max_iter:
            return "limite", it

        it += 1
        fila, detalle = elegir_saliente(t, col)
        razones = []
        for i, a, r in detalle:
            if r is None:
                razones.append("—")
            else:
                razones.append("%s ÷ %s = %s" % (t.filas[i][-1], a, r))

        paso = {
            "tipo": "iteracion",
            "fase": fase,
            "numero": it,
            "entra": t.nombres[col],
            "coef_entra": str(t.z[col]),
            "criterio": criterio,
            "sale": None,
            "pivote": None,
            "cociente": None,
            "tabla": foto(t, col, fila, razones),
            "operaciones": [],
            "resumen": None,
        }
        if fila is None:
            pasos.append(paso)
            return "no_acotado", it

        paso["sale"] = t.nombres[t.base[fila]]
        paso["pivote"] = str(t.filas[fila][col])
        paso["cociente"] = str(t.filas[fila][-1] / t.filas[fila][col])
        paso["operaciones"] = pivotear(t, fila, col)
        paso["resumen"] = resumen(t)
        pasos.append(paso)


# =====================================================================
#   FORMA ESTÁNDAR
# =====================================================================

def lineas_modelo(prob):
    n = len(prob["c"])
    x = ["x%d" % (j + 1) for j in range(n)]
    return {
        "objetivo": "%s Z = %s" % ("Max" if prob["sentido"] == "max" else "Min",
                                  combinacion(prob["c"], x)),
        "restricciones": ["%s %s %s" % (combinacion(coefs, x),
                                        {"<=": "≤", ">=": "≥", "=": "="}[signo], ld)
                          for coefs, signo, ld in prob["restr"]],
        "no_negatividad": ", ".join(x) + " ≥ 0",
    }


def construir_forma_estandar(prob):
    """Agrega holguras, excesos y artificiales. Devuelve un diccionario."""
    n = len(prob["c"])
    notas = []
    restr = []
    for i, (coefs, signo, ld) in enumerate(prob["restr"]):
        if ld < 0:
            nuevo = {"<=": ">=", ">=": "<=", "=": "="}[signo]
            notas.append("La restricción %d tiene lado derecho negativo: se multiplicó "
                         "por -1 y el signo %s cambió a %s."
                         % (i + 1, signo.replace("<=", "≤").replace(">=", "≥"),
                            nuevo.replace("<=", "≤").replace(">=", "≥")))
            coefs, signo, ld = [-v for v in coefs], nuevo, -ld
        restr.append((coefs, signo, ld))

    nombres = ["x%d" % (j + 1) for j in range(n)]
    tipos = ["x"] * n
    m = len(restr)
    col_hol = [None] * m
    col_art = [None] * m
    for i, (_, signo, _) in enumerate(restr):
        if signo == "<=":
            col_hol[i] = len(nombres)
            nombres.append("s%d" % (i + 1))
            tipos.append("s")
        elif signo == ">=":
            col_hol[i] = len(nombres)
            nombres.append("e%d" % (i + 1))
            tipos.append("e")
    for i, (_, signo, _) in enumerate(restr):
        if signo in (">=", "="):
            col_art[i] = len(nombres)
            nombres.append("a%d" % (i + 1))
            tipos.append("a")

    total = len(nombres)
    filas, base = [], []
    for i, (coefs, signo, ld) in enumerate(restr):
        fila = list(coefs) + [Fraccion(0)] * (total - n) + [ld]
        if signo == "<=":
            fila[col_hol[i]] = Fraccion(1)
            base.append(col_hol[i])
        elif signo == ">=":
            fila[col_hol[i]] = Fraccion(-1)
            fila[col_art[i]] = Fraccion(1)
            base.append(col_art[i])
        else:
            fila[col_art[i]] = Fraccion(1)
            base.append(col_art[i])
        filas.append(fila)
    return {"n": n, "nombres": nombres, "tipos": tipos, "filas": filas,
            "base": base, "notas": notas}


def lineas_forma_estandar(prob, fe, con_m=False):
    n = fe["n"]
    nombres = fe["nombres"]
    objetivo = combinacion(prob["c"], nombres[:n])
    if con_m:
        signo = " - " if prob["sentido"] == "max" else " + "
        for j, tp in enumerate(fe["tipos"]):
            if tp == "a":
                objetivo += signo + "M" + nombres[j]
    return {
        "objetivo": "%s Z = %s" % ("Max" if prob["sentido"] == "max" else "Min", objetivo),
        "restricciones": ["%s = %s" % (combinacion(f[:-1], nombres), f[-1])
                          for f in fe["filas"]],
        "no_negatividad": ", ".join(nombres) + " ≥ 0",
    }


def renglon0_original(prob, total):
    z = [ExprM() for _ in range(total + 1)]
    for j in range(len(prob["c"])):
        z[j] = ExprM(0, -prob["c"][j])
    return z


def texto_r0(t):
    """Renglón 0 como ecuación:  Z - 3x1 - 5x2 + Ma1 = 0."""
    texto = combinacion(t.z[:-1], t.nombres)
    if texto == "0":
        return "%s = %s" % (t.etiqueta, t.z[-1])
    if texto.startswith("-"):
        texto = "- " + texto[1:]
    else:
        texto = "+ " + texto
    return "%s %s = %s" % (t.etiqueta, texto, t.z[-1])


# =====================================================================
#   RESULTADO FINAL
# =====================================================================

def armar_resultado(t, estado, n):
    art_pos = [(t.nombres[b], str(t.filas[i][-1])) for i, b in enumerate(t.base)
               if t.tipos[b] == "a" and t.filas[i][-1] > 0]

    if estado == "limite":
        return {"estado": "limite", "titulo": "Límite de iteraciones alcanzado",
                "mensaje": "No se llegó a una solución dentro del número máximo de iteraciones."}

    if estado == "no_acotado":
        if art_pos:
            return {"estado": "no_acotado",
                    "titulo": "El problema no tiene solución óptima",
                    "mensaje": "El problema resultó no acotado mientras las variables "
                               "artificiales (%s) seguían siendo positivas. Puede ser no "
                               "factible o no acotado; se recomienda verificarlo con el "
                               "Método de las Dos Fases."
                               % ", ".join("%s = %s" % p for p in art_pos)}
        return {"estado": "no_acotado",
                "titulo": "Solución no acotada",
                "mensaje": "La variable que entra puede aumentar indefinidamente sin que "
                           "ninguna restricción lo impida, así que Z puede %s sin límite. "
                           "No existe una solución óptima finita."
                           % ("crecer" if t.sentido == "max" else "disminuir")}

    if art_pos or t.z[-1].m != 0:
        return {"estado": "infactible",
                "titulo": "El problema no tiene solución factible",
                "mensaje": "En la tabla óptima quedan variables artificiales con valor "
                           "positivo (%s). No existe una solución básica factible (BF) que "
                           "satisfaga todas las restricciones originales."
                           % ", ".join("%s = %s" % p for p in art_pos)}

    valores = [Fraccion(0)] * len(t.nombres)
    for i, b in enumerate(t.base):
        valores[b] = t.filas[i][-1]
    return {
        "estado": "optimo",
        "titulo": "Solución óptima",
        "sentido": t.sentido,
        "z": str(t.z[-1].c),
        "variables": [(t.nombres[j], str(valores[j])) for j in range(n)],
        "holguras": [(t.nombres[j], str(valores[j])) for j in range(n, len(t.nombres))
                     if t.tipos[j] in ("s", "e")],
        "multiples": [t.nombres[j] for j in range(len(t.nombres))
                      if j not in t.base and t.tipos[j] != "a" and t.z[j].es_cero()],
    }


# =====================================================================
#   MÉTODOS
# =====================================================================

def _simplex(prob, pasos):
    fe = construir_forma_estandar(prob)
    hay_art = "a" in fe["tipos"]
    pasos.append({"tipo": "modelo", "original": lineas_modelo(prob),
                  "estandar": None if hay_art else lineas_forma_estandar(prob, fe),
                  "titulo_estandar": "Forma estándar (con holguras)",
                  "notas": fe["notas"]})
    if hay_art:
        return {"estado": "no_aplica",
                "titulo": "El método simplex no se puede aplicar",
                "mensaje": "El problema tiene restricciones de tipo ≥ o = (con lado derecho "
                           "no negativo). El simplex requiere la forma canónica, con "
                           "restricciones ≤ y lado derecho ≥ 0, para iniciar en el origen. "
                           "Aquí el origen no es una solución básica factible (BF), así que "
                           "hay que usar el Método de la Gran M o el de las Dos Fases."}, 0

    t = Tabla(fe["nombres"], fe["tipos"], fe["filas"],
              renglon0_original(prob, len(fe["nombres"])), fe["base"], prob["sentido"])
    pasos.append({"tipo": "aviso", "nivel": "info", "titulo": "Tabla inicial",
                  "lineas": ["Renglón 0:  " + texto_r0(t),
                             "Las variables de holgura forman la base inicial: el origen "
                             "(todas las x = 0) es la primera solución BF."]})
    estado, it = iterar(t, pasos)
    return armar_resultado(t, estado, fe["n"]), it


def _gran_m(prob, pasos):
    fe = construir_forma_estandar(prob)
    artificiales = [j for j, tp in enumerate(fe["tipos"]) if tp == "a"]
    pasos.append({"tipo": "modelo", "original": lineas_modelo(prob),
                  "estandar": lineas_forma_estandar(prob, fe, con_m=True),
                  "titulo_estandar": "Forma estándar (artificiales penalizadas con M)",
                  "notas": fe["notas"] + ([] if artificiales else [
                      "Todas las restricciones son ≤: no se necesitan variables artificiales "
                      "y el método se reduce al simplex normal."])})

    z = renglon0_original(prob, len(fe["nombres"]))
    # Maximizar: la artificial tiene costo -M, en R0 aparece +M.
    # Minimizar: la artificial tiene costo +M, en R0 aparece -M.
    for j in artificiales:
        z[j] = ExprM(1 if prob["sentido"] == "max" else -1, 0)
    t = Tabla(fe["nombres"], fe["tipos"], fe["filas"], z, fe["base"], prob["sentido"])

    if artificiales:
        antes = foto(t)
        ecuacion = texto_r0(t)
        ops = [op for op in (hacer_cero_en_r0(t, i) for i, b in enumerate(t.base)
                             if t.tipos[b] == "a") if op]
        pasos.append({"tipo": "preparacion", "titulo": "Preparación del renglón Z",
                      "texto": "Renglón 0 inicial:  %s.  Las variables artificiales son "
                               "básicas, por lo que su coeficiente en R0 debe ser 0; se "
                               "eliminan con operaciones de renglón." % ecuacion,
                      "tabla": antes, "operaciones": ops})
    estado, it = iterar(t, pasos)
    return armar_resultado(t, estado, fe["n"]), it


def _dos_fases(prob, pasos):
    fe = construir_forma_estandar(prob)
    n = fe["n"]
    artificiales = [j for j, tp in enumerate(fe["tipos"]) if tp == "a"]
    pasos.append({"tipo": "modelo", "original": lineas_modelo(prob),
                  "estandar": lineas_forma_estandar(prob, fe),
                  "titulo_estandar": "Forma estándar (con artificiales)",
                  "notas": fe["notas"]})

    nombres, tipos, filas, base = fe["nombres"], fe["tipos"], fe["filas"], fe["base"]
    total_it = 0

    if not artificiales:
        pasos.append({"tipo": "aviso", "nivel": "info",
                      "titulo": "La Fase 1 no es necesaria",
                      "lineas": ["No hay variables artificiales: el origen ya es una solución "
                                 "básica factible, así que se pasa directamente a la Fase 2."]})
    else:
        # ----------------------------- FASE 1 -----------------------------
        w_txt = " + ".join(nombres[j] for j in artificiales)
        pasos.append({"tipo": "fase", "numero": 1, "titulo": "Minimizar W = " + w_txt,
                      "descripcion": "Se busca una solución básica factible haciendo cero "
                                     "todas las variables artificiales."})
        z = [ExprM() for _ in range(len(nombres) + 1)]
        for j in artificiales:
            z[j] = ExprM(0, -1)
        t1 = Tabla(nombres, tipos, filas, z, base, "min", "W")
        antes = foto(t1)
        ecuacion = texto_r0(t1)
        ops = [op for op in (hacer_cero_en_r0(t1, i) for i, b in enumerate(t1.base)
                             if t1.tipos[b] == "a") if op]
        pasos.append({"tipo": "preparacion", "titulo": "Preparación del renglón W",
                      "texto": "Renglón 0 inicial:  %s.  Las variables artificiales son "
                               "básicas, por lo que su coeficiente en R0 debe ser 0; se "
                               "eliminan con operaciones de renglón." % ecuacion,
                      "tabla": antes, "operaciones": ops})
        estado, it = iterar(t1, pasos, fase=1)
        total_it += it
        if estado != "optimo":
            return {"estado": "limite", "titulo": "La Fase 1 no terminó",
                    "mensaje": "No se pudo completar la Fase 1."}, total_it

        w = t1.z[-1].c
        if w > 0:
            return {"estado": "infactible",
                    "titulo": "El problema no tiene solución factible",
                    "mensaje": "Al terminar la Fase 1, el valor mínimo de W es %s > 0: no es "
                               "posible hacer cero todas las variables artificiales. No existe "
                               "una solución básica factible (BF) que satisfaga todas las "
                               "restricciones." % w}, total_it

        lineas = ["W mínimo = 0: todas las variables artificiales valen 0, por lo que se "
                  "obtuvo una solución básica factible (BF) del problema original."]
        ops = []
        i = 0
        while i < len(t1.filas):
            b = t1.base[i]
            if t1.tipos[b] == "a":
                j = None
                for k in range(len(t1.nombres)):
                    if t1.tipos[k] != "a" and t1.filas[i][k] != 0:
                        j = k
                        break
                if j is None:
                    lineas.append("%s sigue básica con valor 0 y su renglón no tiene "
                                  "coeficientes en variables reales: la restricción es "
                                  "redundante y se elimina." % t1.nombres[b])
                    del t1.filas[i]
                    del t1.base[i]
                    continue
                lineas.append("%s sigue básica con valor 0; se reemplaza por %s "
                              "(pivote en R%d)." % (t1.nombres[b], t1.nombres[j], i + 1))
                ops += pivotear(t1, i, j)
            i += 1
        lineas.append("Se eliminan las columnas de las variables artificiales.")
        pasos.append({"tipo": "aviso", "nivel": "exito", "titulo": "Fin de la Fase 1",
                      "lineas": lineas, "operaciones": ops})

        conservar = [j for j in range(len(t1.nombres)) if t1.tipos[j] != "a"]
        nuevo = {j: k for k, j in enumerate(conservar)}
        nombres = [t1.nombres[j] for j in conservar]
        tipos = [t1.tipos[j] for j in conservar]
        filas = [[f[j] for j in conservar] + [f[-1]] for f in t1.filas]
        base = [nuevo[b] for b in t1.base]

    # ----------------------------- FASE 2 -----------------------------
    pasos.append({"tipo": "fase", "numero": 2,
                  "titulo": "%s Z = %s" % ("Maximizar" if prob["sentido"] == "max"
                                           else "Minimizar",
                                           combinacion(prob["c"], nombres[:n])),
                  "descripcion": "Se optimiza la función objetivo original a partir de la "
                                 "solución BF encontrada."})
    t2 = Tabla(nombres, tipos, filas, renglon0_original(prob, len(nombres)), base,
               prob["sentido"])
    antes = foto(t2)
    ecuacion = texto_r0(t2)
    ops = [op for op in (hacer_cero_en_r0(t2, i) for i in range(len(t2.base))) if op]
    if ops:
        pasos.append({"tipo": "preparacion", "titulo": "Preparación del renglón Z",
                      "texto": "Renglón 0 con la función objetivo original:  %s.  Las "
                               "variables básicas deben tener coeficiente 0 en R0; se "
                               "eliminan con operaciones de renglón." % ecuacion,
                      "tabla": antes, "operaciones": ops})
    estado, it = iterar(t2, pasos, fase=2)
    total_it += it
    return armar_resultado(t2, estado, n), total_it


METODOS = {"simplex": _simplex, "gran_m": _gran_m, "dos_fases": _dos_fases}


def resolver(metodo, prob):
    """prob = {'sentido': 'max'|'min', 'c': [Fraccion],
               'restr': [([Fraccion], '<='|'>='|'=', Fraccion)]}"""
    pasos = []
    resultado, iteraciones = METODOS[metodo](prob, pasos)
    return {"pasos": pasos, "resultado": resultado, "iteraciones": iteraciones}
