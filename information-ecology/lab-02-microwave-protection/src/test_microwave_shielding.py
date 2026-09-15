"""
Модульные тесты для проверки электродинамических расчетов экранирования СВЧ.
Лабораторная работа № 14р (Информационная экология, Вариант 6).
"""

import unittest
import math
from microwave_shielding_calculator import (
    GeneratorParameters,
    MaterialProperties,
    MicrowaveShieldingCalculator,
    get_variant_6_parameters,
    C_LIGHT,
    MU_0,
    WAVE_IMPEDANCE_0,
    N_ENERGY_DOSE_LIMIT
)


class TestMicrowaveShielding(unittest.TestCase):
    """Набор тестов для верификации расчетов защиты от СВЧ-излучения."""

    def setUp(self):
        self.gen_v6, self.mat_v6 = get_variant_6_parameters()
        self.results = MicrowaveShieldingCalculator.calculate(self.gen_v6, self.mat_v6)

    def test_variant_6_source_parameters(self):
        """Проверка исходных данных Варианта 6."""
        self.assertEqual(self.gen_v6.W, 12)
        self.assertEqual(self.gen_v6.I, 80.0)
        self.assertEqual(self.gen_v6.f, 4.0e8)
        self.assertEqual(self.gen_v6.T, 0.2)
        self.assertEqual(self.gen_v6.D, 0.04)
        self.assertEqual(self.gen_v6.R, 2.0)
        self.assertEqual(self.gen_v6.r, 0.1)

        self.assertEqual(self.mat_v6.screen_material, "Медь")
        self.assertEqual(self.mat_v6.mu, 1.0)
        self.assertEqual(self.mat_v6.gamma, 5.7e7)
        self.assertEqual(self.mat_v6.rod_material, "Эбонит")
        self.assertEqual(self.mat_v6.epsilon, 3.0)

    def test_magnetic_field_and_ratio(self):
        """Проверка расчета напряженности магнитного поля H."""
        # R / r = 2.0 / 0.1 = 20.0 > 10 => beta_m = 1.0
        self.assertEqual(self.results.ratio_R_r, 20.0)
        self.assertEqual(self.results.beta_m, 1.0)
        # H = (12 * 80 * 0.01) / (4 * 8) * 1 = 9.6 / 32 = 0.3000 A/m
        self.assertAlmostEqual(self.results.H, 0.3, places=5)

    def test_wave_zone_conditions(self):
        """Проверка условий волновой зоны излучения."""
        # lambda = 3e8 / 4e8 = 0.75 m
        self.assertAlmostEqual(self.results.wavelength, 0.75, places=4)
        # cond1 = 0.75 / (2*pi) ~= 0.119366 m
        expected_cond1 = 0.75 / (2.0 * math.pi)
        self.assertAlmostEqual(self.results.condition_1_limit, expected_cond1, places=4)
        # cond2 = 0.1^2 / 0.75 = 0.01 / 0.75 ~= 0.013333 m
        expected_cond2 = 0.01 / 0.75
        self.assertAlmostEqual(self.results.condition_2_limit, expected_cond2, places=4)

        # R = 2.0 m >> 0.1194 and R >> 0.0133
        self.assertTrue(self.results.is_wave_zone)

    def test_power_flux_density_and_limits(self):
        """Проверка плотности потока энергии и ПДУ."""
        # PPE = 377 * 0.3^2 / 2 = 377 * 0.09 / 2 = 16.965 W/m^2
        self.assertAlmostEqual(self.results.ppe, 16.965, places=4)
        # PPE_dop = 2.0 / 0.2 = 10.0 W/m^2
        self.assertAlmostEqual(self.results.ppe_dop, 10.0, places=4)
        # Hazard check
        self.assertTrue(self.results.is_hazard)
        self.assertAlmostEqual(self.results.hazard_ratio, 1.6965, places=4)

    def test_attenuation_coefficients(self):
        """Проверка требуемого ослабления электромагнитного поля L."""
        # L = 16.965 / 10 = 1.6965
        self.assertAlmostEqual(self.results.L, 1.6965, places=4)
        # L_db = 10 * lg(1.6965) ~= 2.2955 dB
        expected_ldb = 10.0 * math.log10(1.6965)
        self.assertAlmostEqual(self.results.L_db, expected_ldb, places=4)

    def test_screen_thickness(self):
        """Проверка расчета толщины металлического экрана."""
        # omega = 2 * pi * 4e8 = 8e8 * pi ~= 2.51327e9 rad/s
        expected_omega = 2.0 * math.pi * 4.0e8
        self.assertAlmostEqual(self.results.omega, expected_omega, places=2)

        # mu_a = 4 * pi * 1e-7 * 1.0 ~= 1.25664e-6
        expected_mu_a = 4.0 * math.pi * 1e-7
        self.assertAlmostEqual(self.results.mu_a, expected_mu_a, places=9)

        # Delta (скин-слой) ~= 3.3331 um
        self.assertAlmostEqual(self.results.skin_depth * 1e6, 3.3331, delta=0.01)

        # delta_min ~= 0.88089 um (0.000881 mm)
        self.assertAlmostEqual(self.results.delta_min_um, 0.88089, delta=0.01)
        self.assertAlmostEqual(self.results.delta_min_mm, 0.000881, delta=0.00005)

        # Конструктивная толщина экрана должна быть не менее 0.5 мм
        self.assertGreaterEqual(self.results.delta_constructive_mm, 0.5)

    def test_waveguide_tube_parameters(self):
        """Проверка затухания и длины трубки-волновода."""
        # alpha = 32 / (0.04 * sqrt(3.0)) = 32 / (0.04 * 1.73205) ~= 461.88 dB/m
        expected_alpha = 32.0 / (0.04 * math.sqrt(3.0))
        self.assertAlmostEqual(self.results.alpha, expected_alpha, places=2)

        # l_tube_min = L_db / alpha = 2.2955 / 461.88 ~= 0.00497 m = 4.97 mm
        expected_l = self.results.L_db / expected_alpha
        self.assertAlmostEqual(self.results.l_tube_min, expected_l, places=6)
        self.assertAlmostEqual(self.results.l_tube_min_mm, 4.97, delta=0.05)

        # Конструктивная длина трубки должна быть адекватной для монтажа (>= 30 мм)
        self.assertGreaterEqual(self.results.l_tube_constructive_mm, 30.0)

    def test_safe_non_hazardous_case(self):
        """Проверка поведения при допустимом уровне (без превышения)."""
        safe_gen = GeneratorParameters(
            W=2, I=10.0, f=4.0e8, T=0.2, D=0.04, R=5.0, r=0.05
        )
        res_safe = MicrowaveShieldingCalculator.calculate(safe_gen, self.mat_v6)
        self.assertFalse(res_safe.is_hazard)
        self.assertEqual(res_safe.L, 1.0)
        self.assertEqual(res_safe.L_db, 0.0)
        self.assertEqual(res_safe.delta_min, 0.0)
        self.assertEqual(res_safe.l_tube_min, 0.0)


if __name__ == "__main__":
    unittest.main()
