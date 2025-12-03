# test_fanout.py
from config_loader import display_seeding_command, write_csv, run_parallel_test, config, OUT_DIR
import os

# --- Paramètres de l'expérience ---
C_FIXED = 50
U_TOTAL = 1000
P_FIXED = 100

def run_fanout_test():
    """Expérience 3 : Variation du fanout (fanout.csv)."""
    print("\n\n####################################################################")
    print("## EXPÉRIENCE 3 : VARIATION DU FANOUT (fanout.csv)                ##")
    print("####################################################################")

    # Paramètres Fixes : C=50, U=1000, P=100
    C_TEST = 50
    fanout_levels = [10, 50, 100]
    results = []

    for F in fanout_levels:
        # Affichage de la commande de seeding pour le niveau F actuel
        display_seeding_command(users=U_TOTAL, posts=P_FIXED, followees=F)

        for run in range(1, 4):
            avg_time, failed = run_parallel_test(concurrency=C_TEST, limit_timeline=config['LIMIT_TIMELINE'], param_name=F, run_num=run)
            if avg_time is not None:
                results.append([F, avg_time, run, failed])

    write_csv('fanout.csv', results)

if __name__ == "__main__":
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        print(f"Dossier de sortie '{OUT_DIR}' créé.")
        
    print("Démarrage du script de Benchmark (Fanout)...")
    run_fanout_test()
    print("\n*** TEST DE FANOUT TERMINÉ ***")