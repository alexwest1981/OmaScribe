"""EPUBCheck som *val*: kontroll av EPUB:en, med ett tydligt besked när den saknas (R05.8).

EPUBCheck är det verktyg förlagen och butikerna själva kör, och det är den enda
riktiga kontrollen av en EPUB — inte en egen uppsättning tumregler. Men det är
ett Java-program, och Java finns inte på varje dator. Därför är kontrollen ett
*val* och inte ett krav i exporten: går den inte att köra ska boken ändå skrivas,
och beskedet ska säga exakt vad som fattas och var man lägger det.

Ren Python utan Qt — `python core/epubcheck.py` provar hela vägen.
"""

import os
import re
import shutil
import subprocess

# Där epubcheck.jar letas. Den första är den egna, dokumenterade platsen; de
# övriga är där distributioner och verktygslådor brukar lägga den.
SEARCH_PATHS = (
    "~/.local/share/epubcheck/epubcheck.jar",
    "~/.local/share/java/epubcheck.jar",
    "/usr/share/java/epubcheck.jar",
    "/usr/share/epubcheck/epubcheck.jar",
    "/opt/epubcheck/epubcheck.jar",
)
ENV_VAR = "EPUBCHECK_JAR"


def find_epubcheck(paths=None, env=None, which=shutil.which) -> list | None:
    """Kommandot som kör EPUBCheck, eller None om det inte finns.

    Letar i tur och ordning: miljövariabeln EPUBCHECK_JAR, de kända platserna,
    och sist ett `epubcheck` på PATH. Returnerar hela kommandot så att anroparen
    inte behöver veta om det är en jar eller ett skalprogram.
    """
    miljö = os.environ if env is None else env
    if miljö.get(ENV_VAR):
        kandidat = os.path.expanduser(miljö[ENV_VAR])
        if os.path.isfile(kandidat):
            return ["java", "-jar", kandidat]
    for sökväg in (SEARCH_PATHS if paths is None else paths):
        kandidat = os.path.expanduser(sökväg)
        if os.path.isfile(kandidat):
            return ["java", "-jar", kandidat]
    träff = which("epubcheck")
    if träff:
        return [träff]
    return None


def java_available(which=shutil.which) -> bool:
    return which("java") is not None


def parse_output(text: str) -> dict:
    """Tolkar EPUBChecks utskrift. Ren funktion, så att den går att prova."""
    rader = [rad.rstrip() for rad in (text or "").splitlines()]
    fel = [rad for rad in rader if re.match(r"^(ERROR|FATAL)\(", rad)]
    varningar = [rad for rad in rader if rad.startswith("WARNING(")]
    rent = any("No errors or warnings" in rad for rad in rader)
    klart = any(rad.startswith("Check finished") for rad in rader)
    return {
        "ok": rent or (klart and not fel),
        "errors": len(fel),
        "warnings": len(varningar),
        "messages": (fel + varningar)[:5],
        "clean": rent,
        "finished": klart,
    }


