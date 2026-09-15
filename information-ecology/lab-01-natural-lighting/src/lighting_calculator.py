"""
Модуль инженерного расчета естественной освещенности производственных помещений
в соответствии с методическими указаниями кафедры ЭБЖиЭ МТУСИ (доцент Курбатов В.А.)
и нормами СП 52.13330 (СНиП 23-05-95).
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional


@dataclass
class RoomParameters:
    """Параметры помещения и световых проемов (исходные данные варианта)."""
    variant: int
    work_category: int       # Разряд зрительной работы (1..6)
    A: float                 # Длина помещения, м
    B: float                 # Ширина помещения, м
    h: float                 # Высота помещения, м
    h0: float                # Высота окна, м
    h_pod: float             # Расстояние от пола до подоконника, м
    h_work: float            # Высота рабочей поверхности над уровнем пола, м
    L: float                 # Расстояние до противостоящего здания, м
    H: float                 # Высота карниза противостоящего здания над подоконником, м
    b0: float                # Ширина оконного проема, м
    rho_ceil: float          # Коэффициент отражения потолка (доли единицы, 0..1)
    rho_wall: float          # Коэффициент отражения стен (доли единицы, 0..1)
    rho_floor: float         # Коэффициент отражения пола (доли единицы, 0..1)
    glazing_type: str = "double_steel"  # Тип остекления


@dataclass
class CalculationResult:
    """Результаты пошагового расчета естественного освещения."""
    h1: float                # Параметр окна (возвышение над рабочей поверхностью), м
    ratio_AB: float          # Отношение A / B
    ratio_Bh1: float         # Отношение B / h1
    ratio_LH: float          # Отношение L / H
    l_min: float             # Нормированный КЕО, %
    eta0: float              # Световая характеристика окна
    K_zd: float              # Коэффициент затемнения зданиями
    r0: float                # Общий коэффициент светопропускания
    S_floor: float           # Площадь пола, м2
    S_ceil: float            # Площадь потолка, м2
    S_walls: float           # Площадь стен, м2
    S_total: float           # Полная площадь внутренних поверхностей, м2
    rho_avg: float           # Средневзвешенный коэффициент отражения
    r1_single: float         # Коэффициент r1 при одностороннем освещении
    S0_single: float         # Требуемая площадь световых проемов (одностороннее), м2
    S_window: float          # Площадь одного окна, м2
    n_exact_single: float    # Расчетное число окон (точное)
    n_single: int            # Принятое число окон
    b_single: float          # Межоконный промежуток при одностороннем размещении, м
    is_single_feasible: bool # Возможно ли разместить окна в один ряд на одной стене
    # Параметры при двустороннем освещении:
    r1_double: float         # Коэффициент r1 при двустороннем освещении
    S0_double: float         # Требуемая площадь световых проемов (двустороннее), м2
    n_exact_double: float    # Расчетное число окон для двустороннего
    n_double: int            # Число окон (суммарное на 2 стены)
    n_per_wall: int          # Число окон на одну продольную стену
    b_double: float          # Межоконный промежуток при двустороннем размещении, м


class NaturalLightingCalculator:
    """Инженерный калькулятор естественной освещенности (методика МТУСИ)."""

    # Таблица 4.1: Нормы КЕО при боковом освещении l_min (%)
    TABLE_KEO_SIDE = {
        1: 3.5,
        2: 2.5,
        3: 2.0,
        4: 1.5,
        5: 1.0,
        6: 0.5,
    }

    # Таблица 4.2: Световая характеристика окна eta0
    ETA0_COLUMNS_B_H1 = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
    ETA0_TABLE = {
        0.5: [None, None, 22.0, 27.0, 42.0, None, None, None],
        1.0: [16.0, 15.0, 17.0, 19.0, 25.0, 35.0, 42.0, 45.0],
        1.5: [13.0, 11.5, 12.5, 15.0, 20.0, 25.0, 30.0, 35.0],
        2.0: [11.5, 10.0, 11.0, 13.0, 18.0, 22.0, 26.0, 30.0],
        3.0: [9.5,  8.5,  9.5,  11.5, 16.0, 19.0, 23.0, 26.0],
        4.0: [7.0,  7.0,  7.0,  9.5,  12.0, 15.0, 17.0, 20.0],
    }

    # Таблица 4.3: Коэффициент затемнения противостоящими зданиями K_зд
    TABLE_K_ZD = [
        (0.5, 1.7),
        (1.0, 1.4),
        (1.5, 1.2),
        (2.0, 1.1),
        (3.0, 1.0),
    ]

    # Таблица 4.5: Коэффициент светопропускания r0
    TABLE_R0 = {
        "single_wood": 0.50,
        "double_wood": 0.35,
        "coupled_wood": 0.40,
        "single_steel": 0.60,
        "double_steel": 0.40,
        "coupled_steel": 0.40,
    }

    # Таблица 4.6: Коэффициент r1, учитывающий отраженный свет
    TABLE_R1 = [
        (0.30, 2.0, 1.2),
        (0.40, 3.0, 1.7),
        (0.50, 4.0, 2.2),
    ]

    @classmethod
    def get_keo(cls, work_category: int) -> float:
        if work_category not in cls.TABLE_KEO_SIDE:
            raise ValueError(f"Неизвестный разряд работы: {work_category}. Допустимы 1..6.")
        return cls.TABLE_KEO_SIDE[work_category]

    @classmethod
    def interpolate_k_zd(cls, ratio_LH: float) -> float:
        if ratio_LH <= cls.TABLE_K_ZD[0][0]:
            return cls.TABLE_K_ZD[0][1]
        if ratio_LH >= cls.TABLE_K_ZD[-1][0]:
            return cls.TABLE_K_ZD[-1][1]

        for i in range(len(cls.TABLE_K_ZD) - 1):
            x0, y0 = cls.TABLE_K_ZD[i]
            x1, y1 = cls.TABLE_K_ZD[i + 1]
            if x0 <= ratio_LH <= x1:
                return y0 + (y1 - y0) * (ratio_LH - x0) / (x1 - x0)
        return 1.0

    @classmethod
    def interpolate_eta0(cls, ratio_AB: float, ratio_Bh1: float) -> float:
        ab_keys = sorted(cls.ETA0_TABLE.keys())
        ab_clamped = min(max(ratio_AB, ab_keys[0]), ab_keys[-1])

        if ab_clamped in cls.ETA0_TABLE:
            row_low_key = ab_clamped
            row_high_key = ab_clamped
        else:
            row_low_key = max(k for k in ab_keys if k <= ab_clamped)
            row_high_key = min(k for k in ab_keys if k >= ab_clamped)

        def interp_1d(row_key: float, x: float) -> float:
            row = cls.ETA0_TABLE[row_key]
            cols = cls.ETA0_COLUMNS_B_H1
            valid_pts = [(cols[j], row[j]) for j in range(len(cols)) if row[j] is not None]
            if not valid_pts:
                raise ValueError(f"Нет данных в таблице 4.2 для A/B={row_key}")
            if x <= valid_pts[0][0]:
                return valid_pts[0][1]
            if x >= valid_pts[-1][0]:
                return valid_pts[-1][1]
            for idx in range(len(valid_pts) - 1):
                x0, y0 = valid_pts[idx]
                x1, y1 = valid_pts[idx + 1]
                if x0 <= x <= x1:
                    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
            return valid_pts[-1][1]

        val_low = interp_1d(row_low_key, ratio_Bh1)
        val_high = interp_1d(row_high_key, ratio_Bh1)

        if row_low_key == row_high_key:
            return val_low
        return val_low + (val_high - val_low) * (ab_clamped - row_low_key) / (row_high_key - row_low_key)

    @classmethod
    def interpolate_r1(cls, rho_avg: float) -> Tuple[float, float]:
        pts = cls.TABLE_R1
        if rho_avg <= pts[0][0]:
            return pts[0][1], pts[0][2]
        if rho_avg >= pts[-1][0]:
            return pts[-1][1], pts[-1][2]

        for i in range(len(pts) - 1):
            r0, s0, d0 = pts[i]
            r1, s1, d1 = pts[i + 1]
            if r0 <= rho_avg <= r1:
                factor = (rho_avg - r0) / (r1 - r0)
                return s0 + (s1 - s0) * factor, d0 + (d1 - d0) * factor
        return pts[-1][1], pts[-1][2]

    @classmethod
    def calculate(cls, params: RoomParameters) -> CalculationResult:
        if params.A <= 0 or params.B <= 0 or params.h <= 0:
            raise ValueError("Размеры помещения (A, B, h) должны быть строго положительными.")
        if params.h0 <= 0 or params.b0 <= 0:
            raise ValueError("Размеры окна (h0, b0) должны быть строго положительными.")

        h1 = params.h0 + params.h_pod - params.h_work
        if h1 <= 0:
            raise ValueError(f"Недопустимое значение параметра окна h1={h1}. Проверьте h0, h_pod, h_work.")

        ratio_AB = params.A / params.B
        ratio_Bh1 = params.B / h1
        ratio_LH = params.L / params.H if params.H > 0 else 3.0

        l_min = cls.get_keo(params.work_category)
        eta0 = cls.interpolate_eta0(ratio_AB, ratio_Bh1)
        K_zd = cls.interpolate_k_zd(ratio_LH)
        r0 = cls.TABLE_R0.get(params.glazing_type, 0.40)

        S_floor = params.A * params.B
        S_ceil = params.A * params.B
        S_walls = 2 * (params.A + params.B) * params.h
        S_total = S_floor + S_ceil + S_walls

        rho_avg = (
            params.rho_ceil * S_ceil
            + params.rho_wall * S_walls
            + params.rho_floor * S_floor
        ) / S_total

        r1_single, r1_double = cls.interpolate_r1(rho_avg)

        # Формула МТУСИ: S0 = (S_floor * l_min * eta0 * K_zd) / (100 * r0 * r1)
        S0_single = (S_floor * l_min * eta0 * K_zd) / (100.0 * r0 * r1_single)
        S_window = params.h0 * params.b0
        n_exact_single = S0_single / S_window
        n_single = max(1, round(n_exact_single))

        # Формула межоконного расстояния: b = (A - n * b0) / (n + 1)
        b_single = (params.A - n_single * params.b0) / (n_single + 1)
        is_single_feasible = b_single > 0

        # Двустороннее боковое освещение: расчетная точка находится в середине помещения (B/2),
        # поэтому отношение глубины к высоте окна составляет (B / 2) / h1
        ratio_Bh1_double = (params.B / 2.0) / h1
        eta0_double = cls.interpolate_eta0(ratio_AB, ratio_Bh1_double)
        S0_double = (S_floor * l_min * eta0_double * K_zd) / (100.0 * r0 * r1_double)
        n_exact_double = S0_double / S_window
        n_double = max(2, round(n_exact_double))
        if n_double % 2 != 0:
            n_double += 1
        n_per_wall = n_double // 2
        b_double = (params.A - n_per_wall * params.b0) / (n_per_wall + 1)

        return CalculationResult(
            h1=h1,
            ratio_AB=ratio_AB,
            ratio_Bh1=ratio_Bh1,
            ratio_LH=ratio_LH,
            l_min=l_min,
            eta0=eta0,
            K_zd=K_zd,
            r0=r0,
            S_floor=S_floor,
            S_ceil=S_ceil,
            S_walls=S_walls,
            S_total=S_total,
            rho_avg=rho_avg,
            r1_single=r1_single,
            S0_single=S0_single,
            S_window=S_window,
            n_exact_single=n_exact_single,
            n_single=n_single,
            b_single=b_single,
            is_single_feasible=is_single_feasible,
            r1_double=r1_double,
            S0_double=S0_double,
            n_exact_double=n_exact_double,
            n_double=n_double,
            n_per_wall=n_per_wall,
            b_double=b_double,
        )


def get_variant_6_params() -> RoomParameters:
    """Параметры Варианта №6 студента БСТ2556 Смирнова В.Ю. (МТУСИ)."""
    return RoomParameters(
        variant=6,
        work_category=3,       # Разряд III
        A=20.0,                # Длина, м
        B=10.0,                # Ширина, м
        h=5.0,                 # Высота, м
        h0=3.5,                # Высота окна, м
        h_pod=1.2,             # Подоконник, м
        h_work=1.2,            # Рабочая поверхность, м
        L=30.0,                # Расстояние до здания, м
        H=30.0,                # Высота карниза, м
        b0=2.0,                # Ширина окна, м
        rho_ceil=0.50,         # Потолок: 50%
        rho_wall=0.50,         # Стены: 50%
        rho_floor=0.10,        # Пол: 10%
        glazing_type="double_steel"
    )
