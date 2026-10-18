from fastapi import FastAPI, Request, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.model import predict_upcoming, analyze_single_match
from app.data import COMPETITIONS, COMPETITION_FLAGS, get_team_details, get_team_form, get_head_to_head, get_todays_matches, get_upcoming_matches_all, get_all_teams
from app.i18n import LANGUAGES, FLAGS, get_all

app = FastAPI(title="SOKADATA")
templates = Jinja2Templates(directory="app/templates")


def get_lang(request: Request) -> str:
    """Recupere la langue depuis le cookie, defaut 'en'."""
    lang = request.cookies.get("lang", "en")
    if lang not in LANGUAGES:
        lang = "en"
    return lang


def get_theme(request: Request) -> str:
    """Recupere le theme depuis le cookie, defaut 'dark'."""
    theme = request.cookies.get("theme", "dark")
    if theme not in ("dark", "light"):
        theme = "dark"
    return theme


def base_context(request: Request):
    lang = get_lang(request)
    theme = get_theme(request)
    return {
        "request": request,
        "competitions": COMPETITIONS,
        "languages": LANGUAGES,
        "lang_flags": FLAGS,
        "current_lang": lang,
        "current_theme": theme,
        "t": get_all(lang),
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Page d'accueil : matchs du jour sur toutes les ligues."""
    from app.model import predict_matches_list

    todays = get_todays_matches()
    display_matches = todays
    section_label = "MATCHS DU JOUR"
    is_today = True

    # Si aucun match aujourd'hui, on prend les 3 prochains jours
    if not todays:
        upcoming = get_upcoming_matches_all(days_ahead=3)
        display_matches = upcoming[:20]
        section_label = "PROCHAINS MATCHS"
        is_today = False

    # Filtrer sur nos 11 competitions supportees
    supported_codes = set(COMPETITIONS.keys())
    display_matches = [
        m for m in display_matches
        if m.get("competition", {}).get("code") in supported_codes
    ]

    # Trier par date/heure
    display_matches = sorted(display_matches, key=lambda m: m.get("utcDate", ""))
    display_matches = display_matches[:30]

    try:
        predictions = predict_matches_list(display_matches)
    except Exception as e:
        predictions = []
        print(f"Erreur home : {e}")

    # Compter les lives
    live_count = sum(1 for p in predictions if p.get("status") in ("IN_PLAY", "PAUSED"))

    ctx = base_context(request)
    ctx.update({
        "predictions": predictions,
        "selected": None,
        "selected_name": None,
        "selected_flag": "",
        "search": "",
        "is_home": True,
        "section_label": section_label,
        "is_today": is_today,
        "live_count": live_count,
    })
    return templates.TemplateResponse("index.html", ctx)


@app.get("/analyze/{competition_code}", response_class=HTMLResponse)
def analyze(request: Request, competition_code: str, q: str = Query("", alias="q")):
    if competition_code not in COMPETITIONS:
        raise HTTPException(status_code=404, detail="Competition inconnue")
    try:
        predictions = predict_upcoming(competition_code, limit=20)
    except Exception as e:
        predictions = []
        print(f"Erreur : {e}")

    if q:
        q_lower = q.lower()
        predictions = [
            p for p in predictions
            if q_lower in p["home"].lower() or q_lower in p["away"].lower()
        ]

    ctx = base_context(request)
    ctx.update({
        "predictions": predictions,
        "selected": competition_code,
        "selected_name": COMPETITIONS[competition_code],
        "selected_flag": COMPETITION_FLAGS.get(competition_code, ""),
        "is_home": False,
        "section_label": COMPETITIONS[competition_code].upper(),
        "is_today": False,
        "search": q,
    })
    return templates.TemplateResponse("index.html", ctx)


@app.get("/analyze/{competition_code}/comment/{match_index}")
def comment(competition_code: str, match_index: int, request: Request):
    if competition_code not in COMPETITIONS:
        raise HTTPException(status_code=404, detail="Competition inconnue")

    # VÉRIFICATION PREMIUM
    is_premium = request.cookies.get("premium_access") == "true"
    if not is_premium:
        raise HTTPException(status_code=403, detail="premium_required")

    try:
        predictions = predict_upcoming(competition_code, limit=20)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur prediction: {e}")

    if match_index < 0 or match_index >= len(predictions):
        raise HTTPException(status_code=404, detail="Match introuvable")

    match = predictions[match_index]
    lang = get_lang(request)

    try:
        commentary = analyze_single_match(match, lang=lang)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur IA: {e}")

    return JSONResponse({"commentary": commentary})


@app.get("/compare", response_class=HTMLResponse)
def compare_page(request: Request, team1: int = Query(0), team2: int = Query(0)):
    """Page de comparaison de 2 equipes."""
    ctx = base_context(request)
    ctx.update({
        "team1": None,
        "team2": None,
        "form1": None,
        "form2": None,
        "h2h": None,
        "all_teams": get_all_teams(),
    })

    if team1 and team2:
        details1 = get_team_details(team1)
        details2 = get_team_details(team2)

        if details1 and details2:
            name1 = details1.get("shortName") or details1.get("name")
            name2 = details2.get("shortName") or details2.get("name")

            ctx["team1"] = details1
            ctx["team2"] = details2
            ctx["form1"] = get_team_form(team1, name1, limit=5)
            ctx["form2"] = get_team_form(team2, name2, limit=5)
            ctx["h2h"] = get_head_to_head(team1, team2, name1, name2, limit=5)

    return templates.TemplateResponse("compare.html", ctx)


@app.get("/team/{team_id}", response_class=HTMLResponse)
def team_page(request: Request, team_id: int, from_comp: str = Query("", alias="from")):
    details = get_team_details(team_id)
    if not details:
        raise HTTPException(status_code=404, detail="Equipe introuvable")

    team_name = details.get("name", "Unknown")
    team_short = details.get("shortName", team_name)
    form = get_team_form(team_id, team_short, limit=5)

    ctx = base_context(request)
    ctx.update({
        "team": details,
        "team_name": team_name,
        "team_short": team_short,
        "team_form": form,
        "from_comp": from_comp,
    })
    return templates.TemplateResponse("team.html", ctx)


@app.get("/set-theme/{theme}")
def set_theme(theme: str, request: Request):
    """Change le theme via cookie et redirige vers la page precedente."""
    from fastapi.responses import RedirectResponse
    if theme not in ("dark", "light"):
        theme = "dark"
    referer = request.headers.get("referer", "/")
    response = RedirectResponse(url=referer, status_code=303)
    response.set_cookie("theme", theme, max_age=60*60*24*365)
    return response


@app.get("/set-lang/{lang}")
def set_lang(lang: str, request: Request):
    """Change la langue via cookie et redirige vers la page precedente."""
    from fastapi.responses import RedirectResponse
    if lang not in LANGUAGES:
        lang = "en"
    referer = request.headers.get("referer", "/")
    response = RedirectResponse(url=referer, status_code=303)
    response.set_cookie("lang", lang, max_age=60*60*24*365)
    return response

@app.get("/premium", response_class=HTMLResponse)
def premium_page(request: Request):
    ctx = base_context(request)
    return templates.TemplateResponse("premium.html", ctx)


@app.post("/api/verify-code")
def verify_code(request: Request, payload: dict):
    VALID_CODES = ["SOKA2026", "PREMIUM100", "TANZANIA10", "SOKADATA-VIP"]
    code = payload.get("code", "").strip().upper()
    
    if code in VALID_CODES:
        from fastapi.responses import JSONResponse
        response = JSONResponse({"success": True})
        response.set_cookie("premium_access", "true", max_age=60*60*24*30)
        return response
    
    from fastapi.responses import JSONResponse
    return JSONResponse({"success": False})
