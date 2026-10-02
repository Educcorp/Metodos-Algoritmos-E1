# -*- coding: utf-8 -*-
"""
MOTOR DE CÁLCULO — Método Simplex, Método de la Gran M y Método de las Dos Fases.

No se usa ninguna librería: las fracciones y la M están programadas a mano y
los problemas se resuelven con iteraciones sobre la tabla simplex.

La ventana llama a  resolver(metodo, problema)  y recibe la lista de pasos
(textos y tablas) con todas las iteraciones y el resultado final.

Convenciones:
  - Renglón Z:  Z - c1x1 - c2x2 - ... = 0
  - Maximizar: entra el coeficiente MÁS NEGATIVO del renglón Z (óptimo si todos >= 0).
  - Minimizar: entra el coeficiente MÁS POSITIVO del renglón Z (óptimo si todos <= 0).
  - Sale el renglón con el menor cociente  LD / coeficiente  (solo coeficientes > 0).
  - Variables: x (decisión), s (holgura), e (exceso), a (artificial).

=============================================================================
  ÍNDICE PARA EXPONER  (copiar la etiqueta y buscarla con Ctrl+F)
  Cada método está numerado en el orden en que se ejecuta.
=============================================================================

  MÉTODO SIMPLEX
    #SIMPLEX-01  simplex()              Función principal del método
    #SIMPLEX-02  tabla_inicial()        Forma estándar: se agregan holguras (s)
    #SIMPLEX-03  iterar()               Ciclo de iteraciones
    #SIMPLEX-04  elegir_entrante()      Variable que ENTRA
    #SIMPLEX-05  elegir_saliente()      Variable que SALE (cociente mínimo)
    #SIMPLEX-06  pivotear()             Gauss-Jordan
    #SIMPLEX-07  mostrar_resultado()    Z y valores de las variables

  MÉTODO DE LA GRAN M
    #GRAN_M-01   gran_m()               Función principal del método
    #GRAN_M-02   tabla_inicial()        Forma estándar: holguras, excesos y artificiales
    #GRAN_M-03   (dentro de gran_m)     Penalización de las artificiales con M
    #GRAN_M-04   class ExprM            Cómo se representa y compara la M
    #GRAN_M-05   ajustar_renglon_z()    Se hacen 0 las M de las artificiales básicas
    #GRAN_M-06   iterar()               Ciclo de iteraciones
    #GRAN_M-07   elegir_entrante()      Variable que ENTRA
    #GRAN_M-08   elegir_saliente()      Variable que SALE (cociente mínimo)
    #GRAN_M-09   pivotear()             Gauss-Jordan
    #GRAN_M-10   mostrar_resultado()    Z, variables, o aviso de que no hay solución BF

  MÉTODO DE LAS DOS FASES
    #DOS_FASES-01  dos_fases()            Función principal del método
    #DOS_FASES-02  tabla_inicial()        Forma estándar: holguras, excesos y artificiales
    #DOS_FASES-03  (dentro de dos_fases)  FASE 1: renglón W = suma de artificiales
    #DOS_FASES-04  ajustar_renglon_z()    Se hacen 0 las artificiales básicas en W
    #DOS_FASES-05  iterar()               Ciclo de iteraciones (se usa en ambas fases)
    #DOS_FASES-06  elegir_entrante()      Variable que ENTRA
    #DOS_FASES-07  elegir_saliente()      Variable que SALE (cociente mínimo)
    #DOS_FASES-08  pivotear()             Gauss-Jordan
    #DOS_FASES-09  (dentro de dos_fases)  Fin de la Fase 1: ¿W = 0? si no, no hay solución BF
    #DOS_FASES-10  sacar_artificiales()   Se quitan las artificiales de la tabla
    #DOS_FASES-11  (dentro de dos_fases)  FASE 2: función objetivo original
    #DOS_FASES-12  mostrar_resultado()    Z y valores de las variables

  PARTES DE APOYO (las usan los tres métodos)
    #FRACCIONES    class Fraccion         Aritmética exacta con fracciones
    #LEER_NUMERO   leer_numero()          Convierte '3', '2.5' o '3/4' a Fraccion
    #TABLA         class Tabla            Cómo se guarda la tabla simplex
    #MOSTRAR       foto_tabla(), valores_actuales()   Datos que se muestran en pantalla
    #RESOLVER      resolver()             Punto de entrada que llama la ventana
=============================================================================
"""


