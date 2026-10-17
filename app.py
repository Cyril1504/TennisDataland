import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime

# 1. CONFIGURATION DE LA PAGE MOBILE PORTRAIT
st.set_page_config(page_title="Tennis Dataland Pro", layout="centered", page_icon="🎾")

# 2. DEFINITION PRIORITAIRE DES NOMS POUR AFFICHAGE IMMEDIAT
st.sidebar.header("⚙️ Paramètres")
player_a = st.sidebar.text_input("Joueur A", value="Joueur A")
rank_a = st.sidebar.text_input("Classement Joueur A", value="N/C")
st.sidebar.markdown("---")
player_b = st.sidebar.text_input("Joueur B", value="Joueur B")
rank_b = st.sidebar.text_input("Classement Joueur B", value="N/C")
st.sidebar.markdown("---")
match_date = st.sidebar.date_input("Date du match", datetime.now())

# 3. INITIALISATION DES ETATS SESSIONS
if 'all_match_summaries' not in st.session_state: st.session_state.all_match_summaries = []
if 'all_points_logs' not in st.session_state: st.session_state.all_points_logs = []
if 'match_data' not in st.session_state: st.session_state.match_data = []
if 'score' not in st.session_state:
    st.session_state.score = {
        "pA_points": 0, "pB_points": 0, "pA_jeux": 0, "pB_jeux": 0, "pA_sets": 0, "pB_sets": 0,
        "sets_history_A": [], "sets_history_B": [], "in_tiebreak": False, "in_supertb": False,
        "serveur_actuel": player_a, "pts_servis_tb": 0, "abandon_player": None
    }
if 'score_history' not in st.session_state: st.session_state.score_history = []
if 'service_history' not in st.session_state: st.session_state.service_history = []
if 'service_state' not in st.session_state: st.session_state.service_state = "1ère Balle"
if 'pending_event' not in st.session_state: st.session_state.pending_event = None
# Choix initial du serveur avant le premier point
if not st.session_state.match_data and st.session_state.score["pA_points"] == 0 and st.session_state.score["pA_jeux"] == 0 and len(st.session_state.score["sets_history_A"]) == 0:
    st.session_state.score["serveur_actuel"] = st.sidebar.selectbox("Serveur au tirage :", [player_a, player_b])

# Navigation robuste sans onglets imbriqués instables
app_mode = st.sidebar.radio("📍 Affichage Écran :", ["🕹️ Enregistrement Points", "📊 Radar de Performance", "📋 Historique de la Saison"])
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Réinitialiser le Match en cours", key="reset_current_match"):
    st.session_state.match_data, st.session_state.score_history, st.session_state.service_history, st.session_state.service_state, st.session_state.pending_event = [], [], [], "1ère Balle", None
    st.session_state.score = {"pA_points": 0, "pB_points": 0, "pA_jeux": 0, "pB_jeux": 0, "pA_sets": 0, "pB_sets": 0, "sets_history_A": [], "sets_history_B": [], "in_tiebreak": False, "in_supertb": False, "serveur_actuel": player_a, "pts_servis_tb": 0, "abandon_player": None}
    st.rerun()

if st.sidebar.button("⚠️ Effacer TOUT l'historique de la saison", key="clear_all_season"):
    st.session_state.all_match_summaries, st.session_state.all_points_logs, st.session_state.service_history, st.session_state.service_state, st.session_state.pending_event = [], [], [], "1ère Balle", None
    st.sidebar.success("Historique global vidé !")
    st.rerun()
