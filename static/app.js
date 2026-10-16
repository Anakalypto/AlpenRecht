"use strict";

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
};
const today = () => new Date().toISOString().slice(0, 10);

// ------------------------------------------------------------------ i18n
const T = {
  de: {
    pick_title: "Wählen Sie Ihren Ort auf der Karte", pick_hint: "Klicken Sie auf die Karte, um Ihre Gemeinde zu wählen.", my_pos: "Mein Standort", no_place: "Ohne Ort (nur Bund)", use_place: "Übernehmen", pick_loading: "Gemeinde wird bestimmt…", outside: "Kein Schweizer Gemeindegebiet. Klicken Sie innerhalb der Schweiz.", geo_denied: "Standort nicht verfügbar.", map_offline: "Karte nicht verfügbar (offline).",
    badge: "Bund · Kanton · Gemeinde in einer Antwort", badge_tag: "Neu",
    greet: ["Guten Morgen,", "Guten Tag,", "Guten Abend,"], greet_b1: "welche", greet_em: "Rechtsfrage", greet_b2: "klären wir heute?",
    topics: "Themen", recent: "Verlauf", no_recent: "Noch keine Chats.", new_chat: "Neuer Chat",
    status_ok: "verbunden", status_nokey: "kein API-Schlüssel", status_off: "nicht erreichbar",
    where: "Ort", location: "Adresse, PLZ oder Gemeinde", loc_hint: "Bestimmt Kanton und Gemeinde. Ohne Ort: nur Bundesrecht.",
    asof: "Rechtsstand am", asof_hint: "Bundesrecht in der damals geltenden Fassung.", today: "Heute",
    communal: "Gemeinderecht", communal_title: "Gemeinderecht",
    communal_hint: "Alpenrecht durchsucht automatisch die Website Ihrer Gemeinde nach Reglementen, auch gescannte. Fehlt eines, laden Sie es hier hoch oder fügen Sie einen Link ein.",
    upload: "PDF auswählen oder hierher ziehen", add: "Hinzufügen",
    placeholder: "Stellen Sie eine Frage zum Schweizer Recht…", placeholder_short: "Ihre Frage…", placeholder_follow: "Weitere Frage…",
    disclaimer: "Rechtsinformation, keine Rechtsberatung. Antworten verweisen auf Fedlex, LexFind und Ihre Gemeindedokumente.",
    fed: "Bund", can: "Kanton", com: "Gemeinde", not_loaded: "nicht geladen", none_found: "nichts gefunden",
    sources: "Quellen", tap_hint: "zum Lesen antippen", official: "Amtlichen Text öffnen", copy: "Kopieren", copied: "Kopiert",
    retry: "Erneut", researching: "Recherchiere…", done_in: (s, n) => `Recherche · ${n} Quellen · ${s}s`,
    no_key: "Apertus ist nicht verbunden.", no_key_hint: "Die Quellen wurden trotzdem live abgerufen. Tragen Sie APERTUS_API_KEY in alpenrecht/.env ein.",
    unsupported: "Nicht durch die Quellen belegt: ", failed: "Fehler", provisions: "Bestimmungen", version: "Fassung",
    steps: { loc: "Ort bestimmen", plan: "Suche planen", fed: "Bundesrecht · Fedlex", can: "Kantonsrecht · LexFind", com: "Gemeinderecht", answer: "Antwort verfassen", draft: "Entwurf verfassen" },
    verify_step: "Prüfung", verified: "geprüft", claims: "Aussagen", corrections: "Korrektur(en)", sources_added: "Quelle(n) ergänzt", added_tag: "ergänzt", checking: "Prüfe Antwort an den Quellen…", clean: "keine Beanstandung",
    topic_list: [
      ["home", "Wohnen & Miete", "Wie lange ist die Kündigungsfrist für meine Mietwohnung?", "f"],
      ["build", "Bauen", "Brauche ich eine Baubewilligung für eine Solaranlage auf dem Dach?", "fcg"],
      ["work", "Arbeit", "Darf mein Arbeitgeber Überstunden anordnen und wie werden sie entschädigt?", "f"],
      ["pet", "Tiere", "Muss ich meinen Hund an der Leine führen und anmelden?", "fcg"],
      ["tax", "Steuern", "Welche Abzüge kann ich bei den Kantonssteuern machen?", "fc"],
      ["noise", "Nachbarn & Lärm", "Welche Ruhezeiten gelten nachts und am Sonntag?", "fcg"],
    ],
  },
  fr: {
    pick_title: "Choisissez votre lieu sur la carte", pick_hint: "Cliquez sur la carte pour choisir votre commune.", my_pos: "Ma position", no_place: "Sans lieu (Confédération seulement)", use_place: "Utiliser", pick_loading: "Recherche de la commune…", outside: "Hors du territoire communal suisse. Cliquez en Suisse.", geo_denied: "Position indisponible.", map_offline: "Carte indisponible (hors ligne).",
    badge: "Confédération · canton · commune en une réponse", badge_tag: "Nouveau",
    greet: ["Bonjour,", "Bonjour,", "Bonsoir,"], greet_b1: "quelle", greet_em: "question juridique", greet_b2: "aujourd’hui ?",
    topics: "Thèmes", recent: "Historique", no_recent: "Aucune conversation.", new_chat: "Nouvelle conversation",
    status_ok: "connecté", status_nokey: "pas de clé API", status_off: "injoignable",
    where: "Lieu", location: "Adresse, NPA ou commune", loc_hint: "Détermine le canton et la commune. Sans lieu : droit fédéral seulement.",
    asof: "Droit en vigueur au", asof_hint: "Droit fédéral dans sa version applicable à cette date.", today: "Aujourd’hui",
    communal: "Droit communal", communal_title: "Droit communal",
    communal_hint: "Alpenrecht cherche automatiquement les règlements sur le site de votre commune, même scannés. S’il en manque un, téléversez-le ici ou collez un lien.",
    upload: "Choisir un PDF ou le glisser ici", add: "Ajouter",
    placeholder: "Posez une question sur le droit suisse…", placeholder_short: "Votre question…", placeholder_follow: "Autre question…",
    disclaimer: "Information juridique, pas un conseil juridique. Les réponses renvoient à Fedlex, LexFind et vos documents communaux.",
    fed: "Confédération", can: "Canton", com: "Commune", not_loaded: "non chargé", none_found: "rien trouvé",
    sources: "Sources", tap_hint: "toucher pour lire", official: "Ouvrir le texte officiel", copy: "Copier", copied: "Copié",
    retry: "Relancer", researching: "Recherche…", done_in: (s, n) => `Recherche · ${n} sources · ${s} s`,
    no_key: "Apertus n’est pas connecté.", no_key_hint: "Les sources ont tout de même été récupérées. Ajoutez APERTUS_API_KEY dans alpenrecht/.env.",
    unsupported: "Non étayé par les sources : ", failed: "Erreur", provisions: "dispositions", version: "version",
    steps: { loc: "Localisation", plan: "Plan de recherche", fed: "Droit fédéral · Fedlex", can: "Droit cantonal · LexFind", com: "Droit communal", answer: "Rédaction", draft: "Rédaction du brouillon" },
    verify_step: "Vérification", verified: "vérifié", claims: "affirmations", corrections: "correction(s)", sources_added: "source(s) ajoutée(s)", added_tag: "ajoutée", checking: "Vérification de la réponse…", clean: "aucun problème",
    topic_list: [
      ["home", "Logement & bail", "Quel est le délai de résiliation de mon bail d’appartement ?", "f"],
      ["build", "Construire", "Faut-il un permis de construire pour des panneaux solaires sur le toit ?", "fcg"],
      ["work", "Travail", "Mon employeur peut-il imposer des heures supplémentaires ?", "f"],
      ["pet", "Animaux", "Dois-je tenir mon chien en laisse et l’enregistrer ?", "fcg"],
      ["tax", "Impôts", "Quelles déductions puis-je faire sur mes impôts cantonaux ?", "fc"],
      ["noise", "Voisinage & bruit", "Quelles heures de repos s’appliquent la nuit et le dimanche ?", "fcg"],
    ],
  },
  it: {
    pick_title: "Scegliete il luogo sulla mappa", pick_hint: "Cliccate sulla mappa per scegliere il vostro Comune.", my_pos: "La mia posizione", no_place: "Senza luogo (solo Confederazione)", use_place: "Usa", pick_loading: "Ricerca del Comune…", outside: "Fuori dal territorio comunale svizzero. Cliccate in Svizzera.", geo_denied: "Posizione non disponibile.", map_offline: "Mappa non disponibile (offline).",
    badge: "Confederazione · Cantone · Comune in una risposta", badge_tag: "Nuovo",
    greet: ["Buongiorno,", "Buongiorno,", "Buonasera,"], greet_b1: "quale", greet_em: "questione giuridica", greet_b2: "chiariamo oggi?",
    topics: "Temi", recent: "Cronologia", no_recent: "Ancora nessuna chat.", new_chat: "Nuova chat",
    status_ok: "collegato", status_nokey: "nessuna chiave API", status_off: "non raggiungibile",
    where: "Luogo", location: "Indirizzo, NPA o comune", loc_hint: "Determina Cantone e Comune. Senza luogo: solo diritto federale.",
    asof: "Diritto in vigore al", asof_hint: "Diritto federale nella versione valida a quella data.", today: "Oggi",
    communal: "Diritto comunale", communal_title: "Diritto comunale",
    communal_hint: "Alpenrecht cerca automaticamente i regolamenti sul sito del suo Comune, anche scansionati. Se ne manca uno, lo carichi qui o incolli un link.",
    upload: "Scegliere un PDF o trascinarlo qui", add: "Aggiungi",
    placeholder: "Faccia una domanda sul diritto svizzero…", placeholder_short: "La sua domanda…", placeholder_follow: "Altra domanda…",
    disclaimer: "Informazione giuridica, non consulenza legale. Le risposte rimandano a Fedlex, LexFind e ai documenti comunali.",
    fed: "Confederazione", can: "Cantone", com: "Comune", not_loaded: "non caricato", none_found: "nulla trovato",
    sources: "Fonti", tap_hint: "tocca per leggere", official: "Aprire il testo ufficiale", copy: "Copia", copied: "Copiato",
    retry: "Riprova", researching: "Ricerca…", done_in: (s, n) => `Ricerca · ${n} fonti · ${s} s`,
    no_key: "Apertus non è collegato.", no_key_hint: "Le fonti sono state comunque recuperate. Aggiunga APERTUS_API_KEY in alpenrecht/.env.",
    unsupported: "Non supportato dalle fonti: ", failed: "Errore", provisions: "disposizioni", version: "versione",
    steps: { loc: "Localizzazione", plan: "Piano di ricerca", fed: "Diritto federale · Fedlex", can: "Diritto cantonale · LexFind", com: "Diritto comunale", answer: "Redazione", draft: "Stesura della bozza" },
    verify_step: "Verifica", verified: "verificato", claims: "affermazioni", corrections: "correzione/i", sources_added: "fonte/i aggiunta/e", added_tag: "aggiunta", checking: "Verifica della risposta…", clean: "nessun problema",
    topic_list: [
      ["home", "Abitare & affitto", "Qual è il termine di disdetta del mio appartamento in affitto?", "f"],
      ["build", "Costruire", "Serve una licenza edilizia per pannelli solari sul tetto?", "fcg"],
      ["work", "Lavoro", "Il datore di lavoro può ordinare lavoro straordinario?", "f"],
      ["pet", "Animali", "Devo tenere il cane al guinzaglio e registrarlo?", "fcg"],
      ["tax", "Imposte", "Quali deduzioni posso fare sulle imposte cantonali?", "fc"],
      ["noise", "Vicinato & rumore", "Quali orari di quiete valgono di notte e la domenica?", "fcg"],
    ],
  },
  rm: {
    pick_title: "Tscherni Voss lieu sin la charta", pick_hint: "Cliccai sin la charta per tscherner Vossa vischnanca.", my_pos: "Mia posiziun", no_place: "Senza lieu (mo Confederaziun)", use_place: "Utilisar", pick_loading: "Tschertgar la vischnanca…", outside: "Ordaifer il territori communal svizzer.", geo_denied: "Posiziun betg disponibla.", map_offline: "Charta betg disponibla (offline).",
    badge: "Confederaziun · chantun · vischnanca en ina resposta", badge_tag: "Nov",
    greet: ["Bun di,", "Bun di,", "Buna saira,"], greet_b1: "tge", greet_em: "dumonda giuridica", greet_b2: "scleriain nus oz?",
    topics: "Temas", recent: "Istorgia", no_recent: "Anc nagins chats.", new_chat: "Nov chat",
    status_ok: "collià", status_nokey: "nagina clav API", status_off: "betg cuntanschibel",
    where: "Lieu", location: "Adressa, numer postal u vischnanca", loc_hint: "Determinescha chantun e vischnanca. Senza lieu: mo dretg federal.",
    asof: "Dretg valaivel ils", asof_hint: "Dretg federal en la versiun valaivla da lez di.", today: "Oz",
    communal: "Dretg communal", communal_title: "Dretg communal",
    communal_hint: "Alpenrecht tschertga automaticamain ils reglaments sin la pagina-web da Vossa vischnanca. Sch’i manca in, chargiai el si qua.",
    upload: "Tscherner in PDF u al trair nà", add: "Agiuntar",
    placeholder: "Dumandai insatge davart il dretg svizzer…", placeholder_short: "Vossa dumonda…", placeholder_follow: "Ulteriura dumonda…",
    disclaimer: "Infurmaziun giuridica, nagin cussegl giuridic.",
    fed: "Confederaziun", can: "Chantun", com: "Vischnanca", not_loaded: "betg chargià", none_found: "nagut chattà",
    sources: "Funtaunas", tap_hint: "tutgar per leger", official: "Avrir il text uffizial", copy: "Copiar", copied: "Copià",
    retry: "Danovamain", researching: "Retschertga…", done_in: (s, n) => `Retschertga · ${n} funtaunas · ${s} s`,
    no_key: "Apertus n’è betg collià.", no_key_hint: "Las funtaunas èn tuttina vegnidas chargiadas. Agiuntai APERTUS_API_KEY en alpenrecht/.env.",
    unsupported: "Betg cumprovà da las funtaunas: ", failed: "Errur", provisions: "disposiziuns", version: "versiun",
    steps: { loc: "Lieu", plan: "Planisar", fed: "Dretg federal · Fedlex", can: "Dretg chantunal · LexFind", com: "Dretg communal", answer: "Scriver la resposta", draft: "Sbozz" },
    verify_step: "Controlla", verified: "controllà", claims: "affirmaziuns", corrections: "correctura(s)", sources_added: "funtauna(s) agiuntada(s)", added_tag: "agiuntà", checking: "Controllar la resposta…", clean: "nagins problems",
    topic_list: [
      ["home", "Abitar & fittar", "Tge è il termin da disditga per mia abitaziun?", "f"],
      ["build", "Construir", "Dovrel jau ina permissiun da construcziun per in implant solar?", "fcg"],
      ["work", "Lavur", "Po mes patrun ordinar uras supplementaras?", "f"],
      ["pet", "Animals", "Stoss jau manar mes chaun a la lingia?", "fcg"],
      ["tax", "Taglias", "Tge deducziuns poss jau far tar las taglias chantunalas?", "fc"],
      ["noise", "Vischins & canera", "Tge uras da ruaus valan la notg e la dumengia?", "fcg"],
    ],
  },
  en: {
    pick_title: "Pick your place on the map", pick_hint: "Click the map to choose your commune.", my_pos: "My location", no_place: "No place (federal only)", use_place: "Use this place", pick_loading: "Finding the commune…", outside: "Not inside a Swiss commune. Click within Switzerland.", geo_denied: "Location not available.", map_offline: "Map unavailable (offline).",
    badge: "Federal · cantonal · communal in one answer", badge_tag: "New",
    greet: ["Good morning,", "Good afternoon,", "Good evening,"], greet_b1: "which", greet_em: "legal question", greet_b2: "can I help with?",
    topics: "Topics", recent: "History", no_recent: "No chats yet.", new_chat: "New chat",
    status_ok: "connected", status_nokey: "no API key", status_off: "unreachable",
    where: "Place", location: "Address, postcode or commune", loc_hint: "Sets the canton and commune. No place: federal law only.",
    asof: "Law as of", asof_hint: "Federal law in the version that applied on that date.", today: "Today",
    communal: "Communal law", communal_title: "Communal law",
    communal_hint: "Alpenrecht searches your commune’s website for regulations automatically, scanned ones included. If one is missing, upload it here or paste a link.",
    upload: "Choose a PDF or drop it here", add: "Add",
    placeholder: "Ask anything about Swiss law…", placeholder_short: "Your question…", placeholder_follow: "Ask a follow-up…",
    disclaimer: "Legal information, not legal advice. Answers cite Fedlex, LexFind and your communal documents.",
    fed: "Federal", can: "Canton", com: "Commune", not_loaded: "not loaded", none_found: "nothing found",
    sources: "Sources", tap_hint: "tap to read", official: "Open official text", copy: "Copy", copied: "Copied",
    retry: "Retry", researching: "Researching…", done_in: (s, n) => `Researched · ${n} sources · ${s}s`,
    no_key: "Apertus is not connected.", no_key_hint: "The sources were still fetched live. Add APERTUS_API_KEY to alpenrecht/.env.",
    unsupported: "Not backed by the sources: ", failed: "Error", provisions: "provisions", version: "version",
    steps: { loc: "Locating", plan: "Planning the search", fed: "Federal law · Fedlex", can: "Cantonal law · LexFind", com: "Communal law", answer: "Writing the answer", draft: "Drafting" },
    verify_step: "Verification", verified: "verified", claims: "claims", corrections: "correction(s)", sources_added: "source(s) added", added_tag: "added", checking: "Checking the answer against the sources…", clean: "no issues",
    topic_list: [
      ["home", "Housing & rent", "What is the notice period for my rented flat?", "f"],
      ["build", "Building", "Do I need a building permit for rooftop solar panels?", "fcg"],
      ["work", "Work", "Can my employer order overtime, and how is it paid?", "f"],
      ["pet", "Animals", "Do I have to keep my dog on a leash and register it?", "fcg"],
      ["tax", "Taxes", "Which deductions can I claim on cantonal taxes?", "fc"],
      ["noise", "Neighbours & noise", "Which quiet hours apply at night and on Sundays?", "fcg"],
    ],
  },
};
// Landing map: the three plates (Switzerland, canton, commune).
Object.assign(T.de, { hero_fed: "Schweiz", pick_commune: "Gemeinde wählen" });
Object.assign(T.fr, { hero_fed: "Suisse", pick_commune: "Choisir la commune" });
Object.assign(T.it, { hero_fed: "Svizzera", pick_commune: "Scegliere il Comune" });
Object.assign(T.rm, { hero_fed: "Svizra", pick_commune: "Tscherner la vischnanca" });
Object.assign(T.en, { hero_fed: "Switzerland", pick_commune: "Pick your commune" });