# =============================================================================
#   #FRACCIONES
#   Fracciones exactas (no float) para que los resultados salgan igual que
#   en la libreta: 21/4 y no 5.2499999...
# =============================================================================

def mcd(a, b):
    """Máximo común divisor (algoritmo de Euclides)."""
    while b:
        a, b = b, a % b
    return abs(a)


def fr(x):
    """Convierte un entero a Fraccion (si ya es Fraccion la deja igual)."""
    return x if isinstance(x, Fraccion) else Fraccion(x)


class Fraccion:
    """Número racional num/den, siempre simplificado y con den > 0."""

    def __init__(self, num=0, den=1):
        if den == 0:
            raise ZeroDivisionError("División entre cero")
        if den < 0:                     # el signo se guarda en el numerador
            num, den = -num, -den
        g = mcd(num, den)               # simplificar:  6/8 -> 3/4
        self.num, self.den = num // g, den // g

    # a/b + c/d = (ad + cb)/bd      a/b · c/d = ac/bd      a/b ÷ c/d = ad/bc
    def __add__(self, o):
        o = fr(o)
        return Fraccion(self.num * o.den + o.num * self.den, self.den * o.den)

    def __neg__(self):
        return Fraccion(-self.num, self.den)

    def __sub__(self, o):
        return self + (-fr(o))

    def __mul__(self, o):
        o = fr(o)
        return Fraccion(self.num * o.num, self.den * o.den)

    def __truediv__(self, o):
        o = fr(o)
        return Fraccion(self.num * o.den, self.den * o.num)

    # Para comparar a con b se revisa el signo de (a - b).
    def __eq__(self, o):
        o = fr(o)
        return self.num == o.num and self.den == o.den

    def __lt__(self, o):
        return (self - o).num < 0

    def __gt__(self, o):
        return (self - o).num > 0

    def __str__(self):
        return str(self.num) if self.den == 1 else "%d/%d" % (self.num, self.den)


# =============================================================================
#   #GRAN_M-04   class ExprM — cómo se representa y compara la M
# =============================================================================

class ExprM:
    """Expresión  m·M + c,  donde M es un número muy grande (Método de la Gran M).

    Se guarda por separado el coeficiente de M (m) y la constante (c).
    Ejemplo:  3M - 1/2  ->  m = 3, c = -1/2.
    Al comparar manda la parte de M; si es igual, decide la constante.
    En Simplex y Dos Fases m siempre vale 0 y se comporta como un número normal.
    """

    def __init__(self, m=0, c=0):
        self.m, self.c = fr(m), fr(c)

    def __add__(self, o):
        return ExprM(self.m + o.m, self.c + o.c)

    def __sub__(self, o):
        return ExprM(self.m - o.m, self.c - o.c)

    def __mul__(self, k):
        """Producto por una fracción:  k·(mM + c) = kmM + kc."""
        return ExprM(self.m * k, self.c * k)

    def es_cero(self):
        return self.m == 0 and self.c == 0

    def signo(self):
        # Si hay parte en M, esa decide el signo; si no, decide la constante.
        v = self.m if self.m != 0 else self.c
        return (v.num > 0) - (v.num < 0)

    def __lt__(self, o):
        o = o if isinstance(o, ExprM) else ExprM(0, o)
        return (self - o).signo() < 0

    def __gt__(self, o):
        o = o if isinstance(o, ExprM) else ExprM(0, o)
        return (self - o).signo() > 0

    def __str__(self):
        if self.m == 0:
            return str(self.c)
        if self.m == 1:
            texto = "M"
        elif self.m == -1:
            texto = "-M"
        elif self.m.den == 1:
            texto = "%sM" % self.m
        else:
            texto = "(%s)M" % self.m
        if self.c == 0:
            return texto
        return texto + ("+%s" % self.c if self.c > 0 else "%s" % self.c)


