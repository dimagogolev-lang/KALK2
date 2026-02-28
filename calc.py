# -*- coding: utf-8 -*-
"""
Расчёт коммунальных платежей по логике Excel (показания счётчиков Одинцово).
Вход: предыдущие и текущие показания ХВС, ГВС, электричество день, электричество ночь.
"""


def calculate(
    xvs_prev: float,
    xvs_curr: float,
    gvs_prev: float,
    gvs_curr: float,
    el_day_prev: float,
    el_day_curr: float,
    el_night_prev: float,
    el_night_curr: float,
    tariff_sewage: float = 46.73,
    tariff_xvs: float = 43.24,
    tariff_gvs: float = 43.24,
    tariff_heating_per_gcal: float = 2891.74,
    norm_gcal_per_m3: float = 0.06,
    tariff_el_day: float = 6.79,
    tariff_el_night: float = 2.81,
):
    """
    Возвращает словарь с расчётами как в Excel.
    """
    # Расходы (м³ или кВт·ч)
    consumption_xvs = xvs_curr - xvs_prev
    consumption_gvs = gvs_curr - gvs_prev
    consumption_sewage = (xvs_curr + gvs_curr) - (xvs_prev + gvs_prev)  # D = E+G
    consumption_el_day = el_day_curr - el_day_prev
    consumption_el_night = el_night_curr - el_night_prev

    # Предварительный расчёт (руб) — как в Excel
    sum_sewage = consumption_sewage * tariff_sewage
    sum_xvs = consumption_xvs * tariff_xvs
    sum_heating = consumption_gvs * norm_gcal_per_m3 * tariff_heating_per_gcal
    sum_gvs = consumption_gvs * tariff_gvs

    # Итоговая сумма за воду
    sum_water = sum_sewage + sum_xvs + sum_heating + sum_gvs

    # Электричество
    sum_el_day = consumption_el_day * tariff_el_day
    sum_el_night = consumption_el_night * tariff_el_night
    sum_electricity = sum_el_day + sum_el_night

    # ИТОГО
    total = sum_water + sum_electricity

    return {
        "consumption": {
            "xvs": consumption_xvs,
            "gvs": consumption_gvs,
            "sewage": consumption_sewage,
            "el_day": consumption_el_day,
            "el_night": consumption_el_night,
        },
        "sum_sewage": round(sum_sewage, 2),
        "sum_xvs": round(sum_xvs, 2),
        "sum_heating": round(sum_heating, 2),
        "sum_gvs": round(sum_gvs, 2),
        "sum_water": round(sum_water, 2),
        "sum_el_day": round(sum_el_day, 2),
        "sum_el_night": round(sum_el_night, 2),
        "sum_electricity": round(sum_electricity, 2),
        "total": round(total, 2),
    }