st.markdown("""
<style>
    .stApp { background-color: #b14d2a !important; }
    
    .sticky-score-wrapper {
        position: fixed; top: 0; left: 0; right: 0;
        background-color: #b14d2a; z-index: 999;
        padding: 10px 10px 0 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .main-control-spacer { margin-top: 240px; }
    
    .header-container {
        text-align: center; padding: 10px; margin-bottom: 8px;
        background-color: #0b110b; border-radius: 8px; border: 1px solid #1e2b1e;
    }
    .header-title {
        color: #ffeb3b !important; font-family: 'Arial Black', sans-serif;
        font-size: 20px; text-transform: uppercase; letter-spacing: 2px; margin: 0;
    }
    
    .stWidgetForm label, .stMarkdown p, p, h3, h4 { color: #ffffff !important; font-weight: bold; }
    
    .stButton > button, .stButton > button p, .stButton > button span,
    div.btn-srv div.stButton > button, div.btn-blue div.stButton > button, div.btn-red div.stButton > button {
        color: #000000 !important; font-weight: 900 !important; font-size: 11px !important;
        padding: 4px 6px !important; min-height: 40px !important;
    }
    .stButton > button:hover { color: #ffffff !important; }
    
    div.btn-srv > div.stButton > button { background-color: #1b4d3e !important; border-radius: 4px !important; border: 1px solid #0f3025 !important; }
    div.btn-srv > div.stButton > button:hover { background-color: #27664c !important; }
    div.btn-blue > div.stButton > button { background-color: #93c5fd !important; border-radius: 4px !important; border: 1px solid #1e3a8a !important; }
    div.btn-blue > div.stButton > button:hover { background-color: #b14d2a !important; border-color: #ffffff !important; }
    div.btn-red > div.stButton > button { background-color: #fca5a5 !important; border-radius: 4px !important; border: 1px solid #991b1b !important; }
    div.btn-red > div.stButton > button:hover { background-color: #b14d2a !important; border-color: #ffffff !important; }
    div.btn-undo > div.stButton > button { background-color: #ffeb3b !important; border-radius: 4px !important; border: 1px solid #ccb200 !important; padding: 6px 12px !important; margin: 10px auto !important; display: block !important; }
    
    .score-banner-box {
        background-color: #0b110b; padding: 12px; border-radius: 8px;
        border: 2px solid #1e2b1e; margin-bottom: 15px; text-align: center;
    }
</style>
""", unsafe_allow_html=True)
def alterner_serveur():
    sc = st.session_state.score
    sc["serveur_actuel"] = player_b if sc["serveur_actuel"] == player_a else player_a

def valider_fin_set(winner_set):
    sc = st.session_state.score
    sc["sets_history_A"].append(sc["pA_jeux"])
    sc["sets_history_B"].append(sc["pB_jeux"])
    if winner_set == player_a: sc["pA_sets"] += 1
    else: sc["pB_sets"] += 1
    sc["pA_jeux"], sc["pB_jeux"] = 0, 0
    sc["pA_points"], sc["pB_points"] = 0, 0
    sc["in_tiebreak"] = False
    sc["pts_servis_tb"] = 0

