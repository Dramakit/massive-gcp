import subprocess
import re
import csv
import json
import pandas as pd
import matplotlib.pyplot as plt
import os

"""
TO DO : séparer le code ci dessous en 3 scripts (3 fichiers) différents pour chaque type de test, 
faut executer les commandes de peuplement de la bd à la main avant d'appeler chaque test
puis faire un script qui construit les graphes après l'exec de ts les test et la créa des csv.
"""


try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("Erreur: Le fichier config.json est manquant")
    exit(1)

APP_URL = config['APP_URL']
SEED_TOKEN = config['SEED_TOKEN']
USER_TO_TEST = config['USER_TO_TEST']
TOTAL_REQUESTS = config['TOTAL_REQUESTS']
LIMIT_TIMELINE = config['LIMIT_TIMELINE']
AB_PATH = config['AB_PATH']
OUT_DIR = "out"
AB_EXECUTABLE = os.getenv('AB_BIN', config.get('AB_PATH', '/usr/bin/ab'))


def run_ab(concurrency, run_num):
    """Exécute Apache Bench et extrait le temps moyen par requête et le taux d'échec."""
    url = f"{APP_URL}/api/timeline?user={USER_TO_TEST}&limit={LIMIT_TIMELINE}"

    # *** UTILISER LA LISTE D'ARGUMENTS SANS SHELL ***
    # Ceci est la méthode la plus directe pour lancer un binaire
    full_ab_command = f"{AB_EXECUTABLE} -n {TOTAL_REQUESTS} -c {concurrency} -r -k {url}"

    cmd = ["/bin/bash", "-c", full_ab_command]

    print(f"  -> Lancement de ab (C={concurrency}, Run={run_num})...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout
        error_output = result.stderr

        print("\n--- SORTIE AB (stdout) ---")
        print(output)
        print("--------------------------")
        if error_output:
            print("\n--- ERREUR AB (stderr) ---")
            print(error_output)
            print("--------------------------")
        # ----------------------------------------------------

        # Extraction du temps moyen (Time per request (mean): X.XX [ms])
        time_match = re.search(r'Time per request \(mean\):\s+([\d.]+)\s+\[ms\]', output)
        avg_time = float(time_match.group(1)) if time_match else None

        # Extraction des requêtes échouées
        failed_match = re.search(r'Failed requests:\s+(\d+)', output)
        failed_count = int(failed_match.group(1)) if failed_match else 0

        failed = 1 if failed_count > 0 else 0

        if avg_time is None:
            raise ValueError("Impossible d'extraire le temps moyen.")

        return avg_time, failed

    except subprocess.CalledProcessError as e:
        print(f"Erreur d'exécution AB pour C={concurrency}: {e.stderr}")
        return None, 1
    except Exception as e:
        print(f"Erreur lors de l'analyse AB : {e}")
        return None, 1


def run_seeding(users, posts, followees):
    """Lance l'endpoint de seeding."""
    url = f"{APP_URL}/admin/seed?users={users}&posts={posts}&follows_min={followees}&follows_max={followees}&prefix=load"

    cmd = ['curl', '-X', 'POST', '-H', f"X-Seed-Token: {SEED_TOKEN}", url]

    print(f"\n--- Lancement du Seeding : U={users}, P={posts}, F={followees} ---")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Seeding terminé avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur de Seeding : {e.stderr}")
        print("Vérifiez le SEED_TOKEN et l'URL de l'application.")
        exit(1)


def write_csv(filename, results):
    """Écrit les résultats dans un fichier CSV."""
    filepath = os.path.join(OUT_DIR, filename)
    print(f"\nÉcriture des résultats dans {filepath}...")
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['PARAM', 'AVG_TIME', 'RUN', 'FAILED'])
        writer.writerows(results)
    print("Fichier CSV généré.")



def run_concurrency_test():
    """Expérience 1 : Variation de la charge (conc.csv)."""
    print("\n\n#################################################################")
    print("## EXPÉRIENCE 1 : PASSAGE À L'ÉCHELLE SUR LA CHARGE (conc.csv) ##")
    print("#################################################################")

    # Paramètres Fixes : U=1000, P=50, F=20
    run_seeding(users=1000, posts=50, followees=20)

    concurrency_levels = [1, 10, 20, 50, 100, 1000]
    results = []

    for C in concurrency_levels:
        for run in range(1, 4):
            avg_time, failed = run_ab(concurrency=C, run_num=run)
            if avg_time is not None:
                results.append([C, avg_time, run, failed])

    write_csv('conc.csv', results)


