# 📚 Paga-Ya Simulador Educativo — Sin reja, sin préstamo real

Sistema web **educativo** para simular microcrédito pagodiario legal con **todas las tasas colombianas**
(EM, EA, Nominal MV/MA/TV/TA/SV/SA/AV/AA, Periódica, Diaria/Semanal), control de **usura Superfinanciera**
y comparativa gota-vs-legal. **No desembolsa ni cobra plata real.**

| Capa | Tecnología |
|---|---|
| Backend | Django 5.1 puro (**sin** Django REST Framework, solo `JsonResponse`) |
| Frontend | React 18 + Vite |
| Base de datos | SQLite (la que trae Django por defecto) |
| Entorno Python | `venv` aislado en `backend/venv` (no instala nada global) |

---

## 1. Requisitos

- **Python 3.12+** → https://www.python.org/downloads/
  OJO al instalar: marca la casilla **"Add python.exe to PATH"**.
- **Node.js 20+ LTS** → https://nodejs.org
- Puertos libres: **8000** (backend) y **5173** (frontend).

Verifica en terminal:

```bat
python --version
node --version
```

---

## 2. Arranque rápido (recomendado) ⚡

> Ideal para el profe: clona, doble clic y listo. El sistema **se puebla solo** la primera vez.

1. Clona o descarga el proyecto.
2. Doble clic en **`INICIAR_PAGA_YA.bat`** (está en la raíz).
3. Ese script hace todo, en orden ([1/5] a [5/5] como verás en pantalla):
   1. Revisa que existan Python y Node, y crea `backend/venv` si no existe (aislado, no chinga tus otros proyectos).
   2. Instala las librerías (`pip install -r backend/requirements.txt`).
   3. Genera migraciones y crea `db.sqlite3` (`makemigrations` + `migrate`).
      OJO: las migraciones `0001_...py` están en el `.gitignore` (solo se sube
      `migrations/__init__.py`), así que cada PC las genera localmente.
   4. Corre `python backend/manage.py seed_demo` → **crea usuarios y préstamos de prueba**.
      Es idempotente: si ya existen, no duplica nada.
   5. Abre **dos ventanas**: backend en `:8000` y frontend en `:5173` (instala `node_modules` solo si falta), y te abre el navegador.
4. Entra a **http://localhost:5173** y loguéate con una cuenta demo (sección 3).

No cierres las dos ventanas negras mientras uses el sistema.

---

## 3. Cuentas demo (las crea el seed) 🔑

| Usuario | Clave | Rol | Qué vas a ver |
|---|---|---|---|
| `admin` | `admin123` | Administrador | Todo: resumen, usuarios, préstamos, reloj |
| `don_chepe` | `chepe123` | Prestador | Link de registro, clientes Carlos y María (ella en mora + reja) |
| `la_patrona` | `patrona123` | Prestadora | Cliente Juan al día, Lucía con préstamo pagado |
| `carlos` | `cliente123` | Cliente | Préstamo 100mil → 120mil con 1 cuota abonada |
| `maria` | `cliente123` | Cliente | ⚠️ **Alerta gigante "OJO, QUE TE PUEDEN TUMBAR LA REJA"** (varias cuotas caídas) |
| `juan` | `cliente123` | Cliente | Préstamo semanal al día |
| `lucia` | `cliente123` | Cliente | Préstamo quincenal pagado |

Préstamos demo que se crean:

| # | Cliente | Modalidad | Monto | Estado inicial |
|---|---|---|---|---|
| 1 | carlos | 100mil → 120mil en 7 días (diario) | $120.000 | ACTIVO, 1 cuota abonada |
| 2 | maria | 5.000 diarios × 24 días (diario) | $120.000 | **MORA grave + reja tumbada** |

> Los días/cuotas en mora de María dependen del día en que poblaste la demo
> (el seed crea ese préstamo 20 días en el pasado). Si quieres más o menos mora
> para la sustentación, usa el **reloj del admin** (botón "Saltar el día").
| 3 | juan | 500mil → 600mil en 4 semanas | $600.000 | ACTIVO |
| 4 | lucia | 300mil → 360mil en 2 quincenas | $360.000 | PAGADO |