const ICONS = {
  home: '<path d="M4 11 12 4l8 7v8a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z"/>',
  build: '<path d="M3 20h18M5 20V9l7-5 7 5v11"/><path d="M9 20v-5h6v5"/>',
  work: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18"/>',
  pet: '<circle cx="7" cy="9" r="2"/><circle cx="12" cy="6" r="2"/><circle cx="17" cy="9" r="2"/><path d="M8 17c0-3 2-5 4-5s4 2 4 5c0 2-2 3-4 3s-4-1-4-3z"/>',
  tax: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>',
  noise: '<path d="M4 10v4h4l5 4V6L8 10zM16 9a4 4 0 0 1 0 6M18.5 6.5a8 8 0 0 1 0 11"/>',
  pin: '<path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
  chat: '<path d="M4 5h16v11H8l-4 4z"/>',
  chev: '<path d="m6 9 6 6 6-6"/>',
  copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
  retry: '<path d="M4 12a8 8 0 1 0 2.3-5.7M4 4v4h4"/>',
  doc: '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/>',
};
const TOPIC_COLORS = { home: "#e0475b", build: "#e08a1f", work: "#3f7ae0", pet: "#1f9d6b", tax: "#6a5af9", noise: "#0e9bb0" };
const LV = { federal: "f", cantonal: "c", communal: "g" };
const svg = (name, cls = "") => `<svg viewBox="0 0 24 24"${cls ? ` class="${cls}"` : ""}>${ICONS[name]}</svg>`;