# =============================================================================
#   #LEER_NUMERO   leer_numero() — texto de una casilla a Fraccion
# =============================================================================

def leer_numero(texto):
    """Convierte '3', '-2.5' o '3/4' a Fraccion. Lanza ValueError si no es número."""
    t = texto.strip()
    if "/" in t:                                    # fracción a/b
        a, b = t.split("/", 1)
        den = leer_numero(b)
        if den == 0:
            raise ValueError("denominador cero")
        return leer_numero(a) / den
    signo = 1
    if t[:1] in ("+", "-"):
        signo = -1 if t[0] == "-" else 1
        t = t[1:]
    entero, _, decimal = t.partition(".")           # 2.75 -> 275/100
    if not (entero + decimal).isdigit():
        raise ValueError("número inválido")
    return Fraccion(signo * int(entero + decimal), 10 ** len(decimal))


# =============================================================================
#   #TABLA   class Tabla — cómo se guarda la tabla simplex
# =============================================================================

class Tabla:
    """Tabla simplex.  Ejemplo con 2 variables y 2 restricciones <=:

                    x1   x2   s1   s2 | LD
        filas[0]  [  1    0    1    0 |  4 ]   base[0] = columna de s1
        filas[1]  [  3    2    0    1 | 18 ]   base[1] = columna de s2
        z         [ -3   -5    0    0 |  0 ]   (renglón Z)

    En cada renglón, la ÚLTIMA posición es el lado derecho (LD).
    """

    def __init__(self, nombres, tipos, filas, z, base, sentido):
        self.nombres = nombres      # nombre de cada columna: x1, s1, a2...
        self.tipos = tipos          # tipo de cada columna: 'x', 's', 'e' o 'a'
        self.filas = filas          # renglones de las restricciones (Fraccion)
        self.z = z                  # renglón Z (ExprM)
        self.base = base            # columna de la variable básica de cada renglón
        self.sentido = sentido      # 'max' o 'min'
        self.etiqueta = "Z"         # 'Z', o 'W' en la Fase 1


# =============================================================================
#   #MOSTRAR   foto_tabla(), valores_actuales() — datos para la pantalla
# =============================================================================

def foto_tabla(t, col=None, fila=None, cocientes=None):
    """Copia de la tabla (en texto) para que la ventana la dibuje.

    Se guarda una copia porque la tabla cambia al pivotear.
    col / fila: columna que entra y renglón que sale (para resaltarlos).
    """
    return {"nombres": list(t.nombres),
            "base": [t.nombres[b] for b in t.base] + [t.etiqueta],
            "valores": [[str(v) for v in f] for f in t.filas] + [[str(v) for v in t.z]],
            "cocientes": cocientes, "col": col, "fila": fila}


def valores_actuales(t):
    """Solución actual: las básicas valen su LD (las demás valen 0)."""
    basicas = ", ".join("%s = %s" % (t.nombres[b], f[-1]) for b, f in zip(t.base, t.filas))
    return "%s   ->   %s = %s" % (basicas, t.etiqueta, t.z[-1])


# =============================================================================
#   #SIMPLEX-02   #GRAN_M-02   #DOS_FASES-02
#   tabla_inicial() — FORMA ESTÁNDAR y tabla inicial
# =============================================================================

def renglon_z(c, total):
    """Renglón Z de la función objetivo:  Z - c1x1 - c2x2 - ... = 0  ->  [-c1, -c2, ..., 0]."""
    return [ExprM(0, -c[j]) if j < len(c) else ExprM() for j in range(total + 1)]


