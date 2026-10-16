"""Offline checks (no network, no API key): python -m pytest -q tests"""
from alpenrecht import apertus, checks, sources, verify


def test_art_key():
    assert checks.art_key("Art. 257d") == "257d"
    assert checks.art_key("art. 32 abis") == "32abis"
    assert checks.art_key("§ 5") == "5"
    assert checks.art_key("Anhang 1") == "anhang1"  # an annex never passes for Art. 1


def test_annex_becomes_its_own_section():
    text = ("Art. 1 Zweck\nDieses Reglement regelt die Hundetaxe.\n\nArt. 2 Taxe\nDie Taxe richtet sich nach dem\n"
            "Tarif im Anhang.\n\nArt. 3 Inkrafttreten\nDieses Reglement tritt am 1. Januar in Kraft.\n\n"
            "Anhang 1\nHundetaxe pro Jahr: CHF 120.\n")
    arts = sources.split_articles(text)
    numbers = [a["number"] for a in arts]
    assert "Anhang 1" in numbers
    assert "CHF 120" in arts[numbers.index("Anhang 1")]["text"]
    # a wrapped line starting with "Tarif" mid-sentence is not a heading
    art2 = arts[numbers.index("Art. 2")]["text"]
    assert "Tarif im Anhang" in art2


def test_relevance_filter_keeps_federal_top_picks(monkeypatch):
    ev = [{"id": i, "level": "federal" if i < 3 else "cantonal", "law": "X", "number": f"Art. {i}",
           "text": f"Art. {i} text"} for i in range(1, 7)]
    monkeypatch.setattr(apertus, "chat", lambda *a, **k: "[5]")
    kept = [e["id"] for e in verify.relevant_sources("q", ev)]
    assert 5 in kept and 1 in kept and 2 in kept


def test_relevance_filter_survives_api_error(monkeypatch):
    ev = [{"id": i, "level": "federal", "law": "X", "number": f"Art. {i}", "text": "t"} for i in range(1, 6)]

    def boom(*a, **k):
        raise apertus.ApertusError("down")
    monkeypatch.setattr(apertus, "chat", boom)
    assert verify.relevant_sources("q", ev) == ev
