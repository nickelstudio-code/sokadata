import numpy as np
import pandas as pd
import penaltyblog as pb
from app.data import (
    get_finished_matches,
    get_upcoming_matches,
    get_team_form,
    get_head_to_head,
)
from app.ai import generate_commentary


def matches_to_dataframe(matches):
    rows = []
    for m in matches:
        try:
            rows.append({
                "date": pd.to_datetime(m["utcDate"]).tz_localize(None),
                "home_team": m["homeTeam"]["name"],
                "away_team": m["awayTeam"]["name"],
                "home_goals": m["score"]["fullTime"]["home"],
                "away_goals": m["score"]["fullTime"]["away"],
            })
        except (KeyError, TypeError):
            continue
    return pd.DataFrame(rows).dropna()


def train_model(competition_code):
    finished = get_finished_matches(competition_code)
    df = matches_to_dataframe(finished)
    print(f"[DEBUG] {len(df)} matchs recuperes pour {competition_code}")
    if len(df) < 30:
        raise ValueError(f"Pas assez de matchs ({len(df)}).")
    model = pb.models.DixonColesGoalModel(
        df["home_goals"], df["away_goals"],
        df["home_team"], df["away_team"],
    )
    model.fit()
    return model, df


def predict_upcoming(competition_code, limit=20):
    """Genere les predictions SANS commentaire IA (rapide)."""
    model, _ = train_model(competition_code)
    upcoming = get_upcoming_matches(competition_code)
    print(f"[DEBUG] {len(upcoming)} matchs a venir pour {competition_code}")
    predictions = []

    for m in upcoming[:limit]:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        home_id = m["homeTeam"]["id"]
        away_id = m["awayTeam"]["id"]

        try:
            pred = model.predict(home, away)

            # === Statistiques avancees via penaltyblog ===
            # BTTS : pred.both_teams_to_score est un float deja en probabilite
            btts_yes = float(pred.both_teams_to_score)
            btts_no = 1.0 - btts_yes

            # Over/Under 2.5 : methode total_goals(over_under, strike)
            over_25 = float(pred.total_goals("over", 2.5))
            under_25 = float(pred.total_goals("under", 2.5))

            # Top 3 scores exacts : pred.grid est un ndarray (15x15)
            grid = pred.grid
            flat_indices = np.argsort(grid.flatten())[::-1][:3]
            top_scores = []
            for idx in flat_indices:
                h, a = np.unravel_index(idx, grid.shape)
                prob = float(grid[h][a])
                top_scores.append({"score": f"{h}-{a}", "prob": round(prob * 100, 1)})

            predictions.append({
                "date": m["utcDate"][:10],
                "home": home,
                "away": away,
                "home_id": home_id,
                "away_id": away_id,
                "home_crest": m["homeTeam"].get("crest"),
                "away_crest": m["awayTeam"].get("crest"),
                "prob_home": round(pred.home_win * 100, 1),
                "prob_draw": round(pred.draw * 100, 1),
                "prob_away": round(pred.away_win * 100, 1),
                "expected_home_goals": round(pred.home_goal_expectation, 2),
                "expected_away_goals": round(pred.away_goal_expectation, 2),
                "btts_yes": round(btts_yes * 100, 1),
                "btts_no": round(btts_no * 100, 1),
                "over_25": round(over_25 * 100, 1),
                "under_25": round(under_25 * 100, 1),
                "top_scores": top_scores,
                "commentary": "",
            })
        except Exception as e:
            print(f"Erreur prediction {home} vs {away} : {e}")
            continue
    return predictions


def analyze_single_match(match, lang="en"):
    """Genere le commentaire IA pour un match specifique (lent)."""
    home = match["home"]
    away = match["away"]
    home_id = match["home_id"]
    away_id = match["away_id"]

    print(f"[FORM] Recuperation forme {home}...")
    form_home = get_team_form(home_id, home)
    print(f"[FORM] Recuperation forme {away}...")
    form_away = get_team_form(away_id, away)

    print(f"[H2H] Recuperation confrontations {home} vs {away}...")
    h2h = get_head_to_head(home_id, away_id, home, away)

    print(f"[AI] Generation commentaire {home} vs {away}...")
    commentary = generate_commentary(
        home, away,
        match["prob_home"], match["prob_draw"], match["prob_away"],
        match["expected_home_goals"], match["expected_away_goals"],
        form_home, form_away, h2h,
        lang=lang,
    )
    return commentary

def predict_matches_list(matches):
    """Prend une liste de matchs (toutes ligues) et genere les predictions.
    ATTENTION : pour la home, on n'entraine PAS de modele Dixon-Coles par ligue
    (trop long). On utilise une approche simplifiee : 1X2 sans xG ni BTTS.
    Pour les predictions completes, il faut aller sur la page d une ligue."""
    predictions = []
    for m in matches:
        try:
            home = m["homeTeam"]["name"]
            away = m["awayTeam"]["name"]
            comp_code = m.get("competition", {}).get("code", "")
            comp_name = m.get("competition", {}).get("name", "")
            from datetime import datetime

            from datetime import datetime, timedelta, timezone
            utc_dt = datetime.strptime(m["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            tz_tz = utc_dt.astimezone(timezone(timedelta(hours=3)))
            match_date_iso = tz_tz.strftime("%Y-%m-%d")
            match_date_display = tz_tz.strftime("%a %d %b").capitalize()
            match_time = tz_tz.strftime("%H:%M")
            status = m.get("status", "SCHEDULED")

            # Statut plus lisible
            status_display = status
            if status == "IN_PLAY":
                status_display = "LIVE"
            elif status == "PAUSED":
                status_display = "HT"
            elif status == "FINISHED":
                status_display = "FT"
            elif status in ("SCHEDULED", "TIMED"):
                status_display = "UPCOMING"

            # Extraire le score si dispo
            score_home = m.get("score", {}).get("fullTime", {}).get("home")
            score_away = m.get("score", {}).get("fullTime", {}).get("away")

            predictions.append({
                "date": match_date_iso,
                "date_display": match_date_display,
                "time": match_time,
                "status": status,
                "status_display": status_display,
                "score_home": score_home,
                "score_away": score_away,
                "competition_code": comp_code,
                "competition_name": comp_name,
                "home": home,
                "away": away,
                "home_id": m["homeTeam"]["id"],
                "away_id": m["awayTeam"]["id"],
                "home_crest": m["homeTeam"].get("crest"),
                "away_crest": m["awayTeam"].get("crest"),
            })
        except (KeyError, TypeError) as e:
            continue
    return predictions
