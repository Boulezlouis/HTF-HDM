# VOLLEDIGE BOUWINSTRUCTIE — KNOOPPUNT (ZERO-DECISION SPEC)

Je bent een senior full-stack engineer. Jouw taak is het **exact** implementeren van de applicatie **KnoopPunt** volgens deze specificatie.

## HARDE REGELS (NIET VAN AFWIJKEN)
1. **Neem GEEN eigen architectuur-, library- of UI-beslissingen.** Volg elke bestandsnaam, library, tabel, kolom, endpoint en UI-regel exact zoals hieronder beschreven.
2. **Schrijf GEEN placeholder-code, geen `TODO`'s en geen mock-functies** waar echte logica gevraagd wordt. Elke functie moet direct werkend zijn.
3. **Bouw GEEN chatbot.** Er mag nergens een open chat-interface bestaan.
4. **Houd je strikt aan de 3-lagen AI-scheiding:**
   - **Laag 1 (licht model):** enkel 1x bij upload/aanmaken van een vak.
   - **Laag 2 (0 AI):** alle navigatie, graaflogica, 80/20-selectie, scoreberekening, statusupdates en achievements.
   - **Laag 3 (sterker redeneermodel):** uitsluitend on-demand bij (a) het genereren van een nog niet gecachete `bridge_20`-vraag tussen twee knopen en (b) het beoordelen van een `short_open` vraag of het geven van een gerichte hint bij een fout antwoord.
5. Werk exact in de volgorde **Stap 1 t/m Stap 10** onderaan dit document.

---

## 1. VASTE TECH STACK & PACKAGES

### Backend (`/backend`)
- Python 3.11+
- `fastapi==0.115.6`
- `uvicorn[standard]==0.34.0`
- `sqlalchemy==2.0.36`
- `pydantic==2.10.4`
- `pydantic-settings==2.7.0`
- `python-multipart==0.0.20`
- `markitdown[pptx]>=0.1.0`
- `pdfplumber==0.11.5`
- `openai>=1.58.0` (gebruikt voor elke OpenAI-compatibele endpoint: DeepSeek, Gemini OpenAI-compat, OpenRouter, Ollama, etc.)
- `python-dotenv==1.0.1`

### Frontend (`/frontend`)
- Vite + React 18 + TypeScript
- `tailwindcss` (v3.4+) + `postcss` + `autoprefixer`
- `@xyflow/react`
- `@dagrejs/dagre`
- `lucide-react`

---

## 2. EXACTE MAPPENSTRUCTUUR

Maak exact deze projectstructuur aan:

```text
knooppunt/
├── .env.example
├── backend/
│   ├── requirements.txt
│   ├── main.py                   # FastAPI app, CORS, lifespan (DB init + seed)
│   ├── config.py                 # Pydantic settings uit .env
│   ├── database.py               # SQLite engine & SessionLocal
│   ├── models.py                 # SQLAlchemy ORM-modellen
│   ├── schemas.py                # Pydantic request/response schema's
│   ├── docs2md.py                # Lokale PDF/PPTX -> schone Markdown + SHA-256 cache
│   ├── ai_service.py             # Laag 1 & Laag 3 OpenAI-compat calls + JSON validatie
│   ├── graph_engine.py           # Laag 2 deterministische logica (status, 80/20, achievements)
│   ├── seed.py                   # Vooraf geladen demo-vak "Databanken"
│   └── routers/
│       ├── __init__.py
│       ├── courses.py            # /api/courses endpoints
│       ├── nodes.py              # /api/nodes endpoints
│       ├── achievements.py       # /api/achievements endpoint
│       └── metrics.py            # /api/metrics endpoint (zuinigheidsindicator)
└── frontend/
    ├── package.json
    ├── vite.config.ts            # Proxy /api -> http://localhost:8000
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.tsx
        ├── index.css             # Tailwind + @xyflow/react/dist/style.css
        ├── types.ts              # TypeScript interfaces exact gelijk aan API-contract
        ├── api.ts                # Fetch wrappers voor alle REST endpoints
        ├── utils/
        │   └── layout.ts         # Dagre top-down layout voor React Flow
        ├── App.tsx               # Master-Detail layout, state, toasts
        └── components/
            ├── Sidebar.tsx           # Uitklapbare 260px sidebar (vakken, + Nieuw vak, achievements)
            ├── GraphCanvas.tsx       # React Flow canvas, zoom/center controls, legende, metrics badge
            ├── ConceptNode.tsx       # Custom React Flow node (locked/available/completed + active highlight)
            ├── NodeDrawer.tsx        # Slide-over drawer rechts (Tab 1: Kern & Verbanden, Tab 2: 80/20 Check)
            ├── CreateCourseModal.tsx # Modal met vaknaam, drag&drop PDF/PPTX, 4-stappen voortgang
            ├── AchievementsModal.tsx # Volledig overzicht achievements
            └── ToastContainer.tsx    # Subtiele meldingen rechtsboven
```

---

## 3. OMGEVINGSVARIABELEN (`.env.example`)

