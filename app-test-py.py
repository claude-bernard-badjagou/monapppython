import streamlit as st
import json, random, os
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Quiz Python", layout="centered")

# ---------- Fonctions utilitaires ----------
@st.cache_data
def load_questions(filepath="quiz_python.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        # Affiche l’erreur complète (message, ligne, colonne) dans l’UI
        st.error(f"❌ JSONDecodeError: {e.msg} (ligne {e.lineno}, colonne {e.colno})")
        st.stop()


def load_results(filepath="results.json"):
    """Charge l'historique des résultats (ou retourne une liste vide)."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_results(results, filepath="results.json"):
    """Sauvegarde l'historique des résultats."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


# Initialisation de la session
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'skip' not in st.session_state:
    st.session_state['skip'] = False

# Barre de navigation
menu = ["Quiz", "Résultats"]
page = st.sidebar.selectbox("Navigation", menu)

# ---------- Page de connexion (ou passage) ----------
def login_section():
    """Gère l'inscription/connexion ou le passage libre."""
    if st.session_state['user'] is None and not st.session_state['skip']:
        st.sidebar.header("Connexion / Inscription")
        email = st.sidebar.text_input("Adresse Gmail", value="")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Se connecter", key="btn_login"):
                if email.strip().endswith("@gmail.com"):
                    st.session_state['user'] = email.strip()
                    st.sidebar.success(f"Connecté en tant que {email}")
                else:
                    st.sidebar.error("Merci d'utiliser une adresse Gmail valide.")
        with col2:
            if st.button("Passer", key="btn_skip"):
                st.session_state['skip'] = True
    else:
        user_label = st.session_state['user'] if st.session_state['user'] else "Invité"
        st.sidebar.markdown(f"**Utilisateur :** {user_label}")

# Exécuter la section login sur toutes les pages
login_section()

# ---------- Page QUIZ ----------
if page == "Quiz":
    st.title("📝 Quiz Python")
    # Charger les questions
    data = load_questions()
    # Sélection des chapitres
    chapters = list(data.keys())
    selected = st.multiselect("Sélectionnez un ou plusieurs chapitres à évaluer", chapters)
    if not selected:
        st.info("Choisissez au moins un chapitre pour démarrer le quiz.")
        st.stop()

    # Bouton de démarrage
    if st.button("Démarrer le quiz"):
        # Préparer le quiz
        st.session_state['questions'] = []
        for ch in selected:
            st.session_state['questions'] += data[ch]
        random.shuffle(st.session_state['questions'])
        st.session_state['total'] = len(st.session_state['questions'])
        st.session_state['index'] = 0
        st.session_state['score'] = 0
        st.session_state['answered'] = 0
        st.rerun()

    # Si quiz déjà démarré
    if 'questions' in st.session_state:
        idx = st.session_state['index']
        total = st.session_state['total']
        st.progress(idx / total)
        st.write(f"Question {idx+1} sur {total}")
        if idx >= len(st.session_state['questions']):
            q = st.session_state['questions'][idx]
        else:
            st.success("🎉 Félicitations ! Vous avez terminé le quiz.")
            st.stop()
        #st.write(q['question'])
        choice = st.radio("Votre réponse :", q['options'], key=f"opt_{idx}")

        if st.button("Valider", key=f"btn_val_{idx}"):
            correct = q['options'].index(choice) == q['answer_index']
            if correct:
                st.success(q['feedback']['correct'])
                st.session_state['score'] += 1
            else:
                st.error(q['feedback']['incorrect'])
            st.session_state['answered'] += 1
            st.session_state['index'] += 1

            # Quiz terminé
            if st.session_state['index'] >= total:
                score = st.session_state['score']
                answered = st.session_state['answered']
                pct = (score / answered) * 100
                # Affichage du score final avec couleur selon pourcentage
                if pct >= 75:
                    st.success(f"🎉 Score final : {score}/{answered} ({pct:.1f}%) — Bravo ! 🎉")
                elif pct >= 50:
                    st.warning(f"👍 Score final : {score}/{answered} ({pct:.1f}%) — Encourageant !")
                elif pct >= 25:
                    st.info(f"🙂 Score final : {score}/{answered} ({pct:.1f}%) — Continuez vos efforts !")
                else:
                    st.error(f"😕 Score final : {score}/{answered} ({pct:.1f}%) — Persévérez et apprenez davantage !")

                # Enregistrement du résultat
                history = load_results()
                history.append({
                    "user": st.session_state['user'] or "Invité",
                    "chapitres": selected,
                    "score": score,
                    "answered": answered,
                    "pct": round(pct, 1),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                save_results(history)

                # Options post-test
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("Recommencer même test"):
                        # Réinitialiser le même quiz
                        st.session_state['index'] = 0
                        st.session_state['score'] = 0
                        st.session_state['answered'] = 0
                        st.experimental_rerun()
                with col_b:
                    if st.button("Choisir d'autres chapitres"):
                        # Recommencer à la sélection
                        for key in ['questions', 'total', 'index', 'score', 'answered']:
                            st.session_state.pop(key, None)
                        st.experimental_rerun()
                with col_c:
                    if st.button("Quitter"):
                        st.stop()
            else:
                st.rerun()

# ---------- Page RESULTATS ----------
elif page == "Résultats":
    st.title("📊 Historique des résultats")
    history = load_results()
    if history:
        # Filtrer selon utilisateur si connecté
        if st.session_state['user']:
            filt = [r for r in history if r['user'] == st.session_state['user']]
        else:
            filt = history
        if filt:
            # Affichage du tableau
            st.dataframe(filt)
        else:
            st.info("Aucun résultat trouvé pour votre compte.")
    else:
        st.info("Aucun résultat enregistré pour le moment.")
