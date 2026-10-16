"""Question -> plan (Apertus) -> live retrieval on three levels -> cited answer (Apertus, streamed)."""
import datetime as dt
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor

import apertus
import caselaw
import checks
import sources
import uploads
import communal
import lexfind_agent
import verify

LANG_NAMES = {"de": "Deutsch", "fr": "français", "it": "italiano", "rm": "rumantsch", "en": "English"}

PLAN_PROMPT = """You are the retrieval planner of a Swiss legal research tool. Swiss law has three levels:
federal (Bund, SR numbers on Fedlex), cantonal (26 cantons, own law collections) and communal (municipal regulations).

Return ONLY a JSON object, no prose:
{{
  "language": "de|fr|it|rm|en  (language of the user's question)",
  "clarified_question": "the question rewritten as a complete, unambiguous legal question in its own language, expanding abbreviations and fixing typos (e.g. 'permis c' -> 'Quelle est la procédure pour obtenir l'autorisation d'établissement (permis C) ?')",
  "topic": "3-6 word topic in the question's language",
  "levels": {{"federal": true/false, "cantonal": true/false, "communal": true/false}},
  "federal_refs": [{{"sr": "<SR number of a relevant federal act>", "articles": ["<at most 4 article numbers in THAT act that answer THIS question>"]}}],
  "federal_title_terms": ["1-3 SINGLE words in {fed_lang} that appear in titles of relevant federal acts"],
  "federal_keywords": ["5-10 SINGLE words in {fed_lang} likely to appear in the relevant federal article texts"],
  "cantonal_title_terms": ["1-3 SINGLE words in {can_lang} that appear in titles of relevant cantonal laws of {canton}"],
  "cantonal_keywords": ["5-10 SINGLE words in {can_lang} likely to appear in the relevant cantonal article texts"],
  "communal_keywords": ["3-8 SINGLE words in {can_lang} likely to appear in a communal regulation on this"],
  "competence": "One sentence in the question's language: how the levels share this topic (Art. 3 / Art. 49 BV)."
}}
federal_refs: 1-5 acts (include the implementing ordinance when the details are there, e.g. VZV next to SVG). "sr" is the act's SR number (220 = OR), NEVER an article number; put article numbers in "articles".
Federal law almost always sets a framework, so federal is true unless the topic is purely cantonal (e.g. cantonal tax rates, schools).
Examples: dogs → federal 455 (TSchG), 455.1 (TSchV) + cantonal dog law + communal leash/tax rules.
Tenancy → SR 220 (OR; e.g. notice periods art. 266c, rent arrears art. 257d), SR 221.213.11 (VMWG).
Employment → SR 220 (OR; e.g. overtime art. 321c, holidays art. 329a, probation art. 335b, dismissal art. 336c), SR 822.11 (ArG).
Building, zoning, solar panels → federal 700 (RPG/LAT), 700.1 (RPV/OAT) + cantonal building law + communal zoning.
Noise → 814.01 (USG), 814.41 (LSV) + cantonal police law + communal police regulation.
Data protection → 235.1 (DSG). Road traffic → SR 741.01 (SVG; e.g. drink-driving art. 91). Civil/family/inheritance → SR 210 (ZGB; e.g. compulsory share art. 471). Criminal → 311.0 (StGB).
Taxes → 642.11 (DBG), 642.14 (StHG) + cantonal tax law. Constitution → 101 (BV).
Foreign nationals / residence and work permits (permis B, C, L, G; Ausweis B/C; permesso B/C) → SR 142.20 (AIG/LEI/LStrI;
e.g. settlement permit C = Niederlassungsbewilligung / autorisation d'établissement art. 34, residence permit B = art. 33,
integration criteria art. 58a) and SR 142.201 (VZAE/OASA) + the canton's implementing law on foreign nationals
(e.g. "Loi d'application ... sur les étrangers", "Einführungsgesetz zum Ausländer- und Integrationsgesetz").
Citizenship / naturalisation → SR 141.0 (BüG/LN; e.g. 10 years' residence + permit C art. 9, integration art. 11-12),
141.01 (BüV/OLN; language level art. 6) + cantonal citizenship law + communal citizenship rules.
EU/EFTA nationals' permits and cross-border commuters (permis G) → also SR 0.142.112.681 (free-movement agreement, AFMP/FZA)
and 142.203 (VEP/OLCP).
Driving licences, learner permits, categories (permis C/C1 = lorry), medical checks, foreign licences → SR 741.51
(VZV/OAC; e.g. categories art. 3, learner permit validity art. 15, medical check from 75 art. 27, foreign licence art. 42).
Traffic rules, e-bikes, helmets, scooters, speed limits → SR 741.11 (VRV/OCR; e.g. speed limits art. 4a, helmet art. 3b),
741.01 (SVG/LCR; drink-driving art. 91, licence withdrawal art. 16a-16c), 741.41 (VTS/OETV) for vehicle types.
Social insurance: old-age pension AVS/AHV → SR 831.10 (AHVG; reference age art. 21); supplementary benefits → 831.30
(ELG/LPC); disability → 831.20 (IVG/LAI); unemployment → 837.0 (AVIG/LACI; contribution period art. 13); health insurance
→ 832.10 (KVG/LAMal; premium reductions art. 65) and 832.102 (KVV/OAMal; cross-border workers art. 1-6); accident →
832.20 (UVG/LAA); occupational pensions, home-ownership withdrawal → 831.40 (BVG/LPP; art. 30c) and 831.411 (WEFV);
family allowances → 836.2 (FamZG/LAFam); maternity leave → 834.1 (EOG/LAPG; art. 16b-16h) and OR art. 329f;
social assistance → cantonal social-assistance law.
Family: adoption of a stepchild → ZGB art. 264c; marriage age → ZGB art. 94; divorce → ZGB art. 111-114; custody →
ZGB art. 296-298; child maintenance → ZGB art. 276-277; inheritance → ZGB art. 457-462 (legal heirs), 470-471
(compulsory shares), 498-505 (wills); marriage contract → ZGB art. 184. Neighbours: ZGB art. 684 (nuisance, noise),
687 (overhanging branches); condominium (PPE/Stockwerkeigentum) → ZGB art. 712a-712t and 647-647e (works, majorities).
Tenancy details: deposit art. 257e, defects/rent reduction art. 259a-259d, small repairs art. 259, landlord visits
art. 257h, subletting art. 262, initial rent art. 270, retaliatory notice art. 271a, pets/care art. 257f.
Employment details: sick pay art. 324a, 13th salary art. 322d, non-compete art. 340-340c, summary dismissal
art. 337-337c, Sunday work ArG art. 18-19.
Criminal: secret filming StGB art. 179quater, recording calls art. 179bis-179ter, defamation/insult art. 173-177,
assault/slap art. 126, damage to property art. 144, complaint deadline 3 months art. 31.
Data protection: duty to inform DSG art. 19, data breach art. 24, right of access art. 25; private video surveillance
→ DSG art. 6, 30-31. Consumer: doorstep sales OR art. 40a-40f; warranty OR art. 197-210. Debt enforcement: SchKG (SR 281.1;
objection art. 74). Taxes: DBG/LIFD deductions art. 26-33a + cantonal tax law; wealth tax → cantonal tax law, StHG art. 13-14.
Never return empty lists: every Swiss legal question has at least one relevant federal act and search terms.
Same word, different subject: "permis" can mean a driving licence (SR 741.01), a building permit (SR 700) or a residence
permit (SR 142.20); choose the one the question means.
Use single words only (e.g. "Hunde", "Leine", not "Leinenpflicht für Hunde"); titles use nouns like "Bau", "Hunde", "Polizei", "Steuern", "constructions", "chiens", "police".

Question: {question}
Location: {location}"""

