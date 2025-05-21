# prompts.py

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
"""

PROBLEM_KATALOG = [
    {
        "id": "S001", # Changed ID prefix for "Subtle"
        "beskrivning": "Trådlös mus fungerar inte; batteriet är slut.", # Precise technical description (for your reference)
        "losning_nyckelord": ["batteri", "ladda", "ström till musen"], # Slightly broader, focuses on power
        "start_prompt": "Men kära nån, nu har den där lilla saken jag pekar med på skärmen slutat fungera igen! Den är helt tyst och stilla. Jag bytte ju den där lilla glaspinnen i den för inte så länge sen, trodde jag. Kanske den är ledsen på mig?"
        # Subtle hints: "tyst och stilla" (no light, no movement). "Glaspinnen" is Ulla's term for battery.
        # "Inte så länge sen" could be a misremembering, common for battery issues.
    },
    {
        "id": "S002",
        "beskrivning": "Optisk mus beter sig oberäkneligt på grund av smuts/hår på sensorn.", # Precise
        "losning_nyckelord": ["smuts under", "rengöra linsen", "hår ivägen", "blåsa rent"], # Focus on obstruction
        "start_prompt": "Hjälp mig snälla! När jag försöker klicka på mina kortspel på datorn så far pilen runt som en yr höna! Ibland stannar den, ibland hoppar den till ett helt annat ställe. Det är som den har fått ett eget liv! Måns låg just på skrivbordet, men han är ju så renlig av sig..."
        # Subtle hints: "yr höna" implies erratic movement. Mentioning Måns is a slight, indirect clue to pet hair.
        # Focuses on the effect (cursor movement) more than Ulla inspecting the mouse directly.
    },
    {
        "id": "S003",
        "beskrivning": "Router har ingen internetanslutning (t.ex. WAN-problem, ISP-problem, fast orange lampa).", # Precise
        "losning_nyckelord": ["internetlådan", "starta om", "kontakta leverantören", "ingen anslutning", "lampan lyser konstigt"], # Broader keywords
        "start_prompt": "Stackars mig, nu har hela vida världen försvunnit från min läsplatta! Jag skulle just läsa om kungafamiljen, men det står bara att den inte kan hitta något. Den där lilla lådan som ger mig internet står bara och surar med ett konstigt sken, inte alls som den brukar. Kanske den är trött?"
        # Subtle hints: "inte kan hitta något" (no connection). "Konstigt sken" is vaguer than "fast orange".
        # "Surar" and "trött" are Ulla's personifications.
    },
    {
        "id": "S004",
        "beskrivning": "Bildskärmen är inte påslagen eller ingen signalkabel är korrekt ansluten (eller fel ingång vald).", # Precise
        "losning_nyckelord": ["skärmen ström", "kabel till skärmen", "tryck på knappen", "annan ingång", "ingen bild"], # Keywords related to screen power/signal
        "start_prompt": "Åh, elände! Jag skulle just titta på mina foton från semestern, men hela fönstret på datorn är alldeles mörkt. Datorlådan själv verkar brumma på som vanligt, jag hör den. Men inte ett knyst från skärmen. Har den gått och lagt sig mitt på dagen?"
        # Subtle hints: "mörkt fönster" but "datorlådan brummar" (PC on, monitor issue).
        # "Gått och lagt sig" implies no power or signal. Doesn't mention checking cables.
    },
    {
        "id": "S005", # New problem example
        "beskrivning": "Ljudet fungerar inte på datorn; högtalarna kan vara avstängda, urkopplade, eller ljudet är satt på ljudlös (mute).",
        "losning_nyckelord": ["inget ljud", "högtalare", "volym", "ljudlös", "kabel till ljud"],
        "start_prompt": "Men för all del! Jag skulle just lyssna på P4 på datorn som barnbarnet visade, men det är knäpptyst! Alla de där fina melodierna är borta. Jag har provat att vifta med klickern överallt på skärmen men det hjälper inte. Är det fel på mina öron idag, tro?"
        # Subtle hints: "knäpptyst". "Vifta med klickern" (trying to click volume icons, perhaps).
        # Misdirection: "fel på mina öron".
    },
    {
        "id": "S006", # New problem example
        "beskrivning": "Tangentbordet skriver fel tecken eller inga alls (t.ex. NumLock på, fel språklayout, smuts under tangenter, dålig anslutning för trådlöst).",
        "losning_nyckelord": ["tangentbord", "fel tecken", "skriver inte", "num lock", "språkinställning", "rengöra tangentbordet"],
        "start_prompt": "Nu är det väl ändå förargligt! När jag försöker skriva ett brev till min väninna Agda så blir bokstäverna alldeles konstiga, eller så kommer det inga alls! Ibland blir det bara siffror fast jag trycker på bokstäver. Har apparaten fått solsting?"
        # Subtle hints: "konstiga bokstäver" (layout?), "siffror fast jag trycker på bokstäver" (NumLock on a compact keyboard).
    }
]