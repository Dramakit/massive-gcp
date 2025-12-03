# config_loader.py
import subprocess
import re
import csv
import json
import os
import concurrent.futures

# --- CONFIGURATION GLOBALE ---

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("Erreur: Le fichier config.json est manquant")
    exit(1)

APP_URL = config['APP_URL']
SEED_TOKEN = config['SEED_TOKEN']
USER_TO_TEST = config['USER_TO_TEST'] # Utilisé comme préfixe: load1, load2, ...
TOTAL_REQUESTS = config['TOTAL_REQUESTS']
LIMIT_TIMELINE = config['LIMIT_TIMELINE']
OUT_DIR = "out"


# --- FONCTIONS UTILITAIRES ---

def display_seeding_command(users, posts, followees):
    """Affiche la commande à exécuter manuellement sur le serveur."""
    
    # La commande de seeding manuelle est un appel à un script local du serveur
    command_to_run_on_server = f"python3 seed.py --users {users} --posts {posts} --follows-min {followees} --follows-max {followees} --prefix load"
    
    print("\n--------------------------------------------------------------------------------------------------------------------------------")
    print("## ⚠️ ÉTAPE REQUISE : COMMANDE DE SEEDING À EXÉCUTER MANUELLEMENT SUR LE SERVEUR DÉPLOYÉ :")
    print(f"{command_to_run_on_server}")
    print("--------------------------------------------------------------------------------------------------------------------------------")
    input("APPUYEZ SUR ENTRÉE UNE FOIS QUE LE SEEDING EST TERMINÉ SUR LE SERVEUR pour lancer le test...")
    print("--------------------------------------------------------------------------------------------------------------------------------")


def write_csv(filename, results):
    """Écrit les résultats dans un fichier CSV."""
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        print(f"Dossier de sortie '{OUT_DIR}' créé.")
        
    filepath = os.path.join(OUT_DIR, filename)
    print(f"\nÉcriture des résultats dans {filepath}...")
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['PARAM', 'AVG_TIME', 'RUN', 'FAILED'])
        writer.writerows(results)
    print("Fichier CSV généré.")


def fetch_timeline(user_id, limit_timeline):
    """Effectue une seule requête cURL pour une timeline spécifique et retourne le temps."""
    
    # Construction de l'URL avec l'utilisateur spécifique (ex: load1, load2, ...)
    url = f"{APP_URL}/api/timeline?user={user_id}&limit={limit_timeline}"
    
    # Utiliser curl pour obtenir le temps total (time_total) et le statut HTTP
    # -o /dev/null : ignore le corps de la réponse
    # -s : silencieux
    # -w : format d'écriture des données: code_http, time_total
    cmd = ['curl', '-o', '/dev/null', '-s', '-w', '%{http_code}:%{time_total}', url]

    try:
        # Timeout de 60s pour la requête unique
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60) 
        output = result.stdout.strip()
        
        # Le format de sortie est "CODE_HTTP:TIME_TOTAL"
        parts = output.split(':')
        http_code = int(parts[0])
        time_total = float(parts[1]) * 1000 # Convertir en millisecondes
        
        # Le nombre de requêtes échouées pour cette requête est 1 si le code est != 200
        failed = 1 if http_code != 200 else 0 
        
        return time_total, failed

    except subprocess.TimeoutExpired:
        print(f"Timeout (60s) pour utilisateur {user_id}")
        return None, 1
    except Exception as e:
        # Erreur de connexion ou autre
        print(f"Erreur pour utilisateur {user_id}: {e}")
        return None, 1
    
# Nouvelle fonction de test utilisant le parallélisme pour des timelines distinctes
def run_parallel_test(concurrency, limit_timeline, param_name, run_num):
    """
    Exécute les requêtes en parallèle pour simuler la concurrence,
    chaque thread interroge une URL distincte (user=load1, load2, ...).
    """
    
    print(f"  -> Lancement du test (C={concurrency}, Run={run_num})...")
    
    # On teste les utilisateurs load1, load2, ..., loadC
    # Utilisation d'un modulo pour boucler sur les utilisateurs disponibles
    
    requests_to_make = config['TOTAL_REQUESTS']
    
    total_time_ms = 0
    total_failed = 0
    completed_requests = 0
    
    # Utilisation du ThreadPoolExecutor pour gérer les requêtes en parallèle
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        
        # Soumettre toutes les requêtes, en utilisant le modulo pour les utilisateurs
        for i in range(requests_to_make):
            # Le test porte sur les utilisateurs 'load1' à 'loadC'
            user_id = f"load{i % concurrency + 1}"
            futures.append(executor.submit(fetch_timeline, user_id, limit_timeline))

        
        for future in concurrent.futures.as_completed(futures):
            try:
                time_total, failed = future.result()
                if time_total is not None:
                    total_time_ms += time_total
                    total_failed += failed
                    completed_requests += 1
            except Exception as e:
                print(f"Erreur d'exécution de thread: {e}")
                total_failed += 1
                completed_requests += 1 # Compter l'échec pour avancer
            
    # Calcul des métriques
    if completed_requests == 0:
        return None, 1
        
    avg_time = total_time_ms / completed_requests
    
    # Taux d'échec : 1 si le taux d'échec est > 0, 0 sinon
    final_failed_flag = 1 if total_failed > 0 else 0
    
    print(f"  -> Test terminé : Temps moyen={avg_time:.2f}ms, Échecs={total_failed}/{completed_requests}")

    return avg_time, final_failed_flag