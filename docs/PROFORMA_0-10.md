# Proforma — Paga-Ya Simulador Educativo (puntos 0–10)
Base: `Proforma_Propuesta_Prototipo_Finanzas_para_Ingenieros.pdf` (guía) + evidencia verificada en `paga-ya-simulador/`.
Proyecto: simulador educativo de microcrédito pagodiario legal. Sin desembolso real. Sin reja.

---

## 0. Identificación del equipo y del proyecto

| Campo | Información |
|---|---|
| Nombre provisional | Paga-Ya Simulador Educativo |
| Integrantes y programa | [PENDIENTE_EQUIPO — nombres, códigos, Ingeniería de Sistemas / Electrónica] |
| Curso / grupo | [PENDIENTE] |
| Docente | [PENDIENTE] |
| Fecha de presentación | [PENDIENTE] |
| Modalidad de prototipo | Software / simulador web |
| Versión de la propuesta | v1.0 — puntos 0–10 |

Repositorio: https://github.com/Danny7w7/paga-ya-simulator — rama `main`.

---

## 1. Título de la propuesta

**Simulador web de microcrédito pagodiario legal con todas las tasas colombianas y control de usura para estudiantes y prestadores informales**

Contiene lo exigido por la guía:
- Producto: simulador web (Django 5.1 + React 18 + Vite).
- Componente financiero: conversión de tasas (EM, EA, Nominal MV/MA/TV/TA/SV/SA/AV/AA, Periódica, Diaria/Semanal), cuota fija, tabla de amortización y tope de usura Superfinanciera.
- Usuario/contexto: estudiantes de Finanzas para Ingenieros y prestadores/clientes pagodiario en aula y trabajo de campo.

---

## 2. Resumen ejecutivo (203 palabras)

El pagodiario informal en Colombia opera con tasas como 100mil→120mil en 7 días (20% semanal, ~1.344.943% EA verificado en `backend/core/tasas.py:tasa_gota_implicita`), muy por encima de la usura (~39,65% EA educativa en `TasaUsura`), y con cobranza intimidante (“tumbar reja”, hoy eliminada con `410 Gone` en `views.py:api_marcar_reja`). El problema es doble: exclusión del crédito formal y analfabetismo en tasas. La solución es Paga-Ya Simulador Educativo, extensión legal del sistema `paga-ya`: conserva usuarios y trazabilidad pero reemplaza el préstamo real por `Simulacion` sin desembolso (`models.py:Simulacion`), con motor puro `tasas.py` que convierte absolutamente todas las tasas por pivote EA, calcula cuota fija Price y tabla de amortización, bloquea/advierte usura y compara gota-vs-legal. Metodología aplicada cuantitativa: diseño del motor, desarrollo modular Django/React, pruebas unitarias (`tests_tasas.py`, 5/5 OK) y validación contra casos conocidos más `npm run build` verificado. Resultado esperado: simulador funcional en `/simulador` que permite decidir con criterio (¿esta tasa es usura? ¿cuánto pago en total?) y sirve como evidencia transdisciplinaria Finanzas–Ingeniería sin mover plata real.

---

## 3. Planteamiento del problema

**Situación actual y evidencia.** El crédito pagodiario atiende a población sin acceso bancario con cobro diario/semanal en efectivo. El sistema base `paga-ya` lo modelaba fielmente: `Prestamo{monto_prestado,monto_total,num_cuotas}` + `Cuota{valor,saldo,estado}` (`models.py:86-183`), reparto FIFO (`utils.py:aplicar_pago_fifo`) y demo `100mil→120mil/7d` (`seed_demo.py`). Esa fidelidad es el problema: replica usura y cobranza abusiva.
**Causas.** Desconocimiento de equivalencias (EM vs EA vs Nominal MV), ausencia de comparador legal y normalización de la intimidación.
**Afectados.** Clientes pagodiario (sobre-endeudamiento), prestadores informales (riesgo penal art. 305 CP por usura) y estudiantes (aprenden finanzas sin laboratorio).
**Consecuencias financieras/de aprendizaje.** Pago de 33.920x la usura en el ejemplo (1.344.943% EA / 39,65%), sin tabla de amortización ni TAE visibles.
**Limitaciones actuales.** El `paga-ya` original: `Pago metodo=SIMULADO` (`models.py:185-193`), `SECRET_KEY` dura y `DEBUG=True` (`settings.py:9,11`), `RelojSistema` que manipula mora, y endpoint `prestador/reja` activo.
**Situación deseada.** Mismo acceso web, pero solo simulación: el usuario ingresa monto + tasa en cualquier denominación, ve todas las equivalencias, su cuota/total/intereses y si es usura, y compara el gota antes de decidir.