```env
DATABASE_URL=sqlite:///./knooppunt.db

# Laag 1: Licht, snel model voor eenmalige graaf-extractie
LAYER1_API_KEY=your_api_key_here
LAYER1_BASE_URL=https://api.deepseek.com/v1
LAYER1_MODEL=deepseek-chat

# Laag 3: Sterker redeneermodel voor 20%-verbindingsvragen & korte open beoordeling/hints
LAYER3_API_KEY=your_api_key_here
LAYER3_BASE_URL=https://api.deepseek.com/v1
LAYER3_MODEL=deepseek-reasoner

# Documentvoorverwerking
DOCS_REPEAT_THRESHOLD=0.5
```

**Belangrijk:** `ai_service.py` moet een duidelijke HTTP 400/503 foutmelding teruggeven als `LAYER1_API_KEY` ontbreekt of nog op `your_api_key_here` staat bij het aanmaken van een nieuw vak. Het **demo-vak moet echter 100% werken zonder API-key**, omdat alle vragen en 1 gecachete `bridge_20`-vraag al in `seed.py` staan.

---

## 4. EXACT DATABASEMODEL (`backend/models.py`)

Gebruik SQLite met `PRAGMA foreign_keys=ON` (ingesteld via een SQLAlchemy `connect` event listener in `database.py`). Definieer exact deze 8 tabellen:

1. **`courses`**
   - `id`: Integer, Primary Key, autoincrement
   - `title`: String(200), not null
   - `description`: Text, default `""`
   - `source_filenames`: Text (JSON array van strings), default `"[]"`
   - `raw_tokens_est`: Integer, default `0`
   - `clean_tokens_est`: Integer, default `0`
   - `created_at`: DateTime (UTC), default `utcnow`

2. **`nodes`**
   - `id`: Integer, Primary Key, autoincrement
   - `course_id`: Integer, ForeignKey(`courses.id`, ondelete=`CASCADE`), not null
   - `temp_key`: String(64), nullable (gebruikt tijdens JSON-import om edges te mappen)
   - `title`: String(200), not null
   - `summary`: Text, not null
   - `key_points`: Text (JSON array van 3 tot 5 strings), not null
   - `status`: String(20), not null, waarden strikt `'locked' | 'available' | 'completed'`
   - `pos_x`: Float, default `0.0`
   - `pos_y`: Float, default `0.0`
   - `completed_at`: DateTime, nullable

3. **`edges`**
   - `id`: Integer, Primary Key, autoincrement
   - `course_id`: Integer, ForeignKey(`courses.id`, ondelete=`CASCADE`), not null
   - `source_node_id`: Integer, ForeignKey(`nodes.id`, ondelete=`CASCADE`), not null
   - `target_node_id`: Integer, ForeignKey(`nodes.id`, ondelete=`CASCADE`), not null
   - `relation_label`: String(120), default `"bouwt voort op"`

4. **`questions`**
   - `id`: Integer, Primary Key, autoincrement
   - `node_id`: Integer, ForeignKey(`nodes.id`, ondelete=`CASCADE`), not null
   - `linked_node_id`: Integer, ForeignKey(`nodes.id`, ondelete=`SET NULL`), nullable
   - `category`: String(20), not null, waarden strikt `'core_80' | 'bridge_20'`
   - `question_type`: String(20), not null, waarden strikt `'mcq' | 'short_open'`
   - `prompt`: Text, not null
   - `options`: Text (JSON array van 4 strings bij `mcq`, of `"[]"` bij `short_open`), not null
   - `correct_answer`: Text, not null (exacte optietekst bij `mcq`, of modelantwoord bij `short_open`)
   - `explanation`: Text, not null

5. **`quiz_attempts`**
   - `id`: Integer, Primary Key, autoincrement
   - `node_id`: Integer, ForeignKey(`nodes.id`, ondelete=`CASCADE`), not null
   - `score_percentage`: Float, not null
   - `passed`: Boolean, not null
   - `bridge_correct`: Boolean, nullable (`None` indien de quiz geen `bridge_20`-vraag had)
   - `created_at`: DateTime (UTC), default `utcnow`

6. **`achievements`**
   - `id`: Integer, Primary Key, autoincrement
   - `code`: String(50), unique, not null
   - `title`: String(100), not null
   - `description`: Text, not null
   - `icon`: String(50), not null (naam van een Lucide-icoon: `'Award'`, `'GitMerge'`, `'GitBranch'`, `'Sparkles'`, `'Trophy'`)
   - `unlocked_at`: DateTime, nullable

7. **`document_cache`**
   - `file_hash`: String(64), Primary Key (SHA-256 hex digest van raw bytes)
   - `filename`: String(255), not null
   - `clean_markdown`: Text, not null
   - `speaker_notes`: Text, default `""`
   - `raw_tokens_est`: Integer, not null
   - `clean_tokens_est`: Integer, not null
   - `created_at`: DateTime (UTC), default `utcnow`

