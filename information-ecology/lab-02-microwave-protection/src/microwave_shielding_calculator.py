"""
Модуль расчета параметров защиты от электромагнитного излучения СВЧ-диапазона.
Лабораторная работа № 14р (ЛР № 2 курса «Информационная экология»).

Тема: «Расчет защитных параметров при работе с СВЧ-передатчиком».
Методическое пособие: Курбатов В.А., МТУСИ, кафедра ЭБЖиЭ.
"""

from dataclasses import dataclass
import math
from typing import Dict, Any, Tuple


# Фундаментальные физические константы
C_LIGHT: float = 3.0e8          # Скорость света в вакууме/воздухе, м/с
MU_0: float = 4.0 * math.pi * 1e-7  # Магнитная постоянная, Гн/м
WAVE_IMPEDANCE_0: float = 377.0 # Волновое сопротивление свободного пространства, Ом (~120*pi)
N_ENERGY_DOSE_LIMIT: float = 2.0  # Норматив предельно допустимой энергетической нагрузки, Вт*ч/м^2


@dataclass(frozen=True)
class GeneratorParameters:
    """Параметры источника излучения (СВЧ-генератора/выходного контура) по Табл. 14.1."""
    W: int          # Число витков катушки
    I: float        # Сила тока в контуре, А
    f: float        # Рабочая частота, Гц
    T: float        # Время воздействия/регулировок в смену, ч
    D: float        # Диаметр ручки управления / отверстия трубки, м
    R: float        # Расстояние от катушки до рабочего места, м
    r: float        # Радиус катушки индуктивности, м


@dataclass(frozen=True)
class MaterialProperties:
    """Электрофизические параметры материалов экрана и стержня по Табл. 14.2."""
    screen_material: str  # Название металла экрана (например, 'Медь', 'Сталь')
    mu: float             # Относительная магнитная проницаемость материала экрана
    gamma: float          # Удельная электрическая проводимость экрана, См/м
    rod_material: str     # Название диэлектрика стержня (например, 'Эбонит', 'Гетинакс')
    epsilon: float        # Относительная диэлектрическая проницаемость стержня


@dataclass(frozen=True)
class ShieldingCalculationResults:
    """Комплексные результаты электродинамического и защитного расчета."""
    # Геометрические соотношения источника
    ratio_R_r: float
    beta_m: float
    
    # Магнитное поле
    H: float                 # Напряженность магнитного поля на рабочем месте без экрана, А/м
    
    # Характеристики волны и волновой зоны
    wavelength: float        # Длина электромагнитной волны lambda, м
    condition_1_limit: float # Пороговое значение lambda / (2*pi), м
    condition_2_limit: float # Пороговое значение r^2 / lambda, м
    is_wave_zone: bool       # Флаг выполнения условий дальней (волновой) зоны
    
    # Энергетические параметры поля
    ppe: float               # Фактическая плотность потока энергии (ППЭ) без экрана, Вт/м^2
    ppe_dop: float           # Предельно допустимая ППЭ (ППЭ_доп), Вт/м^2
    is_hazard: bool          # Превышает ли фактическая ППЭ допустимую
    hazard_ratio: float      # Кратность превышения нормы
    
    # Требуемое ослабление
    L: float                 # Требуемый коэффициент ослабления поля (безразмерный)
    L_db: float              # Ослабление поля в децибелах (10*lg(L)), дБ
    
    # Параметры металлического экрана
    omega: float             # Круговая частота, рад/с
    mu_a: float              # Абсолютная магнитная проницаемость экрана, Гн/м
    skin_depth: float        # Глубина проникновения (скин-слой) Delta, м
    delta_min: float         # Расчетная минимальная толщина экрана delta, м
    delta_min_mm: float      # Толщина экрана delta, мм
    delta_min_um: float      # Толщина экрана delta, мкм
    delta_constructive_mm: float # Рекомендуемая конструктивная толщина экрана, мм
    
    # Параметры трубки-волновода
    alpha: float             # Коэффициент затухания энергии в трубке на 1 м длины, дБ/м
    l_tube_min: float        # Минимальная расчетная длина трубки l, м
    l_tube_min_mm: float     # Длина трубки l, мм
    l_tube_constructive_mm: float # Рекомендуемая конструктивная длина трубки, мм


