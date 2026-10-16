"""Build eval/questions100.json: 68 federal + 32 cantonal questions, then verify every gold source live.

Federal gold = (SR, article) pairs; each is fetched from Fedlex and its heading printed for review.
Cantonal gold = every in-force act of that canton whose LexFind title contains the topic stem.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from alpenrecht import checks  # noqa: E402
from alpenrecht import sources  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent

# (lang, location, question, [(sr, article), ...] alternatives)
FEDERAL = [
    # tenancy (OR)
    ("de", "8001 Zürich", "Wie hoch darf die Mietkaution maximal sein?", [("220", "257e")]),
    ("fr", "1003 Lausanne", "Mon propriétaire peut-il augmenter le loyer sans formulaire officiel ?", [("220", "269d")]),
    ("it", "6900 Lugano", "Posso subaffittare il mio appartamento?", [("220", "262")]),
    ("de", "4051 Basel", "Kann ich eine Mietzinserhöhung anfechten?", [("220", "270b")]),
    ("fr", "1204 Genève", "Puis-je contester le loyer initial de mon nouvel appartement ?", [("220", "270")]),
    ("en", "8001 Zürich", "Can I leave my rented flat before the end of the notice period?", [("220", "264")]),
    ("de", "3011 Bern", "Muss die Kündigung meiner Wohnung durch den Vermieter auf einem amtlichen Formular erfolgen?", [("220", "266l")]),
    ("fr", "2000 Neuchâtel", "Mon conjoint peut-il résilier le bail de notre logement familial sans mon accord ?", [("220", "266m"), ("220", "266n")]),
    ("de", "6003 Luzern", "Meine Wohnung hat Schimmel – darf ich den Mietzins herabsetzen?", [("220", "259d")]),
    ("it", "6500 Bellinzona", "Il proprietario può disdire il contratto perché ho chiesto delle riparazioni?", [("220", "271a")]),
    ("fr", "1700 Fribourg", "Puis-je obtenir une prolongation du bail après une résiliation ?", [("220", "272")]),
    ("de", "9000 St. Gallen", "Darf der Vermieter Nebenkosten verlangen, die nicht im Mietvertrag stehen?", [("220", "257a")]),
    # employment (OR, ArG)
    ("de", "8400 Winterthur", "Wie lange muss mein Lohn bei Krankheit weiterbezahlt werden?", [("220", "324a")]),
    ("fr", "1950 Sion", "Quel est le délai de congé après deux ans de travail ?", [("220", "335c")]),
    ("it", "6600 Locarno", "Il datore di lavoro deve rilasciarmi un certificato di lavoro?", [("220", "330a")]),
    ("en", "4051 Basel", "Can my employer dismiss me with immediate effect?", [("220", "337")]),
    ("de", "5000 Aarau", "Ist eine Kündigung wegen meiner Gewerkschaftszugehörigkeit missbräuchlich?", [("220", "336")]),
    ("fr", "1204 Genève", "Une clause de non-concurrence dans mon contrat de travail est-elle valable ?", [("220", "340"), ("220", "340a")]),
    ("de", "7000 Chur", "Habe ich Anspruch auf eine Gratifikation oder einen 13. Monatslohn?", [("220", "322d")]),
    ("it", "6900 Lugano", "Quante pause mi spettano durante una giornata di lavoro?", [("822.11", "15")]),
    ("de", "6300 Zug", "Wie viele Stunden pro Woche darf ich höchstens arbeiten?", [("822.11", "9")]),
    ("fr", "1003 Lausanne", "Mon employeur peut-il me faire travailler le dimanche ?", [("822.11", "18")]),
    ("de", "3011 Bern", "Muss ich Schäden ersetzen, die ich bei der Arbeit verursacht habe?", [("220", "321e")]),
    ("en", "1204 Genève", "How many weeks of holiday do employees under 20 get?", [("220", "329a")]),
    ("de", "4500 Solothurn", "Wie wird mein Ferienlohn berechnet, wenn ich im Stundenlohn arbeite?", [("220", "329d")]),
    ("fr", "2800 Delémont", "Mon employeur peut-il traiter mes données personnelles comme il veut ?", [("220", "328b")]),
    ("it", "6500 Bellinzona", "Posso essere licenziata durante la gravidanza?", [("220", "336c")]),
    # contracts, consumer, debt
    ("de", "8001 Zürich", "Kann ich einen an der Haustür abgeschlossenen Vertrag widerrufen?", [("220", "40b"), ("220", "40e")]),
    ("fr", "1400 Yverdon-les-Bains", "Dans quel délai dois-je signaler un défaut sur un objet acheté ?", [("220", "201")]),
    ("en", "6003 Luzern", "How long can I claim under the warranty when I buy a product?", [("220", "210")]),
    ("it", "6900 Lugano", "Dopo quanto tempo si prescrive un credito?", [("220", "127"), ("220", "128")]),
    ("de", "4051 Basel", "Ich habe einen Zahlungsbefehl erhalten – wie und wann erhebe ich Rechtsvorschlag?", [("281.1", "74")]),
    ("fr", "1204 Genève", "Comment engager une poursuite contre quelqu'un qui me doit de l'argent ?", [("281.1", "67")]),
    ("de", "9000 St. Gallen", "Darf man Verzugszins verlangen, wenn eine Rechnung zu spät bezahlt wird?", [("220", "104")]),
    ("fr", "2000 Neuchâtel", "Un contrat conclu par un mineur est-il valable ?", [("210", "19")]),
    # family, inheritance, property (ZGB)
    ("de", "3011 Bern", "Ab welchem Alter ist man in der Schweiz volljährig?", [("210", "14")]),
    ("fr", "1003 Lausanne", "Comment rédiger un testament manuscrit valable ?", [("210", "505")]),
    ("it", "6900 Lugano", "Quanto eredita il coniuge superstite?", [("210", "462")]),
    ("de", "8001 Zürich", "Wer erbt, wenn kein Testament vorhanden ist und ich Kinder habe?", [("210", "457")]),
    ("en", "6300 Zug", "What share of my estate is reserved for my children?", [("210", "471")]),
    ("de", "6003 Luzern", "Die Äste vom Baum meines Nachbarn ragen auf mein Grundstück – darf ich sie abschneiden?", [("210", "687")]),
    ("fr", "1700 Fribourg", "Mon voisin cause du bruit et de la fumée excessifs, que dit le Code civil ?", [("210", "684")]),
    ("de", "5000 Aarau", "Muss ich Unterhalt für mein volljähriges Kind in Ausbildung bezahlen?", [("210", "277")]),
    ("it", "6500 Bellinzona", "Chi ha l'autorità parentale dopo il divorzio?", [("210", "133"), ("210", "296"), ("210", "298")]),
    ("fr", "1204 Genève", "Quelles sont les conditions pour pouvoir se marier ?", [("210", "94")]),
    ("de", "7000 Chur", "Was gilt beim Stockwerkeigentum für die Nutzung meiner Wohnung?", [("210", "712a")]),
    # criminal (StGB)
    ("de", "8001 Zürich", "Ist es strafbar, jemanden heimlich zu fotografieren oder zu filmen?", [("311.0", "179quater")]),
    ("fr", "1003 Lausanne", "Insulter quelqu'un sur les réseaux sociaux est-il punissable ?", [("311.0", "177")]),
    ("it", "6900 Lugano", "Cosa rischio se danneggio una cosa altrui?", [("311.0", "144")]),
    ("de", "3011 Bern", "Ist eine Ohrfeige strafbar?", [("311.0", "126")]),
    ("en", "4051 Basel", "Is it a crime to enter someone's home without permission?", [("311.0", "186")]),
    ("fr", "2000 Neuchâtel", "Que risque-t-on pour un vol ?", [("311.0", "139")]),
    ("de", "9000 St. Gallen", "Ist es strafbar, ein Telefongespräch ohne Einwilligung aufzunehmen?", [("311.0", "179ter")]),
    ("fr", "1950 Sion", "Qu'est-ce que la diffamation en droit suisse ?", [("311.0", "173")]),
    # road traffic (SVG, VRV)
    ("de", "8400 Winterthur", "Welche Höchstgeschwindigkeit gilt innerorts?", [("741.11", "4a")]),
    ("fr", "1204 Genève", "Combien de temps perd-on son permis après un grave excès de vitesse ?", [("741.01", "16c")]),
    ("it", "6500 Bellinzona", "Cosa succede se rifiuto il test dell'alcol?", [("741.01", "91a")]),
    ("de", "6300 Zug", "Was gilt als grobe Verletzung der Verkehrsregeln?", [("741.01", "90")]),
    ("en", "8001 Zürich", "Do drivers have to stop for pedestrians at a zebra crossing?", [("741.01", "33")]),
    ("de", "6003 Luzern", "Wie viele Promille darf ich beim Autofahren haben?", [("741.01", "55"), ("741.01", "91")]),
    # data protection (DSG)
    ("fr", "1003 Lausanne", "Une entreprise doit-elle m'informer quand elle collecte mes données ?", [("235.1", "19")]),
    ("de", "4051 Basel", "Muss ein Unternehmen eine Datenschutzverletzung melden?", [("235.1", "24")]),
    ("it", "6900 Lugano", "Posso chiedere la cancellazione dei miei dati personali?", [("235.1", "32")]),
    ("en", "1204 Genève", "What principles apply when a company processes my personal data?", [("235.1", "6")]),
    # constitution (BV)
    ("de", "3011 Bern", "Ist die Meinungsfreiheit in der Bundesverfassung garantiert?", [("101", "16")]),
    ("fr", "1700 Fribourg", "La Constitution garantit-elle l'égalité entre femmes et hommes ?", [("101", "8")]),
    ("it", "6600 Locarno", "Ho diritto alla protezione della sfera privata?", [("101", "13")]),
    ("en", "8001 Zürich", "From what age can I vote in federal elections?", [("101", "136")]),
]

# (lang, location, question, canton, LexFind search term, title stem)
CANTONAL = [
    # dog laws
    ("de", "6003 Luzern", "Muss ich meinen Hund im Kanton Luzern registrieren?", "LU", "Hunde", "hund"),
    ("de", "9000 St. Gallen", "Gilt im Kanton St. Gallen eine Leinenpflicht für Hunde?", "SG", "Hunde", "hund"),
    ("de", "5000 Aarau", "Welche Pflichten habe ich als Hundehalter im Aargau?", "AG", "Hunde", "hund"),
    ("de", "4500 Solothurn", "Muss ich für meinen Hund eine Haftpflichtversicherung haben?", "SO", "Hunde", "hund"),
    ("fr", "1950 Sion", "Quelles règles s'appliquent aux chiens en Valais ?", "VS", "chiens", "chien"),
    ("fr", "2000 Neuchâtel", "Dois-je déclarer mon chien à la commune ?", "NE", "chiens", "chien"),
    ("fr", "1700 Fribourg", "Mon chien doit-il être tenu en laisse dans le canton de Fribourg ?", "FR", "chiens", "chien"),
    ("fr", "1003 Lausanne", "Certaines races de chiens sont-elles interdites dans le canton de Vaud ?", "VD", "chiens", "chien"),
    ("de", "8500 Frauenfeld", "Welche Regeln gelten für Hunde im Thurgau?", "TG", "Hunde", "hund"),
    ("de", "7000 Chur", "Brauche ich eine Bewilligung für einen grossen Hund in Graubünden?", "GR", "Hunde", "hund"),
    # tax laws
    ("de", "8001 Zürich", "Welche Abzüge kann ich bei den Staatssteuern im Kanton Zürich machen?", "ZH", "Steuergesetz", "steuergesetz"),
    ("de", "3011 Bern", "Wie werden Kapitalgewinne auf Grundstücken im Kanton Bern besteuert?", "BE", "Steuergesetz", "steuergesetz"),
    ("de", "6003 Luzern", "Wann muss ich meine Steuererklärung im Kanton Luzern einreichen?", "LU", "Steuergesetz", "steuergesetz"),
    ("de", "5000 Aarau", "Gibt es im Aargau einen Abzug für Kinderbetreuungskosten?", "AG", "Steuergesetz", "steuergesetz"),
    ("de", "9000 St. Gallen", "Muss ich im Kanton St. Gallen Vermögenssteuer bezahlen?", "SG", "Steuergesetz", "steuergesetz"),
    ("fr", "1204 Genève", "Comment est imposée la fortune dans le canton de Genève ?", "GE", "impôt", "impôt"),
    ("fr", "1003 Lausanne", "Quelles déductions puis-je faire sur mes impôts dans le canton de Vaud ?", "VD", "impôts", "impôt"),
    ("fr", "2000 Neuchâtel", "Quand dois-je payer mes impôts cantonaux à Neuchâtel ?", "NE", "contributions", "contributions"),
    ("it", "6900 Lugano", "Quali deduzioni fiscali posso fare in Ticino?", "TI", "tributaria", "tributaria"),
    # building laws
    ("de", "8001 Zürich", "Brauche ich im Kanton Zürich eine Baubewilligung für einen Gartenschuppen?", "ZH", "Baugesetz", "baugesetz"),
    ("de", "3011 Bern", "Welche Bauten sind im Kanton Bern baubewilligungsfrei?", "BE", "Baugesetz", "baugesetz"),
    ("de", "6003 Luzern", "Wie lange dauert ein Baubewilligungsverfahren im Kanton Luzern?", "LU", "Baugesetz", "baugesetz"),
    ("de", "5000 Aarau", "Welche Grenzabstände gelten für Bauten im Aargau?", "AG", "Baugesetz", "baugesetz"),
    ("de", "4051 Basel", "Brauche ich in Basel eine Bewilligung, um mein Haus umzubauen?", "BS", "Baugesetz", "bau"),
    ("fr", "1204 Genève", "Ai-je besoin d'une autorisation pour construire une véranda à Genève ?", "GE", "constructions", "construction"),
    ("fr", "1700 Fribourg", "Quelles constructions sont dispensées de permis dans le canton de Fribourg ?", "FR", "constructions", "construction"),
    ("it", "6500 Bellinzona", "Serve una licenza edilizia per una piccola tettoia in Ticino?", "TI", "edilizia", "ediliz"),
    # school laws
    ("de", "8001 Zürich", "Wie lange dauert die Schulpflicht im Kanton Zürich?", "ZH", "Volksschulgesetz", "volksschul"),
    ("de", "3011 Bern", "Darf ich mein Kind im Kanton Bern zu Hause unterrichten?", "BE", "Volksschulgesetz", "volksschul"),
    ("de", "6003 Luzern", "Ab welchem Alter beginnt im Kanton Luzern der Kindergarten?", "LU", "Volksschulbildung", "volksschul"),
    ("fr", "1204 Genève", "Jusqu'à quel âge la formation est-elle obligatoire à Genève ?", "GE", "instruction publique", "instruction publique"),
    ("it", "6900 Lugano", "Quanti anni dura la scuola obbligatoria in Ticino?", "TI", "scuola", "scuol"),
]


def main():
    items, problems = [], []
    for i, (lang, loc, q, gold) in enumerate(FEDERAL, 1):
        heads = []
        for sr, art in gold:
            acts = sources.fedlex_find_acts([sr], [], "de")
            if not acts:
                problems.append(f"F{i} no act {sr}")
                continue
            _, arts = sources.fedlex_articles(acts[0], "2026-10-15", "de")
            hit = [a for a in arts if checks.art_key(a["number"]) == art]
            if not hit:
                problems.append(f"F{i} {sr} art {art} not found")
            else:
                heads.append(f"{acts[0]['short'] or sr} {hit[0]['number']} · {hit[0]['path'].split(' › ')[-1][:60]}")
        print(f"F{i:02d} [{lang}] {q[:60]:<60} -> {' | '.join(heads)}")
        items.append({"id": f"F{i:02d}", "lang": lang, "loc": loc, "q": q, "fed": [list(g) for g in gold]})

    for i, (lang, loc, q, canton, term, stem) in enumerate(CANTONAL, 1):
        found = sources.lexfind_search(term, canton, lang if lang in sources.CANTONS[canton][1] else sources.CANTONS[canton][1][0], limit=12)
        gold = sorted({t["sr"] for t in found if stem in sources.fold(t["title"])})
        titles = [t["title"][:50] for t in found if t["sr"] in gold][:3]
        print(f"C{i:02d} [{lang}] {canton} {q[:50]:<50} -> {gold} {titles}")
        if not gold:
            problems.append(f"C{i} {canton} no act for '{term}'")
        items.append({"id": f"C{i:02d}", "lang": lang, "loc": loc, "q": q, "can": [[sr, None] for sr in gold]})

    (HERE / "questions100.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(items)} questions written. Problems ({len(problems)}):")
    for p in problems:
        print("  ", p)


if __name__ == "__main__":
    main()