let lang = store.get("alp.lang", "de");
if (!T[lang]) lang = "de";
const t = (k) => T[lang][k] ?? T.en[k] ?? k;
const locale = () => (lang === "rm" ? "de-CH" : `${lang}-CH`);

const state = {
  location: store.get("alp.loc", ""),
  locationLabel: store.get("alp.locLabel", ""),
  asof: today(),
  docs: [],
  chat: null,          // {id, title, at, turns: []}
  busy: null,          // AbortController while streaming
};

// ------------------------------------------------------------------ language
function applyLang() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("#langs button").forEach((b) => b.classList.toggle("on", b.dataset.lang === lang));
  $("#lang-select").value = lang;
  const h = new Date().getHours();
  $("#greet-a").textContent = t("greet")[h < 11 ? 0 : h < 18 ? 1 : 2];
  const topics = t("topic_list");
  $("#topics").innerHTML = topics.map(([ic, title, q, lv]) => `
    <button type="button" class="nav-item" style="--tc:${TOPIC_COLORS[ic]}" data-q="${esc(q)}" title="${esc(q)}">
      <span class="ni">${svg(ic)}</span><span class="nt">${esc(title)}</span>
      <span class="dots">${["f", "c", "g"].map((l) => `<i class="${lv.includes(l) ? l : ""}"></i>`).join("")}</span>
    </button>`).join("");
  // Three quick suggestions under the composer, from the same topics.
  $("#examples").innerHTML = [3, 1, 0, 5].map((i) => topics[i]).map(([ic, , q]) =>
    `<button type="button" class="sugg" style="--tc:${TOPIC_COLORS[ic]}" data-q="${esc(q)}"><span class="si">${svg(ic)}</span>${esc(q)}</button>`).join("");
  renderChips(); renderRecent(); updatePlaceholder(); renderStatus(); renderHero();
}
function setLang(l) { lang = l; store.set("alp.lang", lang); applyLang(); }
$("#langs").addEventListener("click", (e) => { const b = e.target.closest("button[data-lang]"); if (b) setLang(b.dataset.lang); });
$("#lang-select").addEventListener("change", (e) => setLang(e.target.value));