def update_score(winner):
    sc = st.session_state.score
    backup = sc.copy()
    backup["sets_history_A"] = sc["sets_history_A"].copy()
    backup["sets_history_B"] = sc["sets_history_B"].copy()
    st.session_state.score_history.append(backup)
    st.session_state.service_history.append(st.session_state.service_state)
    
    if winner == player_a: sc["pA_points"] += 1
    else: sc["pB_points"] += 1
    
    evenement = "Echange"
    if sc["in_supertb"]:
        sc["pts_servis_tb"] += 1
        if sc["pts_servis_tb"] % 2 == 1: alterner_serveur()
        if sc["pA_points"] >= 10 and (sc["pA_points"] - sc["pB_points"]) >= 2:
            sc["pA_jeux"] = sc["pA_points"]; sc["pB_jeux"] = sc["pB_points"]
            valider_fin_set(player_a); sc["in_supertb"] = False; evenement = "🎉 FIN DE MATCH"
        elif sc["pB_points"] >= 10 and (sc["pB_points"] - sc["pA_points"]) >= 2:
            sc["pA_jeux"] = sc["pA_points"]; sc["pB_jeux"] = sc["pB_points"]
            valider_fin_set(player_b); sc["in_supertb"] = False; evenement = "🎉 FIN DE MATCH"
    elif sc["in_tiebreak"]:
        sc["pts_servis_tb"] += 1
        if sc["pts_servis_tb"] % 2 == 1: alterner_serveur()
        if sc["pA_points"] >= 7 and (sc["pA_points"] - sc["pB_points"]) >= 2:
            sc["pA_jeux"] = 7; sc["pB_jeux"] = 6
            valider_fin_set(player_a); alterner_serveur(); evenement = "🎉 CHANGEMENT DE SET"
        elif sc["pB_points"] >= 7 and (sc["pB_points"] - sc["pA_points"]) >= 2:
            sc["pA_jeux"] = 6; sc["pB_jeux"] = 7
            valider_fin_set(player_b); alterner_serveur(); evenement = "🎉 CHANGEMENT DE SET"
    else:
        if sc["pA_points"] >= 4 and (sc["pA_points"] - sc["pB_points"]) >= 2:
            sc["pA_jeux"] += 1; sc["pA_points"], sc["pB_points"] = 0, 0; alterner_serveur(); evenement = "🎉 CHANGEMENT DE JEU"
        elif sc["pB_points"] >= 4 and (sc["pB_points"] - sc["pA_points"]) >= 2:
            sc["pB_jeux"] += 1; sc["pA_points"], sc["pB_points"] = 0, 0; alterner_serveur(); evenement = "🎉 CHANGEMENT DE JEU"
        if sc["pA_points"] >= 4 and sc["pB_points"] >= 4 and sc["pA_points"] == sc["pB_points"]: sc["pA_points"], sc["pB_points"] = 3, 3
        if sc["pA_jeux"] == 6 and sc["pB_jeux"] == 6: sc["in_tiebreak"] = True; sc["pts_servis_tb"] = 0
        elif sc["pA_jeux"] >= 6 and (sc["pA_jeux"] - sc["pB_jeux"]) >= 2: valider_fin_set(player_a); evenement = "🎉 CHANGEMENT DE SET"
        elif sc["pB_jeux"] >= 6 and (sc["pB_jeux"] - sc["pA_jeux"]) >= 2: valider_fin_set(player_b); evenement = "🎉 CHANGEMENT DE SET"

    if sc["pA_sets"] == 1 and sc["pB_sets"] == 1 and not sc["in_supertb"] and len(sc["sets_history_A"]) == 2: sc["in_supertb"] = True; sc["pts_servis_tb"] = 0
    return evenement

def get_pts(pa, pb, in_tb, in_stb):
    if in_tb or in_stb: return str(pa), str(pb)
    if pa >= 3 and pb >= 3:
        if pa == pb: return "40", "40"
        return ("Ad", "40") if pa > pb else ("40", "Ad")
    conversion = {0: "0", 1: "15", 2: "30", 3: "40"}
    return conversion.get(pa, "0"), conversion.get(pb, "0")

def undo_last_point():
    if st.session_state.match_data and st.session_state.score_history and st.session_state.service_history:
        st.session_state.match_data.pop()
        st.session_state.score = st.session_state.score_history.pop()
        st.session_state.service_state = st.session_state.service_history.pop()
        st.toast("↩️ Point annulé !", icon="✅")
sc = st.session_state.score
pt_a, pt_b = get_pts(sc["pA_points"], sc["pB_points"], sc["in_tiebreak"], sc["in_supertb"])
match_termine = sc["pA_sets"] == 2 or sc["pB_sets"] == 2 or sc["abandon_player"] is not None
set_actuel = sc["pA_sets"] + sc["pB_sets"] + 1

if match_termine:
    s1_a = sc["sets_history_A"] if len(sc["sets_history_A"]) >= 1 else ""
    s1_b = sc["sets_history_B"] if len(sc["sets_history_B"]) >= 1 else ""
    s2_a = sc["sets_history_A"] if len(sc["sets_history_A"]) >= 2 else ""
    s2_b = sc["sets_history_B"] if len(sc["sets_history_B"]) >= 2 else ""
    s3_a = sc["sets_history_A"] if len(sc["sets_history_A"]) >= 3 else ""
    s3_b = sc["sets_history_B"] if len(sc["sets_history_B"]) >= 3 else ""