---

## 4. Pregunta de investigación

¿De qué manera un simulador web que convierte todas las tasas colombianas a EA, calcula cuota fija y tabla de amortización y contrasta contra la usura vigente puede facilitar la comprensión del costo real del microcrédito pagodiario y desincentivar la usura en estudiantes y usuarios pagodiario en aula y campo?

Estructura guía: [simulador web] + [facilitar comprensión/comparación del costo] + [microcrédito pagodiario] + [aula/campo].

---

## 5. Justificación

- **Académica.** Laboratorio verificable para Finanzas para Ingenieros: equivalencias, anualidades y usura con código + tests, no solo tablero. Reutiliza un sistema real y lo legaliza, aprendizaje por refactorización.
- **Financiera.** Hace visible lo invisible: TAE, total pagado, intereses y veces-usura. Previene usura y sobre-endeudamiento con números, no con sermones.
- **Tecnológica.** Demuestra extensión modular escalable (nuevo `tasas.py` puro + `TasaUsura/Simulacion` + 7 endpoints) sin reconstruir auth/usuarios; mismo patrón JsonResponse, migraciones versionadas, build frontend verificado.
- **Utilidad.** Estudiante simula tarea; prestador/cliente compara su gota en 30 segundos en `/simulador`; docente usa casos (20% semanal = usura) en clase.
- **Escalabilidad.** Motor sin I/O → reutilizable en móvil, API pública, nuevas frecuencias exactas, carga masiva de usura histórica SFC, multi-sede. Sin captación ni desembolso, escala sin licencia financiera (Dec. 1981/88).

---

## 6. Objetivo general

Diseñar un simulador web que convierta todas las tasas colombianas a su equivalente efectivo, calcule cuota fija y tabla de amortización y valide contra la usura vigente, para apoyar decisiones de microcrédito pagodiario legal en contexto académico y de campo.

Verbo + prototipo + finalidad financiera + contexto, según guía.

---

## 7. Objetivos específicos

1. Caracterizar el modelo gota actual (monto, cuota lineal, mora FIFO, reja) y sus brechas legales a partir del código `paga-ya` para definir qué se elimina y qué se conserva como histórico. Evidencia: informe + `410 Gone`.
2. Diseñar el motor de tasas con pivote EA que soporte EM, EA, Nominal MV/MA/TV/TA/SV/SA/AV/AA, Periódica y Diaria/Semanal, con fórmulas documentadas y precisión a 4 decimales. Evidencia: `tasas.py` + tabla de equivalencias.
3. Desarrollar el módulo de simulación (`TasaUsura`, `Simulacion`, endpoints `/tasas/*`, `/simular`) y la página `/simulador` con tabla de amortización y comparador gota-vs-legal, sin desembolso real. Evidencia: migración `0002`, build Vite OK.
4. Validar exactitud financiera y técnica con 5 pruebas unitarias (ida/vuelta EM↔EA, nominal MV, cuota/tabla, gota=usura) más casos conocidos (2% EM=26,82% EA; 24% NAMV=26,82% EA) y prueba de endpoints (410 reja, simular OK). Evidencia: `tests_tasas.py`, log de smoke.

---

## 8. Usuarios, beneficiarios y contexto de uso

- **Primario — Estudiante (rol cliente/prestador en demo).** Necesita convertir tasas y ver costo total sin saber fórmulas de memoria. Conocimiento: matemática básica. Escenario: aula/lab con `http://localhost:5173/simulador`. Decisión: ¿qué tasa conviene? ¿es usura?
- **Secundario — Prestador/cliente pagodiario real.** Necesita comparar su gota en lenguaje simple (veces-usura, $ total). Conocimiento: uso WhatsApp. Escenario: campo con celular. Decisión: no prestar/pagar usura, buscar alternativa formal.
- **Terciario — Docente/admin.** Carga `TasaUsura` mensual (`POST /tasas/usura/actualizar/`), revisa simulaciones, usa históricos sin reja. Escenario: clase y seguimiento.
- Sin desembolso ni datos sensibles reales; solo simulaciones guardadas por usuario (`mis-simulaciones/`).

