import os
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

COMPETITIONS = {
    "PL": "Premier League",
    "ELC": "Championship",
    "FL1": "Ligue 1",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    "PD": "La Liga",
    "DED": "Eredivisie",
    "PPL": "Primeira Liga",
    "BSA": "Brasileirao",
    "CL": "Champions League",
    "CLI": "Copa Libertadores",
}

COMPETITION_FLAGS = {
    "ELC": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "BSA": "🇧🇷",
    "CLI": "🌎",
    "PL": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "FL1": "🇫🇷",
    "BL1": "🇩🇪",
    "SA": "🇮🇹",
    "PD": "🇪🇸",
    "DED": "🇳🇱",
    "PPL": "🇵🇹",
    "CL": "🇪🇺",
}


def _fetch_matches(competition_code, status, season=None):
    url = f"{BASE_URL}/competitions/{competition_code}/matches"
    params = {"status": status}
    if season:
        params["season"] = season
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if r.status_code != 200:
        print(f"ERREUR API {r.status_code}: {r.text[:200]}")
        return []
    return r.json().get("matches", [])


def get_finished_matches(competition_code):
    current_season = datetime.now().year
    previous_season = current_season - 1

    current = _fetch_matches(competition_code, "FINISHED", season=current_season)
    previous = _fetch_matches(competition_code, "FINISHED", season=previous_season)

    seen_ids = set()
    all_matches = []
    for m in current + previous:
        mid = m.get("id")
        if mid not in seen_ids:
            seen_ids.add(mid)
            all_matches.append(m)

    print(f"[DATA] {current_season}: {len(current)} | {previous_season}: {len(previous)} | Total unique: {len(all_matches)}")
    return all_matches


def get_upcoming_matches(competition_code):
    return _fetch_matches(competition_code, "SCHEDULED")


def get_team_form(team_id, team_name, limit=5):
    """Retourne les N derniers resultats d'une equipe + bilan."""
    url = f"{BASE_URL}/teams/{team_id}/matches"
    params = {"status": "FINISHED", "limit": limit}
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if r.status_code != 200:
        return {"name": team_name, "results": [], "summary": "Donnees indisponibles"}

    matches = r.json().get("matches", [])[-limit:]
    results = []
    wins = draws = losses = 0
    goals_for = goals_against = 0

    for m in matches:
        home_id = m["homeTeam"]["id"]
        hg = m["score"]["fullTime"]["home"]
        ag = m["score"]["fullTime"]["away"]
        if hg is None or ag is None:
            continue

        if home_id == team_id:
            gf, ga = hg, ag
            opp = m["awayTeam"]["shortName"] or m["awayTeam"]["name"]
            where = "dom"
        else:
            gf, ga = ag, hg
            opp = m["homeTeam"]["shortName"] or m["homeTeam"]["name"]
            where = "ext"

        if gf > ga:
            res = "V"; wins += 1
        elif gf < ga:
            res = "D"; losses += 1
        else:
            res = "N"; draws += 1

        goals_for += gf
        goals_against += ga
        results.append(f"{res} {gf}-{ga} vs {opp} ({where})")

    summary = f"{wins}V {draws}N {losses}D, {goals_for} buts marques, {goals_against} encaisses"
    return {"name": team_name, "results": results, "summary": summary}


def get_head_to_head(team1_id, team2_id, team1_name, team2_name, limit=3):
    """Retourne les N derniers face-a-face entre 2 equipes."""
    url = f"{BASE_URL}/teams/{team1_id}/matches"
    params = {"status": "FINISHED", "limit": 50}
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if r.status_code != 200:
        return {"summary": "Donnees indisponibles", "results": []}

    all_matches = r.json().get("matches", [])
    h2h = []
    for m in all_matches:
        home_id = m["homeTeam"]["id"]
        away_id = m["awayTeam"]["id"]
        if {home_id, away_id} == {team1_id, team2_id}:
            h2h.append(m)
        if len(h2h) >= limit:
            break

    results = []
    for m in h2h:
        home = m["homeTeam"]["shortName"] or m["homeTeam"]["name"]
        away = m["awayTeam"]["shortName"] or m["awayTeam"]["name"]
        hg = m["score"]["fullTime"]["home"]
        ag = m["score"]["fullTime"]["away"]
        date = m["utcDate"][:10]
        results.append(f"{date} : {home} {hg}-{ag} {away}")

    summary = f"{len(results)} confrontation(s) recente(s)" if results else "Aucune confrontation recente"
    return {"summary": summary, "results": results}

def get_team_crest(team_id):
    """Recupere l URL du logo d une equipe via l API."""
    url = f"{BASE_URL}/teams/{team_id}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        return None
    return r.json().get("crest")

def get_team_details(team_id):
    """Recupere les details complets d'une equipe."""
    url = f"{BASE_URL}/teams/{team_id}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        return None
    data = r.json()

    # Enrichir chaque joueur avec son drapeau
    for player in data.get('squad', []):
        player['flag'] = get_flag(player.get('nationality'))

    return data

