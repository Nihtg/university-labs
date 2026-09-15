"""
Модульные тесты для проверки расчетов естественной освещенности и граничных случаев.
"""

import unittest
from lighting_calculator import NaturalLightingCalculator, RoomParameters, get_variant_6_params


class TestNaturalLightingCalculator(unittest.TestCase):
    """Тестирование основного расчета и граничных случаев."""

    def test_variant_6_baseline(self):
        """Проверка базового расчета для Варианта №6 (МТУСИ)."""
        params = get_variant_6_params()
        res = NaturalLightingCalculator.calculate(params)

        # 1. Геометрия
        self.assertAlmostEqual(res.h1, 3.5, places=2)
        self.assertAlmostEqual(res.ratio_AB, 2.0, places=2)
        self.assertAlmostEqual(res.ratio_Bh1, 10.0 / 3.5, places=2)
        self.assertAlmostEqual(res.ratio_LH, 1.0, places=2)

        # 2. Нормативные коэффициенты
        self.assertEqual(res.l_min, 2.0)
        self.assertAlmostEqual(res.K_zd, 1.4, places=2)
        self.assertEqual(res.r0, 0.40)
        self.assertGreater(res.eta0, 16.0)
        self.assertLess(res.eta0, 17.5)

        # 3. Площади и средневзвешенное отражение
        self.assertEqual(res.S_floor, 200.0)
        self.assertEqual(res.S_ceil, 200.0)
        self.assertEqual(res.S_walls, 300.0)
        self.assertEqual(res.S_total, 700.0)
        # rho_cp = (0.5*200 + 0.5*300 + 0.1*200) / 700 = 270 / 700 = 0.3857
        self.assertAlmostEqual(res.rho_avg, 270.0 / 700.0, places=3)

        # 4. Проверка одностороннего размещения
        self.assertEqual(res.S_window, 7.0)
        self.assertGreater(res.S0_single, 70.0)
        self.assertLess(res.S0_single, 90.0)
        # Число окон 11..12
        self.assertIn(res.n_single, [11, 12])
        # При n=11 или 12 на стене 20 м окна не помещаются в один ряд (b < 0)
        self.assertFalse(res.is_single_feasible)
        self.assertLess(res.b_single, 0)

        # 5. Проверка двустороннего размещения
        self.assertTrue(res.n_double >= 8)
        self.assertEqual(res.n_double % 2, 0)
        # На каждой стене b_double > 0 (физически реализуемо)
        self.assertGreater(res.b_double, 0.5)

    def test_square_room(self):
        """Граничный случай: квадратное помещение (A = B)."""
        params = get_variant_6_params()
        params.A = 12.0
        params.B = 12.0
        res = NaturalLightingCalculator.calculate(params)
        self.assertEqual(res.ratio_AB, 1.0)
        self.assertGreater(res.S0_single, 0)

    def test_maximum_shading(self):
        """Граничный случай: сильное затемнение высотным зданием (L / H <= 0.5)."""
        params = get_variant_6_params()
        params.L = 10.0
        params.H = 30.0  # L/H = 0.33 <= 0.5
        res = NaturalLightingCalculator.calculate(params)
        self.assertEqual(res.K_zd, 1.7)

    def test_no_shading(self):
        """Граничный случай: открытый горизонт (L / H >= 3.0)."""
        params = get_variant_6_params()
        params.L = 100.0
        params.H = 20.0  # L/H = 5.0 >= 3.0
        res = NaturalLightingCalculator.calculate(params)
        self.assertEqual(res.K_zd, 1.0)

    def test_reflection_limits(self):
        """Граничные случаи: абсолютно темное и идеально светлое помещение."""
        # Темное помещение (rho = 0.10 везде)
        params_dark = get_variant_6_params()
        params_dark.rho_ceil = 0.10
        params_dark.rho_wall = 0.10
        params_dark.rho_floor = 0.10
        res_dark = NaturalLightingCalculator.calculate(params_dark)
        self.assertAlmostEqual(res_dark.rho_avg, 0.10, places=2)
        self.assertEqual(res_dark.r1_single, 2.0)  # нижняя граница таблицы

        # Светлое помещение (rho = 0.70 везде)
        params_light = get_variant_6_params()
        params_light.rho_ceil = 0.70
        params_light.rho_wall = 0.70
        params_light.rho_floor = 0.70
        res_light = NaturalLightingCalculator.calculate(params_light)
        self.assertAlmostEqual(res_light.rho_avg, 0.70, places=2)
        self.assertEqual(res_light.r1_single, 4.0)  # верхняя граница таблицы

        # В светлом помещении требуется меньше площади остекления, чем в темном
        self.assertLess(res_light.S0_single, res_dark.S0_single)

    def test_all_work_categories(self):
        """Проверка всех разрядов зрительной работы от I до VI."""
        for cat in range(1, 7):
            params = get_variant_6_params()
            params.work_category = cat
            res = NaturalLightingCalculator.calculate(params)
            self.assertGreater(res.l_min, 0)
            self.assertGreater(res.S0_single, 0)

    def test_invalid_category_raises(self):
        """Проверка обработки некорректного разряда работы."""
        params = get_variant_6_params()
        params.work_category = 7
        with self.assertRaises(ValueError):
            NaturalLightingCalculator.calculate(params)

    def test_invalid_geometry_raises(self):
        """Проверка обработки некорректной геометрии (h1 <= 0)."""
        params = get_variant_6_params()
        params.h_work = 6.0  # рабочая поверхность выше верхнего края окна
        with self.assertRaises(ValueError):
            NaturalLightingCalculator.calculate(params)


if __name__ == "__main__":
    unittest.main()