8. **`usage_metrics`** (1 enkele rij met `id=1`, voor de live jury-zuinigheidsindicator)
   - `id`: Integer, Primary Key, default `1`
   - `layer1_calls`: Integer, default `0`
   - `layer3_calls`: Integer, default `0`
   - `zero_ai_actions`: Integer, default `0`
   - `tokens_saved_est`: Integer, default `0`

---

## 5. DOCUMENTVOORVERWERKING (`backend/docs2md.py`)

Implementeer zowel een herbruikbare functie `process_file(file_bytes: bytes, filename: str, db: Session, repeat_threshold: float = 0.5, include_notes: bool = False) -> dict` als een CLI-entrypoint (`python docs2md.py <bestand> --drempel 0.5`).

### Exacte verwerkingsstappen
1. **SHA-256 Cache-check:** Bereken `hashlib.sha256(file_bytes).hexdigest()`. Als deze `file_hash` in `document_cache` staat: geef direct het gecachete resultaat terug (`cached: True`), zonder opnieuw te parsen.
2. **Extractie per pagina/slide (lokaal, 0 tokens):**
   - **`.pdf`:** Gebruik `pdfplumber.open(io.BytesIO(file_bytes))`. Haal per pagina `page.extract_text() or ""` op als lijst `pages: list[str]`. Als de totale geextraheerde tekst over alle pagina's korter is dan 50 tekens, gooi een `ValueError("Deze PDF bevat geen tekstlaag (gescande PDF). Gebruik een tekst-PDF of zet eerst om met Docling OCR.")`.
   - **`.pptx`:**
     - Gebruik `MarkItDown(enable_plugins=False).convert_stream(io.BytesIO(file_bytes), file_extension=".pptx")` voor de hoofdtekst. Splits slides op slide-markers (`<!-- Slide number:` of `\n---\n`, of fallback per `#`-sectie).
     - Haal sprekersnotities apart op indien aanwezig in de `### Notes:` secties van MarkItDown: verplaats ze naar `speaker_notes` en verwijder ze uit de hoofdtekst (tenzij `include_notes=True`).
   - Andere extensies: gooi `ValueError("Alleen .pdf en .pptx worden ondersteund.")`.
3. **Bereken `raw_tokens_est`:** `len(raw_full_text) // 4`.
4. **Opschoonregels (in exact deze volgorde):**
   - **Afbeeldingen strippen:** Verwijder alle Markdown image-tags met regex `r'!\[[^\]]*\]\([^\)]*\)'`.
   - **Losse paginanummers verwijderen:** Verwijder elke regel die (na `.strip()`) matcht met:
     - `r'^\d{1,4}$'`
     - `r'^(pagina|page|slide|dia)\s*\d+(\s*(van|of|/)\s*\d+)?$'` (case-insensitive)
     - `r'^\d+\s*/\s*\d+$'`
   - **Herhaalde headers/footers verwijderen (`repeat_threshold`, standaard `0.5`):** Tel voor elke unieke genormaliseerde regel (lowercase, gestript) op hoeveel pagina's/slides die voorkomt. Indien `len(pages) >= 3` en `(aantal_paginas_met_regel / len(pages)) >= repeat_threshold`, verwijder die regel uit alle pagina's.
   - **Titelpagina samenvatten:** Neem de eerste niet-lege pagina (pagina 0). Extraheer max 2 eerste niet-lege regels als een contextregel: `# Context: <samengevoegde titel>` en vervang pagina 0 hierdoor.
   - **Lege/triviale slides overslaan:** Sla elke vervolgpagina over waarvan het aantal woorden (`len(re.findall(r'\w+', page_text))`) kleiner is dan `3`.
   - **Witruimte comprimeren:** Vervang 3+ opeenvolgende newlines door `\n\n` en strip overbodige spaties.
5. **Bereken `clean_tokens_est`:** `len(clean_markdown) // 4`.
6. **Opslaan in `document_cache`** en verhoog `usage_metrics.tokens_saved_est += max(0, raw_tokens_est - clean_tokens_est)`.
7. Retourneer dict: `{"clean_markdown": ..., "speaker_notes": ..., "raw_tokens_est": ..., "clean_tokens_est": ..., "cached": False}`.

---

## 6. AI-SERVICE (`backend/ai_service.py`)

Gebruik de `openai.OpenAI` client met twee aparte functies (Laag 1 en Laag 3). Verhoog bij elke effectieve API-call direct `usage_metrics.layer1_calls` of `usage_metrics.layer3_calls` in de database.

