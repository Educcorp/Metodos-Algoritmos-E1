
# =============================================================================
#   #FRACCIONES
#   Fracciones exactas (no float) para que los resultados salgan igual que
#   en la libreta: 21/4 y no 5.2499999...
#
#   Variables:
#     a, b   -> números enteros a los que se les saca el MCD
#     x      -> número a convertir (entero o Fraccion)
#     num    -> numerador de la fracción
#     den    -> denominador de la fracción (siempre positivo)
#     g      -> MCD de num y den (se usa para simplificar)
#     self   -> la fracción actual
#     o      -> la otra fracción con la que se opera o compara
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
#
#   Variables:
#     m      -> coeficiente de M          (en 3M - 1/2, m = 3)
#     c      -> constante, parte sin M    (en 3M - 1/2, c = -1/2)
#     o      -> la otra expresión con la que se opera o compara
#     k      -> fracción que multiplica a la expresión
#     v      -> parte que decide el signo (m si no es 0; si no, c)
#     texto  -> cómo se escribe la expresión en pantalla ("3M-1/2")
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
#
#   Variables:
#     texto    -> lo que el usuario escribió en la casilla
#     t        -> el texto sin espacios (se va recortando)
#     a, b     -> numerador y denominador cuando se escribe una fracción "a/b"
#     den      -> el denominador ya convertido a Fraccion
#     signo    -> 1 si es positivo, -1 si es negativo
#     entero   -> parte antes del punto   ("2.75" -> "2")
#     decimal  -> parte después del punto ("2.75" -> "75")
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
#
#   Variables:
#     nombres   -> nombre de cada columna: x1, x2, s1, e2, a2...
#     tipos     -> tipo de cada columna: 'x' decisión, 's' holgura,
#                  'e' exceso, 'a' artificial
#     filas     -> renglones de las restricciones (R1, R2, ...)
#     z         -> renglón Z (o W en la Fase 1)
#     base      -> columna de la variable básica de cada renglón
#     sentido   -> 'max' (maximizar) o 'min' (minimizar)
#     etiqueta  -> nombre del renglón objetivo: 'Z', o 'W' en la Fase 1
#     LD        -> lado derecho; es la ÚLTIMA posición de cada renglón
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
#
#   Variables:
#     t          -> la tabla simplex actual
#     col        -> columna de la variable que ENTRA (None si no hay)
#     fila       -> renglón de la variable que SALE (None si no hay)
#     cocientes  -> textos de la prueba del cociente ("12 ÷ 3 = 4")
#     b          -> columna de una variable básica
#     f          -> un renglón de la tabla
#     f[-1]      -> LD del renglón = valor de su variable básica
#     basicas    -> texto con los valores, ej. "s1 = 4, x2 = 6"
# =============================================================================

def foto_tabla(t, col=None, fila=None, cocientes=None):
    """Copia de la tabla (en texto) para que la ventana la dibuje.

    Se guarda una copia porque la tabla cambia al pivotear.
    col / fila: columna que entra y renglón que sale (para resaltarlos).
    """
    return {"nombres": list(t.nombres),                        # columnas: x1, x2, s1, e2, a2...
            "base": [t.nombres[b] for b in t.base] + [t.etiqueta],
            # "valores": cada renglón en texto; el último valor de cada uno es
            # el LD (viene de fila[-1]/t.z[-1]), que la ventana dibuja en la
            # columna "LD" de la tabla.
            "valores": [[str(v) for v in f] for f in t.filas] + [[str(v) for v in t.z]],
            "cocientes": cocientes, "col": col, "fila": fila}


def valores_actuales(t):
    """Solución actual: las básicas valen su LD (las demás valen 0)."""
    # Aquí se arma el texto "x1 = 4, x2 = 6": f[-1] es el LD de cada renglón,
    # que es justo el valor de su variable básica t.nombres[b].
    basicas = ", ".join("%s = %s" % (t.nombres[b], f[-1]) for b, f in zip(t.base, t.filas))
    return "%s   ->   %s = %s" % (basicas, t.etiqueta, t.z[-1])   # t.z[-1] = LD del renglón Z/W