---

## 9. Antecedentes y estado de soluciones

Financieros (brecha: no conectan con pagodiario ni con todas las tasas en un simulador local):
1. Superfinanciera — certificaciones mensuales de usura y microcrédito. Aprendizaje: tope legal EA. Brecha: solo publica tasa, no simula.
2. Banco de la República — conceptos de tasa efectiva y nominal. Aprendizaje: base teórica. Brecha: sin herramienta.
3. Ross, Westerfield & Jaffe (2012), Finanzas corporativas — valor del dinero en el tiempo. Brecha: enfoque corporativo, no microdiario.
4. Horngren, Datar & Rajan (2012), Contabilidad de costos — costo de servir. Brecha: no aplica a usura.
5. Ley 1328/09 + Ley 2300/23 (cobranza digna) y art. 305 CP (usura). Brecha: norma sin laboratorio.

Tecnológicos/comerciales:
6. Simuladores bancarios (Bancolombia, Davivienda) — cuota fija y tabla. Brecha: solo su producto, sin todas las denominaciones ni comparador gota, requieren internet/cuenta.
7. `paga-ya` original (Django+React, FIFO, demo gota) — base del presente. Brecha que abordamos: era operativo-ilegal (reja + usura + pago simulado como real); lo convertimos en educativo-legal.

Vacío abordado: simulador abierto, local, con absolutamente todas las tasas + usura actualizable + comparador gota, sin mover dinero.

---

## 10. Marco conceptual financiero

Sustento y cómo se incorpora en `paga-ya-simulador` (fórmulas en COP/%):

- **Tasa efectiva vs nominal (Superfinanciera; BancoRep).** Efectiva capitaliza; nominal solo divide: `i_per = j/m`. En código: `tasas.py:nominal_a_periodica`, `periodica_vencida_a_ea: (1+i)^m-1`. El usuario ingresa `NAMV 24%` y el sistema muestra `EM 2,00% → EA 26,82%` (`convertir_a_ea`, `tabla_tasas_desde_ea`).
- **Vencida vs anticipada.** `iv = ia/(1-ia)`; `EA = (1+iv)^m-1`. Implementado en `periodica_anticipada_a_ea`, `ea_a_periodica_anticipada`. Cubre NAMA/NATA/NASA/NAAA y PMA.
- **Equivalencia por pivote EA.** Toda tasa → EA → todas. Garantiza “absolutamente todas”: EM, EA, NAMV/NAMA/NATV/NATA/NASV/NASA/NAAV/NAAA, PMV/PMA, ED/ES. Verificado: `EA 26,8242% → EM 2,0, NAMV 24,0, ED 0,0651` (smoke).
- **Anualidad cuota fija (Price) y amortización (Ross et al.).** `R = P*i/(1-(1+i)^-n)` en `cuota_fija`; tabla con `interés=saldo*i`, `abono=R-interés` en `generar_tabla_amortizacion` (ajuste redondeo última cuota). Ej.: 500k, 2% EM, 12 → cuota 47.280.
- **Usura como regla de decisión (art. 305 CP; SFC).** `es_usura = EA > usura_EA` (`TasaUsura`, `_usura_vigente_ea`, default educativo 39,65% EA). Si usura: badge + advertencia, se guarda pero no se avala. Ej.: gota 20% en 7d → `EA 1.344.943,72%` (`tasa_gota_implicita: (1+i)^(365/d)-1`) = 33.920x usura → mensaje “Ilegal por usura”.
- **Costo total y costo de oportunidad.** `total_pagar = Σcuotas`, `total_intereses = total-monto`. El comparador muestra gota vs legal en $ y en veces-usura para decidir.

Fuentes preliminares (APA 7, ampliar en secc 28): Banco de la República. (s.f.). Tasas de interés; Superintendencia Financiera de Colombia. (s.f.). Certificación de usura y microcrédito; Ross, S. A., Westerfield, R. W., & Jaffe, J. F. (2012). Finanzas corporativas (9.ª ed.). McGraw-Hill; Horngren, C. T., Datar, S. M., & Rajan, M. V. (2012). Contabilidad de costos (14.ª ed.). Pearson; Congreso de Colombia. (2009). Ley 1328; (2023). Ley 2300; Código Penal, art. 305.
