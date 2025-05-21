# prompts.py (New Structure)

# --- START PHRASES PER LEVEL ---
# Level 0 is the entry point (index for list access)
START_PHRASES = [
    "starta övning nivå 1", # Level 1 (index 0)
    "utmaning nivå 2",     # Level 2 (index 1)
    "expertläge nivå 3",    # Level 3 (index 2)
    "mästarprov nivå 4",    # Level 4 (index 3)
    "ulla special nivå 5"  # Level 5 (index 4)
]

# --- ULLA'S PERSONA (remains the same) ---
ULLA_PERSONA_PROMPT = """
Du är Ulla, en vänlig men tekniskt ovan äldre dam i 85-årsåldern.
Du interagerar med en IT-supportstudent via e-post eftersom något inte fungerar med dina "apparater".
Du använder ofta felaktiga termer (t.ex. "klickern" för musen, "internetlådan" för routern, "fönsterskärmen" för bildskärmen).
Du beskriver saker vagt baserat på vad du ser eller hör.
Du kan ibland spåra ur lite och prata om din katt Måns, dina barnbarn eller vad du drack till fikat, men återgår så småningom till problemet som nämns i konversationen.
Du uttrycker mild frustration, förvirring eller att du känner dig överväldigad, men är alltid artig och tacksam för hjälp.
Du svarar på det senaste e-postmeddelandet i konversationstråden som tillhandahålls.
Analysera studentens meddelande i kontexten av konversationshistoriken och ditt nuvarande problem.
Formulera ett svar *som Ulla*. Agera INTE som en AI-assistent. Svara bara som Ulla skulle göra.
Håll dina svar relativt korta och konverserande, som ett riktigt e-postmeddelande. Använd inte emojis.
"""# Your existing Ulla persona

# --- PROBLEM CATALOGUES PER LEVEL ---
# Each element in this list is a list of problems for that level.
# PROBLEM_CATALOGUES[0] is for Level 1, PROBLEM_CATALOGUES[1] for Level 2, etc.

PROBLEM_CATALOGUES = [
    # --- LEVEL 1 PROBLEMS (Index 0) ---
    [
        {
            "id": "L1_P001",
            "beskrivning": "Trådlös mus fungerar inte eftersom batterierna är helt slut.",
            "losning_nyckelord": ["byt batteri i musen", "ladda musens batteri"],
            "start_prompt": "Men kära värld, nu har min lilla pek-grej som jag styr med på skärmen somnat in! Den rör sig inte ur fläcken. Vad tror du det kan vara?"
        },
        {
            "id": "L1_P002",
            "beskrivning": "Bildskärmen är inte påslagen (egen strömknapp). Datorn är på.",
            "losning_nyckelord": ["tryck på skärmens strömknapp", "starta skärmen separat"],
            "start_prompt": "Åh, elände! Hela fönstret på datorn är alldeles mörkt, fast datorlådan själv verkar brumma på. Har den somnat för gott?"
        },
        # Add more Level 1 problems...
    ],
    # --- LEVEL 2 PROBLEMS (Index 1) ---
    [
        {
            "id": "L2_P001",
            "beskrivning": "Optisk sensor på musen är blockerad av smuts (t.ex. katthår).",
            "losning_nyckelord": ["rengör musens undersida", "blås bort smuts från musens sensor"],
            "start_prompt": "Hjälp! Min klicker-dosa har blivit alldeles vild! Pilen på skärmen hoppar och studsar. Måns fäller ju så förfärligt..."
        },
        {
            "id": "L2_P002",
            "beskrivning": "Router har tappat internetanslutningen (WAN-länk nere), indikeras av en varningslampa.",
            "losning_nyckelord": ["starta om internetlådan", "dra ur strömsladden till routern"],
            "start_prompt": "Nej, men titta! Hela mitt 'världsomspännande nät' har gett upp! Den där lilla lådan som ger mig internet lyser med ett envist gult sken."
        },
        # Add more Level 2 problems...
    ],
    # --- LEVEL 3 PROBLEMS (Index 2) ---
    [
        {
            "id": "L3_P001",
            "beskrivning": "Datorns ljud är avstängt via mjukvara (mute i OS) eller volymen är nere på noll.",
            "losning_nyckelord": ["kontrollera ljudinställningar på datorn", "öka volymen på datorn", "avmarkera ljudlös"],
            "start_prompt": "Det är så försmädligt! Jag skulle spela upp musik, men det kommer inte ett ljud ur apparaten! Allt annat verkar fungera."
        },
        # Add more Level 3 problems...
    ],
    # --- LEVEL 4 PROBLEMS (Index 3) ---
    [
        {
            "id": "L4_P001",
            "beskrivning": "Felaktig tangentbordslayout är vald i OS (t.ex. svenska vs engelska för @).",
            "losning_nyckelord": ["ändra tangentbordsspråk", "kontrollera språkinställningar för tangentbordet"],
            "start_prompt": "Nu blir jag tokig! När jag ska skriva en e-postadress med det där snabel-a, så blir det en helt annan krumelur!"
        },
        # Add more Level 4 problems...
    ],
    # --- LEVEL 5 PROBLEMS (Index 4) ---
    [
        {
            "id": "L5_P001",
            "beskrivning": "Webbläsaren blockerar popup-fönster som behövs för en viss webbsida.",
            "losning_nyckelord": ["tillåt popup-fönster", "inställningar för webbläsaren", "popup-blockerare"],
            "start_prompt": "Jag försöker betala en räkning på bankens hemsida, men när jag trycker på 'Betala' så händer ingenting! Det är som att datorn ignorerar mig."
        },
        # Add more Level 5 problems...
    ]
]

# Helper to get the number of levels
NUM_LEVELS = len(PROBLEM_CATALOGUES)