ANSWER_SYSTEM = """You are Alpenrecht AI, a Swiss legal information assistant built on Apertus.
You answer using ONLY the numbered sources the user gives you, retrieved live from Fedlex (federal), LexFind (cantonal), communal documents and entscheidsuche.ch (court decisions).

Citation style (strict):
- Every sentence that states a rule ends with its source number(s) in square brackets: [9] or [2][3].
- Do NOT write citations in prose like "(Art. 7 Abs. 1 lit. a Hundegesetz BE)" — write the rule, then [n].
- Never start a sentence, paragraph or bullet with [n].
Correct: "Auf Schulanlagen und in öffentlichen Verkehrsmitteln gilt eine Leinenpflicht [9]. Gemeinden können weitere Orte bezeichnen [9]."
Wrong: "[9] Art. 7 Leinenpflicht: ..." and "... gilt eine Leinenpflicht (Art. 7 Hundegesetz BE)."
You may name the act briefly before the bracket when it helps ("nach dem kantonalen Hundegesetz [9]").
Never name articles or acts that are not in the sources (no "Art. 80 BV" etc.) and never invent content.
Ignore sources that only share words with the question but concern another subject (a driving licence
"permis" says nothing about a residence "permis"; a building permit says nothing about a work permit).
One exception: you may mention the precedence of federal law, "Art. 49 BV" (Cst. in French, Cost. in Italian), without brackets."""

