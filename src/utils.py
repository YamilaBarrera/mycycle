import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import time
from pathlib import Path


def color_por_hora(h, min_good_slot, max_good_slot) -> str:
    """

    :param h:
    :param min_good_slot:
    :param max_good_slot:
    :return: If the hour is in the good slot, returns black color. If less, blue. If more, red.
    """
    if not pd.isna(h):
        if h < time(min_good_slot):
            ret = "blue"
        elif h >= time(min_good_slot) and h <= time(max_good_slot):
            ret = "black"
        else:
            ret = 'red'
    else:
        ret = 'black'
    return ret

def agrupar_fechas_consecutivas(fechas):
    fechas = sorted(set(fechas))
    grupos = []
    inicio = fechas[0]
    fin = fechas[0]
    for fecha in fechas[1:]:
        if (fecha - fin).days == 1:
            fin = fecha
        else:
            grupos.append((inicio, fin))
            inicio = fecha
            fin = fecha
    grupos.append((inicio, fin))
    return grupos


def calcular_fases(inicio, ovulacion, prox_menstruacion):
    """
    Calculate follicular and luteal phase lengths in days.

    Parameters:
    - inicio: datetime of start of menstruation (first day)
    - ovulacion: datetime of ovulation
    - prox_menstruacion: datetime of next menstruation start (or estimated)

    Returns:
    - folicular: length of follicular phase in days
    - lutea: length of luteal phase in days
    """
    # Follicular phase: from menstruation start to day before ovulation
    folicular = (ovulacion - inicio).days

    # Luteal phase: from ovulation to day before next menstruation
    lutea = (prox_menstruacion - ovulacion).days

    return folicular, lutea


def detectar_ovulacion_3_sobre_6(df_cycle, min_rise=0.05):

    df_clean = (
        df_cycle[["fecha", "temperaturaC"]]
        .dropna()
        .sort_values("fecha")
        .reset_index(drop=True)
    )

    for i in range(len(df_clean)):

        fecha_actual = df_clean.loc[i, "fecha"]

        prev_window = df_clean[
            (df_clean["fecha"] < fecha_actual) &
            (df_clean["fecha"] >= fecha_actual - pd.Timedelta(days=6))
            ]

        if len(prev_window) < 3:  # not enough data
            continue

        threshold = prev_window["temperaturaC"].max() + min_rise

        next3 = df_clean.loc[i:i + 2, "temperaturaC"]

        if len(next3) < 3:
            continue

        if (next3 > threshold).all():
            return df_clean.loc[i - 1, "fecha"]

    return None


def estimar_proxima_menstruacion(bloques_menstruacion, len_ciclo):
    """
    Returns:
        - fecha_ultima_menstruacion (first day of last block)
        - fecha_proxima_menstruacion_estimada
    """

    if not bloques_menstruacion:
        return None, None

    # Last block
    ultimo_inicio, _ = bloques_menstruacion[-1]

    fecha_proxima = ultimo_inicio + pd.Timedelta(days=len_ciclo)

    return fecha_proxima


def temperaturas_fases(df, fecha_inicio_ciclo, fecha_ovulacion, fecha_prox_menstruacion=None):
    """
    Computes average and median temperature for follicular and luteal phases.

    Args:
        df: DataFrame with columns 'fecha' and 'temperaturaC'
        fecha_inicio_ciclo: first day of menstruation (pd.Timestamp)
        fecha_ovulacion: ovulation day (pd.Timestamp)
        fecha_prox_menstruacion: next menstruation start (pd.Timestamp), optional

    Returns:
        tuple: (avg_folicular, median_folicular, avg_luteal, median_luteal)
    """
    # Follicular phase
    folicular_mask = (df['fecha'] >= fecha_inicio_ciclo) & (df['fecha'] < fecha_ovulacion)
    temps_folicular = df.loc[folicular_mask, 'temperaturaC']
    avg_folicular = temps_folicular.mean() if not temps_folicular.empty else np.nan
    median_folicular = temps_folicular.median() if not temps_folicular.empty else np.nan

    # Luteal phase
    if fecha_prox_menstruacion is not None:
        luteal_mask = (df['fecha'] >= fecha_ovulacion) & (df['fecha'] < fecha_prox_menstruacion)
    else:
        luteal_mask = df['fecha'] >= fecha_ovulacion
    temps_luteal = df.loc[luteal_mask, 'temperaturaC']
    avg_luteal = temps_luteal.mean() if not temps_luteal.empty else np.nan
    median_luteal = temps_luteal.median() if not temps_luteal.empty else np.nan

    return avg_folicular, median_folicular, avg_luteal, median_luteal

