# Architectuurdocument — Interactieve Kennisgraaf (Werktitel: *KnoopPunt*)

> **Doel:** Een interactief leerplatform dat passief samenvattingen lezen vervangt door actief leren via een visuele Knowledge Graph, een 80/20-verbindingsquiz en een uiterst zuinige, gelaagde AI-architectuur.

---

## 1. Architectuurprincipes

Om binnen één dag een overtuigend Proof of Concept (PoC) te bouwen én te scoren op de hackathon-criteria (vernieuwende inzet van AI, energie- en tokenzuinigheid, schaalbaarheid), steunt het ontwerp op vier kernprincipes:

1. **Zuinige 3-lagen AI (Frugal by Design):** AI wordt nooit gebruikt voor navigatie, voortgang of eenvoudige logica. Een licht model verwerkt cursusmateriaal *eenmalig* tot een graaf; een sterker redeneermodel schakelt *enkel* in voor complexe verbanden of gerichte feedback bij fouten.
2. **Geen chatbot, maar ruimtelijk begrip:** De Knowledge Graph is de primaire interface. Studenten zien direct de structuur van een vak en hoe concepten op elkaar voortbouwen.
3. **80/20 Actieve Toetsing:** Elke knoop combineert een bondige kernuitleg met een korte check (80% huidige knoop, 20% terugkoppeling naar eerder voltooide buurknopen) om de illusie van kennis te doorbreken.
4. **Rustige, functionele beloning:** Geen overdreven gamification, wel duidelijke visuele voldoening (voltooide knopen kleuren groen) en inhoudelijke achievements die echt begrip belonen.

---

## 2. UI/UX Architectuur & Schermstructuur

De applicatie gebruikt een rustige **Master-Detail layout** bestaande uit een vaste linker-sidebar, een interactief hoofdcanvas en een contextueel zijpaneel (drawer) voor de inhoud van een knoop.

### 2.1 Hoofdlayout (Wireframe)

```text
+-----------------------------------------------------------------------------------+
|  SIDEBAR (vast, 260px)     |  HOOFDCANVAS (Interactieve Knowledge Graph)          |
|----------------------------|------------------------------------------------------|
|  [Logo] KnoopPunt          |  Header: [Naam Vak]   Voortgang: 4/10 knopen (40%)   |
|                            |------------------------------------------------------|
|  [ + Nieuw vak aanmaken ]  |                                                      |
|                            |        (o) Basisconcept A [GROEN]                    |
|  MIJN VAKKEN               |            /             \                           |
|  > [●] Databanken    40%   |           v               v                          |
|    [ ] Besturingssys 10%   |    (o) Normalisatie   (o) SQL Joins [BESCHIKBAAR]    |
|    [ ] Economie     100%   |        [GROEN]             |                         |
|                            |           \               /                          |
|                            |            v             v                           |
|                            |          (o) Indexering & Transacties [VERGRENDELD]  |
|                            |                                                      |
|----------------------------|                                                      |
|  MIJN ACHIEVEMENTS         |  [Zoom -] [Zoom +] [Centreer]    [Legende]           |
|  ★ Bruggenbouwer (3/3)     |                                                      |
|  ★ Fundament Gelegd        |                                                      |
+----------------------------+------------------------------------------------------+
```

### 2.2 De 4 Kerncomponenten van de UI

1. **Vakken-Sidebar (Links)**
   * **Vakoverzicht:** Lijst van alle aangemaakte vakken met per vak een compacte voortgangsindicator (bijv. percentage of een subtiel groen balkje).
   * **Vakselectie:** Klikken op een vak laadt direct de bijbehorende interactieve Knowledge Graph op het hoofdcanvas (zonder volledige paginaverversing).
   * **Nieuw vak aanmaken (`+ Nieuw vak`):** Opent een overzichtelijke modal waarin de student een vaknaam invult en één of meerdere cursusbestanden (PDF/PPTX) uploadt. Tijdens de eenmalige verwerking toont de modal heldere voortgangsstappen (*Tekst uitlezen → Kernconcepten bepalen → Verbanden leggen → Graaf klaar*).
   * **Achievement-balk (onderaan sidebar):** Compacte weergave van recent behaalde mijlpalen (met mogelijkheid om het volledige overzicht te openen).