# =============================================================================
#   #SIMPLEX-02   #GRAN_M-02   #DOS_FASES-02
#   tabla_inicial() — FORMA ESTÁNDAR y tabla inicial
#
#   Variables:
#     prob     -> problema capturado: {'sentido', 'c', 'restr'}
#     salida   -> lista de textos y tablas que se muestran en pantalla
#     c        -> coeficientes de la función objetivo Z
#     total    -> número de columnas de la tabla (sin contar el LD)
#     n        -> número de variables de decisión (x1 ... xn)
#     i        -> número de restricción (i = 0 es R1, i = 1 es R2...)
#     j        -> número de columna
#     coefs    -> coeficientes de las x en la restricción
#     signo    -> '<=', '>=' o '='
#     ld       -> lado derecho de la restricción
#     restr    -> restricciones ya corregidas (todas con ld >= 0)
#     nombres  -> nombre de cada columna (x1, s1, e2, a2...)
#     tipos    -> tipo de cada columna ('x', 's', 'e', 'a')
#     fila     -> renglón que se está armando
#     k        -> columna de la variable básica de ese renglón (s o a)
#     filas    -> todos los renglones de la tabla inicial
#     base     -> variable básica inicial de cada renglón
# =============================================================================

def renglon_z(c, total):
    """Renglón Z de la función objetivo:  Z - c1x1 - c2x2 - ... = 0  ->  [-c1, -c2, ..., 0]."""
    # range(total + 1): las "total" columnas de la tabla + 1 más para el LD de Z,
    # que arranca en 0 (ExprM() = 0) y va cambiando con cada pivoteo.
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
    nombres = ["x%d" % (j + 1) for j in range(n)]   # aquí se crean las columnas x1, x2, ..., xn
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
        # coefs ocupa las columnas x1..xn;  el LD (lado derecho) se agrega
        # al final de la lista -> fila[-1] siempre es el LD de ese renglón.
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
#
#   Variables:
#     t           -> la tabla simplex
#     salida      -> lista de textos y tablas que se muestran en pantalla
#     i           -> número de renglón (R1, R2, ...)
#     b           -> columna de la variable básica de ese renglón
#     f           -> coeficiente de esa básica en el renglón Z (el que se hace 0)
#     a           -> valor del renglón Z en una columna
#     v           -> valor del renglón Ri en esa misma columna
#     t.etiqueta  -> 'Z', o 'W' en la Fase 1
#   Operación:  Z <- Z - f · Ri
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
#
#   Se llama una vez por cada método (Simplex, Gran M) y dos veces en Dos
#   Fases (una por fase). Lo primero que hace SIEMPRE es mostrar la tabla
#   inicial con la que va a trabajar esa llamada, antes de decidir nada: así
#   queda visible la tabla de forma estándar ya lista (penalizada con M, o
#   con el renglón W/Z recién armado, según el método) y no solo la primera
#   iteración.
#
#   Variables:
#     t                   -> la tabla simplex
#     salida              -> lista de textos y tablas que se muestran en pantalla
#     max_iter            -> máximo de iteraciones (evita ciclos infinitos)
#     it                  -> número de la iteración actual
#     col                 -> columna de la variable que ENTRA
#     fila                -> renglón de la variable que SALE
#     cocientes           -> textos de la prueba del cociente
#     t.z[col]            -> coeficiente de la que entra en el renglón Z
#     t.filas[fila][col]  -> el PIVOTE
#     estado devuelto     -> 'optimo', 'no_acotado' o 'limite'
# =============================================================================

