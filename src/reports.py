import pandas as pd
from pathlib import Path
from src.utils import calcular_fases, temperaturas_fases

def cycle_report(df, bloques_menstruacion,ovulaciones_final, path_results,len_ciclo,ovulaciones_detectadas):
    cycles_data = []

    for i, (inicio, fin) in enumerate(bloques_menstruacion):
        ovulacion = ovulaciones_final[i]

        # Skip cycle if no ovulation info at all
        if ovulacion is None:
            print(f"Ciclo {i + 1}: sin ovulación detectada o probable")
            continue

        # Next menstruation start (or estimated if last cycle)
        if i < len(bloques_menstruacion) - 1:
            prox_menstruacion = bloques_menstruacion[i + 1][0]
        else:
            prox_menstruacion = inicio + pd.Timedelta(days=len_ciclo)

        # Determine detection method
        if i < len(ovulaciones_detectadas) and ovulaciones_detectadas[i] == ovulacion:
            metodo = "3 sobre 6"
        else:
            metodo = "Probable"

        # Phase lengths
        folicular, lutea = calcular_fases(inicio, ovulacion, prox_menstruacion)

        # Average and median temperatures
        avg_folicular, median_folicular, avg_luteal, median_luteal = temperaturas_fases(
            df, inicio, ovulacion, prox_menstruacion
        )

        # Print info
        print(
            f"Ciclo {i + 1}: Follicular = {folicular} días, Luteal = {lutea} días, Duracion: {folicular + lutea} dias")
        print(f"             Ovulacion = {ovulacion.date()} (Metodo: {metodo})")
        print(f"             Avg Follicular Temp = {avg_folicular:.2f}°C, Median = {median_folicular:.2f}°C")
        print(f"             Avg Luteal Temp = {avg_luteal:.2f}°C, Median = {median_luteal:.2f}°C")
        print(
            f"             Diff avg = {avg_luteal - avg_folicular:.2f}°C, Diff Median = {median_luteal - median_folicular:.2f}°C")

        # Save to list
        cycles_data.append({
            "Ciclo": i + 1,
            "Inicio_menstruacion": inicio.date(),
            "Fin_menstruacion": fin.date(),
            "Ovulacion": ovulacion.date(),
            "Metodo_ovulacion": metodo,
            "Duracion_folicular": folicular,
            "Duracion_lutea": lutea,
            "Duracion_total": folicular + lutea,
            "Avg_folicular_temp": round(avg_folicular,2),
            "Median_folicular_temp": round(median_folicular,2),
            "Avg_luteal_temp": round(avg_luteal,2),
            "Median_luteal_temp": round(median_luteal,2),
            "Diff_avg_temp": round(avg_luteal - avg_folicular,2),
            "Diff_median_temp": round(median_luteal - median_folicular,2)
        })

    # Convert list to DataFrame and save CSV
    df_cycles = pd.DataFrame(cycles_data)
    path_report = Path(path_results) / "reporte_ciclos.csv"
    df_cycles.to_csv(path_report, index=False)
    print(f" Cycle report saved at {path_report}")

    return None