else:
    if set_actuel == 1:
        s1_a, s1_b, s2_a, s2_b, s3_a, s3_b = sc["pA_jeux"], sc["pB_jeux"], "", "", "", ""
    elif set_actuel == 2:
        s1_a = sc["sets_history_A"]; s1_b = sc["sets_history_B"]
        s2_a, s2_b, s3_a, s3_b = sc["pA_jeux"], sc["pB_jeux"], "", ""
    else:
        s1_a = sc["sets_history_A"]; s1_b = sc["sets_history_B"]
        s2_a = sc["sets_history_A"]; s2_b = sc["sets_history_B"]
        s3_a, s3_b = sc["pA_jeux"], sc["pB_jeux"]

if not match_termine and len(st.session_state.match_data) > 0:
    st.sidebar.markdown("---")
    if st.sidebar.button(f"Abandon de {player_a}", key="abandon_a"): sc["abandon_player"] = player_a; st.rerun()
    if st.sidebar.button(f"Abandon de {player_b}", key="abandon_b"): sc["abandon_player"] = player_b; st.rerun()

st.markdown('<div class="header-container"><h1 class="header-title">🎾 Tennis Dataland</h1></div>', unsafe_allow_html=True)

with st.container():
    st.markdown(f"""
    <div class="score-banner-box">
        <p style='margin:0; font-size:16px; color:#ffeb3b;'><b>{player_a}</b> vs <b>{player_b}</b></p>
        <p style='margin:4px 0 0 0; font-size:22px; letter-spacing:3px;'>
            <span style='color:#cbd5e0;'>({s1_a}/{s1_b}) ({s2_a}/{s2_b}) ({s3_a}/{s3_b})</span> 
            <b style='color:#ffeb3b; margin-left:10px;'>{pt_a if not match_termine else 'Fin'} - {pt_b if not match_termine else 'Fin'}</b>
        </p>
        <p style='margin:4px 0 0 0; font-size:12px; color:#a0aec0;'>{"Serveur actuel : " + sc["serveur_actuel"] + " 🟡" if not match_termine else "Match Terminé 🔒"}</p>
    </div>
    """, unsafe_allow_html=True)

if match_termine:
    winner_name = player_b if sc["abandon_player"] == player_a else (player_a if sc["pA_sets"] == 2 or sc["abandon_player"] == player_b else player_b)
    st.success(f"🏆 MATCH TERMINÉ — Victoire de {winner_name}", icon="🎉")

if sc["in_supertb"] and not match_termine: st.error("🔥 SUPER TIE-BREAK AU 3ÈME SET (10 POINTS)", icon="🎾")
elif sc["in_tiebreak"] and not match_termine: st.warning("⚠️ JEU DÉCISIF (TIE-BREAK)", icon="🎾")

def queue_event(w, p, t, s="N/A"):
    if t in ["Ace", "Double Faute"]: execute_log(w, p, t, s, "- 4 échanges")
    else: st.session_state.pending_event = {"w": w, "p": p, "t": t, "s": s}; st.rerun()

def execute_log(w, p, t, s, rally_length):
    current_service = st.session_state.service_state; evt_msg = update_score(w)
    st.session_state.match_data.append({
        "Date": match_date.strftime("%d/%m/%Y"), "Match": f"{player_a} vs {player_b}", "Gagnant du point": w,
        "Joueur ayant fait l'action/erreur": p, "Type d'action": t, "Côté du coup": s, "Longueur Échange": rally_length,
        "Serveur du point": sc["serveur_actuel"], "Balle de service": current_service, "Événement Match": evt_msg
    })
    st.session_state.service_state = "1ère Balle"; st.session_state.pending_event = None; st.rerun()
st.markdown('<div class="main-control-spacer"></div>', unsafe_allow_html=True)

