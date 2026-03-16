import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from src.utils import color_por_hora, agrupar_fechas_consecutivas, detectar_ovulacion_3_sobre_6, estimar_proxima_menstruacion, temperaturas_fases
from pathlib import Path

def plot_cycle(df, path_results, plot_deseo, plot_good_slot, len_ciclo, acne_markers, bloques_menstruacion, ovulaciones_final, ovulaciones_detectadas):
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # ==========================
    # Grouped shading
    # ==========================

    if plot_deseo:
        # --- High desire (green block)
        deseo_fechas = df[df["deseo_sexual"] == 1]["fecha"].dt.normalize().unique()
        for fecha in deseo_fechas:
            ax1.axvspan(fecha - pd.Timedelta(hours=12),
                        fecha + pd.Timedelta(hours=12),
                        color="green", alpha=0.15)
        if len(deseo_fechas) > 0:
            ax1.axvspan(deseo_fechas[0] - pd.Timedelta(hours=12),
                        deseo_fechas[0] + pd.Timedelta(hours=12),
                        color="green", alpha=0.15, label="deseo")

        # --- Flujo
    flujo_fechas = df[df["flujo"] == 'claraHuevo']["fecha"].dt.normalize().unique()
    for fecha in flujo_fechas:
        ax1.axvspan(fecha - pd.Timedelta(hours=12),
                    fecha + pd.Timedelta(hours=12),
                    color="orange", alpha=0.15)
    if len(flujo_fechas) > 0:
        ax1.axvspan(flujo_fechas[0] - pd.Timedelta(hours=12),
                    flujo_fechas[0] + pd.Timedelta(hours=12),
                    color="orange", alpha=0.15, label="flujo Clara de Huevo")

    # --- Estimated ovulation for each menstruation block
    for i, (inicio, fin) in enumerate(bloques_menstruacion):
        fecha_inicio_ciclo = inicio
        fecha_ovulacion_est = fecha_inicio_ciclo + pd.Timedelta(days=len_ciclo - 14 - 1)
        ax1.axvspan(fecha_ovulacion_est - pd.Timedelta(days=0.5),
                    fecha_ovulacion_est + pd.Timedelta(days=0.5),
                    color="blue", alpha=0.2,
                    label=f'Ovulación estimada dia {len_ciclo}-14={len_ciclo-14}' if i == 0 else None)

    # --- Menstruation (red block)
    menstruacion_fechas = df[df["menstruacion"] == 1]["fecha"].dt.normalize().unique()
    for fecha in menstruacion_fechas:
        ax1.axvspan(fecha - pd.Timedelta(hours=12),
                    fecha + pd.Timedelta(hours=12),
                    color="red", alpha=0.15)

    # ==========================
    # Plot lines only for consecutive points
    # ==========================
    df_plot = df[df.color_hora == 'black'] if plot_good_slot else df

    fechas = df_plot["fecha_norm"].tolist()

    grupos = agrupar_fechas_consecutivas(fechas)

    for inicio, fin in grupos:
        segment = df_plot[(df_plot["fecha_norm"] >= inicio) & (df_plot["fecha_norm"] <= fin)]
        ax1.plot(segment["fecha"], segment["temperaturaC"], color="gray", linewidth=1.5)

    # ==========================
    # Scatter points and day labels
    # ==========================
    for _, row in df_plot.iterrows():
        ax1.scatter(row["fecha"], row["temperaturaC"], color=row["color_hora"], zorder=3)
        if not np.isnan(row["dias_desde_menstruacion"]):
            ax1.text(row["fecha"], row["temperaturaC"] + 0.03,
                     int(row["dias_desde_menstruacion"]),
                     fontsize=8, ha='center', va='bottom', color='black')

    # Acne markers
    if acne_markers:
        acne_df = df_plot[df_plot["acne"] == 1]
        ax1.scatter(acne_df["fecha"], acne_df["temperaturaC"], marker="*", color="black", s=100, label="grano")

    # ==========================
    # Ovulation spans (detected vs probable) with proper legend
    # ==========================
    added_labels = {"detectada": False, "probable": False}

    for i, fecha_ovu in enumerate(ovulaciones_final):
        if fecha_ovu is not None:
            # Check if detected or probable
            if i < len(ovulaciones_detectadas) and ovulaciones_detectadas[i] == fecha_ovu:
                color = "purple"
                label = "Ovulación detectada (3 sobre 6)" if not added_labels["detectada"] else None
                added_labels["detectada"] = True
            else:
                color = "orange"
                label = "Ovulación probable" if not added_labels["probable"] else None
                added_labels["probable"] = True

            ax1.axvspan(fecha_ovu - pd.Timedelta(days=0.3),
                        fecha_ovu + pd.Timedelta(days=0.3),
                        color=color, alpha=0.4,
                        label=label)

    # ==========================
    # Phase average/median temperature annotations
    # ==========================
    for i, (inicio, fin) in enumerate(bloques_menstruacion):
        ovulacion = ovulaciones_final[i]
        if ovulacion is None:
            continue
        if i < len(bloques_menstruacion) - 1:
            prox_menstruacion = bloques_menstruacion[i + 1][0]
        else:
            prox_menstruacion = inicio + pd.Timedelta(days=len_ciclo)

        avg_fol, med_fol, avg_lut, med_lut = temperaturas_fases(df, inicio, ovulacion, prox_menstruacion)

        # Follicular annotation
        fol_mask = (df_plot['fecha'] >= inicio) & (df_plot['fecha'] < ovulacion)
        if not df_plot.loc[fol_mask, 'temperaturaC'].empty:
            x_fol = df_plot.loc[fol_mask, 'fecha'].iloc[len(df_plot.loc[fol_mask]) // 2]
            y_fol = df_plot.loc[fol_mask, 'temperaturaC'].max() + 0.1
            ax1.text(x_fol, y_fol, f"Fol: med {med_fol:.2f}",
                     fontsize=8, color='blue', ha='center')

        # Luteal annotation
        lut_mask = (df_plot['fecha'] >= ovulacion) & (df_plot['fecha'] < prox_menstruacion)
        if not df_plot.loc[lut_mask, 'temperaturaC'].empty:
            x_lut = df_plot.loc[lut_mask, 'fecha'].iloc[len(df_plot.loc[lut_mask]) // 2]
            y_lut = df_plot.loc[lut_mask, 'temperaturaC'].max() + 0.1
            ax1.text(x_lut, y_lut, f"Lut: med {med_lut:.2f}",
                     fontsize=8, color='purple', ha='center')

    # ==========================
    # Formatting
    # ==========================
    mens_max = estimar_proxima_menstruacion(bloques_menstruacion, len_ciclo=33).date()
    mens_min = estimar_proxima_menstruacion(bloques_menstruacion, len_ciclo=30).date()
    ax1.set_title(
        f"Temperatura basal (°C) en función del día. Próxima menstruación probable entre {mens_min} y {mens_max}")
    ax1.set_xlabel("Fecha")
    ax1.set_ylabel("°C")
    ax1.grid(True, linestyle="--", alpha=0.5)

    ymin = np.floor(df["temperaturaC"].min() * 10) / 10 - 0.1
    ymax = np.ceil(df["temperaturaC"].max() * 10) / 10 + 0.1
    ax1.set_ylim(ymin, ymax)
    ax1.set_yticks(np.arange(ymin, ymax + 0.1, 0.1))
    ax1.grid(which="major", axis="y", linestyle="--", alpha=0.6)
    ax1.grid(which="major", axis="x", linestyle="--", alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()
    path_plot = Path(path_results) / "temperature.png"
    plt.savefig(path_plot)
    print(f'Temperature plot saved at {path_plot}')
    plt.show()

    return None