### Re-poblar o resetear la demo

El seed es idempotente: crea los usuarios que falten y solo crea los préstamos
si no hay ninguno (nunca duplica). Al terminar **imprime en consola** las
credenciales y los links de registro de cada prestador.

```bat
cd backend
call venv\Scripts\activate.bat
python manage.py seed_demo
```

Para empezar de cero borrando TODO (incluye demo):

```bat
cd backend
call venv\Scripts\activate.bat
del db.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
```

---

## 4. Arranque manual (paso a paso) 🛠️

### Backend

```bat
cd backend
python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Backend en **http://localhost:8000/api/**. El panel clásico de Django sigue disponible en
**http://localhost:8000/admin/** (entra con `admin` / `admin123`).

### Frontend

```bat
cd frontend
npm install
npm run dev
```

Frontend en **http://localhost:5173**. Para compilar a producción: `npm run build`.

> Si en PowerShell `npm` te da error de *Execution Policy*, usa `npm.cmd install`
> o ejecuta `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

---

## 5. Cómo se usa (guía por rol) 📖

### Administrador 🛠️ (`/admin`)
- Ve **todo**: total de usuarios, préstamos, plata prestada, plata recaudada y cuántos van en mora.
- **Regula todo**: cambia el rol de cualquier usuario (admin/prestador/cliente).
- **⏰ Reloj del sistema**: botón **"⏩ Saltar el día"** (+N días) para adelantar la fecha
  y simular vencimientos sin esperar días reales. Botón **"Volver a fecha real"** para restablecer.
  Saltar días es lo que hace que las cuotas impagas caigan en mora y se prendan las alertas.

### Prestador 💰 (`/prestador`)
1. Copia **tu link** (`http://localhost:5173/register?code=XXXX`) y mándalo por WhatsApp.
2. Quien se registre con ese link queda automáticamente como **tu cliente** (1 prestador : N clientes).
3. **Crear préstamo**: escribe el usuario del cliente y juega con las 3 plantillas
   (los valores son 100% variables, solo ejemplos):
   - *100mil → 120mil en 7 días* (total en plazo)
   - *5.000 diarios por X días* (cuota diaria fija; total = cuota × días)
   - *Semanal / quincenal / mensual* (periódico)
4. Si un cliente se cae: te sale el aviso **"ve a tumbarle la reja"** con sus cuotas
   vencidas y días en mora → botón **"Marcar como Reja tumbada con éxito"**.

### Cliente 📅 (`/cliente`)
- Ve **cuánto ha abonado a capital**, **cuánto debe en plata ($)** y **cuánto debe en días**,
  más el detalle cuota por cuota (valor, pagado, saldo, estado, vencimiento).
- **Pagar en línea**: botón de pago (hoy **simulado**; la pasarela real se conecta después
  en el endpoint `POST /api/cliente/pagar/` — el backend ya reparte el pago a las cuotas
  más antiguas primero).
- Si se cae en una o varias cuotas, al entrar le aparece la alerta gigante:
  **"⚠️ OJO, QUE TE PUEDEN TUMBAR LA REJA ⚠️"**.

---

## 6. Reglas del negocio (sin interés compuesto) 📐

Todo es **lineal**, como prestan los gota a gota de verdad:

```
valor_cuota = monto_total_a_pagar / num_cuotas   (fijo al crear el préstamo)
```

- El `monto_total` se pacta al inicio (capital + ganancia fija) y **nunca** se recalcula
  sobre el saldo. No hay capitalización.
- Deuda en plata = suma de saldos de cuotas no pagadas.
- Deuda en días = días desde el vencimiento impago más antiguo hasta hoy.
- Cuota vencida = `fecha_vencimiento < hoy` y no está pagada.
- Los pagos se reparten a las cuotas **más antiguas primero** (FIFO).

---