### 6.1 Laag 1 — `generate_course_graph(course_title: str, clean_markdown: str, db: Session) -> dict`
- Gebruikt `LAYER1_BASE_URL`, `LAYER1_API_KEY`, `LAYER1_MODEL`.
- `temperature=0.2`, `response_format={"type": "json_object"}`.
- Kap `clean_markdown` veilig af op max 60.000 tekens als de input extreem groot is (met vermelding in logs).
- **Systeemprompt (exact gebruiken):**
  > Je bent een onderwijskundig curriculum-architect. Zet het aangeleverde cursusmateriaal in het Nederlands om in een compacte, gerichte Knowledge Graph (DAG zonder cycli). Geef UITSLUITEND geldig JSON terug zonder extra tekst.
  > Regels:
  > - Maak tussen 5 en 10 kernconcepten (`nodes`), afhankelijk van de inhoud.
  > - Leg gerichte afhankelijkheden (`edges`) van basisconcept (`source`) naar vervolgconcept (`target`), zonder cycli. Minstens 1 knoop heeft geen inkomende edges (startknoop).
  > - Per knoop: een korte, scanbare `summary` (max 3 zinnen) en 3 tot 5 `key_points`.
  > - Per knoop: exact 5 `core_questions` (meerkeuzevragen `mcq` met 4 opties, exact 1 juist antwoord dat letterlijk overeenkomt met een van de 4 opties, en een korte `explanation` van max 2 zinnen).
- **Verplicht JSON-uitvoerformaat:**
  ```json
  {
    "description": "Korte omschrijving van het vak (1 zin)",
    "nodes": [
      {
        "temp_key": "n1",
        "title": "Korte concepttitel",
        "summary": "Max 3 heldere zinnen.",
        "key_points": ["Punt 1", "Punt 2", "Punt 3"],
        "core_questions": [
          {
            "prompt": "Vraagtekst?",
            "options": ["Optie A", "Optie B", "Optie C", "Optie D"],
            "correct_answer": "Optie A",
            "explanation": "Waarom Optie A juist is."
          }
        ]
      }
    ],
    "edges": [
      {
        "source": "n1",
        "target": "n2",
        "relation_label": "is voorwaarde voor"
      }
    ]
  }
  ```
- **Validatie na ontvangst:** Controleer met Pydantic. Verwijder ongeldige edges (niet-bestaande keys of self-loops) en breek eventuele cycli deterministisch (via DFS cycle check) voor opslag in SQLite.

### 6.2 Laag 3 — `generate_bridge_question(prev_node: Node, curr_node: Node, relation_hint: str, db: Session) -> dict`
- Gebruikt `LAYER3_BASE_URL`, `LAYER3_API_KEY`, `LAYER3_MODEL`.
- **Context-beperking (cruciaal voor zuinigheid):** Stuur NOOIT de volledige cursus mee! Stuur enkel: `prev_node.title`, `prev_node.summary`, `curr_node.title`, `curr_node.summary` en `relation_hint`.
- `response_format={"type": "json_object"}`.
- **Systeemprompt (exact gebruiken):**
  > Je bent een kritische examinator. Maak in het Nederlands exact EEN verbindingsvraag (`mcq` met 4 opties) die toetst of de student begrijpt hoe het vorige concept (`prev_node`) direct samenhangt met of invloed heeft op het huidige concept (`curr_node`). Vermijd triviale definitievragen; toets inzicht in het verband. Geef UITSLUITEND geldig JSON terug:
  > `{"prompt": "...", "options": ["...", "...", "...", "..."], "correct_answer": "...", "explanation": "..."}`

### 6.3 Laag 3 — `evaluate_open_answer_or_hint(question: Question, user_answer: str, node: Node, db: Session) -> dict`
- Enkel gebruikt indien `question.question_type == "short_open"`.
- Stuurt enkel `question.prompt`, `question.correct_answer`, `user_answer`, `node.summary`.
- Retourneert strikt JSON: `{"is_correct": true/false, "feedback": "Korte, gerichte uitleg waarom de redenering klopt of waar de denkfout zit (max 2 zinnen)."}`.

---

## 7. DETERMINISTISCHE GRAAFLOGICA — LAAG 2 (`backend/graph_engine.py`, 0 AI)

Elke functie hieronder draait op pure Python/SQL zonder AI-calls. Elke aangeroepen actie vanuit de endpoints verhoogt `usage_metrics.zero_ai_actions += 1`.

### 7.1 Initiele statusberekening bij vak-aanmaak (`compute_initial_statuses`)
- Voor elke knoop $N$ in het vak:
  - Tel het aantal inkomende edges (`target_node_id == N.id`).
  - Indien `0`: zet `N.status = 'available'`.
  - Anders: zet `N.status = 'locked'`.
- Veiligheidsnet: als door een vreemde graaf geen enkele knoop `available` is, zet de eerste knoop op `available`.

### 7.2 Status-updates na slagen (`unlock_dependent_nodes`)
- Wanneer knoop $N$ op `completed` wordt gezet (`completed_at = utcnow()`):
  - Zoek alle knopen $T$ waarvoor een edge `(N -> T)` bestaat en `T.status == 'locked'`.
  - Voor elke kandidaat $T$: haal alle directe voorgangers $P$ op (`Edge(P -> T)`).
  - Indien **alle** directe voorgangers $P$ status `'completed'` hebben, zet `T.status = 'available'`.
  - Retourneer de lijst van nieuw ontgrendelde `node_id`s.

