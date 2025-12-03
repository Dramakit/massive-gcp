# generate_plots.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from config_loader import OUT_DIR # Pour l'accès à OUT_DIR

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
    print("Démarrage du script de Génération des Graphiques...")
    generate_all_plots()
    print("\n*** GÉNÉRATION DES GRAPHIQUES TERMINÉE ***")