## 7. API del backend (referencia) 🔌

Base: `http://localhost:8000/api/`. Sesiones con cookie (el front usa `credentials: 'include'`).
Todas las respuestas son `{"ok": true, "data": ...}` o `{"ok": false, "error": ...}`.

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| POST | `register/` | público | Crea usuario. Con `codigo` de prestador crea cliente vinculado |
| POST | `login/` / `logout/` | público | Entra / sale |
| GET | `me/` | logueado | Quién soy |
| GET | `mi-codigo/` | prestador | Mi código y link de registro |
| GET | `prestador/clientes/` | prestador | Mis clientes + cuotas caídas |
| GET | `prestador/prestamos/` | prestador | Mis préstamos (detalle + mora) |
| POST | `prestador/prestamos/crear/` | prestador | Crea préstamo + cuotas (valores variables) |
| POST | `prestador/reja/<id>/` | prestador | Marca "Reja tumbada con éxito" |
| GET | `cliente/mis-prestamos/` | cliente | Mis préstamos, abonos y deudas |
| GET | `cliente/prestamo/<id>/` | cliente | Detalle + cuotas |
| POST | `cliente/pagar/` | cliente | **Pago simulado** (aquí va la pasarela real) |
| GET | `admin/resumen/` | admin | Totales del sistema |
| GET | `admin/usuarios/` | admin | Todos los usuarios |
| POST | `admin/usuarios/rol/` | admin | Cambia rol |
| GET | `admin/reloj/` | admin | Fecha real vs fecha del sistema |
| POST | `admin/reloj/avanzar/` | admin | Salta N días (`{"dias": 3}`) |
| POST | `admin/reloj/reset/` | admin | Vuelve a fecha real |
| GET | `calculadora/` | público | Previsualiza plan: `?monto_prestado=100000&monto_total=120000&num_cuotas=7&frecuencia=DIARIO` |

---

## 8. Estructura del proyecto 📁

```
paga-ya/
├── INICIAR_PAGA_YA.bat      ← doble clic: instala, migra, puebla demo y levanta todo
├── README.md
├── .gitignore
├── backend/
│   ├── venv/                ← entorno aislado (se crea solo, no se sube a git)
│   ├── requirements.txt     ← Django + django-cors-headers
│   ├── activar.bat          ← activa el venv para trabajar manual
│   ├── manage.py
│   ├── db.sqlite3           ← se crea con makemigrations + migrate (no se sube a git)
│   ├── config/              ← settings, urls, wsgi
│   └── core/
│       ├── models.py        ← Perfil, Prestamo, Cuota, Pago, RelojSistema
│       ├── utils.py         ← cálculo lineal + reparto FIFO (sin interés compuesto)
│       ├── views.py         ← API JSON con JsonResponse (sin DRF)
│       ├── urls.py
│       ├── admin.py
│       └── management/commands/seed_demo.py  ← datos demo
└── frontend/
    ├── package.json         ← React + Vite + react-router
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx, App.jsx, api.js, index.css
        └── pages/           ← Login, Register, AdminDashboard,
                                PrestadorDashboard, ClienteDashboard
```

---

## 9. Solución de problemas 🆘

| Problema | Solución |
|---|---|
| `python` no se reconoce | Reinstala Python marcando **Add to PATH** |
| `node` no se reconoce | Instala Node 20+ LTS y reabre la terminal |
| PowerShell bloquea `npm` | Usa `npm.cmd` o `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Puerto 8000/5173 ocupado | Cierra la otra ventana que lo use o cambia el puerto |
| Frontend no conecta al backend | El backend debe estar corriendo en `:8000` con CORS a `:5173` (ya configurado en `settings.py`) |
| Quiero base limpia | Borra `backend/db.sqlite3`, corre `makemigrations` + `migrate` + `seed_demo` |
| El seed no duplica | Es idempotente: si ya hay datos demo, avisa y no crea nada |

---

Hecho con Django + React para **Paga Ya** 💸 — plata en mano, reja de pie 🧱.