NATIONALITY_FLAGS = {
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "Northern Ireland": "🇬🇧",
    "France": "🇫🇷",
    "Spain": "🇪🇸",
    "Portugal": "🇵🇹",
    "Italy": "🇮🇹",
    "Germany": "🇩🇪",
    "Netherlands": "🇳🇱",
    "Belgium": "🇧🇪",
    "Brazil": "🇧🇷",
    "Argentina": "🇦🇷",
    "Uruguay": "🇺🇾",
    "Colombia": "🇨🇴",
    "Chile": "🇨🇱",
    "Mexico": "🇲🇽",
    "United States": "🇺🇸",
    "Canada": "🇨🇦",
    "Japan": "🇯🇵",
    "South Korea": "🇰🇷",
    "China": "🇨🇳",
    "Australia": "🇦🇺",
    "Nigeria": "🇳🇬",
    "Ghana": "🇬🇭",
    "Senegal": "🇸🇳",
    "Ivory Coast": "🇨🇮",
    "Cameroon": "🇨🇲",
    "Morocco": "🇲🇦",
    "Algeria": "🇩🇿",
    "Egypt": "🇪🇬",
    "Tunisia": "🇹🇳",
    "South Africa": "🇿🇦",
    "Kenya": "🇰🇪",
    "Tanzania": "🇹🇿",
    "Uganda": "🇺🇬",
    "Zimbabwe": "🇿🇼",
    "Mali": "🇲🇱",
    "Burkina Faso": "🇧🇫",
    "Guinea": "🇬🇳",
    "Croatia": "🇭🇷",
    "Serbia": "🇷🇸",
    "Poland": "🇵🇱",
    "Czech Republic": "🇨🇿",
    "Czechia": "🇨🇿",
    "Austria": "🇦🇹",
    "Switzerland": "🇨🇭",
    "Denmark": "🇩🇰",
    "Sweden": "🇸🇪",
    "Norway": "🇳🇴",
    "Finland": "🇫🇮",
    "Ireland": "🇮🇪",
    "Republic of Ireland": "🇮🇪",
    "Turkey": "🇹🇷",
    "Greece": "🇬🇷",
    "Russia": "🇷🇺",
    "Ukraine": "🇺🇦",
    "Haiti": "🇭🇹",
    "Jamaica": "🇯🇲",
    "Costa Rica": "🇨🇷",
    "Peru": "🇵🇪",
    "Ecuador": "🇪🇨",
    "Paraguay": "🇵🇾",
    "Venezuela": "🇻🇪",
    "Bolivia": "🇧🇴",
}


def get_flag(nationality):
    """Retourne le drapeau emoji d'une nationalite."""
    if not nationality:
        return ""
    return NATIONALITY_FLAGS.get(nationality, "🏳️")

def get_todays_matches():
    """Recupere tous les matchs du jour sur toutes les competitions."""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    url = f"{BASE_URL}/matches"
    params = {"dateFrom": today, "dateTo": today}
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if r.status_code != 200:
        print(f"[TODAY] Erreur API {r.status_code}")
        return []
    return r.json().get("matches", [])


def get_upcoming_matches_all(days_ahead=7):
    """Recupere les prochains matchs sur toutes les competitions."""
    from datetime import datetime, timedelta
    today = datetime.now().strftime("%Y-%m-%d")
    future = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    url = f"{BASE_URL}/matches"
    params = {"dateFrom": today, "dateTo": future, "status": "SCHEDULED"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if r.status_code != 200:
        print(f"[UPCOMING] Erreur API {r.status_code}")
        return []
    return r.json().get("matches", [])

def get_all_teams():
    """Recupere toutes les equipes des 11 competitions supportees (avec cache)."""
    import time
    import json

    cache_file = Path.home() / "football-ai" / "teams_cache.json"

    # Si le cache existe et date de moins de 24h, on le lit
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < 86400:  # 24 heures
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[TEAMS] Erreur lecture cache: {e}")

    # Sinon, on appelle l'API
    all_teams = {}
    for code in COMPETITIONS.keys():
        url = f"{BASE_URL}/competitions/{code}/teams"
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 429:
            print(f"[TEAMS] Limite API atteinte pour {code}, pause de 6s...")
            time.sleep(6)
            r = requests.get(url, headers=HEADERS, timeout=30)
            
        if r.status_code != 200:
            print(f"[TEAMS] Erreur {r.status_code} pour {code}")
            continue
            
        for t in r.json().get('teams', []):
            tid = t.get('id')
            if tid and tid not in all_teams:
                all_teams[tid] = {
                    'id': tid,
                    'name': t.get('name'),
                    'shortName': t.get('shortName') or t.get('name'),
                    'tla': t.get('tla', ''),
                    'crest': t.get('crest'),
                    'country': t.get('area', {}).get('name', ''),
                    'competition': COMPETITIONS[code],
                }
    result = sorted(all_teams.values(), key=lambda x: x['shortName'] or '')

    # Sauvegarder dans le cache
    try:
        with open(cache_file, "w") as f:
            json.dump(result, f)
        print(f"[TEAMS] Cache sauvegarde: {len(result)} equipes")
    except Exception as e:
        print(f"[TEAMS] Erreur ecriture cache: {e}")

    return result
