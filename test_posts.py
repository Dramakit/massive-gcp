# test_posts.py
from config_loader import display_seeding_command, write_csv, run_parallel_test, config, OUT_DIR
import os

# --- Paramètres de l'expérience ---
C_FIXED = 50
U_TOTAL = 1000
F_FIXED = 20

def run_posts_test():
    """Expérience 2 : Variation des posts (post.csv)."""
    print("\n\n####################################################################")
    print("## EXPÉRIENCE 2 : VARIATION DU NOMBRE DE POSTS (post.csv)         ##")
    print("####################################################################")

    # Paramètres Fixes : C=50, U=1000, F=20
    C_TEST = 50
    post_counts = [10, 100, 1000]
    results = []

    for P in post_counts:
        # Affichage de la commande de seeding pour le niveau P actuel
        display_seeding_command(users=U_TOTAL, posts=P, followees=F_FIXED)
        
        for run in range(1, 4):
            avg_time, failed = run_parallel_test(concurrency=C_TEST, limit_timeline=config['LIMIT_TIMELINE'], param_name=P, run_num=run)
            if avg_time is not None:
                results.append([P, avg_time, run, failed])

    write_csv('post.csv', results)

if __name__ == "__main__":
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        print(f"Dossier de sortie '{OUT_DIR}' créé.")
        
    print("Démarrage du script de Benchmark (Posts)...")
    run_posts_test()
    print("\n*** TEST DE POSTS TERMINÉ ***")