def tabla_inicial(prob, salida):
    """Pasa el problema a forma estándar y arma la tabla inicial.

        <=  ->  + s  (holgura)                     básica inicial: s
        >=  ->  - e  (exceso)  + a  (artificial)   básica inicial: a
        =   ->  + a  (artificial)                  básica inicial: a
    Columnas en orden:  x1..xn, holguras/excesos, artificiales.
    """
    n = len(prob["c"])

    # Si el lado derecho es negativo se multiplica la restricción por -1.
    restr = []
    for i, (coefs, signo, ld) in enumerate(prob["restr"]):
        if ld < 0:
            coefs, ld = [-v for v in coefs], -ld
            signo = {"<=": ">=", ">=": "<=", "=": "="}[signo]
            salida.append("R%d tiene lado derecho negativo: se multiplicó por -1 (queda %s)."
                          % (i + 1, signo))
        restr.append((coefs, signo, ld))

    # Nombres de las columnas.
    nombres = ["x%d" % (j + 1) for j in range(n)]
    tipos = ["x"] * n
    for i, (_, signo, _) in enumerate(restr):
        if signo == "<=":
            nombres.append("s%d" % (i + 1))
            tipos.append("s")
        elif signo == ">=":
            nombres.append("e%d" % (i + 1))
            tipos.append("e")
    for i, (_, signo, _) in enumerate(restr):
        if signo != "<=":
            nombres.append("a%d" % (i + 1))
            tipos.append("a")

    # Renglones:  [coeficientes de x, 0, ..., 0, LD]  + el 1 / -1 de s, e, a.
    filas, base = [], []
    for i, (coefs, signo, ld) in enumerate(restr):
        fila = list(coefs) + [Fraccion(0)] * (len(nombres) - n) + [ld]
        if signo == "<=":
            k = nombres.index("s%d" % (i + 1))
            fila[k] = Fraccion(1)
        if signo == ">=":
            fila[nombres.index("e%d" % (i + 1))] = Fraccion(-1)
        if signo != "<=":
            k = nombres.index("a%d" % (i + 1))
            fila[k] = Fraccion(1)
        filas.append(fila)
        base.append(k)
    return Tabla(nombres, tipos, filas, renglon_z(prob["c"], len(nombres)), base,
                 prob["sentido"])


# =============================================================================
#   #GRAN_M-05   #DOS_FASES-04
#   ajustar_renglon_z() — hacer 0 las variables básicas en el renglón Z (o W)
# =============================================================================

def ajustar_renglon_z(t, salida):
    """Hace 0 en el renglón Z los coeficientes de las variables básicas.

    Es necesario antes de iterar en la Gran M y en las Dos Fases, porque las
    artificiales (o las x de la Fase 2) son básicas pero tienen coeficiente
    distinto de 0 en el renglón Z.   Operación:  Z <- Z - (coef) · Ri
    """
    for i, b in enumerate(t.base):
        f = t.z[b]
        if not f.es_cero():
            t.z = [a - f * v for a, v in zip(t.z, t.filas[i])]
            salida.append("%s <- %s - (%s)·R%d" % (t.etiqueta, t.etiqueta, f, i + 1))


# =============================================================================
#   #SIMPLEX-03   #GRAN_M-06   #DOS_FASES-05
#   iterar() — CICLO DE ITERACIONES (lo usan los tres métodos)
# =============================================================================

def iterar(t, salida, max_iter=100):
    """Repite hasta llegar al óptimo. Devuelve el estado final.

        1. ¿Hay variable que entre?  No -> la tabla es óptima.
        2. ¿Hay variable que salga?  No -> el problema es no acotado.
        3. Pivotear y repetir.
    """
    it = 0
    while True:
        # 1. Variable que entra (si no hay, la tabla es óptima).
        col = elegir_entrante(t)
        if col is None:
            salida.append("\nTabla óptima (ya no hay variable que entre):")
            salida.append(foto_tabla(t))
            return "optimo"
        if it == max_iter:
            return "limite"         # protección contra ciclos infinitos
        it += 1

        # 2. Variable que sale (si no hay, el problema es no acotado).
        fila, cocientes = elegir_saliente(t, col)
        salida.append("\n--- Iteración %d ---" % it)
        salida.append(foto_tabla(t, col, fila, cocientes))
        salida.append("Entra: %s  (coeficiente %s en el renglón %s)"
                      % (t.nombres[col], t.z[col], t.etiqueta))
        if fila is None:
            salida.append("Sale: ninguna (ningún coeficiente de %s es positivo)" % t.nombres[col])
            return "no_acotado"
        salida.append("Sale: %s  (menor cociente)   Pivote: %s"
                      % (t.nombres[t.base[fila]], t.filas[fila][col]))

        # 3. Pivotear y mostrar los resultados de la iteración.
        pivotear(t, fila, col)
        salida.append("Resultado de la iteración %d:  %s" % (it, valores_actuales(t)))