def iterar(t, salida, max_iter=100):
    """Repite hasta llegar al óptimo. Devuelve el estado final.

        0. Mostrar la tabla inicial, tal cual queda antes de la primera decisión.
        1. ¿Hay variable que entre?  No -> la tabla es óptima.
        2. ¿Hay variable que salga?  No -> el problema es no acotado.
        3. Pivotear y repetir.
    """
    salida.append("\nTabla inicial:")
    salida.append(foto_tabla(t))

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
#
#   Significado: el renglón Z (o W, en la Fase 1 de Dos Fases) indica cuánto
#   cambia el objetivo por cada unidad que aumenta una variable no básica.
#   Se elige la que más lo mejora: la más negativa al maximizar, la más
#   positiva al minimizar. Si ninguna mejora el objetivo, la tabla es óptima.
#
#   Variables:
#     t          -> la tabla simplex
#     j          -> columna que se está revisando
#     v          -> coeficiente de esa columna en el renglón Z
#     mejor      -> columna elegida hasta ahora (la que entra); None si ninguna
#     t.base     -> columnas de las variables básicas (esas no pueden entrar)
#     t.sentido  -> 'max' busca el más negativo, 'min' el más positivo
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
#
#   Significado: cada variable básica se puede despejar como
#   básica = LD - coef·(variable que entra); como ninguna básica puede
#   quedar negativa, cada renglón pone un límite a cuánto puede crecer la
#   variable que entra. El menor cociente es ese límite, y la variable
#   básica de ese renglón es la que llega a 0 primero (la que sale).
#
#   Variables:
#     t          -> la tabla simplex
#     col        -> columna de la variable que ENTRA
#     i          -> número de renglón
#     fila       -> el renglón i
#     a          -> coeficiente del renglón en la columna que entra (debe ser > 0)
#     fila[-1]   -> LD (lado derecho) del renglón
#     q          -> cociente  LD ÷ a
#     mejor      -> renglón que SALE (el del menor cociente)
#     menor      -> el menor cociente encontrado
#     cocientes  -> texto de cada cociente para la tabla ("-" si a <= 0)
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
#
#   Significado: reescribe la tabla para que la columna de la variable que
#   entra quede con un 1 en el renglón pivote y 0 en todos los demás
#   renglones (incluido Z/W). Eso es justamente lo que hace básica a esa
#   variable y saca de la base a la que estaba en el renglón pivote.
#
#   Variables:
#     t    -> la tabla simplex
#     r    -> renglón pivote (el de la variable que SALE)
#     c    -> columna pivote (la de la variable que ENTRA)
#     piv  -> el elemento PIVOTE = t.filas[r][c]
#     v    -> cada valor del renglón pivote (se divide entre piv)
#     i    -> cada uno de los otros renglones
#     f    -> coeficiente que se quiere hacer 0 en la columna c
#     a    -> valor del renglón que se modifica
#     b    -> valor del renglón pivote en la misma columna
#   Operación:  Ri <- Ri - f · Rr
# =============================================================================

def pivotear(t, r, c):
    """Gauss-Jordan sobre el pivote (renglón r, columna c)."""
    # El LD de cada renglón es su última posición (índice -1): como estas
    # operaciones recorren la fila completa, el LD se actualiza aquí mismo
    # junto con el resto de los coeficientes, sin ningún caso especial.
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
#
#   Variables:
#     t             -> la tabla final
#     estado        -> cómo terminó iterar(): 'optimo', 'no_acotado' o 'limite'
#     salida        -> lista de textos y tablas que se muestran en pantalla
#     artificiales  -> artificiales básicas con valor > 0 (no hay solución BF)
#     b             -> columna de una variable básica
#     f             -> su renglón;   f[-1] -> su valor (LD)
#     t.z[-1]       -> valor de Z (último elemento del renglón Z)
#     t.z[-1].m     -> parte en M de Z (si no es 0, quedó una artificial)
#     valores       -> valor de cada básica por columna (las no básicas valen 0)
#     j, nombre     -> columna y nombre de cada variable
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
        # valores: para cada columna básica b, su valor es el LD (f[-1]) de su
        # renglón; las columnas que no están en valores son no básicas y valen 0.
        valores = {b: f[-1] for b, f in zip(t.base, t.filas)}
        salida.append("Z %s = %s" % ("máxima" if t.sentido == "max" else "mínima", t.z[-1].c))
        for j, nombre in enumerate(t.nombres):
            if t.tipos[j] != "a":
                # Aquí se imprime el valor final de cada variable: "x1 = ...", "x2 = ...", etc.
                salida.append("%s = %s" % (nombre, valores.get(j, 0)))