// ------------------------------------------------------------------ layout: home <-> chat
const narrow = window.matchMedia("(max-width: 560px)");
function updatePlaceholder() {
  $("#q").placeholder = state.chat?.turns.length ? t("placeholder_follow") : narrow.matches ? t("placeholder_short") : t("placeholder");
}
narrow.addEventListener("change", updatePlaceholder);

function showHome() {
  state.busy?.abort();
  state.chat = null;
  document.body.classList.add("is-home");
  $("#welcome").hidden = false; $("#thread").hidden = true; $("#thread").innerHTML = "";
  $("#chat-title").textContent = "";
  closeDrawer(); closeSide(); renderRecent(); updatePlaceholder();
}
function showThread() {
  document.body.classList.remove("is-home");
  $("#welcome").hidden = true; $("#thread").hidden = false;
  $("#chat-title").textContent = state.chat?.title || "";
  closeSide(); renderRecent(); updatePlaceholder();
}
$("#home-btn").addEventListener("click", showHome);
$("#new-chat").addEventListener("click", () => { showHome(); $("#q").focus(); });

function pickQuestion(q) { $("#q").value = q; autosize(); closeSide(); $("#q").focus(); }
$("#topics").addEventListener("click", (e) => { const b = e.target.closest("[data-q]"); if (b) { if (state.chat) showHome(); pickQuestion(b.dataset.q); } });
$("#examples").addEventListener("click", (e) => { const b = e.target.closest("[data-q]"); if (b) send(b.dataset.q); });

// mobile sidebar
function openSide() { $("#side").classList.add("open"); $("#side-scrim").hidden = false; }
function closeSide() { $("#side").classList.remove("open"); $("#side-scrim").hidden = true; }
$("#menu").addEventListener("click", openSide);
$("#side-close").addEventListener("click", closeSide);
$("#side-scrim").addEventListener("click", closeSide);

// ------------------------------------------------------------------ Apertus status
let health = null;
function renderStatus() {
  const dot = $("#status-dot"); dot.className = "dot";
  if (!health) { $("#status-text").textContent = "…"; return; }
  const name = (health.model || "Apertus").split("/").pop().replace(/-/g, " ");
  $("#model-name").textContent = name; $("#model-pill").textContent = name;
  if (!health.key_set) { dot.classList.add("bad"); $("#status-text").textContent = t("status_nokey"); }
  else if (health.ok === false) { dot.classList.add("bad"); $("#status-text").textContent = t("status_off"); }
  else { dot.classList.add("ok"); $("#status-text").textContent = t("status_ok"); }
}
fetch("/api/health?check=1").then((r) => r.json()).then((h) => { health = h; renderStatus(); }).catch(() => {});