ANSWER_PROMPT = """Rules:
- Write everything in {language}, including headings.
- BE CONCRETE. The reader wants the actual rules, not a description of where rules exist. For THIS question, state
  the numbers (years, months, CHF amounts, percentages, times of day), deadlines, conditions (each one), exceptions,
  required documents, competent authority (by name) and procedural steps (in order) that the sources give.
- BE RELEVANT. Include only rules that answer this exact question. Drop rules about other situations even if they come
  from the same act (asked about getting a permit: no detention or removal rules; asked about rental deposits: no court
  deposits and no rent increases). A source about a different situation that shares a word is off-topic: skip it.
- Never write empty sentences that only say a law "regelt / legt fest / konkretisiert / regulates / applique /
  disciplina" something, or that a canton "can issue additional rules", unless the same sentence gives the content.
  Bad: "Das OR regelt die Höhe der Kaution [1]."  Good: "Bei Wohnungen darf die Kaution höchstens drei Monatszinse
  betragen und muss auf einem Konto auf den Namen des Mieters hinterlegt werden [1]."
- Use only the sources that answer the question; silently skip off-topic ones. Do not walk through the sources one by one.
- Do not repeat the same rule in several sections: put it under its level, and summarise it in the short answer.
- NEVER invent figures. Every number, deadline, amount, age, rate, address and authority name you write, also under
  "{h_next}", must appear in a cited source. If the sources give no deadline or fee, do not guess one: say it is not in
  the sources. Copy figures exactly (a rate "‰" is per mille, not percent; a minimum is not a maximum; a statute of
  limitation is not a deadline for filing a complaint).
- Paraphrase faithfully: "may/kann/peut/può" stays optional, a rule for one category (e.g. public employees,
  fast e-bikes, joint adoption) is not presented as the general rule.
- When the rule differs by situation (EU/EFTA vs other nationals, tenant vs owner, employee vs employer, private
  person vs public body, Swiss vs foreign licence), give each relevant case in one short bullet.
- Use a CANTONAL or COMMUNAL source under its level heading, with its concrete content (amounts, times, conditions),
  only if it states a rule for THIS question. A cantonal or communal provision on another matter (police rules on
  fires or posters for a permit question, a fee tariff for another kind of permit, public-staff rules for a private
  employee) is off-topic: skip it and write "{none}" for that level.
- If the question was short or ambiguous (see "Understood as"), begin the short answer with one clause saying how you
  understood it (e.g. "Assuming you mean the settlement permit C, …").
- If the sources do not cover something important, say so in one sentence and name where it would be regulated.
- "{h_next}": only steps a source supports (authority, form, deadline, fee from a cited source). If the sources
  name no authority or deadline, give one bullet saying which authority to ask, without any figure.
- Hard limit: 330 words. No filler; when space is short, keep figures and conditions, drop background.
- Use exactly these markdown headings:
  ## {h_short}   (2-4 sentences: the direct, concrete answer with the key figures and conditions)
  ## {h_fed}   (bullets: each concrete federal rule with its figures/conditions)
  ## {h_can}   (bullets: each concrete cantonal rule)
  ## {h_com}   (bullets: each concrete communal rule)
  ## {h_levels}   (ONE sentence: what the canton/commune adds to federal law, concretely; federal law prevails, Art. 49 BV)
  ## {h_next}   (2-5 bullets: concrete actions, with the authority, form, fee or deadline when the sources give them)
  Under a level heading without relevant sources, write only the plain sentence "{none}" (not a heading). Under
  "{h_levels}", do not repeat the generic Art. 49 BV sentence when there is no cantonal or communal rule: then say in
  one sentence that federal law applies directly. Use no other headings.
- Legal state as of {asof}. End with this italic line: *{disclaimer}*

Location: {location_line}

SOURCES
{sources}

QUESTION
{question}"""

HEADINGS = {
    "de": ("Kurzantwort", "Bund", "Kanton {canton}", "Gemeinde {commune}", "Zusammenspiel der Ebenen", "Nächste Schritte",
           "Rechtsinformation, keine Rechtsberatung.", "Keine einschlägige Quelle abgerufen.",
           "Rechtsprechung"),
    "fr": ("Réponse courte", "Confédération", "Canton de {canton}", "Commune de {commune}", "Articulation des niveaux",
           "Prochaines étapes", "Information juridique, pas un conseil juridique.", "Aucune source pertinente récupérée.",
           "Jurisprudence"),
    "it": ("Risposta breve", "Confederazione", "Cantone {canton}", "Comune di {commune}", "Interazione dei livelli",
           "Prossimi passi", "Informazione giuridica, non consulenza legale.", "Nessuna fonte pertinente recuperata.",
           "Giurisprudenza"),
    "rm": ("Resposta curta", "Confederaziun", "Chantun {canton}", "Vischnanca {commune}", "Interacziun dals nivels",
           "Proxims pass", "Infurmaziun giuridica, nagin cussegl giuridic.", "Nagina funtauna relevanta chattada.",
           "Giurisprudenza"),
    "en": ("Short answer", "Federal level", "Canton {canton}", "Commune {commune}", "How the levels fit together",
           "Next steps", "Legal information, not legal advice.", "No relevant source retrieved.", "Case law"),
}

MAX_FED_ACTS = 5
VERIFY_ROUNDS = 3
MAX_CAN_TEXTS = 3
PER_ACT = 4
TOTAL_FED = 8
TOTAL_CAN = 6
TOTAL_COM = 5


STOPWORDS = set("""
aber alle auch dass dem den der des die dies diese dieser durch eine einem einen einer eines habe haben
hat ich ihn ihr immer kann kein keine man mein meine meinen meiner meines mich mir muss müssen nach nicht
oder sein seine sich sie sind soll über und uns unter vom von was weil welche welcher wenn werden wie wird
wir zum zur darf dürfen gibt gilt gelten brauche benötige
alors avec avoir dans des doit dois est être faut leur mais mes mon mes nos notre nous par pas peut pour
quel quelle quelles quels qui que sans ses son sont sur une vos votre vous
anche alla alle come con del della delle devo dei gli hanno nel nella non per può quale quali sono una
about does have must need should that the their there this what when where which will with your
""".split())


def _words(question):
    return [w for w in re.findall(r"[^\W\d_]{4,}", question) if w.lower() not in STOPWORDS]


LANG_MARKERS = {
    "de": "der die das und ich ist nicht mein meine meinen muss darf wie was wer wann für mit auf ein eine einer werden",
    "fr": "le la les des un une et est je mon ma mes que qui pour dans sur pas faut quel quelle quels peut",
    "it": "il lo la gli le un una e è che di per con non sono mi mio mia quali quale devo posso spettano",
    "en": "the a an and is are i my me to of for in on can do does which what who how must should it",
    # Only words Italian doesn't share: "il", "che", "per", "mia" made an Italian question look Romansh.
    "rm": "ils las ina cun betg jau tge dovrel stoss sin quai nus vus vossa vischnanca",
}
_MARKERS = {k: set(v.split()) for k, v in LANG_MARKERS.items()}


def detect_lang(text):
    """Pick the language with clearly the most function-word hits; None when unsure."""
    words = re.findall(r"[a-zàâçéèêëîïôûùüÿñæœäöß']+", text.lower())
    scores = sorted(((sum(w in m for w in words), k) for k, m in _MARKERS.items()), reverse=True)
    (best, lang), (second, _) = scores[0], scores[1]
    return lang if best >= 2 and best > second else None


