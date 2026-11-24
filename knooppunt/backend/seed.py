"""Vooraf geladen demo-vak "Databanken".

Werkt 100% zonder API-key: alle kernvragen én één gecachete brugvraag staan
hier lokaal in de database.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from models import (
    Achievement,
    Course,
    Edge,
    Node,
    Question,
    UsageMetric,
    utcnow,
)

ACHIEVEMENTS: list[dict[str, str]] = [
    {
        "code": "FIRST_FOUNDATION",
        "title": "Eerste Fundament",
        "description": "Je eerste knoop succesvol afgerond en groen gekleurd.",
        "icon": "Award",
    },
    {
        "code": "BRIDGE_BUILDER",
        "title": "Bruggenbouwer",
        "description": "3 keer op rij een 20%-verbindingsvraag correct beantwoord.",
        "icon": "GitMerge",
    },
    {
        "code": "BRANCH_COMPLETE",
        "title": "Tak Voltooid",
        "description": "Een volledige keten van basisconcept tot eindconcept afgerond.",
        "icon": "GitBranch",
    },
    {
        "code": "NO_ILLUSION",
        "title": "Geen Illusie",
        "description": "Een knoop in een poging foutloos (100%) afgerond.",
        "icon": "Sparkles",
    },
    {
        "code": "COURSE_MASTERY",
        "title": "Vakbeheersing",
        "description": "100% van de knopen in een vak groen gekleurd.",
        "icon": "Trophy",
    },
]


def _mcq(
    prompt: str, options: list[str], correct: int, explanation: str
) -> dict[str, Any]:
    """Kleine helper: 'correct' is de 1-gebaseerde index van het juiste antwoord."""
    return {
        "prompt": prompt,
        "options": options,
        "correct_answer": options[correct - 1],
        "explanation": explanation,
    }


DEMO_NODES: list[dict[str, Any]] = [
    {
        "title": "Relationeel Model & Sleutels",
        "summary": (
            "Het relationele model beschrijft data als tabellen (relaties) met "
            "rijen en kolommen. Elke tabel heeft een primaire sleutel die elke "
            "rij uniek identificeert, en vreemde sleutels leggen relaties tussen "
            "tabellen. Deze basis vormt het fundament voor normalisatie en SQL."
        ),
        "key_points": [
            "Een primaire sleutel identificeert elke rij uniek en is nooit NULL.",
            "Een vreemde sleutel verwijst naar de primaire sleutel van een andere tabel.",
            "Kandidaatsleutels zijn alle minimale unieke identificaties waaruit je kiest.",
            "Referentiële integriteit waarborgt dat elke verwijzing naar een bestaande rij wijst.",
        ],
        "questions": [
            _mcq(
                "Wat doet een primaire sleutel in een relationele tabel?",
                [
                    "Hij identificeert elke rij uniek binnen de tabel.",
                    "Hij verwijst naar de primaire sleutel van een andere tabel.",
                    "Hij bepaalt de sorteervolgorde van de rijen.",
                    "Hij slaat de geschiedenis van wijzigingen op.",
                ],
                1,
                "Een primaire sleutel is uniek en niet-NULL, zodat elke rij ondubbelzinnig te identificeren is.",
            ),
            _mcq(
                "Waarvoor dient een vreemde sleutel?",
                [
                    "Om een relatie te leggen naar de primaire sleutel van een andere tabel.",
                    "Om dubbele rijen automatisch te verwijderen.",
                    "Om alle kolommen van een tabel uniek te maken.",
                    "Om de tabel fysiek te indexeren op elke kolom.",
                ],
                1,
                "Een vreemde sleutel verwijst naar een primaire sleutel en bewaakt zo de referentiële integriteit.",
            ),
            _mcq(
                "Wat is een kandidaatsleutel?",
                [
                    "Een kolom of kolomcombinatie die uniek kan zijn en waaruit de primaire sleutel wordt gekozen.",
                    "Een sleutel die enkel gebruikt wordt in een JOIN.",
                    "Een sleutel die altijd uit één kolom bestaat.",
                    "Een tijdelijke sleutel die alleen tijdens het importeren bestaat.",
                ],
                1,
                "Elke minimale unieke identificatie is een kandidaatsleutel; daaruit kiest men één primaire sleutel.",
            ),
            _mcq(
                "Wat betekent referentiële integriteit?",
                [
                    "Elke vreemde-sleutelwaarde verwijst naar een bestaande rij (of is NULL).",
                    "Elke tabel heeft minstens één index.",
                    "Elke rij heeft een unieke waarde in alle kolommen.",
                    "Verwijderde rijen worden automatisch gearchiveerd.",
                ],
                1,
                "De database weigert een vreemde sleutel die naar een niet-bestaande rij zou verwijzen.",
            ),
            _mcq(
                "Wat is een samengestelde sleutel?",
                [
                    "Een primaire sleutel die uit twee of meer kolommen bestaat.",
                    "Een sleutel die naar twee databases tegelijk verwijst.",
                    "Een unieke index zonder primaire sleutel.",
                    "Een sleutel die automatisch wordt gegenereerd door de database.",
                ],
                1,
                "Bij een samengestelde sleutel is de combinatie van kolommen uniek, niet elke kolom afzonderlijk.",
            ),
        ],
    },
    {
        "title": "Normalisatie (1NF - 3NF)",
        "summary": (
            "Normalisatie herstructureert tabellen om redundantie en anomalieën "
            "te vermijden. De eerste normaalvorm eist atomaire waarden, de tweede "
            "verwijdert partiële afhankelijkheden en de derde verwijdert "
            "transitieve afhankelijkheden op niet-sleutelkolommen."
        ),
        "key_points": [
            "1NF: alle waarden zijn atomair en er zijn geen herhalende groepen.",
            "2NF: elke niet-sleutelkolom hangt volledig af van de volledige sleutel.",
            "3NF: geen transitieve afhankelijkheden tussen niet-sleutelkolommen.",
            "Normaliseren voorkomt update-, insert- en delete-anomalieën.",
        ],
        "questions": [
            _mcq(
                "Waaraan voldoet een tabel in de eerste normaalvorm (1NF)?",
                [
                    "Alle waarden zijn atomair en er zijn geen herhalende groepen.",
                    "Elke niet-sleutelkolom hangt volledig af van de hele sleutel.",
                    "Er bestaan geen transitieve afhankelijkheden.",
                    "Elke vreemde sleutel is geïndexeerd.",
                ],
                1,
                "1NF verbiedt lijsten of herhalende groepen in één cel; elke waarde moet atomair zijn.",
            ),
            _mcq(
                "Wat eist de tweede normaalvorm (2NF) bovenop 1NF?",
                [
                    "Dat elke niet-sleutelkolom volledig afhankelijk is van de volledige primaire sleutel.",
                    "Dat er geen vreemde sleutels meer zijn.",
                    "Dat elke tabel precies één kolom heeft.",
                    "Dat alle kolommen een index hebben.",
                ],
                1,
                "2NF verwijdert partiële afhankelijkheden: geen kolom mag slechts van een deel van een samengestelde sleutel afhangen.",
            ),
            _mcq(
                "Wat is een transitieve afhankelijkheid?",
                [
                    "Een niet-sleutelkolom die afhangt van een andere niet-sleutelkolom.",
                    "Een vreemde sleutel die naar dezelfde tabel verwijst.",
                    "Een primaire sleutel die uit twee kolommen bestaat.",
                    "Een index die automatisch wordt aangemaakt.",
                ],
                1,
                "Bij een transitieve afhankelijkheid bereik je een kolom via een andere niet-sleutelkolom; 3NF verbiedt dat.",
            ),
            _mcq(
                "Wat is een partiële afhankelijkheid?",
                [
                    "Een niet-sleutelkolom die slechts van een deel van een samengestelde sleutel afhangt.",
                    "Een kolom die deels NULL is.",
                    "Een relatie tussen twee tabellen zonder vreemde sleutel.",
                    "Een index die slechts de helft van de rijen bevat.",
                ],
                1,
                "Bij een samengestelde sleutel mag een niet-sleutelkolom niet enkel van één onderdeel afhangen.",
            ),
            _mcq(
                "Welk probleem lost normaliseren vooral op?",
                [
                    "Overbodige opslag en update-, insert- en delete-anomalieën.",
                    "Trage netwerkverbindingen.",
                    "Het ontbreken van een gebruikersinterface.",
                    "Het automatisch back-uppen van de database.",
                ],
                1,
                "Door redundantie te verwijderen treden minder tegenstrijdige of onvolledige gegevens op.",
            ),
        ],
    },
    {
        "title": "SQL Joins & Relaties",
        "summary": (
            "Joins combineren rijen uit meerdere tabellen op basis van een "
            "joinvoorwaarde. INNER JOIN levert enkel matches, LEFT JOIN behoudt "
            "alle rijen van links, en CROSS JOIN maakt het cartesisch product. "
            "Self joins vergelijken een tabel met zichzelf."
        ),
        "key_points": [
            "INNER JOIN: enkel rijen met een match in beide tabellen.",
            "LEFT JOIN: alle rijen links, aangevuld met NULL bij geen match.",
            "De ON-clausule definieert de joinvoorwaarde.",
            "Self joins gebruik je voor hiërarchieën binnen één tabel.",
        ],
        "questions": [
            _mcq(
                "Welke rijen levert een INNER JOIN?",
                [
                    "Alleen rijen waarvoor de joinvoorwaarde in beide tabellen een match heeft.",
                    "Alle rijen uit de linker tabel, met NULL voor ontbrekende rechterwaarden.",
                    "Alle rijen uit beide tabellen, ongeacht een match.",
                    "Alleen rijen zonder match.",
                ],
                1,
                "Een INNER JOIN filtert rijen weg die geen tegenpartij hebben in de andere tabel.",
            ),
            _mcq(
                "Wat doet een LEFT JOIN?",
                [
                    "Alle rijen uit de linker tabel behouden en rechts NULL invullen bij geen match.",
                    "Alleen de rijen uit de rechter tabel behouden.",
                    "Rijen verwijderen die niet matchen.",
                    "Elke rij uit beide tabellen combineren.",
                ],
                1,
                "De linker tabel is leidend; ontbrekende rechterwaarden worden NULL.",
            ),
            _mcq(
                "Wat is het resultaat van een CROSS JOIN?",
                [
                    "Het cartesisch product: elk paar rijen uit beide tabellen.",
                    "Alleen de gedeelde rijen van beide tabellen.",
                    "Een foutmelding, omdat CROSS JOIN niet bestaat.",
                    "De som van het aantal rijen van beide tabellen.",
                ],
                1,
                "Bij een CROSS JOIN wordt elke rij van de ene tabel met elke rij van de andere gecombineerd.",
            ),
            _mcq(
                "Wanneer gebruik je een self join?",
                [
                    "Om een tabel met zichzelf te vergelijken, bijvoorbeeld voor een hiërarchie.",
                    "Om een tabel twee keer op te slaan.",
                    "Om een tabel te verwijderen zonder cascade.",
                    "Om een index op de primaire sleutel te maken.",
                ],
                1,
                "Met aliassen vergelijk je rijen binnen dezelfde tabel, bijvoorbeeld manager en medewerker.",
            ),
            _mcq(
                "Waarvoor dient de ON-clausule bij een JOIN?",
                [
                    "Om de voorwaarde te bepalen waarop rijen aan elkaar gekoppeld worden.",
                    "Om de kolommen te sorteren.",
                    "Om de tabelnaam te wijzigen.",
                    "Om de transactie te committen.",
                ],
                1,
                "De ON-clausule beschrijft de gelijkheid of voorwaarde tussen kolommen van beide tabellen.",
            ),
        ],
    },
    {
        "title": "Indexering (B-Trees)",
        "summary": (
            "Een index is een hulpmiddel dat het opzoeken van rijen versnelt, "
            "meestal via een gebalanceerde B-tree. De winst bij lezen weegt "
            "tegen extra opslag en tragere schrijfacties. Clusterindexen bepalen "
            "de fysieke rijvolgorde; samengestelde indexen werken via leftmost prefix."
        ),
        "key_points": [
            "Een index versnelt zoeken op de geïndexeerde kolommen.",
            "Elke index kost opslag en vertraagt INSERT/UPDATE/DELETE.",
            "Een B-tree blijft gebalanceerd, dus logaritmische opzoektijd.",
            "Bij een samengestelde index (a, b) werkt vooral de leftmost prefix.",
        ],
        "questions": [
            _mcq(
                "Wat is het doel van een database-index?",
                [
                    "Het versnellen van het opzoeken van rijen op basis van één of meer kolommen.",
                    "Het automatisch normaliseren van tabellen.",
                    "Het versleutelen van gevoelige kolommen.",
                    "Het verwijderen van dubbele rijen.",
                ],
                1,
                "Een index is een extra datastructuur die het zoeken op die kolommen goedkoper maakt.",
            ),
            _mcq(
                "Welke kost heeft een index?",
                [
                    "Extra opslag en tragere schrijfacties, omdat de index moet worden bijgewerkt.",
                    "Tragere leesacties op alle kolommen.",
                    "Meer netwerkverkeer bij elke SELECT.",
                    "Verplichte normalisatie tot 3NF.",
                ],
                1,
                "Bij elke wijziging moet de index mee worden onderhouden, wat ruimte en tijd kost.",
            ),
            _mcq(
                "Waarom is een B-tree geschikt voor indexen?",
                [
                    "Hij blijft gebalanceerd, zodat zoeken, invoegen en verwijderen logaritmisch blijven.",
                    "Hij slaat alle rijen in één blok op.",
                    "Hij sorteert alleen tekstkolommen.",
                    "Hij werkt zonder vergelijkingen.",
                ],
                1,
                "Door de gebalanceerde boom blijft de hoogte klein, ook bij veel rijen.",
            ),
            _mcq(
                "Wat kenmerkt een clusterindex?",
                [
                    "Hij bepaalt de fysieke volgorde van de tabelrijen; er is er maximaal één per tabel.",
                    "Hij bestaat alleen op vreemde sleutels.",
                    "Er kunnen er honderden per tabel bestaan.",
                    "Hij wordt alleen gebruikt bij JOINs.",
                ],
                1,
                "Omdat de fysieke rijvolgorde maar één keer kan, bestaat er maximaal één clusterindex per tabel.",
            ),
            _mcq(
                "Op welke kolommen kan een samengestelde index (a, b) efficiënt filteren?",
                [
                    "Op a, of op a en b samen (leftmost prefix).",
                    "Alleen op b.",
                    "Alleen op b en a samen, in die volgorde.",
                    "Op elke willekeurige combinatie, ongeacht volgorde.",
                ],
                1,
                "De index begint met a; daarom profiteer je van a alleen of van a plus b, maar niet van b alleen.",
            ),
        ],
    },
    {
        "title": "Transacties & ACID",
        "summary": (
            "Een transactie bundelt meerdere bewerkingen tot één geheel. ACID "
            "garandeert atomiciteit, consistentie, isolatie en duurzaamheid: "
            "alles of niets, geldige toestanden, geen interferentie en "
            "blijvende resultaten na een commit."
        ),
        "key_points": [
            "Atomicity: de hele transactie slaagt of wordt teruggedraaid.",
            "Consistency: constraints en regels blijven gelden.",
            "Isolation: gelijktijdige transacties hinderen elkaar niet.",
            "Durability: een commit overleeft een crash.",
        ],
        "questions": [
            _mcq(
                "Wat betekent atomiciteit (A) in ACID?",
                [
                    "Een transactie wordt volledig uitgevoerd of volledig teruggedraaid.",
                    "Een transactie is altijd sneller dan losse queries.",
                    "Een transactie mag nooit gelijktijdig lopen.",
                    "Een transactie wordt automatisch geïndexeerd.",
                ],
                1,
                "Atomiciteit maakt de transactie ondeelbaar: een fout halverwege draait alles terug.",
            ),
            _mcq(
                "Wat betekent consistentie (C) in ACID?",
                [
                    "De database gaat van de ene geldige toestand naar de andere, met behoud van constraints.",
                    "Alle gebruikers zien altijd dezelfde gegevens.",
                    "Elke transactie duurt even lang.",
                    "Alle tabellen hebben dezelfde structuur.",
                ],
                1,
                "Constraints, triggers en regels moeten na de transactie nog steeds gelden.",
            ),
            _mcq(
                "Wat betekent isolatie (I) in ACID?",
                [
                    "Gelijktijdige transacties beïnvloeden elkaars tussenresultaten niet alsof ze na elkaar draaien.",
                    "Een transactie draait op een geïsoleerde server.",
                    "Gegevens worden versleuteld op schijf.",
                    "Elke transactie heeft een eigen index.",
                ],
                1,
                "Isolatieniveaus bepalen in welke mate tussentijdse wijzigingen zichtbaar zijn voor anderen.",
            ),
            _mcq(
                "Wat betekent duurzaamheid (D) in ACID?",
                [
                    "Na een commit blijven wijzigingen behouden, ook na een crash.",
                    "Een transactie kan oneindig lang duren.",
                    "Gegevens worden nooit verwijderd.",
                    "Elke wijziging wordt direct geïndexeerd.",
                ],
                1,
                "Na een succesvolle commit zijn wijzigingen persistent, bijvoorbeeld via het write-ahead log.",
            ),
            _mcq(
                "Wat doet ROLLBACK?",
                [
                    "Hij draait alle wijzigingen van de huidige transactie terug.",
                    "Hij bevestigt alle wijzigingen definitief.",
                    "Hij maakt een volledige back-up van de database.",
                    "Hij herstart de databaseserver.",
                ],
                1,
                "ROLLBACK herstelt de toestand van vóór de transactie; COMMIT bevestigt juist.",
            ),
        ],
    },
    {
        "title": "Query Optimalisatie",
        "summary": (
            "Query-optimalisatie maakt queries sneller zonder de resultaten te "
            "wijzigen. Je leest uitvoeringsplannen, gebruikt passende indexen, "
            "vermijdt onnodige kolommen en zorgt dat filtervoorwaarden "
            "sargable zijn zodat indexen daadwerkelijk worden gebruikt."
        ),
        "key_points": [
            "Gebruik EXPLAIN om het gekozen uitvoeringsplan te lezen.",
            "Vermijd SELECT * en haal enkel de nodige kolommen op.",
            "Houd predikaten sargable: geen functies op geïndexeerde kolommen.",
            "Beperk resultaten met LIMIT waar dat functioneel mag.",
        ],
        "questions": [
            _mcq(
                "Wat toont EXPLAIN in de meeste relationele databases?",
                [
                    "Het uitvoeringsplan dat de database voor een query kiest.",
                    "De volledige inhoud van alle tabellen.",
                    "De lijst van alle gebruikers en rechten.",
                    "De geschiedenis van alle transacties.",
                ],
                1,
                "Met EXPLAIN zie je onder meer welke indexen en joins de optimizer gebruikt.",
            ),
            _mcq(
                "Waarom is SELECT * vaak onzuinig?",
                [
                    "Het haalt onnodige kolommen op, wat extra I/O en geheugen kost.",
                    "Het is syntactisch ongeldig in SQL.",
                    "Het blokkeert alle andere queries.",
                    "Het verwijdert automatisch indexen.",
                ],
                1,
                "Enkel de kolommen ophalen die je nodig hebt, verkleint het datavolume en kan index-only scans mogelijk maken.",
            ),
            _mcq(
                "Wat maakt een filtervoorwaarde 'sargable'?",
                [
                    "De index op de kolom kan worden gebruikt, bijvoorbeeld doordat er geen functie op de kolom staat.",
                    "De voorwaarde bevat altijd een LIKE met een wildcard vooraan.",
                    "De voorwaarde staat in de SELECT-lijst.",
                    "De voorwaarde gebruikt alleen OR.",
                ],
                1,
                "Bij een niet-sargable voorwaarde moet de database de functie op elke rij toepassen en vervalt het indexvoordeel.",
            ),
            _mcq(
                "Hoe kun je een dure sortering vaak vermijden?",
                [
                    "Met een passende index op de kolommen waarop je filtert en sorteert.",
                    "Door alle kolommen als tekst op te slaan.",
                    "Door SELECT * te gebruiken.",
                    "Door de query in een transactie te zetten.",
                ],
                1,
                "Een index levert de rijen al in de gewenste volgorde aan, waardoor een aparte sort kan vervallen.",
            ),
            _mcq(
                "Waarom is LIMIT nuttig?",
                [
                    "Het beperkt het aantal opgehaalde rijen, zodat onnodig werk achterwege blijft.",
                    "Het versnelt INSERT-statements.",
                    "Het maakt kolommen automatisch uniek.",
                    "Het schakelt de query-cache uit.",
                ],
                1,
                "Als je slechts een deel van de rijen nodig hebt, voorkomt LIMIT dat de database de rest nog verwerkt.",
            ),
        ],
    },
]

DEMO_STATUSES = [
    "completed",
    "completed",
    "available",
    "locked",
    "locked",
    "locked",
]

# (source-index, target-index, relation_label) — indices in DEMO_NODES.
DEMO_EDGES = [
    (0, 1, "is voorwaarde voor"),
    (0, 2, "vormt basis voor"),
    (1, 3, "beinvloedt structuur van"),
    (2, 3, "versnelt"),
    (2, 4, "gebruikt operaties in"),
    (3, 5, "maakt mogelijk"),
    (4, 5, "begrenst"),
]

DEMO_BRIDGE = {
    "prompt": (
        "INNER JOIN koppelt rijen via een gelijkheid. Welke eigenschap van het "
        "relationele model maakt die koppeling betrouwbaar en betekenisvol?"
    ),
    "options": [
        "De vreemde sleutel in de ene tabel verwijst naar de primaire sleutel van de andere tabel.",
        "Elke tabel heeft een automatisch gegenereerde sorteerindex.",
        "Alle kolommen hebben dezelfde naam in beide tabellen.",
        "De database slaat de joinresultaten permanent op.",
    ],
    "correct_answer": (
        "De vreemde sleutel in de ene tabel verwijst naar de primaire sleutel van de andere tabel."
    ),
    "explanation": (
        "De joinvoorwaarde koppelt de vreemde sleutel aan de primaire sleutel; "
        "referentiële integriteit garandeert dat elke verwijzing naar een "
        "bestaande rij wijst."
    ),
}


def ensure_achievements(db: Session) -> None:
    existing = {row.code for row in db.query(Achievement).all()}
    for definition in ACHIEVEMENTS:
        if definition["code"] not in existing:
            db.add(Achievement(**definition))
    db.commit()


def _seed_demo_course(db: Session) -> None:
    course = Course(
        title="Databanken",
        description=(
            "Relationele databases: van het relationele model en normalisatie "
            "tot joins, indexering, transacties en query-optimalisatie."
        ),
        source_filenames=json.dumps(
            ["databanken_hoorcollege_1.pdf", "databanken_slides.pptx"],
            ensure_ascii=False,
        ),
        raw_tokens_est=12400,
        clean_tokens_est=6100,
    )
    db.add(course)
    db.flush()

    nodes: list[Node] = []
    now = utcnow()
    for index, definition in enumerate(DEMO_NODES):
        status = DEMO_STATUSES[index]
        node = Node(
            course_id=course.id,
            temp_key=f"n{index + 1}",
            title=definition["title"],
            summary=definition["summary"],
            key_points=json.dumps(definition["key_points"], ensure_ascii=False),
            status=status,
            pos_x=0.0,
            pos_y=0.0,
            completed_at=now if status == "completed" else None,
        )
        db.add(node)
        db.flush()
        nodes.append(node)

        for question in definition["questions"]:
            db.add(
                Question(
                    node_id=node.id,
                    linked_node_id=None,
                    category="core_80",
                    question_type="mcq",
                    prompt=question["prompt"],
                    options=json.dumps(question["options"], ensure_ascii=False),
                    correct_answer=question["correct_answer"],
                    explanation=question["explanation"],
                )
            )

    for source_index, target_index, label in DEMO_EDGES:
        db.add(
            Edge(
                course_id=course.id,
                source_node_id=nodes[source_index].id,
                target_node_id=nodes[target_index].id,
                relation_label=label,
            )
        )

    # Gecachete brugvraag op knoop 3 (SQL Joins) gelinkt aan knoop 1
    # (Relationeel Model & Sleutels): de demo werkt hiermee volledig offline.
    db.add(
        Question(
            node_id=nodes[2].id,
            linked_node_id=nodes[0].id,
            category="bridge_20",
            question_type="mcq",
            prompt=DEMO_BRIDGE["prompt"],
            options=json.dumps(DEMO_BRIDGE["options"], ensure_ascii=False),
            correct_answer=DEMO_BRIDGE["correct_answer"],
            explanation=DEMO_BRIDGE["explanation"],
        )
    )

    metric = db.get(UsageMetric, 1)
    if metric is None:
        metric = UsageMetric(id=1)
        db.add(metric)
    metric.layer1_calls = 1
    metric.layer3_calls = 1
    metric.zero_ai_actions = 4
    metric.tokens_saved_est = 6300

    foundation = (
        db.query(Achievement)
        .filter(Achievement.code == "FIRST_FOUNDATION")
        .first()
    )
    if foundation is not None and foundation.unlocked_at is None:
        foundation.unlocked_at = now

    db.commit()


def seed_if_empty(db: Session) -> None:
    """Zorgt altijd voor de 5 achievements; laadt het demo-vak bij lege DB."""
    ensure_achievements(db)
    if db.query(Course).count() == 0:
        _seed_demo_course(db)