### 7.3 80/20-Quizselectie (`build_80_20_quiz(node_id: int, db: Session)`)
1. Haal alle `core_80`-vragen op voor knoop $N$.
2. Zoek via **BFS achteruit** over `Edge` alle voorgaande knopen op afstand **1 stap** en **2 stappen** van $N$ die `status == 'completed'` hebben.
   - Prioriteit: kies bij voorkeur een voltooide directe voorganger (afstand 1). Zo niet, kies een voltooide voorganger op afstand 2.
3. **Indien een voltooide voorganger $P$ gevonden is:**
   - Zoek in `questions` naar een bestaande `bridge_20`-vraag met `node_id == N.id` en `linked_node_id == P.id`.
   - **Cache hit (0 tokens):** Gebruik deze bestaande vraag.
   - **Cache miss:** Roep 1x `ai_service.generate_bridge_question(P, N, relation_label, db)` aan en sla het resultaat op in `questions` (`category='bridge_20'`, `linked_node_id=P.id`).
   - Stel de quiz samen uit: **4 vragen uit `core_80`** + **1 vraag `bridge_20`** (totaal 5 vragen, `bridge_20` als laatste vraag zodat de student eerst de kern checkt en dan de brug slaat).
4. **Indien GEEN voltooide voorganger $P$ bestaat (bijv. startknoop):**
   - Stel de quiz samen uit: **5 vragen uit `core_80`** (100% op $N$).

### 7.4 Quiz-beoordeling (`grade_quiz`)
- Vergelijk voor `mcq`-vragen exact (na `.strip()`) met `correct_answer` (**0 AI**).
- Enkel voor `short_open`-vragen: roep `ai_service.evaluate_open_answer_or_hint` aan.
- Bereken `score_percentage = round((correct_count / total_questions) * 100, 1)`.
- `passed = score_percentage >= 80.0`.
- Bepaal `bridge_correct`: `True`/`False` als er een `bridge_20`-vraag in de quiz zat, anders `None`.
- Sla `QuizAttempt` op.
- Indien `passed` is `True`: zet `node.status = 'completed'`, `node.completed_at = utcnow()`, en voer `unlock_dependent_nodes` uit.
- Voer direct `check_and_unlock_achievements(db, node.course_id, attempt)` uit en retourneer de lijst met **nieuw ontgrendelde** achievements (zodat de frontend toasts kan tonen).

### 7.5 Deterministische Achievement-Engine (`check_and_unlock_achievements`)
Pre-seed deze exact 5 achievements in `achievements` (met `unlocked_at = None`):
1. `FIRST_FOUNDATION` — *"Eerste Fundament"* — *"Je eerste knoop succesvol afgerond en groen gekleurd."* (`Award`)
   - Conditie: minstens 1 `Node` in de DB heeft `status == 'completed'`.
2. `BRIDGE_BUILDER` — *"Bruggenbouwer"* — *"3 keer op rij een 20%-verbindingsvraag correct beantwoord."* (`GitMerge`)
   - Conditie: de laatste 3 `QuizAttempt`-rijen waarbij `bridge_correct IS NOT NULL` (gesorteerd op `created_at DESC`) hebben allemaal `bridge_correct == True`.
3. `BRANCH_COMPLETE` — *"Tak Voltooid"* — *"Een volledige keten van basisconcept tot eindconcept afgerond."* (`GitBranch`)
   - Conditie: in het huidige vak bestaat een gericht pad van een startknoop (0 inkomende edges) naar een eindknoop (0 uitgaande edges) van lengte $\ge 2$ knopen waarbij **elke** knoop op het pad `status == 'completed'` heeft (check via DFS over enkel `completed` knopen).
4. `NO_ILLUSION` — *"Geen Illusie"* — *"Een knoop in een poging foutloos (100%) afgerond."* (`Sparkles`)
   - Conditie: voor `attempt.node_id` is het totaal aantal `QuizAttempt`-rijen gelijk aan `1` en `attempt.score_percentage == 100.0`.
5. `COURSE_MASTERY` — *"Vakbeheersing"* — *"100% van de knopen in een vak groen gekleurd."* (`Trophy`)
   - Conditie: in `course_id` zijn er $\ge 1$ knopen en `0` knopen met `status != 'completed'`.

---

## 8. EXACT API-CONTRACT (`backend/routers/*`)

Alle endpoints hebben prefix `/api`. CORS toestaan voor `http://localhost:5173`.

1. **`GET /api/courses`**
   - Response: lijst van `{ id, title, description, source_filenames: string[], total_nodes, completed_nodes, progress_percentage, raw_tokens_est, clean_tokens_est, created_at }`
2. **`POST /api/courses`** (`multipart/form-data`)
   - Velden: `title: str` (Form), `files: list[UploadFile]` (minstens 1 `.pdf` of `.pptx`).
   - Flow:
     1. Draai `docs2md.process_file` op elk bestand en voeg de schone Markdown samen.
     2. Draai 1x `ai_service.generate_course_graph`.
     3. Sla `Course`, `Node`s, `Edge`s en `Question`s (`core_80`) op.
     4. Draai `graph_engine.compute_initial_statuses`.
   - Response (`201`): het aangemaakte course-object (zelfde formaat als item uit `GET /api/courses`).