2. **Interactieve Knowledge Graph (Hoofdcanvas)**
   * Vrij navigeerbaar canvas (slepen/pannen, in- en uitzoomen, automatisch centreren).
   * **Knoopstaten (duidelijk en rustig kleurgebruik):**
     * **Voltooid (Groen):** De 80/20-check is succesvol afgerond.
     * **Beschikbaar (Accentkleur / Helder omlijnd):** Alle voorvereiste knopen zijn voltooid (of het is een startknoop); klaar om te studeren.
     * **Nog niet bereikt (Lichtgrijs / Gedempt):** Onderliggende basisconcepten zijn nog niet groen. Kan wel bekeken worden voor overzicht, maar de app raadt aan eerst de voorgaande knopen af te ronden.
   * **Verbindingslijnen (Edges):** Gerichte pijlen die tonen hoe concepten op elkaar steunen (optioneel met een kort relatielabel bij hover, bijv. *"bouwt voort op"* of *"is voorwaarde voor"*).

3. **Knoop-Drawer (Slide-over paneel aan de rechterkant)**
   * Opent wanneer de student op een knoop in de graaf klikt, terwijl de graaf links zichtbaar blijft voor ruimtelijke context.
   * **Tab 1 — Kern & Verbanden:**
     * Beknopte, scanbare samenvatting van het onderwerp (geen lange muren tekst; max. 3–5 kernpunten).
     * Visuele chips met directe links naar gerelateerde voorgaande knopen (*"Hangt samen met: Basisconcept A"*).
     * Duidelijke call-to-action: **`Start 80/20 Check`**.
   * **Tab 2 — De 80/20 Check:**
     * Korte, gefocuste reeks van bijv. **5 vragen**:
       * **4 vragen (80%):** Kernvragen over de huidige knoop (meerkeuze, waar/onwaar met nuance, of korte invulvraag).
       * **1 vraag (20%):** Een expliciete **verbindingsvraag** (gelabeld als *"Terugkoppeling"*) die de huidige knoop verbindt met een eerder voltooide buurknoop uit de graaf.
     * **Directe feedback:** Bij een fout geeft de tool gerichte uitleg waarom een redenering niet klopt, in plaats van enkel *"Fout"* te tonen.
     * **Afronding:** Bij het behalen van de drempelscore (bijv. $\ge 80\%$) sluit de check af met een rustige bevestiging, kleurt de knoop direct **groen** op de graaf, en lichten nieuwe vervolgknopen op.

4. **Subtiele Meldingen (Toasts)**
   * Wanneer een student een achievement vrijspeelt (bijv. *Bruggenbouwer* of *Tak Voltooid*), verschijnt een discrete melding rechtsboven zonder de studieflow te onderbreken.

---

## 3. De 3-Lagen Zuinige AI-Architectuur

Dit is de technische én zakelijke kern van het platform. Elke laag gebruikt de lichtst mogelijke technologie die nodig is voor die taak.

