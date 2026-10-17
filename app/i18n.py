"""Systeme de traduction simple FR / EN / SW."""

LANGUAGES = {
    "fr": "Francais",
    "en": "English",
    "sw": "Kiswahili",
}

FLAGS = {
    "fr": "FR",
    "en": "EN",
    "sw": "SW",
}

TRANSLATIONS = {
    "fr": {
        "hero_label": "Analyse football · IA · Statistiques",
        "hero_title_1": "SOKA",
        "hero_title_2": "DATA",
        "hero_subtitle": "Predictions statistiques avancees et analyses generees par intelligence artificielle sur les plus grands championnats europeens.",
        "stat_leagues": "Ligues",
        "stat_model": "Modele",
        "stat_ai": "IA",
        "search_placeholder": "Rechercher une equipe - PSG, Marseille, Real...",
        "section_matches": "matchs",
        "btn_analyze": "Analyser avec l'IA",
        "btn_loading": "Analyse en cours...",
        "btn_retry": "Reessayer",
        "btn_error": "Erreur, reessayer",
        "empty_no_match": "Aucun match pour",
        "empty_no_data": "Aucune prediction disponible",
        "empty_select": "Selectionnez un championnat",
        "ai_label": "Analyse IA",
        "disclaimer": "Outil d'analyse statistique a visee educative et informative. Ne constitue pas un service de pronostics sportifs. Aucun pari n'est encourage. Les probabilites sont issues d'un modele mathematique et ne garantissent aucun resultat.",
    },
    "en": {
        "hero_label": "Football analysis · AI · Statistics",
        "hero_title_1": "SOKA",
        "hero_title_2": "DATA",
        "hero_subtitle": "Advanced statistical predictions and AI-generated analysis across Europe's biggest football leagues.",
        "stat_leagues": "Leagues",
        "stat_model": "Model",
        "stat_ai": "AI",
        "search_placeholder": "Search a team - PSG, Marseille, Real...",
        "section_matches": "matches",
        "btn_analyze": "Analyze with AI",
        "btn_loading": "Analyzing...",
        "btn_retry": "Retry",
        "btn_error": "Error, retry",
        "empty_no_match": "No match for",
        "empty_no_data": "No prediction available",
        "empty_select": "Select a league",
        "ai_label": "AI Analysis",
        "disclaimer": "Statistical analysis tool for educational and informational purposes. Not a sports betting advisory service. No betting is encouraged. Probabilities are produced by a mathematical model and do not guarantee any outcome.",
    },
    "sw": {
        "hero_label": "Uchambuzi wa mpira · AI · Takwimu",
        "hero_title_1": "SOKA",
        "hero_title_2": "DATA",
        "hero_subtitle": "Utabiri wa kina wa kitakwimu na uchambuzi uliotengenezwa na akili bandia katika ligi kuu za Ulaya.",
        "stat_leagues": "Ligi",
        "stat_model": "Modeli",
        "stat_ai": "AI",
        "search_placeholder": "Tafuta timu - PSG, Marseille, Real...",
        "section_matches": "mechi",
        "btn_analyze": "Changanua na AI",
        "btn_loading": "Inachanganua...",
        "btn_retry": "Jaribu tena",
        "btn_error": "Hitilafu, jaribu tena",
        "empty_no_match": "Hakuna mechi kwa",
        "empty_no_data": "Hakuna utabiri unaopatikana",
        "empty_select": "Chagua ligi",
        "ai_label": "Uchambuzi wa AI",
        "disclaimer": "Zana ya uchambuzi wa kitakwimu kwa madhumuni ya elimu na taarifa. Si huduma ya ushauri wa kuweka fedha. Hakuna kuweka fedha kunakohimizwa. Uwezekano unatokana na modeli ya kihisabati na hauhakikishi matokeo yoyote.",
    },
}


def get_text(key, lang="en"):
    """Retourne la traduction d'une cle pour la langue donnee."""
    if lang not in TRANSLATIONS:
        lang = "en"
    return TRANSLATIONS[lang].get(key, TRANSLATIONS["en"].get(key, key))


def get_all(lang="en"):
    """Retourne tout le dictionnaire pour une langue."""
    if lang not in TRANSLATIONS:
        lang = "en"
    return TRANSLATIONS[lang]