class MicrowaveShieldingCalculator:
    """Калькулятор защитных параметров при работе с СВЧ-передатчиком."""

    @staticmethod
    def calculate(gen: GeneratorParameters, mat: MaterialProperties) -> ShieldingCalculationResults:
        """
        Выполняет полный цикл вычислений согласно методике лабораторной работы № 14р.
        """
        # 1. Соотношение расстояния и радиуса катушки
        ratio_R_r = gen.R / gen.r
        # В методичке: при R/r > 10, beta_m = 1
        beta_m = 1.0 if ratio_R_r >= 10.0 else (gen.R / math.sqrt(gen.R**2 + gen.r**2))
        
        # 2. Напряженность магнитного поля H без экрана
        # H = (W * I * r^2) / (4 * R^3) * beta_m
        H = (gen.W * gen.I * (gen.r ** 2)) / (4.0 * (gen.R ** 3)) * beta_m
        
        # 3. Оценка волновой зоны
        wavelength = C_LIGHT / gen.f
        cond1_limit = wavelength / (2.0 * math.pi)
        cond2_limit = (gen.r ** 2) / wavelength
        # Условия R >> lambda/(2*pi) и R >> r^2/lambda считаем выполненными при превосходстве в 5+ раз
        is_wave_zone = (gen.R >= 5.0 * cond1_limit) and (gen.R >= 5.0 * cond2_limit)
        
        # 4. Плотность потока энергии излучения (ППЭ)
        # sigma = 377 * H^2 / 2
        ppe = WAVE_IMPEDANCE_0 * (H ** 2) / 2.0
        
        # 5. Предельно допустимая величина ППЭ
        # sigma_доп = N / T
        ppe_dop = N_ENERGY_DOSE_LIMIT / gen.T
        
        is_hazard = ppe > ppe_dop
        hazard_ratio = ppe / ppe_dop
        
        # 6. Требуемое ослабление электромагнитного поля
        # L = sigma / sigma_доп
        L = max(1.0, hazard_ratio)
        L_db = 10.0 * math.log10(L)
        
        # 7. Расчет толщины металлического экрана
        omega = 2.0 * math.pi * gen.f
        mu_a = MU_0 * mat.mu
        
        # Подкоренное выражение: omega * mu_a * gamma / 2
        radicand = (omega * mu_a * mat.gamma) / 2.0
        # Скин-слой: Delta = sqrt(2 / (omega * mu_a * gamma)) = 1 / sqrt(radicand)
        skin_depth = 1.0 / math.sqrt(radicand)
        
        # delta = ln(L) / (2 * sqrt(omega * mu_a * gamma / 2))
        denom = 2.0 * math.sqrt(radicand)
        delta_min = math.log(L) / denom
        delta_min_mm = delta_min * 1000.0
        delta_min_um = delta_min * 1.0e6
        
        # Конструктивная толщина экрана (по условиям жесткости и прочности)
        delta_constructive_mm = max(0.5, round(delta_min_mm * 10.0) / 10.0 if delta_min_mm > 0.5 else 0.5)
        
        # 8. Ослабление энергии в трубке-волноводе на 1 м длины
        # alpha = 32 / (D * sqrt(epsilon)), дБ/м
        alpha = 32.0 / (gen.D * math.sqrt(mat.epsilon))
        
        # 9. Требуемая длина трубки
        # l = (10 * lg(L)) / alpha, м
        l_tube_min = L_db / alpha
        l_tube_min_mm = l_tube_min * 1000.0
        
        # Конструктивная длина трубки (с учетом монтажа и надежности, не менее диаметра D)
        l_tube_constructive_mm = max(gen.D * 1000.0, 30.0, math.ceil(l_tube_min_mm * 1.5 / 5.0) * 5.0)
        
        return ShieldingCalculationResults(
            ratio_R_r=ratio_R_r,
            beta_m=beta_m,
            H=H,
            wavelength=wavelength,
            condition_1_limit=cond1_limit,
            condition_2_limit=cond2_limit,
            is_wave_zone=is_wave_zone,
            ppe=ppe,
            ppe_dop=ppe_dop,
            is_hazard=is_hazard,
            hazard_ratio=hazard_ratio,
            L=L,
            L_db=L_db,
            omega=omega,
            mu_a=mu_a,
            skin_depth=skin_depth,
            delta_min=delta_min,
            delta_min_mm=delta_min_mm,
            delta_min_um=delta_min_um,
            delta_constructive_mm=delta_constructive_mm,
            alpha=alpha,
            l_tube_min=l_tube_min,
            l_tube_min_mm=l_tube_min_mm,
            l_tube_constructive_mm=l_tube_constructive_mm
        )


def get_variant_6_parameters() -> Tuple[GeneratorParameters, MaterialProperties]:
    """Возвращает параметры Варианта 6 (Табл. 14.1 вар 6, Табл. 14.2 вар 6)."""
    gen = GeneratorParameters(
        W=12,
        I=80.0,
        f=4.0e8,    # 4*10^8 Гц = 400 МГц
        T=0.2,      # 0.2 ч = 12 мин
        D=0.04,     # 4*10^-2 м = 4 см
        R=2.0,      # 2 м
        r=0.1       # 10^-1 м = 10 см
    )
    mat = MaterialProperties(
        screen_material="Медь",
        mu=1.0,
        gamma=5.7e7,  # 5.7*10^7 См/м
        rod_material="Эбонит",
        epsilon=3.0
    )
    return gen, mat


if __name__ == "__main__":
    gen_v6, mat_v6 = get_variant_6_parameters()
    res = MicrowaveShieldingCalculator.calculate(gen_v6, mat_v6)
    print("=== Результаты расчета для Варианта 6 ===")
    print(f"H = {res.H:.4f} А/м")
    print(f"ППЭ = {res.ppe:.4f} Вт/м^2, ППЭ_доп = {res.ppe_dop:.4f} Вт/м^2")
    print(f"Ослабление L = {res.L:.4f} ({res.L_db:.2f} дБ)")
    print(f"Толщина экрана delta = {res.delta_min_um:.3f} мкм ({res.delta_min_mm:.6f} мм)")
    print(f"Затухание в трубке alpha = {res.alpha:.2f} дБ/м")
    print(f"Длина трубки l = {res.l_tube_min_mm:.2f} мм")
