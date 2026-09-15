"""
Модуль расчета шумовых параметров рабочей зоны.
Лабораторная работа № 9р (ЛР № 3 курса «Информационная экология»).

Тема: «Исследование шумовых параметров рабочей зоны».
Методическое пособие: Курбатов В.А., МТУСИ, кафедра ЭБЖиЭ.
"""

from dataclasses import dataclass
import math
from typing import List, Dict, Tuple


# Таблица 9.1: Поправка Delta L (дБ) в зависимости от разности уровней (L_A - L_B)
TABLE_9_1: Dict[int, float] = {
    0: 3.0,
    1: 2.5,
    2: 2.0,
    3: 1.8,
    4: 1.5,
    5: 1.2,
    6: 1.0,
    7: 0.8,
    8: 0.6,
    9: 0.5,
    10: 0.4,
    15: 0.2,
    20: 0.0
}


def get_delta_l(diff: float) -> float:
    """
    Возвращает поправку Delta L по Таблице 9.1 с линейной интерполяцией
    для промежуточных значений разности уровней.
    """
    diff_val = abs(diff)
    keys = sorted(TABLE_9_1.keys())
    if diff_val <= keys[0]:
        return TABLE_9_1[keys[0]]
    if diff_val >= keys[-1]:
        return 0.0

    for i in range(len(keys) - 1):
        k1, k2 = keys[i], keys[i + 1]
        if k1 <= diff_val <= k2:
            v1, v2 = TABLE_9_1[k1], TABLE_9_1[k2]
            return v1 + (v2 - v1) * (diff_val - k1) / (k2 - k1)
    return 0.0


@dataclass(frozen=True)
class NoiseSource:
    """Параметры отдельного источника шума и его преграды (Табл. 9.2, 9.4)."""
    source_id: int        # Номер источника (1, 2, 3)
    name: str             # Наименование установки
    R: float              # Расстояние от источника до рабочего места, м
    L: float              # Уровень интенсивности шума источника на расстоянии 1 м, дБ
    wall_number: int      # Номер стены-преграды по Табл. 9.4
    wall_material: str    # Материал и конструкция стены-преграды
    wall_thickness_m: float # Толщина конструкции, м
    wall_mass_kg: float   # Масса 1 м^2 преграды (G), кг


@dataclass(frozen=True)
class RoomAcousticsParameters:
    """Геометрические и акустические параметры помещения (Табл. 9.3)."""
    S_ceiling: float      # Площадь потолка S_пт, м^2
    S_walls: float        # Площадь стен S_с, м^2
    S_floor: float        # Площадь пола S_пл (равна S_пт), м^2
    alpha_1: float        # Коэффициент поглощения потолка без спец. покрытия
    alpha_2: float        # Коэффициент поглощения потолка со спец. покрытием
    beta_1: float         # Коэффициент поглощения стен без спец. покрытия
    beta_2: float         # Коэффициент поглощения стен со спец. покрытием
    gamma_floor: float = 0.061 # Коэффициент поглощения паркетного пола


@dataclass(frozen=True)
class SourceCalculationResult:
    """Результаты расчета уровней для отдельного источника."""
    source: NoiseSource
    L_R: float            # Уровень шума на расстоянии R без преграды, дБ
    N_wall: float         # Снижение уровня шума стеной-преградой, дБ
    L_R_eff: float        # Эффективный уровень шума на рабочем месте с учетом преграды, дБ


@dataclass(frozen=True)
class NoiseCalculationResults:
    """Комплексные результаты расчетов уровней шума и звукопоглощения."""
    sources_results: List[SourceCalculationResult]
    
    # Порядок сложения уровней
    addition_steps: List[Dict[str, float]]
    
    # Суммарные уровни шума
    L_sigma_table: float       # Суммарный уровень шума по методике (Табл. 9.1), дБ
    L_sigma_exact: float       # Точный суммарный уровень (энергетическое сложение), дБ
    
    # Параметры звукопоглощения
    M1: float                  # Эквивалентное звукопоглощение до покрытия, ед. погл.
    M2: float                  # Эквивалентное звукопоглощение после покрытия, ед. погл.
    K: float                   # Величина снижения уровня шума акустической обработкой, дБ
    
    # Результирующий уровень шума со звукопоглощением
    L_prime_sigma_table: float # Результирующий уровень (по Табл. 9.1), дБ
    L_prime_sigma_exact: float # Результирующий уровень (энергетический), дБ
    
    # Санитарные нормативы
    pdu_norm: float            # Допустимый уровень шума по нормам (60 дБ для залов с ВТ)
    is_safe_before: bool       # Соответствие нормам до звукопоглощения
    is_safe_after: bool        # Соответствие нормам после звукопоглощения
    margin_after: float        # Запас до ПДУ после обработки, дБ