# =============================================================================
#   #SIMPLEX-04   #GRAN_M-07   #DOS_FASES-06
#   elegir_entrante() — variable que ENTRA a la base
# =============================================================================

def elegir_entrante(t):
    """Columna que entra a la base, o None si la tabla ya es óptima.

    Maximizar: la más negativa del renglón Z.   Minimizar: la más positiva.
    """
    mejor = None
    for j in range(len(t.nombres)):
        if j in t.base:                 # solo entran variables no básicas
            continue
        v = t.z[j]
        if t.sentido == "max":
            if v < 0 and (mejor is None or v < t.z[mejor]):
                mejor = j
        else:
            if v > 0 and (mejor is None or v > t.z[mejor]):
                mejor = j
    return mejor


# =============================================================================
#   #SIMPLEX-05   #GRAN_M-08   #DOS_FASES-07
#   elegir_saliente() — variable que SALE (prueba del cociente mínimo)
# =============================================================================

def elegir_saliente(t, col):
    """Devuelve (renglón que sale o None, cocientes en texto).

    Solo cuentan los renglones con coeficiente positivo en la columna que entra.
    En caso de empate sale la variable básica de menor índice.
    Si ningún coeficiente es positivo devuelve None (problema no acotado).
    """
    mejor, menor, cocientes = None, None, []
    for i, fila in enumerate(t.filas):
        a = fila[col]
        if a > 0:
            q = fila[-1] / a
            cocientes.append("%s ÷ %s = %s" % (fila[-1], a, q))
            if mejor is None or q < menor or (q == menor and t.base[i] < t.base[mejor]):
                mejor, menor = i, q
        else:
            cocientes.append("-")
    return mejor, cocientes


# =============================================================================
#   #SIMPLEX-06   #GRAN_M-09   #DOS_FASES-08
#   pivotear() — operaciones de Gauss-Jordan
# =============================================================================

def pivotear(t, r, c):
    """Gauss-Jordan sobre el pivote (renglón r, columna c)."""
    piv = t.filas[r][c]
    t.filas[r] = [v / piv for v in t.filas[r]]             # 1. el pivote se hace 1
    for i in range(len(t.filas)):                           # 2. ceros en la columna
        f = t.filas[i][c]
        if i != r and f != 0:
            t.filas[i] = [a - f * b for a, b in zip(t.filas[i], t.filas[r])]
    f = t.z[c]                                              # 3. cero en el renglón Z
    if not f.es_cero():
        t.z = [a - f * b for a, b in zip(t.z, t.filas[r])]
    t.base[r] = c                                           # 4. la variable entra a la base


# =============================================================================
#   #SIMPLEX-07   #GRAN_M-10   #DOS_FASES-12
#   mostrar_resultado() — Z, variables, o aviso de que no hay solución
# =============================================================================

