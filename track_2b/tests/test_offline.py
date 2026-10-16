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


def test_history_keeps_last_messages_and_strips_citations():
    from alpenrecht import pipeline
    hist = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i} [3]\n\n*Rechtsinformation.*"}
            for i in range(10)]
    block = pipeline.history_block(hist, limit=6)
    assert "m3" not in block and "m4" in block and "m9" in block
    assert "Alpenrecht: m5\n" in block and "User: m4 [3]" in block  # only answers lose citations and disclaimer
    assert "*Rechtsinformation.*" in block.split("Alpenrecht: m5")[0] and "[3]" not in block.split("Alpenrecht: m5")[1].split("User:")[0]
    assert pipeline.history_block(hist, limit=0) == ""
    assert pipeline.history_block([]) == ""


def test_history_default_is_six(monkeypatch):
    from alpenrecht import config, pipeline
    assert config.HISTORY_MESSAGES == 6 or "HISTORY_MESSAGES" in __import__("os").environ
    monkeypatch.setattr(config, "HISTORY_MESSAGES", 6)
    hist = [{"role": "user", "content": f"q{i}"} for i in range(9)]
    block = pipeline.history_block(hist)
    assert "q2" not in block and all(f"q{i}" in block for i in range(3, 9))


def test_cache_cleared_when_idle_but_uploads_kept(tmp_path, monkeypatch):
    from alpenrecht import cache, config
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "KEEP_CACHE", False)
    (tmp_path / "communes").mkdir()
    (tmp_path / "uploads").mkdir()
    law, crawl, up = tmp_path / "a.bin", tmp_path / "communes" / "docs-x.json", tmp_path / "uploads" / "u.json"
    for f in (law, crawl, up):
        f.write_text("x")
    with cache.in_use():
        with cache.in_use():
            pass
        assert law.exists()  # another question is still running
    assert not law.exists() and not crawl.exists() and up.exists()
    assert (tmp_path / "communes").is_dir()  # modules write into it without re-creating it


def test_cache_stream_clears_after_last_event(tmp_path, monkeypatch):
    from alpenrecht import cache, config
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "KEEP_CACHE", False)
    f = tmp_path / "a.txt"

    def events():
        f.write_text("x")
        yield 1
        assert f.exists()
        yield 2
    assert list(cache.stream(events())) == [1, 2]
    assert not f.exists()


def test_unsupported_amounts_compares_across_notations():
    ev = [{"text": "Die Grundgebühr beträgt Fr. 140.00 pro Jahr, für Wohnungen 90.00 Fr.; Satz 3,5 %; Fr. 1'200.–"}]
    answer = "Es kostet CHF 140.– (Wohnung 90 Franken), 3.5 % Zins, Fr. 1 200 und CHF 95.00."
    assert checks.unsupported_amounts(answer, ev) == ["CHF 95.00"]


def test_fee_companion_found_by_title_and_by_reference():
    from alpenrecht import communal
    docs = [{"title": "LC 21314 - Règlement sur les terrasses", "url": "a"},
            {"title": "LC 21318 - Règlement relatif à la taxation des empiètements sur le domaine public", "url": "b"},
            {"title": "LC 21911 - Règlement sur la gestion des déchets", "url": "c"},
            {"title": "Tarif des taxes de gestion des déchets", "url": "d"}]
    texts = ["Art. 12 La taxe est perçue selon le tarif LC 21 318."]
    got = communal.fee_companions("Combien coûte une terrasse ?", [docs[0]], docs, texts)
    assert got and got[0]["url"] == "b"
    got = communal.fee_companions("Combien coûte la taxe sur les déchets ?", [docs[2]], docs, [])
    assert [d["url"] for d in got] == ["d"]
    assert communal.fee_companions("Wie adoptiere ich ein Kind?", [docs[2]], docs, []) == []


def test_tariff_table_split_into_items_without_truncation():
    rows = "".join(f"4.{i} Gebühr Nummer {i}\nGrundgebühr pro Jahr {i}0.00\nZuschlag pro Monat {i}.50\n" + "x " * 300 + "\n"
                   for i in range(1, 10))
    text = ("Art. 1 Zweck\nDieses Reglement regelt Gebühren.\n\nArt. 2 Tarif\nDie Gebühren richten sich nach dem Tarif.\n\n"
            "Art. 3 Inkrafttreten\nSofort.\n\nArt. 4\n" + rows + "4.9 164 \n165 Parkkartengebühren\npro Jahr 264.00\n")
    arts = sources.split_articles(text)
    last = [a for a in arts if "Parkkartengeb" in a["number"]]
    assert last and last[0]["number"].startswith("Tarif 4.9") and "264.00" in last[0]["text"]
    assert checks.art_key(last[0]["number"]) == "tarif4.9"