def run_posts_test():
    """Expérience 2 : Variation des posts (post.csv)."""
    print("\n\n####################################################################")
    print("## EXPÉRIENCE 2 : VARIATION DU NOMBRE DE POSTS (post.csv)         ##")
    print("####################################################################")

    # Paramètres Fixes : C=50, U=1000, F=20
    C_FIXED = 50
    post_counts = [10, 100, 1000]
    results = []

    for P in post_counts:
        run_seeding(users=1000, posts=P, followees=20)
        for run in range(1, 4):
            avg_time, failed = run_ab(concurrency=C_FIXED, run_num=run)
            if avg_time is not None:
                results.append([P, avg_time, run, failed])

    write_csv('post.csv', results)


def run_fanout_test():
    """Expérience 3 : Variation du fanout (fanout.csv)."""
    print("\n\n####################################################################")
    print("## EXPÉRIENCE 3 : VARIATION DU FANOUT (fanout.csv)                ##")
    print("####################################################################")

    # Paramètres Fixes : C=50, U=1000, P=100
    C_FIXED = 50
    fanout_levels = [10, 50, 100]
    results = []

    for F in fanout_levels:
        run_seeding(users=1000, posts=100, followees=F)
        for run in range(1, 4):
            avg_time, failed = run_ab(concurrency=C_FIXED, run_num=run)
            if avg_time is not None:
                results.append([F, avg_time, run, failed])

    write_csv('fanout.csv', results)



def generate_plot(df, title, x_label, filename):
    """Génère un barplot avec barres d'erreur (variance des 3 runs)."""

    # Calcul des statistiques (Moyenne et Écart-type pour les barres d'erreur)
    stats = df.groupby('PARAM')['AVG_TIME'].agg(['mean', 'std']).reset_index()

    plt.figure(figsize=(10, 6))

    # Barres: moyenne du temps
    plt.bar(stats['PARAM'].astype(str), stats['mean'],
            yerr=stats['std'], capsize=5,
            color='skyblue', edgecolor='black', alpha=0.7)

    plt.title(title, fontsize=14)
    plt.xlabel(x_label, fontsize=12)
    plt.ylabel('Temps d\'exécution moyen (ms)', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plot_path = os.path.join(os.getcwd(), filename)
    plt.savefig(plot_path)
    print(f"Graphique généré et sauvegardé : {filename}")
    plt.close()  # Fermer la figure pour ne pas accumuler


def generate_all_plots():
    """Charge les CSV et génère les 3 graphiques."""

    print("\n\n#################################################################")
    print("## GÉNÉRATION DES GRAPHIQUES (.png)                            ##")
    print("#################################################################")

    # 1. conc.csv
    try:
        df_conc = pd.read_csv(os.path.join(OUT_DIR, 'conc.csv'))
        generate_plot(df_conc,
                      "Performance vs. Concurrence (Passage à l'échelle sur la charge)",
                      "Nombre d'utilisateurs simultanés (C)",
                      "conc.png")
    except FileNotFoundError:
        print("Avertissement: conc.csv manquant. Impossible de générer conc.png.")

    # 2. post.csv
    try:
        df_post = pd.read_csv(os.path.join(OUT_DIR, 'post.csv'))
        generate_plot(df_post,
                      "Performance vs. Taille des données (Nombre de Posts)",
                      "Nombre de posts par utilisateur (P)",
                      "post.png")
    except FileNotFoundError:
        print("Avertissement: post.csv manquant. Impossible de générer post.png.")

    # 3. fanout.csv
    try:
        df_fanout = pd.read_csv(os.path.join(OUT_DIR, 'fanout.csv'))
        generate_plot(df_fanout,
                      "Performance vs. Fanout (Nombre de Followees)",
                      "Nombre de followees par utilisateur (F)",
                      "fanout.png")
    except FileNotFoundError:
        print("Avertissement: fanout.csv manquant. Impossible de générer fanout.png.")


if __name__ == "__main__":
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        print(f"Dossier de sortie '{OUT_DIR}' créé.")

    print("Démarrage du script de Benchmark...")

    # Lancement des expériences
    run_concurrency_test()
    """
    run_posts_test()
    run_fanout_test()
    """
    # Génération des rendus
    generate_all_plots()

    print("\n*** PROCESSUS COMPLET TERMINÉ ***")
    print("Veuillez vérifier le dossier 'out/' pour les CSV et la racine pour les PNG.")