def parse_plan(text):
    """Planner JSON, tolerating what Apertus actually emits: stray braces, trailing commas, runaway lists."""
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            return json.loads(re.sub(r",\s*([}\]])", r"\1", m.group(0)))
        except ValueError:
            pass
    # Salvage field by field.
    plan = {}
    for key in ("language", "topic", "competence"):
        f = re.search(rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
        if f:
            plan[key] = f.group(1)
    for key in ("federal_title_terms", "federal_keywords", "cantonal_title_terms", "cantonal_keywords", "communal_keywords"):
        f = re.search(rf'"{key}"\s*:\s*\[([^\]]*)', text)
        if f:
            plan[key] = re.findall(r'"([^"]+)"', f.group(1))[:12]
    plan["federal_refs"] = [
        {"sr": sr, "articles": re.findall(r'"([^"]+)"', arts)[:4]}
        for sr, arts in re.findall(r'"sr"\s*:\s*"([\d.]+)"\s*,\s*"articles"\s*:\s*\[([^\]]*)', text)][:4]
    lv = re.search(r'"levels"\s*:\s*\{([^}]*)\}', text)
    plan["levels"] = {k: v == "true" for k, v in re.findall(r'"(\w+)"\s*:\s*(true|false)', lv.group(1))} if lv else {}
    if not (plan.get("federal_refs") or plan.get("federal_keywords") or plan.get("cantonal_keywords")):
        raise ValueError(f"unparseable plan: {text[:120]}")
    return plan


_ENDINGS = ("en", "es", "er", "e", "n", "s", "i", "a", "o")


def _title_stem(word):
    """Search stem for a title word: 'Schulpflicht' -> 'schul', 'Steuern' -> 'steue', 'chiens' -> 'chien'."""
    w = word.lower().strip("*")
    if len(w) >= 7:
        return w[:5]
    for end in _ENDINGS:
        if w.endswith(end) and len(w) - len(end) >= 3:
            return w[:-len(end)]
    return w


NOISE_WORDS = set("""
kanton kantons kantonal kantonale canton cantonal cantonale cantone cantonale gemeinde gemeinden commune communes
comune comuni schweiz suisse svizzera bund bewilligung bewilligungen autorisation autorizzazione gesetz gesetze
loi lois legge leggi verordnung reglement regeln regles regole pflicht pflichten obligation obligations
""".split())

_MAIN_ACT = ("gesetz", "loi", "legge", "lescha", "kantonsverfassung", "constitution", "costituzione")


def _text_rank(tol, stems):
    """Topic overlap + 'is this the main act?': formal law, short title, not a directive or agreement."""
    title = sources.fold(tol["title"])
    category = sources.fold(tol.get("category", ""))
    overlap = sum(s in title for s in stems if len(s) >= 3)
    if not overlap:
        return -100.0  # off-topic, however "main" it looks
    score = 2.0 * overlap
    if any(category.startswith(c) for c in ("gesetz", "loi", "legge")):
        score += 3
    elif category.startswith(("verordnung", "ordonnance", "regolamento", "reglement", "règlement")):
        score += 1
    if any(m in title.split()[0] for m in _MAIN_ACT) if title.split() else False:
        score += 2  # "Steuergesetz", "Loi sur les chiens"
    score += 2 if len(title) <= 45 else (1 if len(title) <= 80 else 0)
    if category.startswith(("interkant", "intercant", "anderes", "autre", "altro")):
        score -= 2
    return score


def _federal_refs(plan):
    """{sr: {article keys}} from the planner; tolerates the older flat "federal_sr" list."""
    refs = {}
    for ref in plan.get("federal_refs") or []:
        if isinstance(ref, dict):
            sr = str(ref.get("sr", "")).strip()
            if re.fullmatch(r"\d+(?:\.\d+)*", sr):
                refs.setdefault(sr, set()).update(checks.art_key(str(a)) for a in ref.get("articles") or [] if str(a).strip())
    for sr in plan.get("federal_sr") or []:
        sr = str(sr).strip()
        if re.fullmatch(r"\d+(?:\.\d+)*", sr):
            refs.setdefault(sr, set())
    return refs


def _fallback_plan(question, location):
    words = _words(question)
    # German nouns are capitalised: "Hund", "Leine" beat verbs like "führen" as title terms.
    first = question.split()[0] if question.split() else ""
    nouns = [w for w in words if w[0].isupper() and w != first]
    titles = (nouns or sorted(words, key=len, reverse=True))[:2]
    return {"language": "", "topic": question[:40], "levels": {"federal": True, "cantonal": bool(location),
            "communal": bool(location)}, "federal_refs": [], "federal_title_terms": titles,
            "federal_keywords": words, "cantonal_title_terms": titles, "cantonal_keywords": words,
            "communal_keywords": words, "competence": "", "fallback": True}


def run(question, location_text="", asof=None, lang_hint="", upload_ids=()):
    """Generator of events for the UI: step / plan / location / sources / token / done / error."""
    t0 = time.time()
    asof = asof or dt.date.today().isoformat()

    def step(key, label, status="running", **extra):
        return {"type": "step", "key": key, "label": label, "status": status, **extra}

    # 1. location -------------------------------------------------------------------------------
    location = None
    if location_text.strip():
        yield step("loc", "Locating commune and canton (swisstopo)")
        try:
            location = sources.resolve_location(location_text)
        except Exception as e:  # network trouble shouldn't kill the answer
            yield step("loc", f"Location lookup failed: {e}", "warn")
        if location:
            yield {"type": "location", "location": location}
            yield step("loc", f"{location['commune']} · {location['canton_name']} ({location['canton']}) · BFS {location['bfs']}", "done")
        else:
            yield step("loc", f"No Swiss location found for “{location_text}”", "warn")

    canton = location["canton"] if location else None
    can_langs = location["canton_languages"] if location else ["de"]

    # 2. plan -----------------------------------------------------------------------------------
    yield step("plan", "Apertus plans the search across levels")
    fed_lang = lang_hint if lang_hint in ("de", "fr", "it") else "de"
    can_lang = lang_hint if lang_hint in can_langs else can_langs[0]
    loc_line = (f"{location['commune']}, canton {location['canton_name']} ({canton}), "
                f"official languages {', '.join(can_langs)}") if location else "unknown (federal only)"
    try:
        plan_msg = PLAN_PROMPT.format(
            question=question, location=loc_line, fed_lang=LANG_NAMES[fed_lang],
            can_lang=LANG_NAMES[can_lang], canton=location["canton_name"] if location else "the canton")
        plan = parse_plan(apertus.chat([{"role": "user", "content": plan_msg}], temperature=0.0, max_tokens=800))
        if not (plan.get("federal_refs") or plan.get("federal_keywords") or plan.get("cantonal_title_terms")):
            # An empty plan means a blind search (a "permis C" question once landed in the road-traffic law): ask again.
            plan = parse_plan(apertus.chat([
                {"role": "user", "content": plan_msg},
                {"role": "assistant", "content": json.dumps(plan, ensure_ascii=False)},
                {"role": "user", "content": "Your lists are empty. Fill federal_refs (SR number + articles), the title "
                                            "terms and the keywords for this exact legal subject. Return the full JSON."}],
                temperature=0.2, max_tokens=800)) or plan
    except (apertus.ApertusError, ValueError) as e:
        # Keep retrieving even without the model: the sources alone are still useful.
        yield step("plan", f"Planner unavailable, using keywords ({str(e)[:120]})", "warn")
        plan = _fallback_plan(question, location)
    plan.setdefault("levels", {})
    # Answer in the question's language: function words are more reliable than the planner's guess,
    # which drifts towards the canton's language (an English question about Zürich came back German).
    lang = detect_lang(question) or (plan.get("language") if plan.get("language") in LANG_NAMES else (lang_hint or "de"))
    # Short, abbreviated or misspelled questions ("permis de sejour c") are searched as Apertus understood them.
    clarified = str(plan.get("clarified_question") or "").strip()
    search_q = clarified if len(clarified) > len(question) * 0.6 and len(clarified) < 400 else question
    # Every later step (cantonal search, act and article picking, relevance filter, fact-check) must share the
    # planner's reading. "permis C" is also a lorry licence: without the topic, those steps chose road-traffic law.
    topic = str(plan.get("topic") or "").strip()
    acts = ", ".join(f"SR {r['sr']}" for r in (plan.get("federal_refs") or []) if isinstance(r, dict) and r.get("sr"))
    context = "; ".join(x for x in (topic, f"federal law: {acts}" if acts else "") if x)
    if context and context.lower() not in search_q.lower():
        search_q = f"{search_q} [subject: {context}]"
    # The question's language decides which federal text version we read (DE/FR/IT are equally authentic).
    if lang in ("de", "fr", "it") and lang != fed_lang and not lang_hint:
        fed_lang = lang
    if lang in can_langs and not lang_hint:
        can_lang = lang
    yield {"type": "plan", "plan": plan}
    levels = [k for k, v in plan["levels"].items() if v]
    if plan.get("fallback"):
        yield step("plan", f"Keyword search (no planner): {', '.join(plan['federal_title_terms'])}", "warn")
    else:
        yield step("plan", f"{plan.get('topic', '')} → levels: {', '.join(levels) or 'federal'}", "done")

    q_words = _words(search_q)
    # Apertus writes the LexFind queries while federal retrieval runs.
    lexfind_queries = (ThreadPoolExecutor(1).submit(lexfind_agent.write_queries, search_q,
                       location["canton_name"], LANG_NAMES[can_lang]) if canton else None)
    # The commune's own website is crawled for regulations at the same time (cached for a week).
    communal_job = (ThreadPoolExecutor(1).submit(communal.retrieve, search_q, location,
                    plan.get("communal_keywords", []) + q_words) if location else None)
    evidence = []  # (level, source dict)
    library = []   # every law text loaded, so verification can pull more articles from it

    # 3a. federal -------------------------------------------------------------------------------
    # Always searched: the planner steers the terms, but it is too eager to call a topic "purely cantonal".
    yield step("fed", "Searching Fedlex (federal law in force)")
    try:
        refs = _federal_refs(plan)
        sr = list(refs)
        acts = sources.fedlex_find_acts(sr, plan.get("federal_title_terms", []), fed_lang, limit=MAX_FED_ACTS)
        if not refs:
            # The planner sometimes wrongly calls a topic cantonal (e.g. inheritance shares). Daily-life
            # questions mostly land in the Civil Code or Code of Obligations, so let ranking look there too.
            known = {a["act"] for a in acts}
            acts += [a for a in sources.fedlex_find_acts(["210", "220"], [], fed_lang) if a["act"] not in known]
        terms = plan.get("federal_keywords", []) + plan.get("federal_title_terms", []) + q_words
        def fed_one(a):  # one failed act download used to drop every federal source
            try:
                return (a, *sources.fedlex_articles(a, asof, fed_lang))
            except Exception:
                return a, None, []

        loaded = sources.parallel(fed_one, acts)
        library += [{"kind": "federal", "act": a, "version": v, "arts": arts} for a, v, arts in loaded if v]
        pool, candidates = [], []
        stems = {sources.fold(t)[:6] for t in terms if len(t) >= 5}
        for act, version, arts in loaded:
            if not version:
                continue
            # Articles the planner named are looked up exactly (an invented number simply finds nothing).
            named = refs.get(act["sr"], set())
            exact_idx = [i for i, a in enumerate(arts) if checks.art_key(a["number"]) in named]
            exact = [dict(arts[i], score=100.0) for i in exact_idx][:PER_ACT]
            seen_art = {a["anchor"] for a in exact}
            ranked = [a for a in sources.rank_articles(arts, terms, top=PER_ACT) if a["anchor"] not in seen_art]
            for art in exact + ranked[:max(1, PER_ACT - len(exact))]:
                pool.append(dict(art, act=act, version=version))
            # Candidates for Apertus: named articles and their neighbours (the governing rule is often next to
            # the one remembered), keyword hits, and articles whose heading names the topic.
            near = [arts[j] for i in exact_idx for j in range(max(0, i - 2), min(len(arts), i + 3))]
            heading = [a for a in arts if any(st in sources.fold(a["number"]) for st in stems)][:15]
            mine, seen_c = [], set()
            for a in near + sources.rank_articles(arts, terms, top=20) + heading:
                if a["anchor"] not in seen_c:
                    seen_c.add(a["anchor"])
                    mine.append((act, version, a))
            candidates += mine[:35]
        pool.sort(key=lambda a: -a["score"])
        picked = lexfind_agent.pick_federal(search_q, candidates, n=TOTAL_FED)
        if picked:
            chosen = [dict(a, act=act, version=v) for act, v, a in picked]
            # Articles the planner named from memory stay in too (the picker skipped OCR art. 3b "Port du casque"
            # for a helmet question); the relevance filter drops them if they are off-topic.
            have = {(c["act"]["sr"], c["anchor"]) for c in chosen}
            chosen += [a for a in pool if a["score"] >= 100 and (a["act"]["sr"], a["anchor"]) not in have][:3]
        else:
            chosen = pool
        for art in chosen[:TOTAL_FED]:
            evidence.append(verify.federal_evidence(art["act"], art["version"], art))
        names = ", ".join(f"{a['short'] or a['sr']}" for a in acts) or "none"
        yield step("fed", f"{len(acts)} acts ({names}) → {min(len(chosen), TOTAL_FED)} articles"
                          f"{' chosen by Apertus' if picked else ''}", "done")
    except Exception as e:
        yield step("fed", f"Fedlex error: {e}", "warn")

    # Court decisions interpreting those statutes: Apertus writes the entscheidsuche.ch queries from the question and
    # the federal articles just found, then picks at most two rulings. Runs while cantonal/communal retrieval goes on.
    statutes = [f"Art. {checks.art_key(e['number'])} {e['law']}" for e in evidence
                if e["level"] == "federal" and checks.art_key(e["number"])[:1].isdigit() and len(e["law"]) <= 12][:4]
    case_job = ThreadPoolExecutor(1).submit(caselaw.retrieve, search_q, statutes, canton, lang)

    # 3b. cantonal ------------------------------------------------------------------------------
    if canton:
        yield step("can", f"Apertus searches LexFind ({canton} cantonal law)")
        try:
            # Planner terms vary between runs, so the question's own nouns ("Hund") are searched too.
            # German nouns are capitalised; for FR/IT fall back to the longest content words.
            nouns = ([w for w in q_words if w[0].isupper()] or sorted(q_words, key=len, reverse=True))[:3]
            place = {sources.fold(x) for x in (location["commune"], *location["canton_name"].split(" / "))}
            words = [w for t in plan.get("cantonal_title_terms", [])[:3] + nouns for w in re.split(r"[\s'’-]+", t)
                     if len(w) >= 3 and sources.fold(w) not in place and sources.fold(w) not in NOISE_WORDS]
            # LexFind matches whole words, so "Steuern" never finds "Steuergesetz": search wildcard stems,
            # both as a prefix (titles that start with the topic) and anywhere inside compound words.
            stems_q = list(dict.fromkeys(_title_stem(w) for w in words))[:4]
            search_terms = [t for st in stems_q for t in (f"{st}*", f"*{st}*")]
            # Apertus-written queries first: likely act titles of this canton + title stems.
            try:
                ai_queries = lexfind_queries.result(timeout=60) if lexfind_queries else []
            except Exception:  # a slow query writer used to drop the whole cantonal level; stems still work
                ai_queries = []
            search_terms = list(dict.fromkeys(ai_queries + search_terms))[:12]
            tols, seen = [], set()
            def search_one(term):  # one slow or failing query must not cost the whole cantonal level
                try:
                    return sources.lexfind_search(term, canton, can_lang, limit=15)
                except Exception:
                    return []

            for found in sources.parallel(search_one, search_terms):
                for tol in found:
                    if tol["tol_id"] not in seen:
                        seen.add(tol["tol_id"])
                        tols.append(tol)
            if not tols:  # titles missed: fall back to full-text
                for term in plan.get("cantonal_keywords", [])[:2]:
                    for tol in sources.lexfind_search(term, canton, can_lang, content=True):
                        if tol["tol_id"] not in seen:
                            seen.add(tol["tol_id"])
                            tols.append(tol)
            terms = plan.get("cantonal_keywords", []) + plan.get("cantonal_title_terms", []) + q_words
            # Main acts first: "Hundegesetz" beats a long "Weisung … über …" that merely mentions the topic.
            stems = {sources.fold(_title_stem(t)) for t in terms + words if len(t) >= 3}
            tols.sort(key=lambda tl: -_text_rank(tl, stems))
            # Titles found by Apertus' own queries count as on-topic even without keyword overlap.
            ai_hits = {sources.fold(q).strip("*") for q in ai_queries}
            on_topic = [t for t in tols if _text_rank(t, stems) > -100
                        or any(h and h in sources.fold(t["title"]) for h in ai_hits)]
            # No on-topic act means the canton has nothing on this: loading the off-topic hits anyway made the
            # answer cite unrelated cantonal law under the canton heading.
            tols = lexfind_agent.pick_acts(search_q, location["canton_name"], on_topic[:25]) or on_topic[:MAX_CAN_TEXTS]
            def load_one(t):
                try:
                    return t, sources.lexfind_articles(t, can_lang)
                except Exception:
                    return t, []

            loaded = [x for x in sources.parallel(load_one, tols) if x[1]]
            library += [{"kind": "cantonal", "tol": t, "arts": arts, "canton": canton, "lang": can_lang} for t, arts in loaded]
            picked = lexfind_agent.pick_articles(search_q, loaded, terms)
            for tol, art in picked[:TOTAL_CAN]:
                evidence.append(verify.cantonal_evidence(tol, art, canton, can_lang))
            yield step("can", f"{len(ai_queries)} AI queries · {len(tols)} acts ({', '.join(t['sr'] for t in tols) or 'none'})"
                              f" → {min(len(picked), TOTAL_CAN)} articles chosen by Apertus", "done")
        except Exception as e:
            yield step("can", f"LexFind error: {e}", "warn")

    # 3c. communal ------------------------------------------------------------------------------
    terms = plan.get("communal_keywords", []) + plan.get("cantonal_keywords", []) + q_words
    docs = [d for d in (uploads.get(u) for u in upload_ids) if d]
    if docs:
        yield step("com", f"Reading {len(docs)} uploaded communal document(s)")
        pool = []
        for d in docs:
            for art in sources.rank_articles(d["articles"], terms, top=3):
                pool.append(dict(art, doc=d))
        pool.sort(key=lambda a: -a["score"])
        for art in pool[:TOTAL_COM]:
            d = art["doc"]
            evidence.append({
                "level": "communal", "law": d["name"], "title": d["name"], "sr": f"upload-{d['id']}", "number": art["number"],
                "path": "", "text": art["text"][:3500], "url": d.get("url", ""), "version": "as provided",
                "lang": "", "origin": "Upload" if not d.get("url") else "Web"})
        yield step("com", f"{min(len(pool), TOTAL_COM)} provisions from uploaded documents", "done")
    if communal_job:
        yield step("com", f"Apertus searches {location['commune']}'s website for regulations")
        try:
            # A cold crawl with OCR of a scanned regulation can take minutes under load; it is cached afterwards.
            site, found, chosen, picked = communal_job.result(timeout=240)
            host = (site or "").split("//")[-1].strip("/")
            for meta, art in picked[:TOTAL_COM]:
                evidence.append({
                    "level": "communal", "law": f"{location['commune']}: {meta['title'][:70]}", "title": meta["title"],
                    "sr": f"{location['bfs']}-{meta['sr']}", "number": art["number"], "path": "", "text": art["text"][:3500],
                    "url": art.get("url") or meta["url"], "version": "as published", "lang": "", "origin": host or "website"})
            if not site:
                yield step("com", f"No website known for {location['commune']} — upload its regulation to include it", "warn")
            elif not found:
                yield step("com", f"{host}: no regulation list readable — upload a regulation to include it", "warn")
            elif not chosen:
                yield step("com", f"{host}: {len(found)} regulations listed, none on this topic", "done")
            elif not picked:
                names = ", ".join(m["title"][:40] for m in chosen)
                yield step("com", f"{host}: read {names}, no article answers this", "done")
            else:
                names = ", ".join(m["title"][:40] for m in chosen)
                yield step("com", f"{host}: {len(found)} regulations → {names} → {len(picked[:TOTAL_COM])} articles", "done")
        except Exception as e:
            yield step("com", f"Commune website: {str(e)[:100] or type(e).__name__}", "warn")

    # 3d. case law ------------------------------------------------------------------------------
    yield step("case", "Apertus searches court decisions (entscheidsuche.ch)")
    try:
        queries, cands, rulings = case_job.result(timeout=90)
        evidence += rulings[:caselaw.MAX_PICK]
        if rulings:
            yield step("case", f"{len(cands)} decisions found → {', '.join(r['law'] for r in rulings)}", "done")
        else:
            yield step("case", f"{len(cands)} decisions found, none decides this question", "done")
    except Exception as e:
        yield step("case", f"Court decisions unavailable: {str(e)[:80] or type(e).__name__}", "warn")

    for i, ev in enumerate(evidence, 1):
        ev["id"] = i
    yield {"type": "sources", "sources": evidence}

    # 4. draft, then verify three times before anything reaches the user ---------------------------
    h = HEADINGS.get(lang, HEADINGS["de"])
    canton_name = location["canton_name"].split(" / ")[0] if location else "—"
    commune_name = location["commune"] if location else "—"

    def answer_prompt():
        return ANSWER_PROMPT.format(
            language=LANG_NAMES.get(lang, "Deutsch"), asof=asof, sources=verify.source_block(answer_ev), question=question + (f"\n(Understood as: {search_q})" if search_q != question else ""),
            h_short=h[0], h_fed=h[1], h_can=h[2].format(canton=canton_name), h_com=h[3].format(commune=commune_name),
            h_levels=h[4], h_next=h[5], disclaimer=h[6], none=h[7], h_case=h[8],
            location_line=loc_line, competence=plan.get("competence", ""))

    def write(extra=""):
        raw = apertus.chat([{"role": "system", "content": ANSWER_SYSTEM},
                            {"role": "user", "content": answer_prompt() + extra}], temperature=0.2, max_tokens=2200)
        return checks.repair(raw, evidence)

    # Only the provisions that answer this question go into the answer (the UI still lists everything retrieved).
    # Off-topic hits are dropped from the list the user sees too (they made the source list look random).
    # Rulings are shown under the statutes with their official headnote but never paraphrased by the writer: graded
    # answers misstated what a ruling decided. So they stay out of the answer and out of the relevance filter.
    statute_ev = [e for e in evidence if e["level"] != "case"]
    answer_ev = verify.relevant_sources(search_q, statute_ev) + [e for e in evidence if e["level"] == "case"]
    if len(answer_ev) < len(evidence):
        evidence[:] = answer_ev
        for i, ev in enumerate(evidence, 1):
            ev["id"] = i
        yield {"type": "sources", "sources": evidence}
    answer_ev = [e for e in evidence if e["level"] != "case"]
    yield step("draft", "Apertus drafts a cited answer")
    try:
        text, repaired = write()
    except Exception as e:
        yield step("draft", "Apertus unavailable — sources only", "warn")
        yield {"type": "error", "message": str(e) or type(e).__name__}
        return
    det = checks.check(text, evidence)
    yield step("draft", f"Draft: {det['words']} words, {det['citations']} citations", "done")

    rounds = []
    for r in range(1, VERIFY_ROUNDS + 1):
        key = f"verify{r}"
        yield step(key, f"Verification {r}/{VERIFY_ROUNDS}")
        try:
            added = verify.enrich_from_mentions(text, evidence, library)
            answer_ev += [e for e in added if e not in answer_ev]
            report = verify.fact_check(search_q, text, answer_ev)
            added += verify.fetch_missing(report.get("missing_sources"), evidence, library, asof, fed_lang,
                                           question_hint=" ".join(e["number"] for e in answer_ev))
            answer_ev += [e for e in added if e not in answer_ev]  # in-place: the rewrite sees new sources too
            det = checks.check(text, evidence)
            todo = verify.findings(det, report, added, first_round=(r == 1))
            # (A former nudge told the writer to use every uncited cantonal/communal source. It pushed unrelated
            # police and fee regulations into answers; the fact-checker's "ignored_sources" covers real omissions.)
            revised = False
            if todo:
                text, fixed = write(verify.REVISE_SUFFIX.format(draft=text, findings=todo))
                repaired += fixed
                revised = True
            rounds.append({"round": r, "claims": report.get("claims_checked", 0), "raw_chars": report.get("raw_chars", 0),
                           "unreadable": bool(report.get("unreadable")),
                           "issues": len(report["issues"]) + len(det["unsupported_articles"]) + len(det["invalid_citations"]),
                           "added": [f"{e['law']} {e['number']}" for e in added],
                           "revised": revised, "notes": [i["problem"] for i in report["issues"]][:4]})
            # (An early stop after a clean round was tried and graded worse on the held-out set: the fact-checker is
            # not deterministic, and a later round still caught wrong figures. All rounds run.)
            if added:
                yield {"type": "sources", "sources": evidence}
            checked = f"{rounds[-1]['claims']} claims checked"
            label = (f"{checked}, {rounds[-1]['issues']} issue(s), {len(added)} source(s) added → revised" if revised
                     else f"{checked}, all supported")
            yield step(key, f"Verification {r}/{VERIFY_ROUNDS}: {label}", "done")
        except Exception as e:
            # Any failure (API, malformed verifier JSON, Fedlex) skips this round; the current text is kept.
            msg = str(e) or type(e).__name__
            rounds.append({"round": r, "issues": 0, "added": [], "revised": False, "error": msg[:200]})
            yield step(key, f"Verification {r}/{VERIFY_ROUNDS} skipped: {msg[:80]}", "warn")

    # The case-law heading is optional: drop it when no ruling is cited (the model writes "no source" under it anyway).
    case_ids = {e["id"] for e in evidence if e["level"] == "case"}
    if not case_ids & set(checks.check(text, evidence)["cited_ids"]):
        text = re.sub(rf"(?ms)^##\s*{re.escape(h[8])}\s*\n.*?(?=^##\s|^\*|\Z)", "", text)
    if h[6].rstrip(".") not in text:
        text = text.rstrip() + f"\n\n*{h[6]}*"
    report = dict(checks.check(text, evidence), repaired=repaired)
    yield {"type": "final", "text": text, "check": report, "verification": rounds}
    yield {"type": "done", "seconds": round(time.time() - t0, 1), "language": lang}


def sse(events):
    try:
        for ev in events:
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
    except Exception as e:  # never end the stream silently: the UI would show an empty "finished" answer
        yield f"data: {json.dumps({'type': 'error', 'message': f'Internal error: {type(e).__name__}'})}\n\n"