class NoiseParametersCalculator:
    """Калькулятор шумовых параметров рабочей зоны по методике ЛР № 9р."""

    @staticmethod
    def calculate(sources: List[NoiseSource], room: RoomAcousticsParameters, pdu_norm: float = 60.0) -> NoiseCalculationResults:
        # 1. Расчет затухания расстоянием и звукоизоляции преградой для каждого источника
        sources_res: List[SourceCalculationResult] = []
        for s in sources:
            # L_R = L - 20 * lg(R) - 8
            l_r = s.L - 20.0 * math.log10(s.R) - 8.0
            # N = 14.5 * lg(G) + 15
            n_wall = 14.5 * math.log10(s.wall_mass_kg) + 15.0
            # L_R_eff = L_R - N
            l_r_eff = l_r - n_wall
            sources_res.append(SourceCalculationResult(
                source=s,
                L_R=l_r,
                N_wall=n_wall,
                L_R_eff=l_r_eff
            ))

        # 2. Последовательное сложение уровней по Таблице 9.1 (начиная с наиболее интенсивных)
        # Сортируем по убыванию L_R_eff
        sorted_res = sorted(sources_res, key=lambda x: x.L_R_eff, reverse=True)
        
        addition_steps: List[Dict[str, float]] = []
        current_level = sorted_res[0].L_R_eff
        
        for i in range(1, len(sorted_res)):
            next_src = sorted_res[i]
            l_a = max(current_level, next_src.L_R_eff)
            l_b = min(current_level, next_src.L_R_eff)
            diff = l_a - l_b
            delta_l = get_delta_l(diff)
            new_level = l_a + delta_l
            
            addition_steps.append({
                "step": i,
                "L_A": l_a,
                "L_B": l_b,
                "diff": diff,
                "delta_L": delta_l,
                "result": new_level
            })
            current_level = new_level

        L_sigma_table = current_level

        # Точное энергетическое сложение: 10 * lg(sum(10^(L_i / 10)))
        L_sigma_exact = 10.0 * math.log10(sum(10.0 ** (s.L_R_eff / 10.0) for s in sources_res))

        # 3. Расчет эквивалентного звукопоглощения помещения
        # M = S_пт * alpha + S_с * beta + S_пл * gamma
        M1 = room.S_ceiling * room.alpha_1 + room.S_walls * room.beta_1 + room.S_floor * room.gamma_floor
        M2 = room.S_ceiling * room.alpha_2 + room.S_walls * room.beta_2 + room.S_floor * room.gamma_floor

        # Снижение уровня шума K = 10 * lg(M2 / M1)
        K = 10.0 * math.log10(M2 / M1)

        # Результирующий уровень шума со звукопоглощающими материалами
        L_prime_sigma_table = L_sigma_table - K
        L_prime_sigma_exact = L_sigma_exact - K

        is_safe_before = L_sigma_table <= pdu_norm
        is_safe_after = L_prime_sigma_table <= pdu_norm
        margin_after = pdu_norm - L_prime_sigma_table

        return NoiseCalculationResults(
            sources_results=sources_res,
            addition_steps=addition_steps,
            L_sigma_table=L_sigma_table,
            L_sigma_exact=L_sigma_exact,
            M1=M1,
            M2=M2,
            K=K,
            L_prime_sigma_table=L_prime_sigma_table,
            L_prime_sigma_exact=L_prime_sigma_exact,
            pdu_norm=pdu_norm,
            is_safe_before=is_safe_before,
            is_safe_after=is_safe_after,
            margin_after=margin_after
        )


def get_variant_6_parameters() -> Tuple[List[NoiseSource], RoomAcousticsParameters]:
    """
    Возвращает исходные данные для Варианта 6:
    Табл. 9.2 (последняя цифра 6) + Табл. 9.4;
    Табл. 9.3 (предпоследняя цифра 6).
    """
    sources = [
        NoiseSource(
            source_id=1,
            name="Вентиляционная установка 1",
            R=4.5,
            L=110.0,
            wall_number=6,
            wall_material="Картон в несколько слоев",
            wall_thickness_m=0.04,
            wall_mass_kg=24.0
        ),
        NoiseSource(
            source_id=2,
            name="Вентиляционная установка 2",
            R=9.5,
            L=80.0,
            wall_number=15,
            wall_material="Гипсовая перегородка",
            wall_thickness_m=0.11,
            wall_mass_kg=117.0
        ),
        NoiseSource(
            source_id=3,
            name="Вентиляционная установка 3",
            R=4.5,
            L=110.0,
            wall_number=5,
            wall_material="Картон в несколько слоев",
            wall_thickness_m=0.02,
            wall_mass_kg=12.0
        ),
    ]

    room = RoomAcousticsParameters(
        S_ceiling=350.0,
        S_walls=260.0,
        S_floor=350.0,
        alpha_1=0.45,   # 45 * 10^-2
        alpha_2=0.70,   # 70 * 10^-2
        beta_1=0.031,   # 31 * 10^-3
        beta_2=0.90,    # 90 * 10^-2
        gamma_floor=0.061
    )

    return sources, room


if __name__ == "__main__":
    srcs, rm = get_variant_6_parameters()
    res = NoiseParametersCalculator.calculate(srcs, rm)
    print("=== Результаты расчета для Варианта 6 ===")
    for sr in res.sources_results:
        print(f"{sr.source.name}: LR={sr.L_R:.2f} дБ, N={sr.N_wall:.2f} дБ -> LR_eff={sr.L_R_eff:.2f} дБ")
    print(f"Суммарный шум L_sigma (Табл. 9.1) = {res.L_sigma_table:.2f} дБ (точное = {res.L_sigma_exact:.2f} дБ)")
    print(f"M1 = {res.M1:.2f}, M2 = {res.M2:.2f}, K = {res.K:.2f} дБ")
    print(f"L'_sigma = {res.L_prime_sigma_table:.2f} дБ (точное = {res.L_prime_sigma_exact:.2f} дБ)")