3. **`DELETE /api/courses/{course_id}`**
   - Verwijdert vak (cascade op nodes/edges/questions/attempts). Response: `{"deleted": true}`.
4. **`GET /api/courses/{course_id}/graph`**
   - Verhoogt `zero_ai_actions += 1`.
   - Response:
     ```json
     {
       "course": { "id": 1, "title": "...", "total_nodes": 6, "completed_nodes": 2, "progress_percentage": 33 },
       "nodes": [
         { "id": 1, "title": "...", "status": "completed", "pos_x": 0, "pos_y": 0 }
       ],
       "edges": [
         { "id": 1, "source_node_id": 1, "target_node_id": 2, "relation_label": "is voorwaarde voor" }
       ]
     }
     ```
5. **`GET /api/nodes/{node_id}`**
   - Verhoogt `zero_ai_actions += 1`.
   - Bouwt via `graph_engine.build_80_20_quiz(node_id, db)` de quiz op.
   - Response:
     ```json
     {
       "id": 2,
       "course_id": 1,
       "title": "Normalisatie",
       "summary": "...",
       "key_points": ["...", "..."],
       "status": "available",
       "prerequisites": [
         { "id": 1, "title": "Relationeel Model & Sleutels", "status": "completed" }
       ],
       "quiz": [
         {
           "id": 10,
           "category": "core_80",
           "question_type": "mcq",
           "linked_node_title": null,
           "prompt": "...",
           "options": ["...", "...", "...", "..."]
         },
         {
           "id": 15,
           "category": "bridge_20",
           "question_type": "mcq",
           "linked_node_title": "Relationeel Model & Sleutels",
           "prompt": "...",
           "options": ["...", "...", "...", "..."]
         }
       ]
     }
     ```
   - **Belangrijk:** Stuur `correct_answer` NIET mee in `GET /api/nodes/{node_id}`!
6. **`POST /api/nodes/{node_id}/submit`**
   - Request JSON: `{ "answers": [{ "question_id": 10, "answer": "Optie A" }] }`
   - Verhoogt `zero_ai_actions += 1` (bij pure MCQ).
   - Response JSON:
     ```json
     {
       "score_percentage": 80.0,
       "passed": true,
       "node_status": "completed",
       "results": [
         {
           "question_id": 10,
           "is_correct": true,
           "correct_answer": "Optie A",
           "explanation": "..."
         }
       ],
       "unlocked_node_ids": [4],
       "newly_unlocked_achievements": [
         { "code": "FIRST_FOUNDATION", "title": "Eerste Fundament", "description": "...", "icon": "Award" }
       ]
     }
     ```
7. **`GET /api/achievements`**
   - Response: lijst van alle 5 achievements met `code, title, description, icon, unlocked_at`.
8. **`GET /api/metrics`**
   - Response: `{ "layer1_calls": int, "layer3_calls": int, "zero_ai_actions": int, "tokens_saved_est": int }`.

---

## 9. DEMO-SEED VAK (`backend/seed.py`)

Laad bij lege database automatisch een volledig Nederlands demo-vak **"Databanken"** in, zodat de demo direct rijk oogt zonder eerst te uploaden:
- **6 knopen** met echte, inhoudelijk correcte samenvattingen, 3 tot 4 `key_points` en 5 `core_80` MCQ-vragen per knoop (totaal 30 kernvragen):
  1. `Relationeel Model & Sleutels` — status: **`completed`** (groen)
  2. `Normalisatie (1NF - 3NF)` — status: **`completed`** (groen)
  3. `SQL Joins & Relaties` — status: **`available`** (accentkleur — ideaal om live in de demo aan te klikken!)
  4. `Indexering (B-Trees)` — status: **`locked`**
  5. `Transacties & ACID` — status: **`locked`**
  6. `Query Optimalisatie` — status: **`locked`**
- **7 edges:**
  - `1 -> 2` (`"is voorwaarde voor"`)
  - `1 -> 3` (`"vormt basis voor"`)
  - `2 -> 4` (`"beinvloedt structuur van"`)
  - `3 -> 4` (`"versnelt"`)
  - `3 -> 5` (`"gebruikt operaties in"`)
  - `4 -> 6` (`"maakt mogelijk"`)
  - `5 -> 6` (`"begrenst"`)
- **Pre-cached `bridge_20` vraag** op knoop 3 (`SQL Joins & Relaties`) gelinkt aan knoop 1 (`Relationeel Model & Sleutels`), zodat de 80/20-demo op knoop 3 zelfs **offline / met 0 extra API-calls** direct het label *"Terugkoppeling naar: Relationeel Model & Sleutels"* toont!
- Zet `raw_tokens_est = 12400`, `clean_tokens_est = 6100` en `usage_metrics` initieel op `layer1_calls = 1`, `layer3_calls = 1`, `zero_ai_actions = 4`, `tokens_saved_est = 6300`.
- Zet achievement `FIRST_FOUNDATION` op reeds ontgrendeld (`unlocked_at = utcnow()`), de overige 4 op `None`.