if app_mode == "🕹️ Enregistrement Points":
    if st.session_state.pending_event is not None:
        pe = st.session_state.pending_event
        st.markdown(f"<div style='background-color:#0b110b; border:2px solid #ffeb3b; padding:12px; border-radius:8px; text-align:center; margin-bottom:10px;'><p style='color:#ffeb3b; margin:0;'>📊 COMPTEUR FRAPPES ({pe['p']})</p></div>", unsafe_allow_html=True)
        c_r1, c_r2, c_r3 = st.columns(3)
        if c_r1.button("📉 - 4", key="r_short", use_container_width=True): execute_log(pe["w"], pe["p"], pe["t"], pe["s"], "- 4 échanges")
        if c_r2.button("⚖️ 4-8", key="r_med", use_container_width=True): execute_log(pe["w"], pe["p"], pe["t"], pe["s"], "4-8 échanges")
        if c_r3.button("🚀 + 8", key="r_long", use_container_width=True): execute_log(pe["w"], pe["p"], pe["t"], pe["s"], "+ 8 échanges")
        if st.button("❌ Annuler", key="cancel_pending", use_container_width=True): st.session_state.pending_event = None; st.rerun()
            
    elif match_termine:
        st.warning("🔒 Saisie gelée. Enregistrez le match pour archiver et générer le rapport Excel.")
        if st.button("💾 Clôturer le match et enregistrer", key="force_archive_final_match", use_container_width=True, type="primary"):
            df_temp = pd.DataFrame(st.session_state.match_data)
            if not df_temp.empty:
                if "Type d'action" in df_temp.columns:
                    df_temp["Type d'action"] = df_temp["Type d'action"].replace("As", "Ace")
                
                v_a_1st = len(df_temp[(df_temp["Serveur du point"] == player_a) & (df_temp["Balle de service"] == "1ère Balle")])
                v_a_2nd = len(df_temp[(df_temp["Serveur du point"] == player_a) & (df_temp["Balle de service"] == "2e Balle")])
                v_b_1st = len(df_temp[(df_temp["Serveur du point"] == player_b) & (df_temp["Balle de service"] == "1ère Balle")])
                v_b_2nd = len(df_temp[(df_temp["Serveur du point"] == player_b) & (df_temp["Balle de service"] == "2e Balle")])
                tot_pts = max(1, len(df_temp))
                
                match_summary = {
                    "Date": match_date.strftime("%d/%m/%Y"), "Match": f"{player_a} vs {player_b}", "Total Points Joués": tot_pts,
                    f"Aces % {player_a}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_a) & (df_temp['Type d\'action'] == 'Ace')]) / tot_pts):.1%}",
                    f"Aces % {player_b}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_b) & (df_temp['Type d\'action'] == 'Ace')]) / tot_pts):.1%}",
                    f"% 1er Srv In {player_a}": f"{(v_a_1st/max(1,v_a_1st+v_a_2nd)):.1%}", 
                    f"% Pts Gagne 1er Srv {player_a}": f"{(len(df_temp[(df_temp['Serveur du point'] == player_a) & (df_temp['Balle de service'] == '1ère Balle') & (df_temp['Gagnant du point'] == player_a)])/max(1,v_a_1st)):.1%}", 
                    f"% Pts Gagne 2e Srv {player_a}": f"{(len(df_temp[(df_temp['Serveur du point'] == player_a) & (df_temp['Balle de service'] == '2e Balle') & (df_temp['Gagnant du point'] == player_a)])/max(1,v_a_2nd)):.1%}",
                    f"% 1er Srv In {player_b}": f"{(v_b_1st/max(1,v_b_1st+v_b_2nd)):.1%}",
                    f"% Pts Gagne 1er Srv {player_b}": f"{(len(df_temp[(df_temp['Serveur du point'] == player_b) & (df_temp['Balle de service'] == '1ère Balle') & (df_temp['Gagnant du point'] == player_b)])/max(1,v_b_1st)):.1%}", 
                    f"% Pts Gagne 2e Srv {player_b}": f"{(len(df_temp[(df_temp['Serveur du point'] == player_b) & (df_temp['Balle de service'] == '2e Balle') & (df_temp['Gagnant du point'] == player_b)])/max(1,v_b_2nd)):.1%}",
                    f"CD Winners % {player_a}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_a) & (df_temp['Type d\'action'] == 'Winner') & (df_temp['Côté du coup'] == 'Coup Droit')]) / tot_pts):.1%}",
                    f"REV Winners % {player_a}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_a) & (df_temp['Type d\'action'] == 'Winner') & (df_temp['Côté du coup'] == 'Revers')]) / tot_pts):.1%}",
                    f"CD Winners % {player_b}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_b) & (df_temp['Type d\'action'] == 'Winner') & (df_temp['Côté du coup'] == 'Coup Droit')]) / tot_pts):.1%}",
                    f"REV Winners % {player_b}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_b) & (df_temp['Type d\'action'] == 'Winner') & (df_temp['Côté du coup'] == 'Revers')]) / tot_pts):.1%}",
                    f"F. Directes CD % {player_a}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_a) & (df_temp['Type d\'action'] == 'Faute Directe') & (df_temp['Côté du coup'] == 'Coup Droit')]) / tot_pts):.1%}",
                    f"F. Directes REV % {player_a}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_a) & (df_temp['Type d\'action'] == 'Faute Directe') & (df_temp['Côté du coup'] == 'Revers')]) / tot_pts):.1%}",
                    f"F. Directes CD % {player_b}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_b) & (df_temp['Type d\'action'] == 'Faute Directe') & (df_temp['Côté du coup'] == 'Coup Droit')]) / tot_pts):.1%}",
                    f"F. Directes REV % {player_b}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_b) & (df_temp['Type d\'action'] == 'Faute Directe') & (df_temp['Côté du coup'] == 'Revers')]) / tot_pts):.1%}",
                    f"F. Provoquées CD % {player_a}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_a) & (df_temp['Type d\'action'] == 'Faute Provoquée') & (df_temp['Côté du coup'] == 'Coup Droit')]) / tot_pts):.1%}",
                    f"F. Provoquées REV % {player_a}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_a) & (df_temp['Type d\'action'] == 'Faute Provoquée') & (df_temp['Côté du coup'] == 'Revers')]) / tot_pts):.1%}",
                    f"F. Provoquées CD % {player_b}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_b) & (df_temp['Type d\'action'] == 'Faute Provoquée') & (df_temp['Côté du coup'] == 'Coup Droit')]) / tot_pts):.1%}",
                    f"F. Provoquées REV % {player_b}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_b) & (df_temp['Type d\'action'] == 'Faute Provoquée') & (df_temp['Côté du coup'] == 'Revers')]) / tot_pts):.1%}",
                    f"Rallyes Courts (-4) % {player_a}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_a) & (df_temp['Longueur Échange'] == '- 4 échanges')]) / tot_pts):.1%}",
                    f"Rallyes Moyens (4-8) % {player_a}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_a) & (df_temp['Longueur Échange'] == '4-8 échanges')]) / tot_pts):.1%}",
                    f"Rallyes Longs (+8) % {player_a}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_a) & (df_temp['Longueur Échange'] == '+ 8 échanges')]) / tot_pts):.1%}",
                    f"Rallyes Courts (-4) % {player_b}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_b) & (df_temp['Longueur Échange'] == '- 4 échanges')]) / tot_pts):.1%}",
                    f"Rallyes Moyens (4-8) % {player_b}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_b) & (df_temp['Longueur Échange'] == '4-8 échanges')]) / tot_pts):.1%}",
                    f"Rallyes Longs (+8) % {player_b}": f"{(len(df_temp[(df_temp['Joueur ayant fait l\'action/erreur'] == player_b) & (df_temp['Longueur Échange'] == '+ 8 échanges')]) / tot_pts):.1%}",
                }
                st.session_state.all_match_summaries.append(match_summary)
                st.session_state.all_points_logs.extend(df_temp.to_dict(orient="records"))
                
            st.session_state.match_data, st.session_state.score_history, st.session_state.service_state, st.session_state.service_history = [], [], "1ère Balle", []
            st.session_state.score = {"pA_points":0,"pB_points":0,"pA_jeux":0,"pB_jeux":0,"pA_sets":0,"pB_sets":0,"sets_history_A":[],"sets_history_B":[],"in_tiebreak":False,"in_supertb":False,"serveur_actuel":player_a,"pts_servis_tb":0, "abandon_player":None}
            st.rerun()
    else:
        st.markdown('<div class="btn-srv">', unsafe_allow_html=True)
        c_srv1, c_srv2, c_srv3 = st.columns(3)
        with c_srv1:
            if st.button("🔄 2e Balle", use_container_width=True, disabled=st.session_state.service_state == "2e Balle", key="second_ball_trigger"): st.session_state.service_state = "2e Balle"; st.rerun()
        with c_srv2:
            if st.button("🎯 Ace", key="ace_direct", use_container_width=True): queue_event(sc["serveur_actuel"], sc["serveur_actuel"], "Ace", "Service")
        with c_srv3:
            if st.button("❌ DblF.", key="df_direct", use_container_width=True):
                st.session_state.service_state = "2e Balle"; rc = player_b if sc["serveur_actuel"] == player_a else player_a; queue_event(rc, sc["serveur_actuel"], "Double Faute", "Service")
        st.markdown('</div><div style="margin:4px 0;"></div>', unsafe_allow_html=True)
        
        col_pA, col_pB = st.columns(2)
        with col_pA:
            st.markdown(f"<p style='text-align:center; font-size:11px; margin:0; color:#93c5fd;'>{player_a[:10]}</p>", unsafe_allow_html=True)
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔥 CD Gagnant", key="w_cd_a", use_container_width=True): queue_event(player_a, player_a, "Winner", "Coup Droit")
            if st.button("🔥 Revers Gagnant", key="w_rev_a", use_container_width=True): queue_event(player_a, player_a, "Winner", "Revers")
            if st.button("📉 Faute CD", key="ue_cd_a", use_container_width=True): queue_event(player_b, player_a, "Faute Directe", "Coup Droit")
            if st.button("📉 Faute Rev.", key="ue_rev_a", use_container_width=True): queue_event(player_b, player_a, "Faute Directe", "Revers")
            if st.button("🛡️ F.Prov. CD", key="fe_cd_a", use_container_width=True): queue_event(player_b, player_a, "Faute Provoquée", "Coup Droit")
            if st.button("🛡️ F.Prov. Rev.", key="fe_rev_a", use_container_width=True): queue_event(player_b, player_a, "Faute Provoquée", "Revers")
            st.markdown('</div>', unsafe_allow_html=True)
        with col_pB:
            st.markdown(f"<p style='text-align:center; font-size:11px; margin:0; color:#fca5a5;'>{player_b[:10]}</p>", unsafe_allow_html=True)
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 CD Gagnant ", key="w_cd_b", use_container_width=True): queue_event(player_b, player_b, "Winner", "Coup Droit")
            if st.button("🔥 Revers Gagnant ", key="w_rev_b", use_container_width=True): queue_event(player_b, player_b, "Winner", "Revers")
            if st.button("📉 Faute CD ", key="ue_cd_b", use_container_width=True): queue_event(player_a, player_b, "Faute Directe", "Coup Droit")
            if st.button("📉 Faute Rev. ", key="ue_rev_b", use_container_width=True): queue_event(player_a, player_b, "Faute Directe", "Revers")
            if st.button("🛡️ F.Prov. CD ", key="fe_cd_b", use_container_width=True): queue_event(player_a, player_b, "Faute Provoquée", "Coup Droit")
            if st.button("🛡️ F.Prov. Rev. ", key="fe_rev_b", use_container_width=True): queue_event(player_a, player_b, "Faute Provoquée", "Revers")
            st.markdown('</div>', unsafe_allow_html=True)
            
    st.markdown('<div class="btn-undo">', unsafe_allow_html=True)
    if st.button("↩️ Annuler", key="undo_btn", disabled=len(st.session_state.match_data) == 0 or match_termine, use_container_width=True): undo_last_point(); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