// ------------------------------------------------------------------ tool row: location, date, communal docs
function renderChips() {
  $("#loc-label").textContent = state.locationLabel || state.location || t("where");
  $("#loc-chip").classList.toggle("set", !!state.location);
  $("#date-label").textContent = state.asof === today() ? t("today")
    : new Date(state.asof + "T12:00").toLocaleDateString(locale(), { day: "numeric", month: "short", year: "numeric" });
  $("#date-chip").classList.toggle("set", state.asof !== today());
  $("#doc-label").textContent = state.docs.length ? `${t("communal")} · ${state.docs.length}` : t("communal");
  $("#doc-chip").classList.toggle("set", state.docs.length > 0);
  $("#docs").innerHTML = state.docs.map((d, i) =>
    `<div class="doc">${svg("doc")}<span>${esc(d.name)}</span><small>${d.articles}</small><button type="button" data-i="${i}" aria-label="remove">×</button></div>`).join("");
}
const pops = { "date-chip": "date-pop", "doc-chip": "doc-pop" };
function closePops() { Object.values(pops).forEach((id) => { $("#" + id).hidden = true; }); }
Object.entries(pops).forEach(([chip, pop]) => {
  $("#" + chip).addEventListener("click", (e) => {
    e.stopPropagation();
    const el = $("#" + pop); const open = el.hidden;
    closePops(); el.hidden = !open;
    if (open) el.querySelector("input:not([type=file])")?.focus();
  });
});
document.addEventListener("click", (e) => { if (!e.target.closest(".chip-wrap")) closePops(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") { closePops(); closeDrawer(); closeSide(); closeMap(); } });

// ------------------------------------------------------------------ location: pick a point on the map
// The exact point goes to the backend ("@lat,lon"), which asks swisstopo for the commune there.
let map = null, marker = null, outline = null, picked = null;
function setPlace(location, label, info = null) {
  state.location = location; state.locationLabel = label;
  store.set("alp.loc", location); store.set("alp.locLabel", label);
  setPlaceInfo(info);
  renderChips();
}
function closeMap() { $("#map-modal").hidden = true; }
function openMap(focus) {
  closePops();
  $("#map-modal").hidden = false;
  if (!window.L) { $("#map-pick").textContent = t("map_offline"); return; }
  if (!map) {
    map = L.map("map", { minZoom: 6, maxBounds: [[45.3, 5.4], [48.3, 11.1]], maxBoundsViscosity: 0.8 }).setView([46.8, 8.23], 7);
    L.tileLayer("https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg",
      { maxZoom: 18, attribution: '&copy; <a href="https://www.swisstopo.admin.ch" target="_blank" rel="noopener">swisstopo</a>' }).addTo(map);
    map.on("click", (e) => pick(e.latlng.lat, e.latlng.lng));
  }
  setTimeout(() => map.invalidateSize(), 80);
  const m = /^@(-?[\d.]+),(-?[\d.]+)$/.exec(state.location || "");
  if (focus) map.setView(focus.latlng, focus.zoom);
  else if (m) map.setView([+m[1], +m[2]], 11);
  if (m) pick(+m[1], +m[2], true);
}
const pinIcon = () => L.divIcon({ className: "map-pin", html: "<span></span>", iconSize: [22, 22], iconAnchor: [11, 11] });
async function pick(lat, lon, keepView) {
  if (marker) marker.setLatLng([lat, lon]); else marker = L.marker([lat, lon], { icon: pinIcon() }).addTo(map);
  $("#map-pick").innerHTML = `<span class="spinner"></span> ${esc(t("pick_loading"))}`;
  $("#map-use").disabled = true; picked = null;
  try {
    const r = await fetch(`/api/reverse?lat=${lat.toFixed(5)}&lon=${lon.toFixed(5)}`);
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || "");
    picked = { lat, lon, label: j.label, canton: j.canton, canton_name: j.canton_name, commune: j.commune, geometry: j.geometry };
    if (outline) outline.remove();
    if (j.geometry) {
      outline = L.geoJSON(j.geometry, { style: { color: "#c8102e", weight: 2, fillColor: "#c8102e", fillOpacity: 0.1 } }).addTo(map);
      if (!keepView) map.fitBounds(outline.getBounds(), { maxZoom: 12, padding: [20, 20] });
    }
    $("#map-pick").innerHTML = `${svg("pin")}<b>${esc(j.label)}</b><span>· ${esc(t("can"))} ${esc(j.canton_name.split(" / ")[0])}</span>`;
    $("#map-use").disabled = false;
  } catch {
    if (outline) { outline.remove(); outline = null; }
    $("#map-pick").textContent = t("outside");
  }
}
$("#loc-chip").addEventListener("click", (e) => { e.stopPropagation(); openMap(); });
$("#map-close").addEventListener("click", closeMap);
$("#map-modal").addEventListener("click", (e) => { if (e.target.id === "map-modal") closeMap(); });
$("#map-use").addEventListener("click", () => {
  if (!picked) return;
  setPlace(`@${picked.lat.toFixed(5)},${picked.lon.toFixed(5)}`, picked.label, picked);
  closeMap(); $("#q").focus();
});
$("#map-clear").addEventListener("click", () => { setPlace("", ""); closeMap(); });
$("#map-locate").addEventListener("click", () => {
  if (!navigator.geolocation) { toast(t("geo_denied")); return; }
  navigator.geolocation.getCurrentPosition(
    (pos) => { map.setView([pos.coords.latitude, pos.coords.longitude], 12); pick(pos.coords.latitude, pos.coords.longitude, true); },
    () => toast(t("geo_denied")), { timeout: 8000 });
});

// ------------------------------------------------------------------ landing: three plates, Switzerland → canton → commune
// static/cantons.json holds swisstopo canton outlines as SVG paths in this projection:
// x = (lon − lon0) · k · cos(latRef), y = (lat0 − lat) · k. Commune outlines from /api/reverse use the same one.
let geo = null;
let placeInfo = store.get("alp.locInfo", null);   // {canton, canton_name, commune, d, x, y} of the chosen place
const DEMO_CANTONS = ["ZH", "GR", "VD", "TI", "BE", "GE", "VS", "LU"];
let demoIdx = 0, demoTimer = null;

const projX = (lon) => (lon - geo.proj.lon0) * geo.proj.k * Math.cos(geo.proj.latRef * Math.PI / 180);
const projY = (lat) => (geo.proj.lat0 - lat) * geo.proj.k;
const unproject = ([x, y]) => [geo.proj.lat0 - y / geo.proj.k, x / (geo.proj.k * Math.cos(geo.proj.latRef * Math.PI / 180)) + geo.proj.lon0];

function pathBox(d) {
  const xs = [], ys = [];
  for (const m of d.matchAll(/(-?[\d.]+),(-?[\d.]+)/g)) { xs.push(+m[1]); ys.push(+m[2]); }
  return { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) };
}
// A viewBox around a shape, padded and matched to the plate's aspect ratio so the shape sits centred.
function viewAround(b, pad = 0.18) {
  const ratio = geo.w / geo.h;
  let w = (b.x1 - b.x0) * (1 + 2 * pad), h = (b.y1 - b.y0) * (1 + 2 * pad);
  if (w / h > ratio) h = w / ratio; else w = h * ratio;
  const cx = (b.x0 + b.x1) / 2, cy = (b.y0 + b.y1) / 2;
  return `${cx - w / 2} ${cy - h / 2} ${w} ${h}`;
}
function geometryPath(g) {
  const polys = g.type === "MultiPolygon" ? g.coordinates : [g.coordinates];
  return polys.flat().map((ring) => "M" + ring.map(([lon, lat]) => `${projX(lon).toFixed(2)},${projY(lat).toFixed(2)}`).join("L") + "Z").join("");
}

function setPlaceInfo(p) {
  if (!p || !geo) { placeInfo = null; store.set("alp.locInfo", null); renderHero(); return; }
  placeInfo = { canton: p.canton, canton_name: p.canton_name, commune: p.commune,
                d: p.geometry ? geometryPath(p.geometry) : "", x: projX(p.lon), y: projY(p.lat) };
  store.set("alp.locInfo", placeInfo.d.length < 80000 ? placeInfo : { ...placeInfo, d: "" });
  renderHero();
}

function renderHero() {
  const legend = $("#lv-legend");
  const row = (lvl) => legend.querySelector(`[data-plate="${lvl}"]`);
  row("federal").querySelector("b").textContent = t("fed");
  row("federal").querySelector("small").textContent = t("hero_fed");
  row("cantonal").querySelector("b").textContent = t("can");
  row("communal").querySelector("b").textContent = t("com");
  if (!geo) return;
  const demo = !placeInfo;
  const ct = demo ? DEMO_CANTONS[demoIdx % DEMO_CANTONS.length] : placeInfo.canton;
  const canton = geo.cantons[ct];
  if (!canton) return;
  const name = demo ? canton.name : (placeInfo.canton_name || canton.name).split(" / ")[0];
  row("cantonal").querySelector("small").textContent = name;
  row("communal").querySelector("small").textContent = demo ? t("pick_commune") : placeInfo.commune;
  $("#stack").classList.toggle("demo", demo);

  const all = Object.entries(geo.cantons).map(([k, c]) =>
    `<path class="${k === ct ? "on" : ""}" data-canton="${k}" d="${c.d}"/>`).join("");

  // Switzerland: every canton, the current one lit.
  const fed = $("#plate-federal");
  fed.setAttribute("viewBox", `-12 -12 ${geo.w + 24} ${geo.h + 24}`);
  fed.innerHTML = `<g class="cantons">${all}</g>`;

  // Canton: zoomed to its outline, neighbours faint, the commune lit.
  const can = $("#plate-cantonal");
  can.setAttribute("viewBox", viewAround(pathBox(canton.d), 0.12));
  can.innerHTML = `<g class="cantons">${all}</g>`
    + (!demo && placeInfo.d ? `<path class="commune" d="${placeInfo.d}"/>` : "")
    + (!demo ? `<circle class="pin" cx="${placeInfo.x}" cy="${placeInfo.y}" r="1"/>` : "");

  // Commune: zoomed to the commune, or an invitation to pick one.
  const com = $("#plate-communal");
  if (demo || !placeInfo.d) {
    com.setAttribute("viewBox", "0 0 300 195");
    com.innerHTML = `<g class="invite"><circle cx="150" cy="92" r="34"/><path d="M150 76v32M134 92h32" transform="rotate(16 150 92)"/></g>`;
  } else {
    const b = pathBox(placeInfo.d);
    com.setAttribute("viewBox", viewAround(b, 0.14));
    const r = Math.max(b.x1 - b.x0, b.y1 - b.y0) * 0.035;
    com.innerHTML = `<g class="cantons">${all}</g><path class="commune" d="${placeInfo.d}"/>`
      + `<circle class="pin" cx="${placeInfo.x}" cy="${placeInfo.y}" r="${r}"/>`;
  }
  // Pins on the canton plate scale with the zoom.
  const pin = can.querySelector(".pin");
  if (pin) { const vb = can.viewBox.baseVal; pin.setAttribute("r", Math.max(vb.width, vb.height) * 0.012); }
}

function startDemo() {
  clearInterval(demoTimer);
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  demoTimer = setInterval(() => {
    if (placeInfo || !document.body.classList.contains("is-home") || document.hidden) return;
    demoIdx++; renderHero();
  }, 2800);
}

// Clicking a plate opens the place picker there: a canton on the Swiss plate, the shown canton, or the commune.
function focusFor(el) {
  const k = el.closest("[data-canton]")?.dataset.canton;
  const plate = el.closest("[data-plate]")?.dataset.plate;
  if (!geo) return null;
  if (k && plate === "federal") return { latlng: unproject(geo.cantons[k].c), zoom: 9 };
  if (placeInfo && plate === "communal") return { latlng: unproject([placeInfo.x, placeInfo.y]), zoom: 12 };
  const ct = placeInfo?.canton || DEMO_CANTONS[demoIdx % DEMO_CANTONS.length];
  if (plate !== "federal" && geo.cantons[ct]) return { latlng: unproject(geo.cantons[ct].c), zoom: 9 };
  return null;
}
function hoverPlate(lvl) {
  document.querySelectorAll("#stack [data-plate], #lv-legend [data-plate]").forEach((el) => el.classList.toggle("lift", el.dataset.plate === lvl));
}
["#stack", "#lv-legend"].forEach((sel) => {
  const box = $(sel);
  box.addEventListener("click", (e) => { if (e.target.closest("[data-plate]")) openMap(focusFor(e.target)); });
  box.addEventListener("mouseover", (e) => hoverPlate(e.target.closest("[data-plate]")?.dataset.plate));
  box.addEventListener("mouseleave", () => hoverPlate(null));
});
$("#plate-federal").addEventListener("mouseover", (e) => {
  const k = e.target.closest("[data-canton]")?.dataset.canton;
  if (!k || placeInfo || !geo || k === DEMO_CANTONS[demoIdx % DEMO_CANTONS.length]) return;
  const i = DEMO_CANTONS.indexOf(k);
  if (i >= 0) demoIdx = i; else { DEMO_CANTONS.push(k); demoIdx = DEMO_CANTONS.length - 1; }
  renderHero(); startDemo();   // follow the pointer, then resume cycling from there
});

fetch("/static/cantons.json").then((r) => r.json()).then(async (g) => {
  geo = g;
  // A place picked before the landing map existed: look it up once to draw its commune.
  const m = /^@(-?[\d.]+),(-?[\d.]+)$/.exec(state.location || "");
  if (m && (!placeInfo || !placeInfo.d)) {
    try { const r = await fetch(`/api/reverse?lat=${m[1]}&lon=${m[2]}`); if (r.ok) { const j = await r.json(); setPlaceInfo({ ...j, lat: +m[1], lon: +m[2] }); return; } } catch {}
  }
  if (!state.location) placeInfo = null;
  renderHero();
}).catch(() => {});
startDemo();

$("#asof").value = state.asof;
$("#asof").addEventListener("change", () => { state.asof = $("#asof").value || today(); renderChips(); });

async function addDoc(req) {
  try {
    const r = await fetch("/api/upload", req);
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || r.statusText);
    state.docs.push(j); renderChips(); toast(`${j.name} · ${j.articles} ${t("provisions")}`);
  } catch (err) { toast(`${t("failed")}: ${err.message}`); }
}
function uploadFile(f) { const fd = new FormData(); fd.append("file", f); return addDoc({ method: "POST", body: fd }); }
$("#file").addEventListener("change", async (e) => { if (e.target.files[0]) await uploadFile(e.target.files[0]); e.target.value = ""; });
$("#drop").addEventListener("dragover", (e) => { e.preventDefault(); $("#drop").classList.add("over"); });
$("#drop").addEventListener("dragleave", () => $("#drop").classList.remove("over"));
$("#drop").addEventListener("drop", (e) => { e.preventDefault(); $("#drop").classList.remove("over"); if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]); });
$("#addurl").addEventListener("click", async () => {
  const url = $("#docurl").value.trim(); if (!url) return;
  $("#addurl").disabled = true;
  await addDoc({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) });
  $("#addurl").disabled = false; $("#docurl").value = "";
});
$("#docs").addEventListener("click", (e) => { if (e.target.dataset.i !== undefined) { state.docs.splice(+e.target.dataset.i, 1); renderChips(); } });