# #############################################################################
#
#   LOS TRES MÉTODOS
#   Todos siguen:  tabla inicial -> (ajustar renglón Z) -> iterar -> resultado
#
# #############################################################################


# =============================================================================
#   #SIMPLEX-01   simplex() — FUNCIÓN PRINCIPAL DEL MÉTODO SIMPLEX
#
#   Variables:
#     prob     -> problema capturado en la ventana
#     salida   -> lista de textos y tablas que se muestran en pantalla
#     t        -> la tabla simplex
#     t.tipos  -> si contiene 'a' hay artificiales, así que el Simplex no aplica
#     estado   -> cómo terminó iterar(): 'optimo', 'no_acotado' o 'limite'
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
#
#   Variables:
#     prob    -> problema capturado en la ventana
#     salida  -> lista de textos y tablas que se muestran en pantalla
#     t       -> la tabla simplex
#     estado  -> cómo terminó iterar(): 'optimo', 'no_acotado' o 'limite'
# =============================================================================

def gran_m(prob, salida):
    """Gran M: las artificiales se penalizan con M en la función objetivo."""
    t = tabla_inicial(prob, salida)                         # -> #GRAN_M-02

    # -------------------------------------------------------------------------
    #   #GRAN_M-03   Penalización de las artificiales con M  (ver #GRAN_M-04)
    #     Max: la artificial cuesta -M  ->  en el renglón Z aparece +M
    #     Min: la artificial cuesta +M  ->  en el renglón Z aparece -M
    #
    #   Variables:
    #     j             -> columna que se revisa
    #     tipo          -> tipo de esa columna ('a' = artificial)
    #     t.z[j]        -> coeficiente de la artificial en el renglón Z
    #     ExprM(1, 0)   -> +M
    #     ExprM(-1, 0)  -> -M
    # -------------------------------------------------------------------------
    for j, tipo in enumerate(t.tipos):
        if tipo == "a":
            t.z[j] = ExprM(1 if t.sentido == "max" else -1, 0)

    salida.append("Se hacen 0 los coeficientes de las artificiales en el renglón Z:")
    ajustar_renglon_z(t, salida)                            # -> #GRAN_M-05
    estado = iterar(t, salida)                              # -> #GRAN_M-06
    mostrar_resultado(t, estado, salida)                    # -> #GRAN_M-10


# =============================================================================
#   #DOS_FASES-01   dos_fases() — FUNCIÓN PRINCIPAL DEL MÉTODO DE LAS DOS FASES
#
#   Estructura completa del método (cada parte remite a su bloque más abajo):
#     Forma estándar -> #DOS_FASES-02 (tabla_inicial, reutilizada de Simplex/Gran M)
#     FASE 1         -> #DOS_FASES-03 a #DOS_FASES-09   (4 pasos: ver más abajo)
#     FASE 2         -> #DOS_FASES-10 a #DOS_FASES-12   (5 pasos: ver más abajo)
#     Si no hay artificiales (todas las restricciones son <=), la Fase 1 se
#     salta por completo: el origen ya es una solución BF y se va directo a
#     optimizar Z (la Fase 2 funciona entonces como un Simplex normal).
#
#   Variables:
#     prob          -> problema capturado en la ventana
#     salida        -> lista de textos y tablas que se muestran en pantalla
#     t             -> la tabla simplex (la misma se usa en las dos fases)
#     artificiales  -> columnas de las variables artificiales
#     W             -> función de la Fase 1 = suma de las artificiales
#     t.z           -> renglón W en la Fase 1, renglón Z en la Fase 2
#     estado        -> cómo terminó iterar(): 'optimo', 'no_acotado' o 'limite'
# =============================================================================