df = pd.DataFrame(st.session_state.match_data)

if app_mode == "📊 Radar de Performance":
    if df.empty and not st.session_state.all_points_logs: st.info("Enregistrez des points pour générer le radar.")
    else:
        df_radar = df if not df.empty else pd.DataFrame(st.session_state.all_points_logs)
        def calc(p, t, c): return len(df_radar[(df_radar["Joueur ayant fait l'action/erreur"] == p) & (df_radar["Type d'action"] == t) & (df_radar["Côté du coup"] == c)])
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=[calc(player_a,"Winner","Coup Droit"), calc(player_a,"Winner","Revers"), calc(player_a,"Faute Directe","Coup Droit"), calc(player_a,"Faute Directe","Revers")], theta=['Win CD','Win REV','Faute CD','Faute REV'], fill='toself', name=player_a, line_color="#3b82f6"))
        fig.add_trace(go.Scatterpolar(r=[calc(player_b,"Winner","Coup Droit"), calc(player_b,"Winner","Revers"), calc(player_b,"Faute Directe","Coup Droit"), calc(player_b,"Faute Directe","Revers")], theta=['Win CD','Win REV','Faute CD','Faute REV'], fill='toself', name=player_b, line_color="#ef4444"))
        fig.update_layout(polar=dict(radialaxis=dict(visible=False)), paper_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

if app_mode == "📋 Historique de la Saison":
    if not st.session_state.all_match_summaries: st.info("Aucun match archivé.")
    else:
        df_global_summary = pd.DataFrame(st.session_state.all_match_summaries)
        df_global_points = pd.DataFrame(st.session_state.all_points_logs)
        st.subheader("📊 Bilan Multi-Matchs de la Saison")
        st.dataframe(df_global_summary, use_container_width=True, hide_index=True)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_global_summary.to_excel(writer, sheet_name='Efficacite Service Saison', index=False)
            df_global_points.to_excel(writer, sheet_name='Historique Detaille Points', index=False)
            
            workbook = writer.book; from openpyxl.styles import PatternFill, Border, Side
            fill_player_a = PatternFill(start_color="E6F0FA", end_color="E6F0FA", fill_type="solid")
            fill_player_b = PatternFill(start_color="FCE8E6", end_color="FCE8E6", fill_type="solid")
            fill_end_match = PatternFill(start_color="C3E6CB", end_color="C3E6CB", fill_type="solid")
            thin_side = Side(style='thin', color='CBD5E1'); double_bottom = Border(bottom=Side(style='double', color='155724')); standard_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

            ws_summary = writer.sheets['Efficacite Service Saison']
            for r_idx in range(2, len(df_global_summary) + 2):
                for c_idx in range(1, len(df_global_summary.columns) + 1):
                    cell = ws_summary.cell(row=r_idx, column=c_idx); header_name = ws_summary.cell(row=1, column=c_idx).value; cell.border = standard_border
                    if header_name and player_a in str(header_name): cell.fill = fill_player_a
                    elif header_name and player_b in str(header_name): cell.fill = fill_player_b

            ws_points = writer.sheets['Historique Detaille Points']
            for row_idx in range(2, len(df_global_points) + 2):
                is_fin_de_match = False
                for col_search in range(1, len(df_global_points.columns) + 1):
                    val = ws_points.cell(row=row_idx, column=col_search).value
                    if val and "FIN DE MATCH" in str(val).upper():
                        is_fin_de_match = True
                        break
                action_player = ws_points.cell(row=row_idx, column=4).value
                
                if is_fin_de_match:
                    for col_idx in range(1, len(df_global_points.columns) + 1): cell = ws_points.cell(row=row_idx, column=col_idx); cell.fill = fill_end_match; cell.border = double_bottom
                else:
                    for col_idx in range(1, len(df_global_points.columns) + 1):
                        cell = ws_points.cell(row=row_idx, column=col_idx); cell.border = standard_border
                        if action_player == player_a: cell.fill = fill_player_a
                        elif action_player == player_b: cell.fill = fill_player_b
                        
        st.download_button(label="📥 Télécharger le Bilan (.xlsx)", data=excel_buffer.getvalue(), file_name="bilan_saison_tennis.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True, key="download_season_report")