---

## 10. FRONTEND & UI/UX SPECIFICATIE (`/frontend`)

Gebruik een rustige, moderne **lichte/neutrale studie-stijl** (slate/wit met smaragdgroen voor voltooid en indigo voor beschikbaar/actief).

### 10.1 Master-Detail Layout (`App.tsx`)
- Volledige schermhoogte (`h-screen w-screen overflow-hidden flex bg-slate-50`).
- **Links: Uitklapbare Sidebar (`Sidebar.tsx`):**
  - Open: `w-[260px] shrink-0 border-r border-slate-200 bg-white flex flex-col transition-all duration-200`.
  - Ingeklapt: `w-14` met een vaste knop bovenaan om weer uit te klappen (`PanelLeftClose` / `PanelLeftOpen`).
  - Inhoud (wanneer open):
    1. Logo + titel **KnoopPunt** + inklapknop.
    2. Primaire knop **`+ Nieuw vak aanmaken`** (opent `CreateCourseModal`).
    3. Sectie **`MIJN VAKKEN`**: lijst van alle vakken. Per vak: vaknaam, percentage (`33%`), een subtiel groen voortgangsbalkje, en een hover-verwijderknopje (prullenbak met bevestiging). Het actieve vak is visueel gemarkeerd. Klikken laadt direct `GET /api/courses/:id/graph` zonder paginaverversing.
    4. Onderaan sectie **`MIJN ACHIEVEMENTS`**: toont de 2 meest recent behaalde achievements (of *"Nog geen achievements"*) + een knop *"Bekijk alle (X/5)"* die `AchievementsModal` opent.

### 10.2 Hoofdcanvas (`GraphCanvas.tsx` + `ConceptNode.tsx` + `utils/layout.ts`)
- **Header boven het canvas:** Toont `[Naam Vak]`, voortgang (`Voortgang: X/Y knopen (Z%)`), en rechts een compacte **Zuinigheidsindicator-pill** (gehaald uit `GET /api/metrics`), bijv.:
  `AI-calls: 1 Graaf | 1 Redenering | Zonder AI: 14 | Bespaard: ~6.3k tokens`
- **Automatische Dagre-layout (`utils/layout.ts`):**
  - Bereken bij het laden van de graaf automatisch `x, y` posities met `@dagrejs/dagre` (`rankdir: 'TB'`, `nodesep: 60`, `ranksep: 90`, `nodeWidth: 230`, `nodeHeight: 74`).
  - Verschuif posities met `-nodeWidth/2` en `-nodeHeight/2` voor React Flow.
- **Custom Node (`ConceptNode.tsx`):**
  - **`completed`:** Zachte smaragdgroene achtergrond (`bg-emerald-50`), groene rand (`border-emerald-500`), groen vinkje (`CheckCircle2`).
  - **`available`:** Witte achtergrond (`bg-white`), heldere indigo rand (`border-indigo-500`), status-icoon (`CircleDot`).
  - **`locked`:** Lichtgrijze gedempte stijl (`bg-slate-100 text-slate-400 border-slate-300`), slot-icoon (`Lock`). Blijft wel klikbaar om te previewen (toont zachte melding in de drawer om eerst voorgangers af te ronden).
  - **Actieve selectie (VERPLICHT):** Wanneer `selectedNodeId === node.id` (dus deze knoop is geopend in de drawer), **licht de node duidelijk op** met een heldere focus-ring en schaduw (`ring-4 ring-indigo-400/50 scale-[1.03] shadow-lg transition-all`).
- **Edges:** Gerichte pijlen (`MarkerType.ArrowClosed`), smoothstep curves, subtiel `relation_label` (toon label netjes als kleine pill op de lijn of bij hover).
- **Controls onderaan het canvas:** React Flow zoom-in, zoom-out, fit-view (centreer) knoppen + een compacte **Legende** (`Voltooid`, `Beschikbaar`, `Nog niet bereikt`).