def mostrar_resultado(t, estado, salida):
    """Interpreta la tabla final: óptimo, no acotado o sin solución factible."""
    salida.append("\n" + "=" * 60 + "\nRESULTADO")
    # Artificiales que siguen básicas con valor positivo -> no hay solución factible.
    artificiales = ["%s = %s" % (t.nombres[b], f[-1]) for b, f in zip(t.base, t.filas)
                    if t.tipos[b] == "a" and f[-1] > 0]

    if estado == "limite":
        salida.append("No se llegó a la solución dentro del máximo de iteraciones.")
    elif estado == "no_acotado":
        salida.append("SOLUCIÓN NO ACOTADA: Z puede %s sin límite, no hay óptimo finito."
                      % ("crecer" if t.sentido == "max" else "disminuir"))
        if artificiales:
            salida.append("(Quedaban artificiales positivas: %s. Conviene verificar con Dos "
                          "Fases si el problema es factible.)" % ", ".join(artificiales))
    elif artificiales or t.z[-1].m != 0:
        # Solo puede pasar en la Gran M: una artificial no logró salir de la base.
        salida.append("EL PROBLEMA NO TIENE SOLUCIÓN FACTIBLE: quedan variables artificiales "
                      "positivas (%s). No existe una solución básica factible (BF)."
                      % ", ".join(artificiales))
    else:
        valores = {b: f[-1] for b, f in zip(t.base, t.filas)}      # no básicas = 0
        salida.append("Z %s = %s" % ("máxima" if t.sentido == "max" else "mínima", t.z[-1].c))
        for j, nombre in enumerate(t.nombres):
            if t.tipos[j] != "a":
                salida.append("%s = %s" % (nombre, valores.get(j, 0)))


# #############################################################################
#
#   LOS TRES MÉTODOS
#   Todos siguen:  tabla inicial -> (ajustar renglón Z) -> iterar -> resultado
#
# #############################################################################


# =============================================================================
#   #SIMPLEX-01   simplex() — FUNCIÓN PRINCIPAL DEL MÉTODO SIMPLEX
# =============================================================================

def simplex(prob, salida):
    """Simplex: solo restricciones <=; las holguras forman la base inicial."""
    t = tabla_inicial(prob, salida)                         # -> #SIMPLEX-02
    # Si hubo que agregar artificiales, el origen no es solución BF: no aplica.
    if "a" in t.tipos:
        salida.append("El Método Simplex no se puede aplicar: hay restricciones >= o =, así "
                      "que el origen no es una solución básica factible (BF).\n"
                      "Use el Método de la Gran M o el de las Dos Fases.")
        return
    estado = iterar(t, salida)                              # -> #SIMPLEX-03
    mostrar_resultado(t, estado, salida)                    # -> #SIMPLEX-07


# =============================================================================
#   #GRAN_M-01   gran_m() — FUNCIÓN PRINCIPAL DEL MÉTODO DE LA GRAN M
# =============================================================================

def gran_m(prob, salida):
    """Gran M: las artificiales se penalizan con M en la función objetivo."""
    t = tabla_inicial(prob, salida)                         # -> #GRAN_M-02

    # #GRAN_M-03  Penalización de las artificiales con M (ver ExprM en #GRAN_M-04):
    #   Max: la artificial cuesta -M  ->  en el renglón Z aparece +M.
    #   Min: la artificial cuesta +M  ->  en el renglón Z aparece -M.
    for j, tipo in enumerate(t.tipos):
        if tipo == "a":
            t.z[j] = ExprM(1 if t.sentido == "max" else -1, 0)

    salida.append("Se hacen 0 los coeficientes de las artificiales en el renglón Z:")
    ajustar_renglon_z(t, salida)                            # -> #GRAN_M-05
    estado = iterar(t, salida)                              # -> #GRAN_M-06
    mostrar_resultado(t, estado, salida)                    # -> #GRAN_M-10


# =============================================================================
#   #DOS_FASES-01   dos_fases() — FUNCIÓN PRINCIPAL DEL MÉTODO DE LAS DOS FASES
# =============================================================================

