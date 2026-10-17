import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPTS = {
    "fr": """Tu es un analyste football professionnel.
On te donne des donnees statistiques precises sur un match a venir :
- les probabilites calculees par un modele Dixon-Coles
- les buts attendus (xG)
- la forme recente des 2 equipes (5 derniers matchs)
- les confrontations directes recentes

Redige un commentaire de 3-4 phrases MAXIMUM, en FRANCAIS, professionnel et neutre.
Croise les donnees : la forme recente confirme-t-elle ou nuance-t-elle les probabilites ?

Regles strictes :
- Ne fais AUCUNE prediction personnelle, tu commentes uniquement les donnees.
- Ne mentionne JAMAIS les paris sportifs, ne donne AUCUN conseil de mise.
- Ne calcule PAS toi-meme. Utilise uniquement les chiffres fournis.
- Termine toujours ta phrase, ne la coupe jamais.
- Sois concis, va droit au but.""",

    "en": """You are a professional football analyst.
You receive precise statistical data about an upcoming match:
- probabilities from a Dixon-Coles model
- expected goals (xG)
- recent form of both teams (last 5 matches)
- recent head-to-head results

Write a commentary of 3-4 sentences MAXIMUM, in ENGLISH, professional and neutral.
Cross-reference the data: does the recent form confirm or nuance the probabilities?

Strict rules:
- Do NOT make any personal prediction, you only comment the given data.
- NEVER mention sports betting, never give any betting advice.
- Do NOT calculate yourself. Use only the provided numbers.
- Always finish your sentence, never cut it off.
- Be concise, get to the point.""",

    "sw": """Wewe ni mchambuzi wa mpira wa kitaalamu.
Unapokea data sahihi ya kitakwimu kuhusu mechi ijayo:
- uwezekano kutoka modeli ya Dixon-Coles
- magoli yanayotarajiwa (xG)
- hali ya hivi karibuni ya timu zote mbili (mechi 5 zilizopita)
- matokeo ya hivi karibuni ya uso kwa uso

Andika uchambuzi wa sentensi 3-4 KWA UPELEKevu, kwa KISWAHILI, wa kitaalamu na usioegemea upande.
Changanua data: hali ya hivi karibuni inathibitisha au inabadilisha uwezekano?

Sheria kali:
- USITOE utabiri wa kibinafsi, unachambua data tu.
- USITAJE kamwe kuweka fedha, usitoe ushauri wa kuweka fedha.
- USIhesabu mwenyewe. Tumia namba zilizotolewa tu.
- Kamilisha sentensi yako kila wakati, usiikate.
- Kuwa mfupi, nenda moja kwa moja.""",
}


def generate_commentary(home, away, prob_home, prob_draw, prob_away,
                        xg_home, xg_away, form_home, form_away, h2h,
                        lang="en"):
    total_xg = round(xg_home + xg_away, 2)

    form_home_txt = "\n".join(f"  - {r}" for r in form_home["results"]) or "  (no data)"
    form_away_txt = "\n".join(f"  - {r}" for r in form_away["results"]) or "  (no data)"
    h2h_txt = "\n".join(f"  - {r}" for r in h2h["results"]) or "  (no recent head-to-head)"

    if lang == "fr":
        prompt = f"""Match : {home} vs {away}

Probabilites du modele :
- Victoire {home} : {prob_home}%
- Match nul : {prob_draw}%
- Victoire {away} : {prob_away}%

Buts attendus (xG) :
- {home} : {xg_home}
- {away} : {xg_away}
- Total : {total_xg}

Forme recente {home} ({form_home["summary"]}) :
{form_home_txt}

Forme recente {away} ({form_away["summary"]}) :
{form_away_txt}

Confrontations directes :
{h2h_txt}

Redige le commentaire d'analyse en 3-4 phrases MAXIMUM."""
        system = SYSTEM_PROMPTS["fr"]
    elif lang == "sw":
        prompt = f"""Mechi: {home} vs {away}

Uwezekano wa modeli:
- {home} kushinda: {prob_home}%
- Sare: {prob_draw}%
- {away} kushinda: {prob_away}%

Magoli yanayotarajiwa (xG):
- {home}: {xg_home}
- {away}: {xg_away}
- Jumla: {total_xg}

Hali ya hivi karibuni {home} ({form_home["summary"]}):
{form_home_txt}

Hali ya hivi karibuni {away} ({form_away["summary"]}):
{form_away_txt}

Uso kwa uso:
{h2h_txt}

Andika uchambuzi kwa sentensi 3-4 KWA UPELEKevu."""
        system = SYSTEM_PROMPTS["sw"]
    else:
        prompt = f"""Match: {home} vs {away}

Model probabilities:
- {home} win: {prob_home}%
- Draw: {prob_draw}%
- {away} win: {prob_away}%

Expected goals (xG):
- {home}: {xg_home}
- {away}: {xg_away}
- Total: {total_xg}

Recent form {home} ({form_home["summary"]}):
{form_home_txt}

Recent form {away} ({form_away["summary"]}):
{form_away_txt}

Head-to-head:
{h2h_txt}

Write the analysis commentary in 3-4 sentences MAXIMUM."""
        system = SYSTEM_PROMPTS["en"]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=700,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return ""
