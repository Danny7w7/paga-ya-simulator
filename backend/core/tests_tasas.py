"""Tests motor tasas. Corre con: python manage.py test core.tests_tasas"""
from django.test import SimpleTestCase
from core import tasas as T


class TasasTest(SimpleTestCase):
    def test_em_ea_ida_vuelta(self):
        ea = T.convertir_a_ea(2.0, 'EM')
        # 2% EM ≈ 26.82% EA
        self.assertAlmostEqual(ea, 26.82, delta=0.05)
        em = T.convertir_desde_ea(ea, 'EM')
        self.assertAlmostEqual(em, 2.0, delta=0.01)

    def test_todas_desde_ea(self):
        tabla = T.tabla_tasas_desde_ea(26.824179)
        for k in ['EM', 'EA', 'NAMV', 'NAMA', 'NATV', 'NATA', 'NASV', 'NASA', 'PMV', 'PMA', 'ED', 'ES']:
            self.assertIn(k, tabla)
        self.assertAlmostEqual(tabla['EM'], 2.0, delta=0.02)

    def test_nominal_mv(self):
        # 24% NAMV -> periódica 2% -> EA 26.82%
        ea = T.convertir_a_ea(24.0, 'NAMV')
        self.assertAlmostEqual(ea, 26.82, delta=0.05)

    def test_cuota_fija(self):
        c = T.cuota_fija(1_000_000, 2.0, 12)
        self.assertTrue(90000 < c < 110000)
        tabla = T.generar_tabla_amortizacion(1_000_000, 2.0, 12)
        self.assertEqual(len(tabla['filas']), 12)
        self.assertEqual(tabla['filas'][-1]['saldo'], 0)

    def test_gota_es_usura(self):
        g = T.tasa_gota_implicita(100000, 120000, 7)
        self.assertGreater(g['ea_pct'], 39.65)
