from src.utils import detect_ovulation, preprocess_data
from src.reports import cycle_report
from src.plots import  plot_cycle
import yaml


def main():

    # -----------------------------------
    # Load parameters
    # -----------------------------------
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    len_ciclo = config['len_ciclo']
    filename = config['filename']
    min_good_slot= config['min_good_slot']
    max_good_slot= config['max_good_slot']
    plot_good_slot= config['plot_good_slot']
    acne_markers= config['acne_markers']
    plot_deseo= config['plot_deseo']
    descartables = config['descartables']
    probable_ovulaciones= config['probable_ovulaciones']
    path_results= config['path_results']
    path_raw = config['path_raw']

    # ==========================================================
    # Load data and formating
    # ==========================================================

    df, bloques_menstruacion = preprocess_data(path_raw, filename, descartables, min_good_slot,max_good_slot)

    # ==========================
    # Detect ovulation from temperature
    # ==========================
    ovulaciones_final, ovulaciones_detectadas = detect_ovulation(df, bloques_menstruacion, plot_good_slot, probable_ovulaciones)

    # ==========================
    # Collect cycle info with ovulation method. Results are at reporte_ciclos.csv
    # ==========================
    cycle_report(df, bloques_menstruacion, ovulaciones_final, path_results, len_ciclo, ovulaciones_detectadas)

    # ==========================
    # Plot
    # ==========================
    plot_cycle(df, path_results, plot_deseo, plot_good_slot, len_ciclo, acne_markers, bloques_menstruacion,
               ovulaciones_final, ovulaciones_detectadas)


if __name__ == '__main__':
    main()