# test_concurrency.py
from config_loader import display_seeding_command, write_csv, run_parallel_test, config, OUT_DIR
import os

# --- Paramètres de l'expérience ---
P_FIXED = 50
F_FIXED = 20
U_TOTAL = 1000

def run_concurrency_test():
    """Expérience 1 : Variation de la charge (conc.csv)."""
    print("\n\n#################################################################")
    print("## EXPÉRIENCE 1 : PASSAGE À L'ÉCHELLE SUR LA CHARGE (conc.csv) ##")
    print("#################################################################")

    # Paramètres Fixes : U=1000, P=50, F=20
    display_seeding_command(users=U_TOTAL, posts=P_FIXED, followees=F_FIXED)
    
    concurrency_levels = [1, 10, 20, 50, 100, 1000]
    results = []

    for C in concurrency_levels:
        for run in range(1, 4):
            avg_time, failed = run_parallel_test(concurrency=C, limit_timeline=config['LIMIT_TIMELINE'], param_name=C, run_num=run)
            if avg_time is not None:
                results.append([C, avg_time, run, failed])

    write_csv('conc.csv', results)


if __name__ == "__main__":
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        print(f"Dossier de sortie '{OUT_DIR}' créé.")
        
    print("Démarrage du script de Benchmark (Concurrence)...")
    run_concurrency_test()
    print("\n*** TEST DE CONCURRENCE TERMINÉ ***")