def dos_fases(prob, salida):
    """Dos Fases: la Fase 1 busca una solución BF y la Fase 2 optimiza Z."""
    t = tabla_inicial(prob, salida)                         # -> #DOS_FASES-02
    artificiales = [j for j, tipo in enumerate(t.tipos) if tipo == "a"]

    if artificiales:
        # ---------------------------------------------------------------------
        #   #DOS_FASES-03   FASE 1 · Paso 1: Minimizar W = suma de las artificiales
        #     Siempre se MINIMIZA W, sin importar si el problema original es
        #     de máximo o de mínimo.  Renglón W:  W - a1 - a2 - ... = 0
        #     (queda -1 en la columna de cada artificial).
        #
        #   Variables:
        #     j             -> columna de la tabla
        #     ExprM(0, -1)  -> el -1 que va en la columna de cada artificial
        #     t.sentido     -> 'min', porque en la Fase 1 siempre se minimiza W
        #     t.etiqueta    -> 'W', para que el renglón se muestre como W
        # ---------------------------------------------------------------------
        salida.append("=== FASE 1: Minimizar W = %s ==="
                      % " + ".join(t.nombres[j] for j in artificiales))
        t.z = [ExprM(0, -1) if j in artificiales else ExprM()
               for j in range(len(t.nombres) + 1)]
        t.sentido, t.etiqueta = "min", "W"

        # #DOS_FASES-04   FASE 1 · Paso 2: hacer 0 el coeficiente de las
        # artificiales en el renglón W (son básicas, deben valer 0 ahí).
        ajustar_renglon_z(t, salida)

        # #DOS_FASES-05   FASE 1 · Paso 3: iterar minimizando W hasta que no
        # quede ningún coeficiente positivo en el renglón W.
        if iterar(t, salida) != "optimo":
            salida.append("No se pudo completar la Fase 1.")
            return

        # ---------------------------------------------------------------------
        #   #DOS_FASES-09   FASE 1 · Paso 4: evaluar el resultado
        #     W > 0  ->  no existe solución BF: el método termina aquí.
        #     W = 0  ->  hay solución BF, se pasa a la Fase 2.
        #     Caso especial (W = 0 con una artificial todavía básica en 0,
        #     o un renglón redundante) lo resuelve sacar_artificiales(),
        #     ya como primer paso de la Fase 2 (#DOS_FASES-10).
        #
        #   Variables:
        #     t.z[-1].c  -> valor mínimo de W (LD del renglón W)
        # ---------------------------------------------------------------------
        if t.z[-1].c > 0:
            salida.append("\nRESULTADO\nEL PROBLEMA NO TIENE SOLUCIÓN FACTIBLE: el mínimo de "
                          "W es %s > 0, las artificiales no pueden valer 0. No existe una "
                          "solución básica factible (BF)." % t.z[-1].c)
            return
        salida.append("W = 0: se obtuvo una solución básica factible.")

    # -------------------------------------------------------------------------
    #   FASE 2: se abandona W y se optimiza la función objetivo original.
    #     Paso 1 -> #DOS_FASES-10  Eliminar las columnas artificiales
    #     Paso 2 -> #DOS_FASES-11  Poner el renglón Z original en vez de W
    #     Paso 3 -> #DOS_FASES-04  Hacer 0 las básicas en el renglón Z
    #     Paso 4 -> #DOS_FASES-05  Iterar con la regla del problema original
    #     Paso 5    (no acotado, si no hay variable que pueda salir) ya lo
    #               detecta iterar()/elegir_saliente() igual que en los
    #               otros métodos.
    # -------------------------------------------------------------------------
    salida.append("\n=== FASE 2: %s Z ===" % ("Maximizar" if prob["sentido"] == "max"
                                              else "Minimizar"))

    # #DOS_FASES-10   FASE 2 · Paso 1: quitar las columnas de las artificiales
    # de la última tabla de la Fase 1 (no aplica si nunca hubo artificiales).
    if artificiales:
        sacar_artificiales(t, salida)

    # ---------------------------------------------------------------------
    #   #DOS_FASES-11   FASE 2 · Paso 2: la fila r/W se reemplaza por el
    #   renglón de la función objetivo original (coeficientes -cⱼ, LD 0).
    #
    #   Variables:
    #     prob["c"]        -> coeficientes originales de Z
    #     prob["sentido"]  -> 'max' o 'min' original del problema
    #     t.z              -> se reemplaza el renglón W por el renglón Z
    #     t.etiqueta       -> regresa a 'Z'
    # ---------------------------------------------------------------------
    t.z = renglon_z(prob["c"], len(t.nombres))
    t.sentido, t.etiqueta = prob["sentido"], "Z"

    # #DOS_FASES-04   FASE 2 · Paso 3: hacer 0 en el renglón Z los
    # coeficientes de las variables que quedaron básicas al salir de la Fase 1.
    ajustar_renglon_z(t, salida)

    # #DOS_FASES-05   FASE 2 · Paso 4: iterar con la regla del problema
    # original (máx o mín) hasta el óptimo, o hasta detectar no acotado.
    estado = iterar(t, salida)
    mostrar_resultado(t, estado, salida)                    # -> #DOS_FASES-12