def validate(epub_path: str, cmd=None, timeout: int = 120) -> dict:
    """Kör kontrollen och returnerar resultatet — eller varför den inte kunde köras."""
    if not os.path.isfile(epub_path):
        return {"ran": False, "reason": "missing_file", "ok": False, "messages": []}
    cmd = cmd or find_epubcheck()
    if cmd is None:
        return {"ran": False, "reason": "no_epubcheck", "ok": False,
                "java": java_available(), "messages": [], "searched": list(SEARCH_PATHS)}
    try:
        klar = subprocess.run(cmd + ["--failonwarnings=false", epub_path],
                              capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as fel:
        return {"ran": False, "reason": "run_failed", "ok": False,
                "messages": [str(fel)]}
    ut = parse_output(klar.stdout + "\n" + klar.stderr)
    ut["ran"] = True
    if not ut["finished"] and not ut["messages"]:
        # Programmet startade men svarade inte som EPUBCheck gör — trasig jar, fel
        # java, ett skalprogram som inte finns. Att då säga "inga fel" vore det
        # farligaste svaret av alla: en ren förklaring på en bok som aldrig blev
        # kontrollerad.
        ut["ran"] = False
        ut["reason"] = "unreadable_output"
        ut["messages"] = [rad for rad in (klar.stdout + klar.stderr).splitlines()
                          if rad.strip()][:3]
    return ut


def _self_test() -> int:
    import tempfile

    grönt = 0

    olika = object()   # så att ett förväntat None går att skilja från inget väntat

    def check(namn: str, fick, väntat=olika) -> None:
        nonlocal grönt
        if väntat is olika:
            assert fick, namn
        else:
            assert fick == väntat, f"{namn}: {fick!r} != {väntat!r}"
        grönt += 1

    mapp = tempfile.mkdtemp(prefix="epubcheck-")
    burk = os.path.join(mapp, "epubcheck.jar")
    with open(burk, "w", encoding="utf-8") as fil:
        fil.write("inte en riktig jar")

    check("utan epubcheck blir svaret None",
          find_epubcheck(paths=[], env={}, which=lambda _n: None), None)
    check("en känd plats hittas", find_epubcheck(paths=[burk], env={}, which=lambda _n: None),
          ["java", "-jar", burk])
    check("och miljövariabeln går före platserna",
          find_epubcheck(paths=["/finns/inte.jar"], env={ENV_VAR: burk},
                         which=lambda _n: None), ["java", "-jar", burk])
    check("en plats som inte finns hoppas över",
          find_epubcheck(paths=["/finns/inte.jar"], env={}, which=lambda _n: None), None)
    check("och ett epubcheck på PATH duger",
          find_epubcheck(paths=[], env={}, which=lambda _n: "/usr/bin/epubcheck"),
          ["/usr/bin/epubcheck"])

    rent = parse_output("No errors or warnings detected.\n")
    check("en ren bok är ren", rent["clean"] and rent["ok"] and rent["errors"] == 0)
    fel = parse_output(
        "ERROR(OPF-001): /OEBPS/content.opf(3,10): element \"meta\" missing\n"
        "WARNING(HTM-014): /OEBPS/text/ch1.xhtml(9,1): unused\n"
        "WARNING(HTM-014): /OEBPS/text/ch1.xhtml(11,1): unused\n"
        "Check finished with warnings or errors\n")
    check("fel och varningar räknas", (fel["errors"], fel["warnings"]), (1, 2))
    check("och en bok med fel är inte ok", fel["ok"], False)
    check("och meddelandena följer med", fel["messages"][0].startswith("ERROR(OPF-001)"), True)
    check("bara varningar är ändå ok",
          parse_output("WARNING(HTM-014): /x\nCheck finished with warnings or errors\n")["ok"], True)
    check("en trasig utskrift ger inga påhittade fel", parse_output("")["errors"], 0)
    trasig = parse_output("Error: Unable to access jarfile /fel/epubcheck.jar\n")
    check("och en kontroll som inte kunde läsa sin egen jar är inte klar", trasig["finished"], False)
    check("och inte heller ren", trasig["clean"], False)
    öppet = os.path.join(mapp, "öppet.epub")
    open(öppet, "wb").close()
    felläs = validate(öppet, cmd=["java", "-jar", burk])
    check("en jar som inte går att läsa ger ett skäl, inte 'inga fel'",
          felläs["reason"], "unreadable_output")
    check("och skälet bär med sig vad programmet sade", bool(felläs["messages"]), True)

    saknas = validate(os.path.join(mapp, "finns-inte.epub"), cmd=None)
    check("en fil som inte finns sägs vara borta", saknas["reason"], "missing_file")
    tom = os.path.join(mapp, "tom.epub")
    open(tom, "wb").close()
    utan = validate(tom, cmd=find_epubcheck(paths=[], env={}, which=lambda _n: None))
    check("och en tom fil utan epubcheck ger skälet", utan["reason"], "no_epubcheck")
    check("med besked om java och var den letades",
          bool("java" in utan and utan["searched"]), True)
    check("och java finns på den här datorn", isinstance(utan["java"], bool), True)
    return grönt


if __name__ == "__main__":
    print(f"epubcheck: {_self_test()} kontroller gröna")
