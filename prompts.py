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
        "id": "U001", # "Ulla's Unique Problem" prefix
        "beskrivning": "Trådlös mus fungerar inte eftersom batterierna är helt slut.", # Precise internal description
        "losning_nyckelord": ["byt batteri i musen", "ladda musens batteri", "kolla om musen behöver nya batterier"], # Action-oriented for battery
        "start_prompt": "Men kära värld, nu har min lilla pek-grej som jag styr med på skärmen somnat in helt och hållet! Den rör sig inte ur fläcken, och ingen liten lampa lyser på den heller. Jag som skulle skriva till Agda... Vad tror du det kan vara?"
        # Hints for AI: "somnat in helt", "ingen liten lampa lyser" -> power issue for a wireless device.
        # For student: Vague "pek-grej", focuses on symptom (not moving).
    },
    {
        "id": "U002",
        "beskrivning": "Optisk sensor på musen är blockerad av smuts (t.ex. katthår), vilket orsakar oberäknelig pekarrörelse.",
        "losning_nyckelord": ["rengör musens undersida", "blås bort smuts från musens sensor", "ta bort skräp under musen"], # Actions for cleaning sensor
        "start_prompt": "Åh, hjälp! Min klicker-dosa har blivit alldeles vild! Pilen på den där fönsterskärmen hoppar och studsar och gör inte alls som jag vill. Det är som den dansar jitterbugg! Måns fäller ju så förfärligt den här årstiden, det är hår överallt här hemma."
        # Hints for AI: "klicker-dosa vild", "hoppar och studsar" -> erratic sensor. "Måns fäller" -> potential for hair.
        # For student: Focus on erratic behavior, cat shedding is a general Ulla comment, not a direct clue *she* makes about the mouse.
    },
    {
        "id": "U003",
        "beskrivning": "Router har tappat internetanslutningen (WAN-länk nere), indikeras av en varningslampa (t.ex. fast orange).",
        "losning_nyckelord": ["starta om internetlådan", "dra ur strömsladden till routern", "vänta och koppla in routern igen"], # Actions for restarting router
        "start_prompt": "Nej, men titta! Hela mitt 'världsomspännande nät' har gett upp! Jag kan inte läsa nyheterna på min platta, och den där lilla blinkande lådan som ger mig internet, den lyser nu med ett väldigt envist och ilsket gult sken. Den brukar ju vara så pigg och grön. Vad kan ha hänt?"
        # Hints for AI: "världsomspännande nät gett upp", "lådan lyser ilsket gult" -> router/internet issue.
        # For student: Ulla's terms, focuses on service loss and unusual light, not specific technicals.
    },
    {
        "id": "U004",
        "beskrivning": "Bildskärmen får ingen ström eller ingen signal (kabel lös/felaktig, skärm avstängd, fel ingång vald). Datorn är på.",
        "losning_nyckelord": ["kontrollera strömkabeln till skärmen", "tryck på skärmens egen strömknapp", "kontrollera bildkabeln mellan dator och skärm", "byt ingångskälla på skärmen"], # Actions for screen power/signal
        "start_prompt": "Men kära hjärtanes, nu är det kolsvart på min stora titt-ruta! Datorlådan själv, den surrar och låter precis som den ska, men skärmen är lika mörk som i en säck. Jag har inte rört någonting, tror jag. Har den somnat för gott?"
        # Hints for AI: "kolsvart på titt-ruta", "datorlådan surrar" -> PC on, monitor issue.
        # For student: Focus on black screen despite PC running. "Inte rört någonting" is classic user statement.
    },
    {
        "id": "U005",
        "beskrivning": "Datorns ljud är avstängt via mjukvara (mute i operativsystemet) eller volymen är nere på noll.",
        "losning_nyckelord": ["kontrollera ljudinställningar på datorn", "öka volymen på datorn", "kontrollera om ljudet är avstängt (mute)"], # Software/OS level audio controls
        "start_prompt": "Det är så försmädligt! Jag skulle spela upp den där fina musiken som mitt barnbarn skickade, men det kommer inte ett ljud ur apparaten! Klickern rör sig fint och allt annat verkar fungera, men tyst är det. Är det något fel på själva musiken, tror du?"
        # Hints for AI: "inte ett ljud", "allt annat verkar fungera" -> likely software mute/volume, not hardware like speakers unplugged (though student might explore that).
        # For student: Focus on no sound, misdirection ("fel på musiken").
    },
    {
        "id": "U006",
        "beskrivning": "Felaktig tangentbordslayout är vald i operativsystemet, vilket gör att vissa tangenter ger fel symboler (t.ex. svenska vs engelska layouten för @, ', osv.).",
        "losning_nyckelord": ["ändra tangentbordsspråk", "kontrollera språkinställningar för tangentbordet", "byta layout på tangentbordet"], # OS keyboard layout setting
        "start_prompt": "Nu blir jag tokig på den här skrivmaskinen som är kopplad till datorn! När jag ska skriva en adress till min e-post, du vet med det där lilla snabel-a, så blir det en helt annan konstig krumelur istället! Och utropstecknet har också rymt! Har någon bytt ut mina knappar?"
        # Hints for AI: "snabel-a blir konstig krumelur", "utropstecknet har rymt" -> classic symptoms of wrong keyboard layout (e.g., US layout instead of Swedish).
        # For student: Focus on specific wrong characters. "Bytt ut knappar" is Ulla's misinterpretation.
    }
]