# =============================================================================
#   #DOS_FASES-10   sacar_artificiales() — cierre de la Fase 1 + Paso 1 de la Fase 2
#
#   Hace dos cosas, una después de la otra:
#     a) FASE 1 · Paso 4 (caso especial): si con W = 0 una artificial sigue
#        básica (en valor 0), se saca pivoteando con una variable real de su
#        mismo renglón; si ese renglón no tiene ninguna, la restricción es
#        redundante y el renglón se elimina.
#     b) FASE 2 · Paso 1: ya con todas las artificiales fuera de la base, se
#        eliminan directamente sus columnas de la tabla.
#
#   Variables:
#     t           -> la tabla al terminar la Fase 1
#     salida      -> lista de textos y tablas que se muestran en pantalla
#     i           -> renglón que se está revisando
#     t.base[i]   -> columna de la variable básica de ese renglón
#     reales      -> columnas NO artificiales con coeficiente != 0 en el renglón i
#     reales[0]   -> la variable que entra en lugar de la artificial
#     conservar   -> columnas que se quedan (todas menos las artificiales)
#     b           -> columna de una básica (se renumera con conservar.index(b))
#     f           -> un renglón;   f[-1] -> su LD
# =============================================================================

def sacar_artificiales(t, salida):
    """Quita las artificiales de la base y luego sus columnas.

    Si una artificial sigue básica (con valor 0) se pivotea con una variable real
    de su renglón; si el renglón no tiene ninguna, la restricción es redundante.
    """
    # a) Caso especial de la Fase 1: ninguna artificial debe quedar básica.
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

    # b) Paso 1 de la Fase 2: se eliminan las columnas artificiales (y se
    # renumera la base, porque los índices de columna cambiaron).
    conservar = [j for j in range(len(t.nombres)) if t.tipos[j] != "a"]
    t.base = [conservar.index(b) for b in t.base]
    t.nombres = [t.nombres[j] for j in conservar]
    t.tipos = [t.tipos[j] for j in conservar]
    t.filas = [[f[j] for j in conservar] + [f[-1]] for f in t.filas]
    salida.append("Se eliminan las columnas de las variables artificiales.")


# =============================================================================
#   #RESOLVER   resolver() — punto de entrada que llama la ventana
#
#   Variables:
#     METODOS          -> relaciona el nombre del método con su función
#     metodo           -> 'simplex', 'gran_m' o 'dos_fases' (lo elige el menú)
#     prob             -> problema capturado en la ventana:
#       prob['sentido']  -> 'max' o 'min'
#       prob['c']        -> coeficientes de Z
#       prob['restr']    -> lista de (coeficientes, signo, lado derecho)
#     salida           -> lista de pasos (textos y tablas) que se devuelve
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