### 10.3 Knoop-Drawer (`NodeDrawer.tsx`)
- Slide-over paneel aan de rechterkant (`w-[440px] max-w-full bg-white border-l border-slate-200 shadow-2xl h-full flex flex-col`) dat naast/over de rechterkant van het canvas opent, terwijl de graaf links zichtbaar blijft.
- Header: knoop-titel, statusbadge, sluitknop (`X`).
- Indien status `locked`: toon bovenaan een rustige infobalk *"Tip: rond eerst de voorgaande knopen af voor het beste begrip."* (de student mag de kern nog steeds bekijken).
- **Twee tabs:**
  - **Tab 1 — `Kern & Verbanden`:**
    - Beknopte samenvatting (`summary`).
    - Genummerde/bulleted lijst met de 3 tot 5 `key_points`.
    - Visuele chips voor `prerequisites` (*"Hangt samen met: [Knoopnaam]"*) — klikken op een chip schakelt direct naar die voorgaande knoop en laat die knoop op de graaf oplichten.
    - Onderaan grote CTA-knop: **`Start 80/20 Check`** (schakelt naar Tab 2).
  - **Tab 2 — `De 80/20 Check`:**
    - Toont **een vraag tegelijk** met een duidelijke voortgangsbalk (`Vraag 1/5`) en `Vorige`/`Volgende` navigatie voor maximale focus.
    - Elke vraag toont een duidelijke badge:
      - `category === 'core_80'` -> grijze/indigo pill **`Kernvraag (80%)`**
      - `category === 'bridge_20'` -> amber/violet pill **`Terugkoppeling naar: {linked_node_title} (20%)`**
    - Na invullen van de laatste vraag: klik op **`Controleer antwoorden`** -> `POST /api/nodes/:id/submit`.
    - Resultaatscherm:
      - Toont score (`80%` / `4 van 5 juist`), of de knoop **groen gekleurd** is (`passed === true`), en per vraag de directe feedback/uitleg (`explanation`) — zeker bij foute antwoorden duidelijk uitgelicht.
      - Knop **`Terug naar de graaf`** (sluit drawer; graaf en sidebar zijn al live bijgewerkt) of **`Opnieuw proberen`** bij score kleiner dan $80\%$.

### 10.4 Nieuw Vak Modal (`CreateCourseModal.tsx`)
- Inputveld voor `Vaknaam`.
- File-upload zone (drag & drop of selectieknop) voor een of meerdere `.pdf` / `.pptx` bestanden.
- Tijdens het indienen (`POST /api/courses`) toont de modal een 4-stappen voortgangsindicator:
  1. `Tekst lokaal uitlezen & opschonen (0 tokens)`
  2. `Kernconcepten bepalen (Laag 1)`
  3. `Verbanden & 80%-vragen genereren`
  4. `Interactieve graaf opbouwen`
  (Laat de stappen visueel vooruitlopen tijdens de async request en spring naar stap 4 bij response; toon heldere foutmelding bij HTTP 400/500).
- Na succes: sluit de modal, voeg het nieuwe vak toe aan de sidebar, selecteer het direct en open de nieuwe graaf.

### 10.5 Subtiele Toasts (`ToastContainer.tsx`)
- Vaste positie rechtsboven (`fixed top-4 right-4 z-50`).
- Wanneer `POST /api/nodes/:id/submit` items teruggeeft in `newly_unlocked_achievements`, toon per achievement een rustige toast met Lucide-icoon, titel en omschrijving die na 5 seconden automatisch verdwijnt.

---

## 11. STAPSGEWIJZE UITVOERINGSVOLGORDE

Voer de implementatie exact in deze volgorde uit en schrijf volledige, direct uitvoerbare bestanden:

- **Stap 1:** Maak `.env.example` en `backend/requirements.txt`.
- **Stap 2:** Schrijf `backend/config.py`, `backend/database.py` (met SQLite `PRAGMA foreign_keys=ON`), `backend/models.py` en `backend/schemas.py`.
- **Stap 3:** Schrijf `backend/docs2md.py` met alle 6 opschoonregels, SHA-256 caching en CLI-ondersteuning.
- **Stap 4:** Schrijf `backend/ai_service.py` met Laag 1 (inclusief cycle-removal) en Laag 3 (`generate_bridge_question` + `evaluate_open_answer_or_hint`).
- **Stap 5:** Schrijf `backend/graph_engine.py` met statusbeheer, 2-staps BFS 80/20-selectie, grading en alle 5 deterministische achievements.
- **Stap 6:** Schrijf `backend/seed.py` (demo-vak "Databanken" met 6 knopen, 7 edges, 30 core-vragen + 1 gecachete bridge-vraag) en alle routers (`courses.py`, `nodes.py`, `achievements.py`, `metrics.py`) + `backend/main.py`.
- **Stap 7:** Zet de frontend op (`package.json`, `vite.config.ts` met `/api` proxy, `tailwind.config.js`, `postcss.config.js`, `index.html`, `src/main.tsx`, `src/index.css`, `src/types.ts`, `src/api.ts`, `src/utils/layout.ts`).
- **Stap 8:** Bouw de UI-componenten: `ConceptNode.tsx`, `GraphCanvas.tsx`, `Sidebar.tsx`, `NodeDrawer.tsx`, `CreateCourseModal.tsx`, `AchievementsModal.tsx`, `ToastContainer.tsx`.
- **Stap 9:** Koppel alles samen in `frontend/src/App.tsx` (inclusief live refresh van graaf, sidebar-voortgang, metrics-pill en achievement-toasts na elke quiz-submit).
- **Stap 10:** Geef onderaan exacte commando's om backend (`uvicorn main:app --reload --port 8000`) en frontend (`npm run dev`) te starten en 3 snelle verificatietests (demo-vak openen + knoop 3 groen maken, metrics controleren, nieuw PDF/PPTX vak aanmaken).