def dos_fases(prob, salida):
    """Dos Fases: la Fase 1 busca una solución BF y la Fase 2 optimiza Z."""
    t = tabla_inicial(prob, salida)                         # -> #DOS_FASES-02
    artificiales = [j for j, tipo in enumerate(t.tipos) if tipo == "a"]

    if artificiales:
        # ---------------------------------------------------------------------
        # #DOS_FASES-03  FASE 1: Minimizar W = suma de las artificiales
        #   Renglón W:  W - a1 - a2 - ... = 0   (coeficiente -1 en cada artificial)
        # ---------------------------------------------------------------------
        salida.append("=== FASE 1: Minimizar W = %s ==="
                      % " + ".join(t.nombres[j] for j in artificiales))
        t.z = [ExprM(0, -1) if j in artificiales else ExprM()
               for j in range(len(t.nombres) + 1)]
        t.sentido, t.etiqueta = "min", "W"
        ajustar_renglon_z(t, salida)                        # -> #DOS_FASES-04
        if iterar(t, salida) != "optimo":                   # -> #DOS_FASES-05
            salida.append("No se pudo completar la Fase 1.")
            return

        # ---------------------------------------------------------------------
        # #DOS_FASES-09  Fin de la Fase 1: si W mínimo > 0 no hay solución BF
        # ---------------------------------------------------------------------
        if t.z[-1].c > 0:
            salida.append("\nRESULTADO\nEL PROBLEMA NO TIENE SOLUCIÓN FACTIBLE: el mínimo de "
                          "W es %s > 0, las artificiales no pueden valer 0. No existe una "
                          "solución básica factible (BF)." % t.z[-1].c)
            return
        salida.append("W = 0: se obtuvo una solución básica factible.")
        sacar_artificiales(t, salida)                       # -> #DOS_FASES-10

    # -------------------------------------------------------------------------
    # #DOS_FASES-11  FASE 2: se regresa a la función objetivo original
    # -------------------------------------------------------------------------
    salida.append("\n=== FASE 2: %s Z ===" % ("Maximizar" if prob["sentido"] == "max"
                                              else "Minimizar"))
    t.z = renglon_z(prob["c"], len(t.nombres))
    t.sentido, t.etiqueta = prob["sentido"], "Z"
    ajustar_renglon_z(t, salida)                            # -> #DOS_FASES-04
    estado = iterar(t, salida)                              # -> #DOS_FASES-05
    mostrar_resultado(t, estado, salida)                    # -> #DOS_FASES-12


# =============================================================================
#   #DOS_FASES-10   sacar_artificiales() — quitar las artificiales al terminar la Fase 1
# =============================================================================

def sacar_artificiales(t, salida):
    """Quita las artificiales de la base y luego sus columnas.

    Si una artificial sigue básica (con valor 0) se pivotea con una variable real
    de su renglón; si el renglón no tiene ninguna, la restricción es redundante.
    """
    i = 0
    while i < len(t.filas):
        if t.tipos[t.base[i]] == "a":
            reales = [k for k in range(len(t.nombres))
                      if t.tipos[k] != "a" and t.filas[i][k] != 0]
            if not reales:
                salida.append("R%d es redundante y se elimina." % (i + 1))
                del t.filas[i], t.base[i]
                continue
            salida.append("%s sigue básica con valor 0: se cambia por %s."
                          % (t.nombres[t.base[i]], t.nombres[reales[0]]))
            pivotear(t, i, reales[0])
        i += 1

    # Se eliminan las columnas artificiales (y se renumera la base).
    conservar = [j for j in range(len(t.nombres)) if t.tipos[j] != "a"]
    t.base = [conservar.index(b) for b in t.base]
    t.nombres = [t.nombres[j] for j in conservar]
    t.tipos = [t.tipos[j] for j in conservar]
    t.filas = [[f[j] for j in conservar] + [f[-1]] for f in t.filas]
    salida.append("Se eliminan las columnas de las variables artificiales.")


# =============================================================================
#   #RESOLVER   resolver() — punto de entrada que llama la ventana
# =============================================================================

METODOS = {"simplex": simplex,          # -> #SIMPLEX-01
           "gran_m": gran_m,            # -> #GRAN_M-01
           "dos_fases": dos_fases}      # -> #DOS_FASES-01


def resolver(metodo, prob):
    """prob = {'sentido': 'max' o 'min',
               'c': [coeficientes de Z],
               'restr': [([coeficientes], '<=' / '>=' / '=', lado derecho), ...]}
    Devuelve la lista de pasos: textos (str) y tablas (dict de foto_tabla).
    """
    salida = []
    METODOS[metodo](prob, salida)
    return salida