// ------------------------------------------------------------------ composer
function autosize() {
  const q = $("#q");
  q.style.height = "auto";
  if (q.value) q.style.height = Math.min(q.scrollHeight, 160) + "px";
  syncSend();
}
function syncSend() {
  const s = $("#send");
  s.classList.toggle("stop", !!state.busy);
  s.disabled = !state.busy && !$("#q").value.trim();
}
window.addEventListener("resize", () => { if ($("#q").value) autosize(); });
$("#q").addEventListener("input", autosize);
$("#q").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); $("#composer").requestSubmit(); } });
$("#composer").addEventListener("submit", (e) => {
  e.preventDefault();
  if (state.busy) { state.busy.abort(); return; }
  send($("#q").value);
});

// ------------------------------------------------------------------ markdown + citations
function inline(s, sources) {
  return esc(s)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
    .replace(/\[(\d{1,2})\]/g, (m, n) => {
      const src = sources.find((x) => x.id === +n);
      return src ? `<button type="button" class="cite ${LV[src.level]}" data-cite="${n}" title="${esc(src.law + " · " + src.number)}">${n}</button>`
                 : `<span class="cite bad" title="not in retrieved sources">${n}</span>`;
    });
}
function markdown(md, sources) {
  const out = []; let list = null;
  const close = () => { if (list) { out.push(`</${list}>`); list = null; } };
  for (const raw of md.split("\n")) {
    const line = raw.trimEnd(); let m;
    if ((m = line.match(/^(#{1,4})\s+(.*)/))) { close(); const l = m[1].length <= 2 ? 2 : 3; out.push(`<h${l}>${inline(m[2], sources)}</h${l}>`); }
    else if ((m = line.match(/^\s*[-*•]\s+(.*)/))) { if (list !== "ul") { close(); out.push("<ul>"); list = "ul"; } out.push(`<li>${inline(m[1], sources)}</li>`); }
    else if ((m = line.match(/^\s*\d+[.)]\s+(.*)/))) { if (list !== "ol") { close(); out.push("<ol>"); list = "ol"; } out.push(`<li>${inline(m[1], sources)}</li>`); }
    else if (!line.trim()) close();
    else { close(); out.push(`<p>${inline(line, sources)}</p>`); }
  }
  close();
  return out.join("");
}

// ------------------------------------------------------------------ messages
function userMessage(turn) {
  const el = document.createElement("div");
  el.className = "msg-user";
  const ctx = [turn.location && `📍 ${turn.locationLabel || turn.location}`, turn.asof !== today() && `📅 ${turn.asof}`, turn.docs?.length && `📎 ${turn.docs.length}`].filter(Boolean);
  el.innerHTML = `<div class="bubble">${esc(turn.q)}</div>${ctx.length ? `<div class="msg-ctx">${ctx.map((c) => `<span>${esc(c)}</span>`).join("")}</div>` : ""}`;
  return el;
}
function botMessage() {
  const el = document.createElement("div");
  el.className = "msg-bot";
  el.innerHTML = `
    <span class="orb orb-sm thinking" aria-hidden="true"></span>
    <div class="bot-body">
      <details class="trace" open>
        <summary><span class="spinner"></span><span class="now">${esc(t("researching"))}</span>${svg("chev", "chev")}</summary>
        <ol class="steps"></ol>
      </details>
      <div class="levelbar" hidden></div>
      <div class="competence" hidden></div>
      <div class="md answer"><div class="skeleton"><i></i><i></i><i></i></div></div>
      <div class="src-wrap" hidden><div class="src-head"><h4></h4></div><div class="src-row"></div></div>
      <div class="bot-actions" hidden>
        <button type="button" class="act" data-act="copy">${svg("copy")}<span>${esc(t("copy"))}</span></button>
        <button type="button" class="act" data-act="retry">${svg("retry")}<span>${esc(t("retry"))}</span></button>
      </div>
    </div>`;
  return el;
}
function setStep(el, ev) {
  const ol = $(".steps", el);
  let li = ol.querySelector(`li[data-key="${ev.key}"]`);
  if (!li) {
    li = document.createElement("li"); li.dataset.key = ev.key;
    li.innerHTML = `<span class="dot"></span><span><b></b><small></small></span>`;
    ol.appendChild(li);
  }
  li.className = ev.status;
  const name = stepName(ev.key);
  $("b", li).textContent = name;
  $("small", li).textContent = ev.status === "running" ? "" : ev.label;
  if (ev.status === "running") $(".now", el).textContent = `${name}…`;
  if (ev.key.startsWith("verify") && ev.status === "running") {
    const box = $(".answer", el);
    if (box.querySelector(".skeleton")) box.innerHTML = `<div class="checking"><span class="spinner"></span>${esc(t("checking"))} ${ev.key.slice(6)}/3</div><div class="skeleton"><i></i><i></i><i></i></div>`;
    else { const c = box.querySelector(".checking"); if (c) c.lastChild.textContent = `${t("checking")} ${ev.key.slice(6)}/3`; }
  }
}
function stepName(key) {
  const m = key.match(/^verify(\d)$/);
  return m ? `${t("verify_step")} ${m[1]}/3` : (t("steps")[key] || key);
}

function verificationBadge(turn) {
  const v = turn.verification;
  if (!v || !v.length) return "";
  const claims = v.reduce((n, r) => n + (r.claims || 0), 0);
  const revised = v.filter((r) => r.revised).length;
  const added = v.reduce((n, r) => n + (r.added || []).length, 0);
  const rows = v.map((r) => `<li><b>${esc(t("verify_step"))} ${r.round}/3</b> · ${r.claims || 0} ${esc(t("claims"))}`
    + (r.revised ? ` · ${r.issues} → ${esc(t("corrections"))}` : ` · ${esc(t("clean"))}`)
    + (r.added && r.added.length ? ` · + ${esc(r.added.join(", "))}` : "")
    + (r.notes && r.notes.length ? `<br><small>${r.notes.map(esc).join("<br>")}</small>` : "") + "</li>").join("");
  return `<details class="verified"><summary><span class="vcheck">✓</span> ${v.length}× ${esc(t("verified"))} · ${claims} ${esc(t("claims"))}`
    + ` · ${revised} ${esc(t("corrections"))} · ${added} ${esc(t("sources_added"))}</summary><ol>${rows}</ol></details>`;
}

function renderLevels(el, turn) {
  const bar = $(".levelbar", el);
  const loc = turn.resolved;
  const by = (lvl) => turn.sources.filter((s) => s.level === lvl);
  const laws = (list) => [...new Set(list.map((s) => s.law))].slice(0, 3).join(", ");
  const rows = [["federal", t("fed"), ""]];
  if (loc) rows.push(["cantonal", `${t("can")} ${loc.canton}`, ""], ["communal", loc.commune, ""]);
  bar.innerHTML = rows.map(([lvl, name, empty]) => {
    const list = by(lvl);
    const status = list.length ? `${list.length} · ${esc(laws(list))}` : turn.sourcesIn ? esc(empty || t("none_found")) : "…";
    return `<button type="button" class="lvl ${LV[lvl]} ${list.length || !turn.sourcesIn ? "" : "empty"}" data-level="${lvl}"><b>${esc(name)}</b><span>${status}</span></button>`;
  }).join("");
  bar.hidden = false;
  const comp = $(".competence", el);
  if (turn.plan?.competence) { comp.textContent = turn.plan.competence; comp.hidden = false; }
}
function renderSources(el, turn) {
  const wrap = $(".src-wrap", el);
  if (!turn.sources.length) { wrap.hidden = true; return; }
  $("h4", wrap).textContent = `${t("sources")} · ${turn.sources.length} — ${t("tap_hint")}`;
  $(".src-row", wrap).innerHTML = turn.sources.map((s) => `
    <button type="button" class="src ${LV[s.level]}" data-src="${s.id}">
      <span class="top"><span class="n">${s.id}</span>${esc(s.origin)} · ${esc(s.version)}${s.added ? ` <i class="added">+ ${esc(t("added_tag"))}</i>` : ""}</span>
      <b>${esc(s.law)} · ${esc(s.number)}</b>
      <p>${esc(s.text.replace(/^(Art\.?|Article|§)\s*\S+\s*/i, "").slice(0, 200))}</p>
    </button>`).join("");
  wrap.hidden = false;
}
function renderAnswer(el, turn, streaming) {
  const box = $(".answer", el);
  if (turn.error && !turn.text) {
    const noKey = /APERTUS_API_KEY|401|403/.test(turn.error);
    box.innerHTML = `<div class="notice"><b>${esc(noKey ? t("no_key") : t("failed"))}</b> ${esc(noKey ? t("no_key_hint") : turn.error)}</div>`;
    return;
  }
  if (!turn.text) return;
  const c = turn.check;
  const flagged = c ? [...(c.unsupported_articles || []), ...(c.invalid_citations || []).map((n) => `[${n}]`)] : [];
  box.innerHTML = markdown(turn.text, turn.sources) + (streaming ? '<span class="caret"></span>' : "")
    + (!streaming && flagged.length ? `<div class="check-warn">⚠ ${esc(t("unsupported"))}${esc(flagged.join(", "))}</div>` : "")
    + (!streaming ? verificationBadge(turn) : "");
}
function finish(el, turn) {
  $(".orb-sm", el).classList.remove("thinking");
  const trace = $(".trace", el);
  trace.classList.add(turn.error ? "failed" : "finished");
  trace.open = false;
  $(".now", el).textContent = turn.error && !turn.sources.length ? t("failed") : t("done_in")(turn.seconds ?? "–", turn.sources.length);
  $(".bot-actions", el).hidden = false;
  el._turn = turn;
}
function staticTurn(turn) {
  const frag = document.createDocumentFragment();
  frag.appendChild(userMessage(turn));
  const el = botMessage();
  (turn.steps || []).forEach((s) => setStep(el, s));
  turn.sourcesIn = true;
  renderLevels(el, turn); renderSources(el, turn); renderAnswer(el, turn, false); finish(el, turn);
  frag.appendChild(el);
  return frag;
}

// ------------------------------------------------------------------ send
async function send(text) {
  const q = (text || "").trim();
  if (!q || state.busy) return;
  closePops();
  if (!state.chat) { state.chat = { id: Date.now().toString(36), title: q, at: Date.now(), turns: [] }; $("#thread").innerHTML = ""; }
  const turn = { q, location: state.location, locationLabel: state.locationLabel, asof: state.asof, docs: state.docs.map((d) => ({ id: d.id, name: d.name })),
                 lang, steps: [], sources: [], text: "", resolved: null, plan: null, error: "" };
  state.chat.turns.push(turn);
  showThread();
  $("#q").value = ""; autosize();

  const thread = $("#thread");
  thread.appendChild(userMessage(turn));
  const el = botMessage(); thread.appendChild(el);
  thread.scrollTop = thread.scrollHeight;

  const ctrl = new AbortController(); state.busy = ctrl; syncSend();
  const started = performance.now();
  let pending = false;
  const stick = () => { if (thread.scrollHeight - thread.scrollTop - thread.clientHeight < 160) thread.scrollTop = thread.scrollHeight; };
  try {
    const r = await fetch("/api/ask", {
      method: "POST", headers: { "Content-Type": "application/json" }, signal: ctrl.signal,
      body: JSON.stringify({ question: q, location: turn.location, asof: turn.asof, lang, uploads: turn.docs.map((d) => d.id) }),
    });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
    const reader = r.body.getReader(); const dec = new TextDecoder(); let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const parts = buf.split("\n\n"); buf = parts.pop();
      for (const part of parts) {
        if (!part.startsWith("data:")) continue;
        const ev = JSON.parse(part.slice(5));
        if (ev.type === "step") {
          const i = turn.steps.findIndex((s) => s.key === ev.key);
          if (i >= 0) turn.steps[i] = ev; else turn.steps.push(ev);
          setStep(el, ev); stick();
        } else if (ev.type === "location") { turn.resolved = ev.location; renderLevels(el, turn); }
        else if (ev.type === "plan") { turn.plan = ev.plan; renderLevels(el, turn); }
        else if (ev.type === "sources") { turn.sources = ev.sources; turn.sourcesIn = true; renderLevels(el, turn); renderSources(el, turn); stick(); }
        else if (ev.type === "token") {
          turn.text += ev.text;
          if (!pending) { pending = true; requestAnimationFrame(() => { pending = false; renderAnswer(el, turn, true); stick(); }); }
        } else if (ev.type === "error") { turn.error = ev.message; renderAnswer(el, turn, false); }
        else if (ev.type === "final") { turn.text = ev.text; turn.check = ev.check; turn.verification = ev.verification; renderAnswer(el, turn, false); stick(); }
        else if (ev.type === "done") { turn.seconds = ev.seconds; }
      }
    }
    renderAnswer(el, turn, false);
  } catch (err) {
    if (err.name === "AbortError") { turn.error = turn.error || "—"; if (turn.text) renderAnswer(el, turn, false); }
    else { turn.error = err.message; renderAnswer(el, turn, false); }
  } finally {
    state.busy = null; syncSend();
    turn.seconds = turn.seconds ?? Math.round((performance.now() - started) / 100) / 10;
    turn.sourcesIn = true; renderLevels(el, turn);
    if (!turn.text && !turn.error) $(".answer", el).innerHTML = "";
    finish(el, turn);
    saveChat();
  }
}

// ------------------------------------------------------------------ thread interactions
$("#thread").addEventListener("click", async (e) => {
  const cite = e.target.closest("[data-cite]");
  const card = e.target.closest("[data-src]");
  const lvl = e.target.closest("[data-level]");
  const act = e.target.closest("[data-act]");
  const msg = e.target.closest(".msg-bot");
  const turn = msg && (msg._turn || state.chat?.turns[[...$("#thread").querySelectorAll(".msg-bot")].indexOf(msg)]);
  if (!turn) return;
  if (cite || card) {
    const id = +(cite?.dataset.cite || card.dataset.src);
    openDrawer(turn.sources.find((s) => s.id === id));
    const target = msg.querySelector(`[data-src="${id}"]`);
    if (target) { target.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" }); target.classList.add("flash"); setTimeout(() => target.classList.remove("flash"), 1200); }
  } else if (lvl) {
    const first = turn.sources.find((s) => s.level === lvl.dataset.level);
    msg.querySelector(first ? `[data-src="${first.id}"]` : "_")?.scrollIntoView({ behavior: "smooth", inline: "start", block: "nearest" });
  } else if (act?.dataset.act === "copy") {
    const plain = turn.text + "\n\n" + turn.sources.map((s) => `[${s.id}] ${s.law} ${s.number} — ${s.url}`).join("\n");
    try { await navigator.clipboard.writeText(plain); toast(t("copied")); } catch { toast(t("failed")); }
  } else if (act?.dataset.act === "retry") {
    send(turn.q);
  }
});

// ------------------------------------------------------------------ drawer
function openDrawer(s) {
  if (!s) return;
  const tag = $("#d-level");
  tag.className = `lvl-tag ${LV[s.level]}`;
  tag.textContent = `${s.id} · ${{ federal: t("fed"), cantonal: t("can"), communal: t("com") }[s.level]}`;
  // Cantonal PDFs start with "Art. 7 Leinen- und Maulkorbpflicht": lift that heading into the title.
  const [first, ...rest] = s.text.split("\n");
  const lifted = first.startsWith(s.number) && first.length < 120 && rest.length;
  $("#d-title").textContent = lifted ? first.replace(/\s*\*\s*/g, " ").trim() : s.number;
  $("#d-law").textContent = s.level === "federal" && s.sr ? `${s.law} · SR ${s.sr}` : s.law;
  $("#d-path").textContent = s.path || s.title;
  $("#d-text").textContent = lifted ? rest.join("\n") : s.text;
  $("#d-meta").textContent = `${s.origin} · ${t("version")} ${s.version}${s.lang ? " · " + s.lang.toUpperCase() : ""}`;
  const link = $("#d-link");
  link.hidden = !s.url; link.href = s.url || "#"; link.textContent = `${t("official")} ↗`;
  $("#drawer").classList.add("open"); $("#drawer").setAttribute("aria-hidden", "false");
}
function closeDrawer() { $("#drawer").classList.remove("open"); $("#drawer").setAttribute("aria-hidden", "true"); }
$("#d-close").addEventListener("click", closeDrawer);
$("#welcome").addEventListener("click", closeDrawer);

// ------------------------------------------------------------------ history (sidebar)
function saveChat() {
  if (!state.chat) return;
  const chats = store.get("alp.chats", []).filter((c) => c.id !== state.chat.id);
  const slim = { ...state.chat, at: Date.now(), turns: state.chat.turns.map((tn) => ({ ...tn, sources: tn.sources.map((s) => ({ ...s, text: s.text.slice(0, 1500) })) })) };
  chats.unshift(slim);
  store.set("alp.chats", chats.slice(0, 15));
  renderRecent();
}
function renderRecent() {
  const chats = store.get("alp.chats", []);
  $("#recent-empty").hidden = chats.length > 0;
  $("#recent").innerHTML = chats.map((c) => {
    const tn = c.turns[c.turns.length - 1] || {};
    const where = tn.resolved ? tn.resolved.canton : "CH";
    return `<button type="button" class="nav-item ${state.chat?.id === c.id ? "on" : ""}" data-chat="${esc(c.id)}" title="${esc(c.title)}">
      <span class="ni">${svg("chat")}</span><span class="nt">${esc(c.title)}</span><small>${esc(where)}</small></button>`;
  }).join("");
}
$("#recent").addEventListener("click", (e) => {
  const b = e.target.closest("[data-chat]"); if (!b || state.busy) return;
  const chat = store.get("alp.chats", []).find((c) => c.id === b.dataset.chat); if (!chat) return;
  state.chat = chat;
  const thread = $("#thread"); thread.innerHTML = "";
  chat.turns.forEach((tn) => thread.appendChild(staticTurn(tn)));
  showThread();
  thread.scrollTop = thread.scrollHeight;
});

// ------------------------------------------------------------------ toast
let toastTimer;
function toast(msg) {
  const el = $("#toast"); el.textContent = msg; el.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => (el.hidden = true), 2400);
}

// ------------------------------------------------------------------ boot
applyLang();
showHome();
autosize();
