from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import send_file
from werkzeug.security import generate_password_hash
from flask import send_file  # Assurez-vous d'importer send_file au début de votre script
import csv
import os
import io       
import base64
import datetime
import matplotlib.pyplot as plt
# Initialisation de Flask
app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Initialisation de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Fichiers CSV pour stocker les étudiants, professeurs et utilisateurs
FILENAME_ETUDIANTS = 'etudiants.csv'
FILENAME_PROFESSEURS = 'professeurs.csv'
FILENAME_UTILISATEURS = 'utilisateurs.csv'
FILENAME_MATIERES = 'matieres.csv'

# Fonction pour initialiser les fichiers
def initialiser_fichiers():
    if not os.path.exists(FILENAME_ETUDIANTS):
        with open(FILENAME_ETUDIANTS, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Nom', 'Matiere', 'Note'])
    if not os.path.exists(FILENAME_PROFESSEURS):
        with open(FILENAME_PROFESSEURS, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Nom', 'Matiere'])
    if not os.path.exists(FILENAME_UTILISATEURS):
        with open(FILENAME_UTILISATEURS, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Nom', 'Mot de passe', 'Role'])  # Role: 'etudiant' ou 'professeur'
    if not os.path.exists(FILENAME_MATIERES):
        with open(FILENAME_MATIERES, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Nom'])  
class User(UserMixin):
    def __init__(self, id, nom, role):
        self.id = id
        self.nom = nom
        self.role = role

# Fonction pour charger un utilisateur
@login_manager.user_loader
def load_user(user_id):
    if os.path.exists(FILENAME_UTILISATEURS):
        with open(FILENAME_UTILISATEURS, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Sauter l'en-tête
            for row in reader:
                if row[0] == user_id:
                    return User(user_id, row[0], row[2])  # row[2] est le rôle
    return None

# Fonction pour ajouter un étudiant et sa note
def ajouter_etudiant(nom):
    with open(FILENAME_ETUDIANTS, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([nom])

# Fonction pour lire tous les étudiants
def lire_etudiants():
    etudiants = []
    if os.path.exists(FILENAME_ETUDIANTS):
        with open(FILENAME_ETUDIANTS, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Sauter l'en-tête
            for row in reader:
                etudiants.append({'Nom': row[0]})
    return etudiants

# Fonction pour ajouter un professeur
def ajouter_professeur(nom, matiere):
    with open(FILENAME_PROFESSEURS, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([nom, matiere])

# Fonction pour lire tous les professeurs
def lire_professeurs():
    professeurs = []
    if os.path.exists(FILENAME_PROFESSEURS):
        with open(FILENAME_PROFESSEURS, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Sauter l'en-tête
            for row in reader:
                professeurs.append({'Nom': row[0], 'Matière': row[1]})
    return professeurs

# Fonction pour calculer la moyenne d'un étudiant
def calculer_moyenne(nom):
    total_notes = 0
    nombre_notes = 0
    if os.path.exists(FILENAME_ETUDIANTS):
        with open(FILENAME_ETUDIANTS, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Sauter l'en-tête
            for row in reader:
                if row[0] == nom:
                    total_notes += float(row[2])
                    nombre_notes += 1
    if nombre_notes > 0:
        return total_notes / nombre_notes
    return None

# Route pour la page d'accueil
@app.route('/')
def index():
    etudiants = lire_etudiants()
    professeurs = lire_professeurs()
    return render_template('index.html', etudiants=etudiants, professeurs=professeurs)

# Route pour ajouter un étudiant (formulaire)
@app.route('/ajouter', methods=['GET', 'POST'])
@login_required  # Nécessite une connexion
def ajouter():
    if request.method == 'POST':
        nom = request.form['nom']
        if nom:
            ajouter_etudiant(nom)
            flash(f"Étudiant {nom} ajouté avec succès.")
            return redirect(url_for('index'))
        else:
            flash("Tous les champs sont obligatoires.")
    return render_template('ajouter_eleve.html')

# Route pour ajouter un professeur (formulaire)
@app.route('/ajouter_professeur', methods=['GET', 'POST'])
@login_required  # Nécessite une connexion
def ajouter_professeur_route():
    if request.method == 'POST':
        nom = request.form['nom']
        matiere = request.form['matiere']
        if nom and matiere:
            ajouter_professeur(nom, matiere)
            flash(f"Professeur {nom} ajouté avec succès.")
            return redirect(url_for('index'))
        else:
            flash("Tous les champs sont obligatoires.")
    return render_template('ajouter_professeur.html')

# Route pour calculer la moyenne d'un étudiant
@app.route('/moyenne', methods=['GET', 'POST'])
@login_required  # Nécessite une connexion
def moyenne():
    if request.method == 'POST':
        nom = request.form['nom']
        moyenne = calculer_moyenne(nom)
        if moyenne is not None:
            flash(f"La moyenne de {nom} est {moyenne:.2f}.")
        else:
            flash(f"Aucune note trouvée pour {nom}.")
        return redirect(url_for('index'))
    return render_template('moyenne.html')

# Route pour la page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nom = request.form['nom']
        mot_de_passe = request.form['mot_de_passe']
        if verifier_utilisateur(nom, mot_de_passe):
            user = User(nom, nom, 'etudiant')  # ou 'professeur' selon le rôle
            login_user(user)
            flash("Connexion réussie.")
            return redirect(url_for('index'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.")
    return render_template('login.html')

# Fonction pour vérifier les informations de l'utilisateur
def verifier_utilisateur(nom, mot_de_passe):
    if os.path.exists(FILENAME_UTILISATEURS):
        with open(FILENAME_UTILISATEURS, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Sauter l'en-tête
            for row in reader:
                if row[0] == nom and row[1] == mot_de_passe:  # Vérification du mot de passe
                    return True
    return False

# Fonction pour ajouter un utilisateur (pour l'inscription)
def ajouter_utilisateur(nom, mot_de_passe, role):
    with open(FILENAME_UTILISATEURS, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([nom, mot_de_passe, role])

# Route pour s'inscrire
@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        nom = request.form['nom']
        mot_de_passe = request.form['mot_de_passe']
        role = request.form['role']  # 'etudiant' ou 'professeur'
        ajouter_utilisateur(nom, mot_de_passe, role)

        # Ajouter à etudiants.csv si l'utilisateur est un étudiant
        if role == 'etudiant':
            ajouter_etudiant(nom)  # Ajouter l'étudiant

        flash(f"Utilisateur {nom} créé avec succès.")
        return redirect(url_for('login'))
    return render_template('inscription.html')

# Route pour ajouter une nouvelle matière
@app.route('/ajouter_matiere', methods=['GET', 'POST'])
@login_required  # Facultatif : Peut être activé pour restreindre l'accès aux utilisateurs connectés
def ajouter_matiere():
    if request.method == 'POST':
        matiere = request.form['matiere']
        if matiere:
            try:
                ajouter_matiere_au_csv(matiere)
                flash(f"Matière '{matiere}' ajoutée avec succès.")
                return redirect(url_for('liste_notes'))
            except Exception as e:
                flash("Erreur lors de l'ajout de la matière. Veuillez réessayer.")
        else:
            flash("Le nom de la matière est obligatoire.")
    
    # Lire les matières existantes en dehors du `if`
    matieres = lire_matieres()
    return render_template('ajouter_matiere.html', matieres=matieres)


# Fonction pour ajouter une matière au fichier CSV
def ajouter_matiere_au_csv(matiere):
    FILENAME_MATIERES = 'matieres.csv'
    with open(FILENAME_MATIERES, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([matiere])

# Fonction pour lire toutes les matières
def lire_matieres():
    matieres = []
    if os.path.exists(FILENAME_MATIERES):
        with open(FILENAME_MATIERES, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Sauter l'en-tête
            for row in reader:
                matieres.append(row[0])  # Récupère uniquement le nom de la matière
    return matieres

@app.route('/ajouter_note', methods=['GET', 'POST'])
@login_required  # Nécessite une connexion
def ajouter_note():
    etudiants = lire_etudiants()  # Fonction pour récupérer les étudiants
    matieres = lire_matieres()  # Fonction pour récupérer les matières

    if request.method == 'POST':
        etudiant_nom = request.form['etudiant']
        matiere = request.form['matiere']
        note = request.form['note']

        # Ajouter la note au fichier CSV
        ajouter_note_csv(etudiant_nom, matiere, note)
        return redirect(url_for('liste_notes'))

    return render_template('ajouter_note.html', etudiants=etudiants, matieres=matieres)

# Fonction pour ajouter une note au fichier CSV
def ajouter_note_csv(nom_etudiant, matiere, note):
    with open(FILENAME_ETUDIANTS, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([nom_etudiant, matiere, note])

# Fonction pour ajouter une note à un étudiant
def ajouter_note_etudiant(Nom, Matière, Note):
    with open(FILENAME_ETUDIANTS, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([Nom, Matière, Note])

# Fonction pour lire les étudiants
def lire_etudiants():
    etudiants = set()  # Utiliser un set pour éliminer les doublons
    with open('etudiants.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            etudiants.add(row['Nom'])  # Ajouter seulement le nom à l'ensemble
    return list(etudiants)  # Convertir l'ensemble en liste avant de retourner

# Fonction pour lire les matières
def lire_matieres():
    matieres = []
    if os.path.exists(FILENAME_MATIERES):
        with open(FILENAME_MATIERES, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Sauter l'en-tête
            for row in reader:
                matieres.append(row[0])
    return matieres

# Fonction pour lire toutes les notes des étudiants
def lire_notes_etudiants():
    notes = {}
    if os.path.exists(FILENAME_ETUDIANTS):
        with open(FILENAME_ETUDIANTS, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Sauter l'en-tête
            for row in reader:
                if len(row) == 3:  # Vérifier que la ligne a exactement 3 colonnes
                    nom = row[0]
                    matiere = row[1]
                    note = float(row[2])
                    if nom not in notes:
                        notes[nom] = {'matières': {}, 'notes_total': 0, 'nombre_notes': 0}
                    if matiere not in notes[nom]['matières']:
                        notes[nom]['matières'][matiere] = {'notes': [], 'moyenne': 0}
                    # Ajouter la note à la matière
                    notes[nom]['matières'][matiere]['notes'].append(note)
                    notes[nom]['notes_total'] += note
                    notes[nom]['nombre_notes'] += 1

    # Calculer les moyennes
    for nom, data in notes.items():
        # Calculer la moyenne générale
        if data['nombre_notes'] > 0:
            data['moyenne_generale'] = data['notes_total'] / data['nombre_notes']
        # Calculer les moyennes par matière
        for matiere, matiere_data in data['matières'].items():
            if len(matiere_data['notes']) > 0:
                matiere_data['moyenne'] = sum(matiere_data['notes']) / len(matiere_data['notes'])

    # Reformatage des données pour le template
    formatted_notes = []
    for nom, data in notes.items():
        etudiant_notes = []
        for matiere, matiere_data in data['matières'].items():
            etudiant_notes.append({
                'matiere': matiere,
                'notes': matiere_data['notes'],
                'moyenne_matiere': matiere_data['moyenne']
            })
        formatted_notes.append({
            'nom': nom,
            'notes': etudiant_notes,
            'moyenne_generale': data.get('moyenne_generale', 0)
        })

    return formatted_notes

# Route pour lister les notes de tous les étudiants
@app.route('/liste_notes')
@login_required  # Nécessite une connexion
def liste_notes():
    notes = lire_notes_etudiants()
    return render_template('liste_notes.html', notes=notes)

# Route pour générer un bulletin et le télécharger
@app.route('/telecharger_bulletin/<nom>', methods=['GET'])
@login_required  # Nécessite une connexion
def telecharger_bulletin(nom):
    notes = lire_notes_etudiants()

    # Trouver les notes de l'étudiant concerné
    bulletin = None
    for etudiant in notes:
        if etudiant['nom'] == nom:
            bulletin = etudiant
            break

    if bulletin:
        # Création du contenu du bulletin
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        contenu = f"Bulletin de {nom}\nDate: {date}\n\n"
        contenu += "Matières et Notes:\n"
        
        for note in bulletin['notes']:
            contenu += f"{note['matiere']}: {note['moyenne_matiere']:.2f}\n"
        
        contenu += f"\nMoyenne Générale: {bulletin['moyenne_generale']:.2f}\n"
        
        # Écriture du bulletin dans un fichier texte
        nom_fichier = f"{nom}_bulletin.txt"
        with open(nom_fichier, 'w') as fichier:
            fichier.write(contenu)

        # Utilisation de send_file pour envoyer le fichier au client
        return send_file(nom_fichier, as_attachment=True)
    else:
        flash(f"Aucune note trouvée pour {nom}.")
        return redirect(url_for('liste_notes'))
    

   #Route pour afficher les notes d'un étudiant
@app.route('/mes_notes', methods=['GET'])
@login_required  # Requires user to be logged in
def mes_notes():
    # Initialize an empty list for student notes
    etudiant_notes = []

    # Read the CSV file and filter notes for the current user
    try:
        with open('etudiants.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Assuming the column for the student name is "Nom"
                if row['Nom'] == current_user.nom:  # Replace 'Nom' with the exact column name in your CSV
                    etudiant_notes.append(row)
    except FileNotFoundError:
        flash('Le fichier etudiants.csv est introuvable.', 'danger')
    except Exception as e:
        flash(f'Une erreur est survenue : {str(e)}', 'danger')

    return render_template('mes_notes.html', etudiant_notes=etudiant_notes)

#Route pour se déconnecter
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash("Déconnexion réussie.")
    return redirect(url_for('index'))

#------- graphique ! 
@app.route('/performances', methods=['GET', 'POST'])
@login_required
def performances():
    if current_user.role != 'etudiant':
        return redirect(url_for('index'))  # Redirige si l'utilisateur n'est pas un étudiant

    etudiant_nom = current_user.nom  # Nom de l'étudiant connecté
    notes_par_matiere = {}

    # Lire les notes de l'étudiant dans etudiants.csv
    with open('etudiants.csv', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Vérifier que la ligne est correcte (nom, matière, note)
            if row.get('Nom') == etudiant_nom and row.get('Matière') and row.get('Note'):
                matiere = row['Matière']
                try:
                    note = float(row['Note'])  # Convertir la note en float
                    if matiere not in notes_par_matiere:
                        notes_par_matiere[matiere] = []
                    notes_par_matiere[matiere].append(note)  # Ajouter la note à la matière
                except ValueError:
                    # Si la note ne peut pas être convertie en nombre, on l'ignore
                    continue

    # Préparer les données pour l'affichage
    etudiant_notes = []
    for matiere, notes in notes_par_matiere.items():
        etudiant_notes.append({
            'Nom': etudiant_nom,
            'Matière': matiere,
            'Note': round(sum(notes) / len(notes), 2) if notes else 0  # Calculer la moyenne
        })

    return render_template('performances.html', etudiant_notes=etudiant_notes)






# Fonction pour ajouter un utilisateur
def ajouter_utilisateur(nom, mot_de_passe, role):
    # Vérifier si l'utilisateur existe déjà dans le fichier
    with open(FILENAME_UTILISATEURS, 'r', newline='') as fichier:
        lecteur_csv = csv.reader(fichier)
        for ligne in lecteur_csv:
            if ligne and ligne[0] == nom:
                print(f"Utilisateur {nom} existe déjà. Aucune action entreprise.")
                return

    # Ajout du nouvel utilisateur dans le fichier CSV
    with open(FILENAME_UTILISATEURS, 'a', newline='') as fichier:
        writer = csv.writer(fichier)
        writer.writerow([nom, mot_de_passe, role])
        print(f"Utilisateur {nom} ajouté avec succès au fichier CSV.")

# Route pour ajouter un étudiant
@app.route('/ajouter_user', methods=['GET', 'POST'])
@login_required  # Nécessite une connexion
def ajouter_user():
    if request.method == 'POST':
        nom = request.form['nom']
        if nom:
            # Étape 1 : Ajouter l'étudiant au système (supposons que cette fonction existe)
            ajouter_etudiant(nom)  # Fonction existante qui gère l'ajout de l'étudiant

            # Étape 2 : Ajouter l'utilisateur dans le CSV des utilisateurs avec le mot de passe par défaut 'mdp'
            ajouter_utilisateur(nom, 'mdp', 'etudiant')

            # Message de confirmation
            flash(f"Étudiant {nom} ajouté avec succès et utilisateur créé avec le mot de passe par défaut 'mdp'.")
            return redirect(url_for('index'))
        else:
            flash("Tous les champs sont obligatoires.")
    return render_template('ajouter_eleve.html')




# Initialisation des fichiers
initialiser_fichiers()

# Démarrage de l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