def detect_ovulation(df, bloques_menstruacion, plot_good_slot, probable_ovulaciones):
    ovulaciones_detectadas = []

    for i, (inicio, fin) in enumerate(bloques_menstruacion):

        # Define end of cycle:
        # next menstruation start OR end of dataset
        if i < len(bloques_menstruacion) - 1:
            siguiente_inicio = bloques_menstruacion[i + 1][0]
            df_cycle = df[
                (df["fecha"] >= inicio) &
                (df["fecha"] < siguiente_inicio)
                ]
        else:
            df_cycle = df[df["fecha"] >= inicio]

        # Keep only good slot if needed
        if plot_good_slot:
            df_cycle = df_cycle[df_cycle["color_hora"] == "black"]

        ovulacion = detectar_ovulacion_3_sobre_6(df_cycle)

        if ovulacion is not None:
            ovulaciones_detectadas.append(ovulacion)

    # Agrego ovulaciones probables
    # Suppose these are your probable ovulations per cycle (from another source
    # Convert detected ovulations to dict keyed by cycle index
    ovulaciones_dict = {i: ov for i, ov in enumerate(ovulaciones_detectadas)}

    # Merge probable ovulations where detection is missing
    for cycle_index, fecha in probable_ovulaciones:
        if cycle_index not in ovulaciones_dict or ovulaciones_dict[cycle_index] is None:
            ovulaciones_dict[cycle_index] = fecha

    # Convert back to list aligned with bloques_menstruacion
    ovulaciones_final = [ovulaciones_dict.get(i, None) for i in range(len(bloques_menstruacion))]

    return ovulaciones_final, ovulaciones_detectadas

def preprocess_data(path_raw, filename, descartables, min_good_slot,max_good_slot):

    # Aux function
    def dias_desde_inicio_ultimo_bloque(fecha):
        if not bloques_menstruacion:
            return np.nan

        # Find blocks that started before or on this date
        bloques_anteriores = [
            (inicio, fin)
            for (inicio, fin) in bloques_menstruacion
            if inicio <= fecha
        ]

        if not bloques_anteriores:
            return np.nan

        # Take the most recent block
        ultimo_inicio, _ = bloques_anteriores[-1]

        return (fecha - ultimo_inicio).days + 1

    # read data
    df = pd.read_csv(Path(path_raw)/filename, parse_dates=["fecha"])

    if descartables:
        df = df[df.descartar != 1]

    if 'temperaturaF' in df.columns:
        df["temperaturaF"] = pd.to_numeric(df["temperaturaF"], errors="coerce")
        df["temperaturaC"] = (df["temperaturaF"] - 32) * 5 / 9

    df['hora'] = pd.to_datetime(df['hora'], format='%I:%M:%S %p').dt.time

    df["fecha"] = pd.to_datetime(
        df["fecha"],
        format="%d/%m/%Y",
        errors="coerce"

    )

    # Normalize dates (remove time component)
    df["fecha_norm"] = df["fecha"].dt.normalize()

    # Get menstruation blocks (using normalized dates)
    menstruacion_fechas = df[df["menstruacion"] == 1]["fecha_norm"].tolist()

    if menstruacion_fechas:
        bloques_menstruacion = agrupar_fechas_consecutivas(menstruacion_fechas)
    else:
        bloques_menstruacion = []

    df["dias_desde_menstruacion"] = df["fecha_norm"].apply(dias_desde_inicio_ultimo_bloque)

    df["color_hora"] = df["hora"].apply(color_por_hora, args=(min_good_slot, max_good_slot))

    return df, bloques_menstruacion