```text
[Upload PDF/PPTX]
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LAAG 1: EENMALIGE VERWERKING (Lokaal + Licht AI-model)              │
│ • Lokale parser (0 tokens): tekst & structuur uit slides halen      │
│ • 1x gestructureerde call (Licht model):                            │
│   -> Nodes (concepten) + Edges (afhankelijkheden)                   │
│   -> Korte samenvattingen + 80%-basisvragen (JSON)                  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ (Opgeslagen in Database)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LAAG 2: DETERMINISTISCHE GRAAFLOGICA (0 AI / 0 Tokens)              │
│ • UI-navigatie & layoutberekening van de graaf                      │
│ • Statusbeheer (groen kleuren, unlocken van volgende knopen)        │
│ • 80/20-vragenkiezer: selecteert via graafstructuur de juiste       │
│   voorgaande knoop voor de 20%-terugkoppeling                       │
│ • Achievement-engine & voortgangsberekening voor de sidebar         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ (Enkel bij complexe verbinding / fout)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LAAG 3: ON-DEMAND REDENEERLAAG (Sterker Redeneermodel)              │
│ • Alleen getriggerd wanneer echt nodig:                             │
│   1. Genereren van de 20%-verbindingsvraag tussen knoop X en Y      │
│      (en cachen voor hergebruik!)                                   │
│   2. Evalueren van een open verbindingsantwoord of geven van een    │
│      gerichte hint wanneer een student vastloopt                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Slimme Optimalisaties voor Token- & Energiebesparing
* **Lokale voorverwerking:** PDF's en PowerPoints worden eerst lokaal geparsed; dubbele headers, voetteksten, lege slides en titelpagina's worden gestript vóórdat er ook maar één token naar een AI-model gaat.
* **Strict JSON Output:** Laag 1 vraagt één strak gestructureerd JSON-schema op (nodes, edges, samenvattingen en basisvragen in één of zo weinig mogelijk calls) in plaats van tientallen losse prompts.
* **Edge-Caching:** Zodra het redeneermodel (Laag 3) een 20%-verbindingsvraag heeft opgesteld tussen knoop A en knoop B, wordt die vraag opgeslagen bij de `Edge` in de database. De volgende keer kost die vraag **0 tokens**.
* **Geen open chatbox:** Omdat er geen vrije chatbot aanwezig is, zijn er geen eindeloze gespreksgeschiedenissen die bij elke beurt opnieuw als context-tokens verstuurd moeten worden.

---

## 4. Datamodel

Het datamodel is bewust relationeel en overzichtelijk gehouden, zodat het eenvoudig in SQLite/PostgreSQL draait tijdens de hackathon en probleemloos opschaalt naar productie.

### Entiteiten & Relaties

| Entiteit | Belangrijkste velden | Beschrijving |
| :--- | :--- | :--- |
| **`Course`** | `id`, `title`, `description`, `source_filenames`, `created_at` | Een vak in de sidebar. Bevat de globale metadata en voortgang. |
| **`Node`** | `id`, `course_id`, `title`, `summary`, `key_points` (JSON), `status` (`locked` \| `available` \| `completed`), `pos_x`, `pos_y`, `completed_at` | Een studieconcept op de interactieve graaf. |
| **`Edge`** | `id`, `course_id`, `source_node_id`, `target_node_id`, `relation_label` | Gerichte afhankelijkheid (*source* is voorkennis of bouwt op naar *target*). |
| **`Question`** | `id`, `node_id`, `linked_node_id` *(nullable)*, `category` (`core_80` \| `bridge_20`), `question_type` (`mcq` \| `short_open`), `prompt`, `options` (JSON), `correct_answer`, `explanation` | Opgeslagen vragen. Bij `bridge_20` verwijst `linked_node_id` naar de eerdere knoop. |
| **`QuizAttempt`** | `id`, `node_id`, `score_percentage`, `passed` (bool), `bridge_correct` (bool), `created_at` | Logboek van pogingen; voedt voortgang en achievements. |
| **`Achievement`** | `id`, `code`, `title`, `description`, `icon`, `unlocked_at` *(nullable)* | Inhoudelijke mijlpalen (globaal of per vak). |

### Deterministische 80/20-Selectielogica (Laag 2)
Wanneer een student op **`Start 80/20 Check`** klikt voor knoop $N$:
1. Haal **4 vragen** op uit `Question` waar `node_id == N` en `category == 'core_80'`.
2. Zoek via `Edge` alle voorgaande knopen ($P$) die leiden naar $N$ (of op maximaal 2 stappen afstand liggen) én die al de status `completed` hebben.
   * *Indien een voltooide voorgaande knoop $P$ bestaat:* Haal de gecachete `bridge_20`-vraag op voor paar $(P, N)$. Bestaat die nog niet? Roep eenmalig **Laag 3 (Redeneermodel)** aan om een gerichte verbindingsvraag tussen $P$ en $N$ te genereren en sla deze op.
   * *Indien $N$ een startknoop is zonder voorgangers:* Gebruik 5 kernvragen (100% op $N$) zodat de leerervaring niet blokkeert.

---

## 5. API-Contract & Dataflow

Alle interacties tussen de frontend en backend verlopen via een kleine set heldere REST-endpoints:

| Methode & Endpoint | Doel | AI-gebruik |
| :--- | :--- | :--- |
| `GET /api/courses` | Haalt alle vakken + berekend voortgangspercentage op voor de **sidebar**. | **0 AI** |
| `POST /api/courses` | Maakt een nieuw vak aan, leest geüploade bestanden lokaal uit en genereert de Knowledge Graph. | **Laag 1 (Licht model, eenmalig)** |
| `DELETE /api/courses/:id` | Verwijdert een vak en bijbehorende knopen/edges. | **0 AI** |
| `GET /api/courses/:id/graph` | Laadt alle `nodes`, `edges` en huidige statussen voor het **interactieve canvas**. | **0 AI** |
| `GET /api/nodes/:id` | Haalt samenvatting, buurknopen en de samengestelde 80/20-quiz op voor de **drawer**. | **0 AI** *(of 1x Laag 3 indien bridge-vraag nog niet gecachet is)* |
| `POST /api/nodes/:id/submit` | Beoordeelt de antwoorden, zet bij slagen de knoop op `completed` (groen), unlockt vervolgknopen en controleert achievements. | **0 AI** bij MCQ *(Laag 3 enkel bij open antwoord of misconceptie-hint)* |
| `GET /api/achievements` | Haalt alle ontgrendelde en nog te behalen achievements op. | **0 AI** |

---

## 6. Subtiel Achievement-Systeem (Deterministisch)

De achievement-engine draait volledig in Laag 2 (pure applicatielogica, **0 AI-tokens**) direct na elke `POST /api/nodes/:id/submit`. Achievements belonen *begrip en regelmaat*, geen oppervlakkig klikgedrag:

* **Eerste Fundament:** Je eerste knoop succesvol afgerond en groen gekleurd.
* **Bruggenbouwer:** 3 keer op rij een 20%-verbindingsvraag correct beantwoord.
* **Tak Voltooid:** Een volledige keten van basisconcept tot eindconcept binnen een vak afgerond.
* **Geen Illusie:** Een knoop in één keer foutloos afgerond zonder extra hints.
* **Vakbeheersing:** 100% van de knopen in een vak groen gekleurd.

---

## 7. Aanbevolen Tech Stack (Snel voor 1 Dag, Klaar voor Schaal)

Om in één dag een vloeiende, demo-waardige applicatie neer te zetten zonder over-engineering:

* **Frontend Framework:** Next.js (React + TypeScript) of Vite + React.
* **Styling & UI-componenten:** Tailwind CSS + shadcn/ui (voor een strakke, rustige sidebar, modals en slide-over drawer).
* **Interactieve Graaf:** **React Flow (`@xyflow/react`)** gecombineerd met **Dagre** of **ELKjs** voor automatische, propere top-down of left-to-right graafpositionering (zodat knopen nooit over elkaar heen liggen).
* **Backend & Document Parsing:**
  * *Optie A (Alles-in-één, snelst):* Next.js API Routes met `pdf-parse` / `officeparser` (leest zowel `.pdf` als `.pptx`).
  * *Optie B (Aparte Python-service):* FastAPI met `pypdf` en `python-pptx` voor nog betrouwbaardere slide-extractie.
* **Database:** SQLite met Prisma of Drizzle ORM (voor de hackathon nul setup-tijd; in productie 1-op-1 vervangbaar door PostgreSQL/Supabase).
* **AI-modellen (Model Routing):**
  * **Laag 1 (Extractie & Graaf):** Klein, snel en goedkoop model met sterke JSON-ondersteuning (bijv. *Gemini Flash-Lite* of vergelijkbaar licht model).
  * **Laag 3 (Redenering & 20%-Verbindingen):** Sterker redeneermodel (bijv. *Gemini Pro* / redeneermodel) dat uitsluitend gericht wordt aangeroepen met een piepkleine context (enkel de samenvattingen van knoop $P$ en knoop $N$, nooit de volledige cursus).

---

## 8. Token- & Energiebudget (Onderbouwing voor de Jury)

Een typisch pijnpunt van standaard AI-studieapps is dat de volledige cursus bij elke chatvraag opnieuw meegestuurd wordt. Door onze architectuur daalt het verbruik drastisch:

| Actie van de student | Klassieke AI-Chatbot | KnoopPunt (3-Lagen Architectuur) |
| :--- | :--- | :--- |
| **Cursus uploaden (100 slides)** | Volledige tekst in elke chatsessie herladen | **1x** lokaal strippen + **1x** licht model (eenmalig) |
| **Door vakken & graaf navigeren** | N.v.t. / telkens prompts typen | **0 tokens** (pure database & UI) |
| **Samenvatting & 80%-quiz maken** | Nieuwe LLM-call per quizsessie | **0 tokens** (vooraf gegenereerd & opgeslagen) |
| **20%-verbindingsvraag maken** | Volledige slides opnieuw meesturen | **Kleine call (Laag 3)** met enkel 2 korte knoop-samenvattingen + gecachet |
| **Schaalvoordeel (100 studenten, zelfde vak)** | $100 \times$ volledige verwerkingskost | **1x** graaf genereren, $100 \times$ hergebruiken |

---

## 9. Hackathon 1-Dag MVP Scope (Prioriteiten)

Om aan het einde van de dag gegarandeerd een werkende demo op het podium te hebben:

### Must-Have voor de Demo (Kern-PoC)
1. **Sidebar** met minstens 1 vooraf geladen demo-vak (zodat de jury direct een rijke graaf ziet) én een werkende knop **`+ Nieuw vak aanmaken`** waarmee live een PDF/PPTX geüpload wordt.
2. **Interactieve Graaf** (React Flow + automatische layout) waar knopen klikbaar zijn en visueel onderscheid tonen tussen *vergrendeld*, *beschikbaar* en *groen (voltooid)*.
3. **Knoop-Drawer** met compacte samenvatting + werkende **80/20-quiz** (inclusief zichtbaar label *"Terugkoppeling naar [vorige knoop]"*).
4. **Live kleurverandering:** Knoop kleurt direct groen na het halen van de quiz, volgende knoop opent, voortgang in de sidebar stijgt, en 1 achievement (*Eerste Fundament* of *Bruggenbouwer*) popt subtiel op.
5. **Zuinigheidsindicator (Bonus voor jury-impact):** Een klein teller-icoontje of debug-paneel voor tijdens de pitch dat live toont: *"AI-calls deze sessie: 1 (Graaf) + 1 (Redenering) | Graaf-acties zonder AI: 14"*.

### Nice-to-Have (Enkel als er tijd over is)
* Open-vraag beoordeling met het redeneermodel (voor de MVP kunnen de 80%-vragen meerkeuze zijn en de 20%-vraag een korte open vraag of meerkeuze-redeneervraag).
* Visueel verval (knopen die na weken zonder herhaling subtiel vervagen).
* Delen van een gegenereerde vakgraaf met medestudenten.