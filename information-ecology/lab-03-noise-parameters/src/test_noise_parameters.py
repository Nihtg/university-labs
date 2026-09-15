"""
Модульные тесты для проверки расчетов шума и звукопоглощения.
Лабораторная работа № 9р (Информационная экология, Вариант 6).
"""

import unittest
import math
from noise_parameters_calculator import (
    NoiseSource,
    RoomAcousticsParameters,
    NoiseParametersCalculator,
    get_variant_6_parameters,
    get_delta_l
)


class TestNoiseParameters(unittest.TestCase):
    """Тесты верификации акустических расчетов шума производственного помещения."""

    def setUp(self):
        self.sources, self.room = get_variant_6_parameters()
        self.results = NoiseParametersCalculator.calculate(self.sources, self.room)

    def test_variant_6_inputs(self):
        """Проверка исходных параметров Варианта 6."""
        self.assertEqual(len(self.sources), 3)

        # Источник 1
        s1 = self.sources[0]
        self.assertEqual(s1.R, 4.5)
        self.assertEqual(s1.L, 110.0)
        self.assertEqual(s1.wall_number, 6)
        self.assertEqual(s1.wall_mass_kg, 24.0)

        # Источник 2
        s2 = self.sources[1]
        self.assertEqual(s2.R, 9.5)
        self.assertEqual(s2.L, 80.0)
        self.assertEqual(s2.wall_number, 15)
        self.assertEqual(s2.wall_mass_kg, 117.0)

        # Источник 3
        s3 = self.sources[2]
        self.assertEqual(s3.R, 4.5)
        self.assertEqual(s3.L, 110.0)
        self.assertEqual(s3.wall_number, 5)
        self.assertEqual(s3.wall_mass_kg, 12.0)

        # Помещение
        self.assertEqual(self.room.S_ceiling, 350.0)
        self.assertEqual(self.room.S_walls, 260.0)
        self.assertEqual(self.room.S_floor, 350.0)
        self.assertEqual(self.room.alpha_1, 0.45)
        self.assertEqual(self.room.alpha_2, 0.70)
        self.assertEqual(self.room.beta_1, 0.031)
        self.assertEqual(self.room.beta_2, 0.90)
        self.assertEqual(self.room.gamma_floor, 0.061)

    def test_distance_attenuation(self):
        """Проверка расчета снижения шума с расстоянием LR = L - 20*lg(R) - 8."""
        # Ист 1: 110 - 20*lg(4.5) - 8 = 110 - 13.064 - 8 = 88.936 дБ
        expected_lr1 = 110.0 - 20.0 * math.log10(4.5) - 8.0
        self.assertAlmostEqual(self.results.sources_results[0].L_R, expected_lr1, places=3)

        # Ист 2: 80 - 20*lg(9.5) - 8 = 80 - 19.554 - 8 = 52.446 дБ
        expected_lr2 = 80.0 - 20.0 * math.log10(9.5) - 8.0
        self.assertAlmostEqual(self.results.sources_results[1].L_R, expected_lr2, places=3)

        # Ист 3: 110 - 20*lg(4.5) - 8 = 88.936 дБ
        expected_lr3 = 110.0 - 20.0 * math.log10(4.5) - 8.0
        self.assertAlmostEqual(self.results.sources_results[2].L_R, expected_lr3, places=3)

    def test_wall_soundproofing(self):
        """Проверка звукоизоляции стен-преград N = 14.5*lg(G) + 15."""
        # Стена 6 (G=24): N = 14.5*lg(24) + 15 = 14.5*1.3802 + 15 = 20.013 + 15 = 35.013 дБ
        expected_n1 = 14.5 * math.log10(24.0) + 15.0
        self.assertAlmostEqual(self.results.sources_results[0].N_wall, expected_n1, places=3)

        # Стена 15 (G=117): N = 14.5*lg(117) + 15 = 14.5*2.0682 + 15 = 29.989 + 15 = 44.989 дБ
        expected_n2 = 14.5 * math.log10(117.0) + 15.0
        self.assertAlmostEqual(self.results.sources_results[1].N_wall, expected_n2, places=3)

        # Стена 5 (G=12): N = 14.5*lg(12) + 15 = 14.5*1.0792 + 15 = 15.648 + 15 = 30.648 дБ
        expected_n3 = 14.5 * math.log10(12.0) + 15.0
        self.assertAlmostEqual(self.results.sources_results[2].N_wall, expected_n3, places=3)

    def test_effective_source_levels(self):
        """Проверка уровней на рабочем месте с учетом преграды."""
        # Ист 1: 88.936 - 35.013 = 53.923 дБ
        self.assertAlmostEqual(self.results.sources_results[0].L_R_eff, 53.923, places=2)
        # Ист 2: 52.446 - 44.989 = 7.457 дБ
        self.assertAlmostEqual(self.results.sources_results[1].L_R_eff, 7.457, places=2)
        # Ист 3: 88.936 - 30.648 = 58.288 дБ
        self.assertAlmostEqual(self.results.sources_results[2].L_R_eff, 58.288, places=2)

    def test_table_addition_and_interpolation(self):
        """Проверка функции поправки Delta L по Таблице 9.1."""
        self.assertEqual(get_delta_l(0.0), 3.0)
        self.assertEqual(get_delta_l(1.0), 2.5)
        self.assertEqual(get_delta_l(2.0), 2.0)
        self.assertEqual(get_delta_l(10.0), 0.4)
        self.assertEqual(get_delta_l(20.0), 0.0)
        self.assertEqual(get_delta_l(25.0), 0.0)

        # Интерполяция: между 4 (1.5) и 5 (1.2) для diff = 4.365
        interp = get_delta_l(4.365)
        self.assertAlmostEqual(interp, 1.5 - 0.3 * 0.365, places=3)

    def test_total_noise_addition(self):
        """Проверка последовательного сложения уровней шума."""
        # Шаг 1: 58.288 (Ист 3) + 53.923 (Ист 1) -> diff = 4.365 -> delta = 1.390 -> L13 = 59.678 дБ
        # Шаг 2: 59.678 + 7.457 (Ист 2) -> diff = 52.221 > 20 -> delta = 0.0 -> L_sigma = 59.678 дБ
        self.assertAlmostEqual(self.results.L_sigma_table, 59.68, delta=0.05)
        # Точное энергетическое сложение
        self.assertAlmostEqual(self.results.L_sigma_exact, 59.64, delta=0.05)

    def test_room_sound_absorption(self):
        """Проверка звукопоглощения и снижения шума K."""
        # M1 = 350 * 0.45 + 260 * 0.031 + 350 * 0.061 = 157.5 + 8.06 + 21.35 = 186.91
        self.assertAlmostEqual(self.results.M1, 186.91, places=2)

        # M2 = 350 * 0.70 + 260 * 0.90 + 350 * 0.061 = 245.0 + 234.0 + 21.35 = 500.35
        self.assertAlmostEqual(self.results.M2, 500.35, places=2)

        # K = 10 * lg(500.35 / 186.91) = 10 * lg(2.6769) = 4.276 дБ
        expected_k = 10.0 * math.log10(500.35 / 186.91)
        self.assertAlmostEqual(self.results.K, expected_k, places=2)
        self.assertAlmostEqual(self.results.K, 4.28, delta=0.02)

    def test_result_level_with_absorption(self):
        """Проверка результирующего уровня L'_sigma."""
        # L'_sigma = 59.68 - 4.28 = 55.40 дБ
        expected_prime = self.results.L_sigma_table - self.results.K
        self.assertAlmostEqual(self.results.L_prime_sigma_table, expected_prime, places=3)
        self.assertAlmostEqual(self.results.L_prime_sigma_table, 55.40, delta=0.05)

        # Соответствие нормам
        self.assertTrue(self.results.is_safe_after)
        self.assertGreater(self.results.margin_after, 4.0)


if __name__ == "__main__":
    unittest.main()
