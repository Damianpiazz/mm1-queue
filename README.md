# Simulacion M/M/1 - Cola de banco con un cajero

## Descripcion

Simulacion por eventos discretos de una cola M/M/1 que modela un banco con un unico cajero.

**Caracteristicas del modelo:**
- Llegadas: proceso de Poisson con tasa $\lambda$ (exponencial entre arribos)
- Servicio: tiempos de servicio exponenciales con tasa $\mu$
- Un solo servidor (cajero)
- Disciplina FIFO
- Capacidad infinita, poblacion infinita

Se barren multiples niveles de utilizacion $\rho = \lambda / \mu$ desde 0.1 hasta 0.95,
comparando los resultados simulados con las formulas analiticas exactas de la teoria de colas.

## Estructura del proyecto

```
mm1/
├── README.md
├── requirements.txt
├── config.json
├── simulation.py          # Motor de eventos discretos M/M/1
├── analytical.py          # Formulas exactas
├── notebooks/
│   └── analysis.ipynb     # Comparacion simulacion vs analitico
└── output/                # Resultados generados
```

## Instalacion

```bash
pip install -r requirements.txt
```

Adicionalmente, para la visualizacion de la cadena de Markov con Graphviz,
instalar el binario de Graphviz (https://graphviz.org/download/).

## Ejecucion

```bash
cd mm1
python simulation.py
```

Esto genera `output/summary.csv` con los resultados para todos los $\rho$ configurados.

Para explorar los resultados interactivamente:

```bash
jupyter notebook notebooks/analysis.ipynb
```

## Parametros

Editar `config.json` para ajustar:
- `arrival_rate_per_hour`: tasa de llegadas base (se escala para cada $\rho$)
- `service_time_minutes_mean`: tiempo medio de servicio en minutos
- `rho_values`: lista de niveles de utilizacion a simular
- `sim_hours`: duracion total de la simulacion
- `warmup_hours`: periodo de calentamiento (no se acumulan estadisticos)
- `costs`: salario del cajero y costo de espera del cliente

## Objetivo

Comparar las metricas simuladas con las formulas exactas de la teoria de colas M/M/1,
y encontrar el nivel de utilizacion $\rho$ que minimiza el costo total (salario + costo de espera).

---

## Fundamento Teorico

### 1. Cadenas de Markov

Un proceso de Markov es un proceso estocastico que satisface la **propiedad de Markov**: la distribucion condicional del estado futuro del sistema depende unicamente del estado actual y no de la historia pasada (propiedad sin memoria).

**Probabilidad de transicion:**

$$p_{ij} = P\{X_t = j \mid X_{t-1} = i\}$$

**Estado estable (ergodicidad):** Si una cadena de Markov es irreducible y positivamente recurrente (ergodica), las probabilidades del sistema convergen asintoticamente a una distribucion de estado estable, independiente de las condiciones iniciales. Estas probabilidades $\pi_j$ satisfacen:

$$\pi_j = \sum_i \pi_i p_{ij}, \qquad \sum_j \pi_j = 1$$

---

### 2. Proceso de Poisson

Un proceso de Poisson es un proceso de conteo que describe eventos que ocurren aleatoriamente a lo largo del tiempo. Se basa en tres propiedades:

- **Independencia:** el numero de eventos en intervalos disjuntos es independiente.
- **Proporcionalidad:** la probabilidad de exactamente un evento en $\Delta t$ es $\lambda \Delta t$.
- **Orden:** la probabilidad de mas de un evento en $\Delta t$ es $o(\Delta t)$.

El numero $X$ de eventos en un intervalo $t$ sigue una distribucion de Poisson con media $\lambda t$:

$$P(X = x) = \frac{e^{-\lambda t} (\lambda t)^x}{x!}, \quad x = 0,1,2,\dots$$

Su esperanza y varianza son $E[X] = Var[X] = \lambda t$.

---

### 3. Distribucion Exponencial y Ausencia de Memoria

Mientras el proceso de Poisson cuenta eventos, la distribucion exponencial modela el tiempo entre ocurrencias sucesivas.

**Funcion de densidad:**

$$f(t) = \lambda e^{-\lambda t}, \quad t \ge 0$$

**Funcion de distribucion acumulada:**

$$F(t) = P(T \le t) = 1 - e^{-\lambda t}$$

**Media y varianza:**

$$E[T] = \frac{1}{\lambda}, \quad Var[T] = \frac{1}{\lambda^2}$$

**Propiedad sin memoria:** La exponencial es la unica distribucion continua que cumple:

$$P(X > t + s \mid X > s) = P(X > t) = e^{-\lambda t}$$

---

### 4. Proceso de Renovacion

Un proceso de renovacion es una clase mas amplia de procesos de conteo donde los tiempos entre llegadas son variables aleatorias independientes e identicamente distribuidas (no negativas).

Si los tiempos entre arribos siguen una distribucion exponencial, el proceso de renovacion se reduce a un proceso de Poisson.

---

### 5. Proceso de Nacimiento y Muerte

Un proceso de nacimiento y muerte es un caso especial de una cadena de Markov en tiempo continuo (CTMC). Las transiciones ocurren mediante saltos unitarios:

- **Nacimiento:** $n \to n+1$ con tasa $\lambda_n$
- **Muerte:** $n \to n-1$ con tasa $\mu_n$

Los estados $\{0,1,2,\dots\}$ representan el tamano de la poblacion. Estando en el estado $n$, el tiempo hasta la proxima llegada es $Exp(\lambda_n)$ y hasta la proxima salida es $Exp(\mu_n)$.

---

### 6. Ecuaciones de Balance

Para que el sistema alcance el equilibrio, el flujo de probabilidad debe balancearse.

**Balance global:** La tasa de flujo hacia adentro de un estado iguala la tasa hacia afuera:

$$(\lambda_n + \mu_n) P_n = \lambda_{n-1} P_{n-1} + \mu_{n+1} P_{n+1}, \quad n \ge 1$$

**Balance local:** El flujo entre estados vecinos se equilibra:

$$\lambda_{i-1} P_{i-1} = \mu_i P_i$$

A partir del balance local se obtienen las probabilidades de estado estable:

$$P_n = \frac{\lambda_{n-1}}{\mu_n} P_{n-1} \quad \Longrightarrow \quad P_n = P_0 \prod_{i=1}^{n} \frac{\lambda_{i-1}}{\mu_i}$$

---

### 7. El Modelo Teorico M/M/1

Es el modelo de colas mas fundamental (notacion de Kendall).

**Caracteristicas:**
- **M:** llegadas Poisson con tasa constante $\lambda$
- **M:** tiempos de servicio exponenciales con tasa constante $\mu$
- **1:** un unico servidor
- Capacidad infinita, disciplina FIFO

**Intensidad de trafico:**

$$\rho = \frac{\lambda}{\mu}$$

**Condicion de estabilidad:** $\rho < 1$ para que la cola no crezca indefinidamente.

**Distribucion de probabilidad de los estados** (balance local con $\lambda_n = \lambda$, $\mu_n = \mu$):

$$P_0 = 1 - \rho$$

$$P_n = (1 - \rho) \rho^n$$

**Metricas de rendimiento:**

Numero promedio de clientes en el sistema:

$$L = E[L] = \frac{\rho}{1 - \rho}$$

Numero promedio de clientes en la cola:

$$L_q = \frac{\rho^2}{1 - \rho}$$

Tiempo promedio en el sistema (Ley de Little: $L = \lambda W$):

$$W = \frac{L}{\lambda} = \frac{1}{\mu - \lambda}$$

Tiempo promedio en cola:

$$W_q = \frac{\rho}{\mu(1 - \rho)} = \frac{\lambda}{\mu(\mu - \lambda)}$$

**Relaciones generales:**

$$W = W_q + \frac{1}{\mu}, \qquad L = L_q + \frac{\lambda}{\mu}$$

---

### 8. Estado Estacionario (Steady State)

Se dice que el sistema alcanza el **estado estacionario** cuando las probabilidades de los estados $P_n(t)$ se vuelven independientes del tiempo $t$. En ese regimen, las metricas $L$, $L_q$, $W$, $W_q$ son constantes en el tiempo (no dependen de las condiciones iniciales).

**Condicion necesaria:** $\rho < 1$. Si $\rho \ge 1$, la cola crece indefinidamente y nunca se alcanza un estado estacionario.

**Regimen transitorio vs estacionario:** Al iniciar la simulacion, el sistema comienza vacio ($n=0$). Durante las primeras horas, las metricas observadas reflejan esa condicion inicial (regimen transitorio). Pasado un tiempo, el sistema "olvida" el estado inicial y las probabilidades convergen a la distribucion geometrica $P_n = (1-\rho)\rho^n$ (regimen estacionario).

**Implementacion en la simulacion:** Se define un periodo de **warmup** (`warmup_hours` en `config.json`). Durante el warmup la simulacion se ejecuta normalmente pero no se acumulan estadisticos. Al finalizar el warmup se reinician los contadores y se comienza a registrar datos. Esto asegura que las metricas calculadas correspondan al regimen estacionario y no esten sesgadas por el estado inicial vacio.
