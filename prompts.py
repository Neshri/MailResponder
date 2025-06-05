# prompts.py

# --- START PHRASES PER LEVEL ---
START_PHRASES = [
    "starta övning", # Level 1 (index 0)
    "utmaning nivå 2",     # Level 2 (index 1)
    "expertläge nivå 3",    # Level 3 (index 2)
    "mästarprov nivå 4",    # Level 4 (index 3)
    "ulla special nivå 5"  # Level 5 (index 4)
]

# --- ULLA PERSONA PROMPT (Refers only to 'PROBLEMBESKRIVNING') ---
ULLA_PERSONA_PROMPT = """
Du är Ulla, en vänlig men tekniskt ovan äldre dam i 85-årsåldern.
Du interagerar med en IT-supportstudent via e-post.
Detaljerna kring ditt problem och vad du försökte göra beskrivs i "PROBLEMBESKRIVNING".
Använd ALLTID informationen från "PROBLEMBESKRIVNING" som grund för dina svar på studentens frågor, men formulera svaren som Ulla skulle göra.
Du använder ofta felaktiga termer (t.ex. "klickern" för musen, "internetlådan" för routern, "fönsterskärmen" för bildskärmen).
Du kan ibland spåra ur lite och prata om din katt Måns, dina barnbarn eller vad du drack till fikat (vilket kan antydas i problembeskrivningen), men återgår så småningom till problemet.
Du uttrycker mild frustration, förvirring eller att du känner dig överväldigad, men är alltid artig och tacksam för hjälp.
Svara på det SENASTE e-postmeddelandet i konversationstråden.
Analysera studentens meddelande i kontexten av konversationshistoriken och ditt nuvarande problem.
Formulera ett svar som Ulla. Agera INTE som en AI-assistent. Svara bara som Ulla skulle göra.
Håll dina svar relativt korta och konverserande, som ett riktigt e-postmeddelande. Använd inte emojis.
När studenten ställer frågor, basera dina svar på informationen i "PROBLEMBESKRIVNING", men återberätta den inte rakt av – väv in den naturligt i ditt Ulla-svar och använd din persona. Du vet inte den exakta tekniska orsaken eller lösningen.
"""

# --- EVALUATOR SYSTEM PROMPT ---
EVALUATOR_SYSTEM_PROMPT = """
Du är en precis och logisk utvärderings-AI. Din uppgift är att strikt avgöra om studentens SENASTE meddelande innehåller en lösning som matchar de givna lösningsnyckelorden för det aktuella tekniska problemet.
Studentens meddelande kan innehålla annat än bara lösningen. Fokusera enbart på om kärnan i något av lösningsnyckelorden har föreslagits.
Svara ENDAST med [LÖST] på en egen rad om en korrekt lösning föreslås.
Svara ENDAST med [EJ_LÖST] på en egen rad om ingen korrekt lösning föreslås.
Ingen annan text, förklaring eller formatering.
"""

# --- PROBLEM CATALOGUES PER LEVEL ---
PROBLEM_CATALOGUES = [
    # --- LEVEL 1 PROBLEMS (Index 0) - Based on "Svårighetsgrad 1" ---
    [
        {
            "id": "L1_P001",
            "beskrivning": """
                Jag ville så gärna titta på mina nya bilder på katten Måns i mitt fotoprogram, det där 'Bildvisaren Deluxe 2.1' som följde med min gamla kamera, en Kodak EasyShare C530. Han var så söt när han lekte med en pappersbit igår!
                Men nu har min gamla dator, en Fujitsu Esprimo, börjat tjata igen.
                Det har kommit upp en ruta flera gånger idag på fönsterskärmen. Den säger 'Viktig systemåtgärd krävs - Felkod WX0078'. Jag har klickat på 'OK'-knappen varje gång, för vad ska man annars göra?
                När jag försöker öppna mitt fotoprogram, så säger det bara 'Väntar på systemuppdatering...' i själva programfönstret. Sen blir det bara grått och ingenting mer händer.
                Jag har provat att stänga av och sätta på hela apparaten, men det hjälpte inte ett dugg.
                Datorn har varit lite extra seg de senaste dagarna, det tar en evighet att öppna saker.
                Inga konstiga ljud från datorlådan, och jag har inte rört några sladdar.
                Måns låg och sov i fönstret när jag försökte senast. Han tittade så undrande på mig när jag suckade.
                Jag hade precis druckit en kopp kaffe och ätit en god kanelbulle, så jag var redo att pyssla med bilderna.
                Det enda andra programmet som var igång var nog det där internet-fönstret.
            """,
            "losning_nyckelord": ["Windows Update fel WX0078 hindrar program ('Bildvisaren Deluxe 2.1') från att starta; systemuppdateringar krävs", "kör Windows Update", "låta datorn installera uppdateringar klart", "starta om datorn efter uppdatering"],
            "start_prompt": "Kära nån, nu tjatar datorn igen om en viktig uppdatering, och mitt fina fotoprogram där jag har alla bilder på Måns vill inte öppna sig längre. Det är ju förargligt!"
        },
        {
            "id": "L1_P002",
            "beskrivning": """
                Jag ville föra över mina stick-recept från minnesstickan till datorn. Jag fick stickan av mitt barnbarn, en röd och svart SanDisk Cruzer Blade 16GB, och den har alltid fungerat förut!
                Men när jag nu har provat att stoppa in min lilla minnes-sticka i den där luckan på framsidan av datorn (min gamla Fujitsu Esprimo P520, där det finns en sån där treuddig symbol), så händer absolut ingenting.
                Den brukade blinka ett litet rött ljus när jag satte i den förut, men nu är den alldeles mörk. Inget ljud från Windows hörs heller, inget 'pling' som det brukar.
                Jag har provat att vicka lite på den och stoppa in den flera gånger. Jag provade även den andra lediga USB-porten på framsidan, men det var likadant.
                Måns var här och nosade på den när jag höll på, men han kunde inte hjälpa till.
                Jag är rädd att alla mina viktiga stick-recept på den där stickan är borta nu! Tänk om den har gått sönder?
            """,
            "losning_nyckelord": ["USB-enhet (SanDisk Cruzer Blade 16GB) känns inte igen (ingen lampa/ljud) på Fujitsu Esprimo P520:s främre USB-port", "prova ett annat USB-uttag", "sätta stickan i en annan USB-port", "testa stickan i en annan dator"],
            "start_prompt": "Nu har jag stoppat in min lilla bild-sticka, du vet den jag fick av barnbarnet, men den hörs inte och syns inte någonstans på skärmen. Måns var precis här och nosade på den, men det hjälpte inte."
        },
        {
            "id": "L1_P003",
            "beskrivning": """
                Jag skulle bara logga in på min Windows 7 dator för att kolla min e-post. Jag har ju mitt vanliga lösenord som jag alltid använder.
                Men nu står det på fönsterskärmen: 'För många felaktiga lösenordsförsök. Kontot är låst. Försök igen om 15:00 minuter. Referens: LCK_USR_03'.
                Jag måste ha slagit fel några gånger, tangenterna är ju så små ibland. Jag minns inte exakt hur många gånger, kanske tre eller fyra?
                Nu är jag rädd att jag inte kommer in alls! Och jag som väntar på ett viktigt mail från min syster.
                Jag har inte provat att göra någonting annat än att titta på meddelandet och bli lite nervös. Klockan på väggen visar att det har gått ungefär fem minuter sen det hände.
            """,
            "losning_nyckelord": ["Windows 7 inloggningsskärm visar 'Kontot är låst. Försök igen om 15:00 minuter' (Ref: LCK_USR_03) efter för många felaktiga lösenordsförsök", "vänta tills kontot låses upp automatiskt", "ha tålamod femton minuter", "försök igen efter utsatt tid"],
            "start_prompt": "Åh, elände! Jag tror jag slog fel kod för många gånger när jag skulle logga in, för nu står det att jag måste vänta en hel kvart! Tänk om jag glömmer vad jag skulle göra under tiden?"
        },
        {
            "id": "L1_P004",
            "beskrivning": """
                Jag ville lyssna på lite Povel Ramel, Måns gillar honom också, så jag startade mitt gamla musikprogram, Winamp 5.6.
                Programmet ser ut att spela musiken, den där lilla tidsstapeln rör sig som den ska. Men det kommer inget ljud ur mina vanliga högtalare, de där Logitech S120 som är kopplade till det gröna uttaget på datorn.
                Jag tittade i ljudinställningarna i Kontrollpanelen, och där står det 'Standardenhet för uppspelning: Hörlurar (Realtek High Definition Audio)'. Men jag har ju inga hörlurar i! Jag drog ur dem igår för att Måns inte skulle trassla in sig i sladden.
                Så nu är det alldeles tyst här, fastän musiken borde spela. Det är ju för tokigt! Jag har inte rört några andra inställningar.
            """,
            "losning_nyckelord": ["Inget ljud från högtalare (Logitech S120 i grönt uttag) trots att Winamp 5.6 spelar; Windows ljudinställningar visar 'Hörlurar (Realtek High Definition Audio)' som standardenhet trots inga anslutna hörlurar", "ändra standardljudenhet till högtalare i ljudinställningarna", "ställ in Windows att använda högtalarna", "välj rätt uppspelningsenhet"],
            "start_prompt": "Min musik går bara i de där hörsnäckorna, fast sladden är urdragen! Jag vill ju att det ska låta ur de vanliga högtalarna så Måns också kan höra. Han gillar Povel Ramel."
        },
        {
            "id": "L1_P005",
            "beskrivning": """
                Jag satt och läste nyheterna på internet när Måns plötsligt hoppade upp på skrivbordet! Han är ju så nyfiken.
                Då råkade han väl komma åt den där blåa sladden med små skruvarna som går från datorn till fönsterskärmen (en Dell E2216H).
                Plötsligt började hela skärmen flimra i gröna och rosa färger, och det blir värre om jag rör vid sladden eller om bordet skakar lite.
                Ibland blir bilden nästan normal en sekund, sen börjar det igen. Det är som ett helt diskotek här hemma!
                Jag har försökt trycka till sladden lite vid skärmen och bak på datorlådan, men jag vet inte om det hjälpte. Jag vågar inte ta i för hårt. Sladden ser hel ut vad jag kan se.
            """,
            "losning_nyckelord": ["Bildskärm (Dell E2216H ansluten med VGA-kabel) visar gröna/rosa flimmer och bildstörningar vid fysisk rörelse av skärmen eller VGA-kabeln", "tryck fast bild-sladden ordentligt i både skärm och dator", "kontrollera att skärmkabeln sitter åt", "se till att VGA-kabeln är ordentligt ansluten"],
            "start_prompt": "Hjälp, om jag eller Måns råkar skaka lite på bordet så blinkar hela fönsterskärmen i alla möjliga konstiga färger! Det är som ett helt diskotek här hemma."
        },
        {
            "id": "L1_P006",
            "beskrivning": """
                Jag skulle titta på mina fina bilder i fotoprogrammet Picasa 3, de som jag har sparat på datorn.
                Men nu när jag öppnar programmet är alla bilderna bara gråa platshållare, och det står 'Bilden är offline. Status: Ingen internetanslutning. Kod: NC-002' på dem.
                Jag tittade nere vid klockan i Windows aktivitetsfält, och där är det en liten bild på en jordglob med ett rött kryss över. Det brukar det inte vara.
                Jag har inte rört några sladdar till internetlådan vad jag vet. Kanske Måns har varit framme igen? Jag har provat att starta om datorn, men det hjälpte inte.
                Det är som att bilderna har rest bort utan att säga till! Hur ska jag nu kunna visa dem för min syster när hon kommer på fika?
            """,
            "losning_nyckelord": ["Fotoprogram (Picasa 3) visar 'Bilden är offline. Status: Ingen internetanslutning. Kod: NC-002'; Nätverksikon i Windows aktivitetsfält visar rött kryss", "datorn saknar internetanslutning", "aktivera nätverksanslutningen (WiFi eller kabel)", "kontrollera att internetkabeln sitter i eller anslut till trådlöst nätverk"],
            "start_prompt": "Alla mina fina moln-bilder, eller vad det nu heter, har blivit gråa rutor med något konstigt ord 'offline'. Det är som att de har rest bort utan att säga till!"
        },
        {
            "id": "L1_P007",
            "beskrivning": """
                Jag skulle skriva ut ett recept på sockerkaka som jag har på datorn, till min skrivare, en gammal trotjänare, HP Deskjet 970Cxi.
                Men när jag tryckte på 'skriv ut' började skrivaren brumma och klicka lite lågt, och sen började en orange lampa med ett utropstecken på att blinka.
                Det kom inget papper alls, och på den lilla displayen på skrivaren står det 'Fel E05. Kontakta service'.
                Jag har provat att stänga av den med knappen och sätta på den igen, men det blev likadant. Den ser så ledsen ut när den blinkar så där. Inget papper har fastnat vad jag kan se.
                Nu blir det ingen sockerkaka till fikat om jag inte får ut receptet!
            """,
            "losning_nyckelord": ["Skrivare (HP Deskjet 970Cxi) ger lågt brummande/klickande ljud, orange 'Fel'-lampa (utropstecken) blinkar, display visar 'Fel E05. Kontakta service', ingen utskrift", "skrivaren har ett internt fel som kan lösas med omstart", "stäng av och på skrivaren (power cycle)", "gör en kall omstart av skrivaren genom att dra ur strömsladden", "vänta en stund innan strömmen kopplas in igen"],
            "start_prompt": "Min skrivar-apparat står bara och surrar lite tyst för sig själv, och sen kommer det ett ilsket felmeddelande. Den vill nog ha fika den också, precis som jag."
        },
        {
            "id": "L1_P008",
            "beskrivning": """
                Jag försöker deklarera på Skatteverkets hemsida, det är ju så viktigt att göra rätt för sig. Jag använder min gamla webbläsare, Internet Explorer 9.
                Jag har fyllt i alla siffror och ska trycka på 'Nästa'-knappen för att komma vidare, men det händer absolut ingenting när jag klickar! Knappen är inte grå eller så, den ser vanlig ut.
                Ibland, men inte alltid, dyker det upp en liten gulaktig rad högst upp i webbläsaren där det står något om 'Ett popup-fönster blockerades. För att se detta popup-fönster eller ytterligare alternativ klickar du här...'.
                Jag vet inte vad ett popup-fönster är, men det är som att sidan ignorerar mig totalt. Jag har provat att klicka på 'Nästa' flera gånger, och även startat om webbläsaren.
            """,
            "losning_nyckelord": ["Interaktion med 'Nästa'-knapp på Skatteverket.se i Internet Explorer 9 resulterar i ingen åtgärd; notis om blockerat popup-fönster visas ibland", "webbläsarens popup-blockerare hindrar sidan från att fungera korrekt", "tillåt pop-up-fönster för den specifika webbplatsen", "inaktivera popup-blockeraren tillfälligt för skatteverket.se"],
            "start_prompt": "Jag försöker göra rätt för mig på den där myndighetssidan, men det händer absolut ingenting när jag trycker på knapparna! Det är som att den ignorerar mig totalt."
        },
        {
            "id": "L1_P009",
            "beskrivning": """
                Jag har fått min räkning från Telia, den heter 'Telia_Faktura_Mars.pdf', och försöker öppna den i Adobe Reader X (version 10.1.0) som jag alltid gör för att se vad jag ska betala.
                Men när jag öppnar den så är hela sidan alldeles kritvit! Jag ser inte ett enda öre av vad jag ska betala, inga siffror, ingenting. Bara en tom vit sida.
                Ibland, om jag försöker igen, så kommer det upp ett litet felmeddelande som säger 'Ett fel uppstod vid bearbetning av sidan. Ogiltig färgrymd.' Vad betyder nu det?
                Måns tittade på skärmen och tyckte också det såg konstigt ut. Han brukar ju gilla när det är siffror och bokstäver. Jag har provat att starta om datorn, men det är likadant.
            """,
            "losning_nyckelord": ["PDF-fil ('Telia_Faktura_Mars.pdf') öppnas i Adobe Reader X (10.1.0) och visas som en helt vit sida, ibland med felmeddelande 'Ogiltig färgrymd'", "PDF-läsaren är för gammal eller har problem att rendera filen", "uppdatera Adobe Reader till senaste versionen", "prova att öppna PDF-filen med en annan PDF-visare (t.ex. webbläsare)"],
            "start_prompt": "Min el-räkning har kommit, men när jag öppnar den så är hela sidan alldeles kritvit! Jag ser inte ett enda öre av vad jag ska betala. Måns tycker det är jättekonstigt."
        },
        {
            "id": "L1_P010",
            "beskrivning": """
                Jag skulle betala mina räkningar och försökte gå in på min bank, Swedbank, med min vanliga webbläsare Firefox ESR 52. Jag skrev in www.swedbank.se som jag brukar.
                Men istället för bankens sida kommer det upp en stor röd varningssida där det står 'Anslutningen är inte säker' och en felkod 'SEC_ERROR_UNKNOWN_ISSUER'.
                Uppe i adressfältet där man skriver in webbadressen står det 'http://www.swedbank.se' och det är ett litet hänglås som är överstruket.
                Jag blir så nervös när det handlar om banken och säkerhet! Jag har inte vågat trycka på något mer. Jag har provat att stänga webbläsaren och försöka igen, men samma röda sida kommer upp.
            """,
            "losning_nyckelord": ["Webbläsare (Firefox ESR 52) visar röd varningssida 'Anslutningen är inte säker' (felkod 'SEC_ERROR_UNKNOWN_ISSUER') vid försök att nå bankens (Swedbank) webbplats via 'http://www.swedbank.se' (överstruket hänglås)", "webbplatsen försöker nås via en osäker anslutning (HTTP istället för HTTPS)", "skriv https:// före webbadressen (t.ex. https://www.swedbank.se)", "klicka på lås-ikonen (om det finns en varning) och välj att fortsätta till säker anslutning", "se till att använda https"],
            "start_prompt": "När jag ska logga in på min bank så säger datorn att anslutningen inte är säker och stänger ner hela rasket! Jag blir så nervös av sånt här."
        }
    ],
    # --- LEVEL 2 PROBLEMS (Index 1) - Based on "Svårighetsgrad 2" ---
    [
        {
            "id": "L2_P001",
            "beskrivning": """
                Jag höll på att skriva ett långt brev till mitt barnbarn på min dator, en Packard Bell iMedia S2883, när den plötsligt bara stängde av sig!
                Datorlådan har känts väldigt varm på sistone, man kan nästan koka ägg på den, och fläkten på insidan har låtit som en dammsugare eller en hårtork, särskilt precis innan den stänger av sig. Det brukar hända efter ungefär en halvtimmes användning.
                Jag tittade på baksidan och på sidan av lådan, och i de där ventilationsgallren ser det alldeles luddigt och dammigt ut. Måns fäller ju en del, men det här var nog mer än bara katthår.
                När jag startar om den efter att den stängt av sig står det ibland något på engelska om 'CPU Fan Error' på skärmen väldigt snabbt, men sen försvinner det och Windows startar.
                Det här har blivit värre de senaste veckorna. Jag har provat att ställa den lite mer fritt så den får luft, men det hjälper inte. Precis när Måns hade lagt sig tillrätta i knät så hände det igen!
            """,
            "losning_nyckelord": ["Datorchassi ('Packard Bell iMedia S2883') blir mycket varmt, systemet stängs av efter ca 30 min, ibland 'CPU Fan Error' i BIOS, högt fläktljud och synligt damm i ventilationsgaller", "datorn överhettas på grund av damm och dålig kylning", "rengör datorns fläktar och kylflänsar från damm", "blås bort dammet ur datorn med tryckluft", "förbättra luftflödet genom att ta bort damm"],
            "start_prompt": "Min datorlåda blir så varm att man nästan kan koka ägg på den, och fläktarna låter som en hårtork! Sen stänger den av sig mitt i allt, precis när Måns har lagt sig tillrätta i knät."
        },
        {
            "id": "L2_P002",
            "beskrivning": """
                Jag väntar på ett viktigt e-postmeddelande från min syster med ett recept på sockerkaka, men det verkar inte komma fram!
                Mitt e-postprogram, Mozilla Thunderbird (version 60.9.1), visar ett meddelande nere i statusfältet: 'Kvoten överskriden för kontot ulla.andersson@gmail.com (105% av 15GB). Felkod: MBX_FULL_001'.
                Jag förstår inte riktigt vad 'kvoten' betyder, men det låter som att det är fullt. Nya e-postmeddelanden verkar inte tas emot alls.
                Om jag försöker skicka ett mail så fastnar det bara i Utkorgen och där står det 'Skickar...'.
                Jag har massor av gamla mail sparade, en del med bilder från barnbarnen. Kan det vara det? Jag har inte raderat något på länge.
            """,
            "losning_nyckelord": ["E-postprogram ('Mozilla Thunderbird 60.9.1') visar 'Kvoten överskriden för kontot ulla.andersson@gmail.com (105% av 15GB). Felkod: MBX_FULL_001'; nya e-postmeddelanden mottas ej, utkorgen visar 'Skickar...'", "e-postlådan på servern är full", "logga in på webbmailen och ta bort gamla/stora mejl", "töm skräpposten och radera meddelanden med stora bilagor från servern", "frigör utrymme i e-postkontot"],
            "start_prompt": "Nu säger min e-post att brevlådan är proppfull och nya brev kommer inte in! Jag som väntar på ett recept på sockerkaka från min syster."
        },
        {
            "id": "L2_P003",
            "beskrivning": """
                Jag har fått ett viktigt brev från Försäkringskassan, det är en fil som heter 'Försäkringskassan_Beslut.pdf' som jag har laddat ner till min Windows 7 dator.
                Men när jag försöker öppna filen genom att dubbelklicka på den, så kommer det upp en dialogruta som säger: 'Windows kan inte öppna den här filtypen (.pdf). För att öppna filen behöver Windows veta vilket program du vill använda...'.
                Sen listar den en massa program, men inget som heter något med PDF vad jag kan se. Jag har inget speciellt PDF-program installerat, tror jag. Brukade inte det bara fungera förut?
                Det är som att datorn inte har rätt glasögon på sig för att kunna läsa filen! Och jag behöver verkligen se vad som står i det där beslutet. Jag har provat att högerklicka och titta efter 'Öppna med', men det hjälpte inte.
            """,
            "losning_nyckelord": ["Försök att öppna nedladdad '.pdf'-fil ('Försäkringskassan_Beslut.pdf') i Windows 7 resulterar i dialogruta: 'Windows kan inte öppna den här filtypen... behöver veta vilket program...' (inget PDF-program installerat)", "program för att visa PDF-filer saknas på datorn", "installera Adobe Acrobat Reader eller annan PDF-läsare", "ladda hem ett gratisprogram för att öppna PDF-dokument"],
            "start_prompt": "Jag har fått ett viktigt dokument från myndigheten, men datorn säger att den inte vet hur den ska öppna det. Det är som att den inte har rätt glasögon på sig!"
        },
        {
            "id": "L2_P004",
            "beskrivning": """
                Jag skulle beställa nya penséer till balkongen från Blomsterlandets hemsida. Jag använder min gamla vanliga webbläsare, Internet Explorer 11.
                Men när jag är inne på sidan och försöker klicka på knapparna, som 'Lägg i varukorg' eller 'Visa mer', så är de alldeles utgråade och inaktiva. Det händer ingenting när jag klickar.
                Jag ser också en liten gul varningstriangel nere i statusfältet på webbläsaren, och om jag håller muspekaren över den står det något i stil med 'Fel på sidan. Detaljer: Objekt stöder inte egenskapen eller metoden 'addEventListener''. Vad betyder nu det?
                Det är som att alla knappar har somnat! Jag har provat att ladda om sidan, och även startat om Internet Explorer, men det hjälper inte. Måns tittade på skärmen och såg lika frågande ut som jag.
            """,
            "losning_nyckelord": ["Webbsida ('Blomsterlandet.se' i Internet Explorer 11) har utgråade/inaktiva knappar; statusfältet visar 'Fel på sidan. Detaljer: Objekt stöder inte egenskapen eller metoden 'addEventListener''", "webbläsaren blockerar eller kan inte köra nödvändiga skript (JavaScript) på sidan", "aktivera JavaScript i webbläsarens inställningar", "kontrollera säkerhetsinställningar för skript i Internet Explorer"],
            "start_prompt": "Jag skulle beställa nya penséer på en webbsida, men alla knappar är alldeles grå och går inte att trycka på. Det är som att de har somnat!"
        },
        {
            "id": "L2_P005",
            "beskrivning": """
                Min Windows 10 dator har börjat pipa och plinga en massa! Nere i aktivitetsfältet dyker det upp en varning: 'Lågt diskutrymme på Lokal Disk (C:). Du har nästan slut på utrymme på den här enheten (bara 250MB ledigt av 120GB står det!)'.
                Jag försökte precis spara några nya bilder på Måns när han jagade en fjäril, från min kamera, en Canon PowerShot A590 IS, till mappen 'Mina Bilder'. Då kom det upp ett annat felmeddelande som sa 'Disken är full'.
                Det är ju katastrof! Jag har massor av bilder och gamla dokument på datorn, men jag trodde det fanns gott om plats. Kan det verkligen bli fullt så där?
                Jag vågar inte radera något själv, tänk om jag tar bort något viktigt! Jag har inte installerat några nya stora program på länge.
            """,
            "losning_nyckelord": ["Systemvarning i Windows 10 aktivitetsfält: 'Lågt diskutrymme på Lokal Disk (C:)... (250MB ledigt av 120GB)'; försök att spara bild från kamera (Canon PowerShot A590 IS) ger fel 'Disken är full'", "hårddisken (C:) är nästan full", "frigör diskutrymme genom att ta bort onödiga filer och program", "använd Diskrensning i Windows för att ta bort temporära filer"],
            "start_prompt": "Datorn plingar och piper och säger att lagringsutrymmet nästan är slut, och nu kan jag inte spara de nya bilderna på Måns när han jagade en fjäril. Det är ju katastrof!"
        },
        {
            "id": "L2_P006",
            "beskrivning": """
                Jag brukar prata med mina barnbarn i det där videoprogrammet Skype (version 7.40) på min bärbara dator, en Asus X550C. Det brukar fungera bra när jag sitter i köket eller vardagsrummet.
                Min internetlåda, en Technicolor TG799vac, står i vardagsrummet. I köket och vardagsrummet visar den lilla WiFi-symbolen i Windows full styrka, alla fem strecken.
                Men om jag går in i sovrummet för att få lite lugn och ro, då blir WiFi-signalen jättesvag, bara ett rött streck. Då börjar Skype-samtalet hacka och visa 'Anslutningen är svag. Återansluter...' och sen bryts det ofta helt.
                Barnbarnen säger att jag bara blir en massa fyrkanter och sen försvinner. Det är så tråkigt när man äntligen får prata med dem!
                Det är ju en tjock vägg mellan vardagsrummet och sovrummet, kan det vara den som stör? Jag har provat att ställa datorn på olika ställen i sovrummet, men det är lika dåligt överallt där inne.
            """,
            "losning_nyckelord": ["Videosamtal i Skype 7.40 på bärbar (Asus X550C) har svag WiFi-signal (1/5 streck, rött) och bryts i sovrum; starkare signal (5/5) i rum närmare WiFi-router (Technicolor TG799vac i vardagsrum)", "WiFi-signalen är för svag i sovrummet", "flytta datorn närmare WiFi-routern", "undvik fysiska hinder (väggar, möbler) mellan dator och router", "använd en WiFi-förstärkare/repeater"],
            "start_prompt": "När jag pratar med barnbarnen i det där video-programmet så bryts det hela tiden om jag går in i sovrummet. De säger att jag bara blir en massa fyrkanter."
        },
        {
            "id": "L2_P007",
            "beskrivning": """
                Jag skulle skriva ut ett brev till min väninna Agda på min skrivare, en HP DeskJet 2710e, som är kopplad till datorn med en USB-sladd.
                Lampan på skrivaren lyser stadigt grönt, så den verkar ju vara på och må bra.
                Men inne i datorn, i Windows under 'Enheter och skrivare', så är ikonen för min 'HP DeskJet 2700 series' alldeles gråtonad, och det står 'Frånkopplad' bredvid den.
                När jag försöker skriva ut så fastnar utskriftsjobbet bara i kön, och statusen blir 'Fel - Skriver ut'. Det kommer ingenting alls.
                Det är som att datorn och skrivaren inte pratar med varandra längre! Jag har provat att dra ur USB-sladden och sätta i den igen, både i skrivaren och datorn, och även testat en annan USB-port på datorn, men det hjälpte inte. Jag har också startat om både skrivaren och datorn.
            """,
            "losning_nyckelord": ["Skrivare (HP DeskJet 2710e ansluten via USB) har stadig grön strömlampa men visas som 'Frånkopplad' i Windows 'Enheter och skrivare'; utskriftsjobb fastnar med status 'Fel - Skriver ut'", "skrivaren är inte korrekt ansluten eller känns inte igen av Windows", "starta om både dator och skrivare", "kontrollera USB-kabeln och prova att ta bort och lägga till skrivaren igen i Windows", "installera om skrivardrivrutinerna"],
            "start_prompt": "Min skrivare är alldeles grå inne i datorn, fast lampan på själva apparaten lyser så snällt grönt. Det är som att de inte pratar med varandra!"
        },
        {
            "id": "L2_P008",
            "beskrivning": """
                Jag satt och tittade på mina semesterbilder från 2023 i mitt fotoprogram, särskilt en jättefin bild på Måns när han sover så sött, den heter 'Måns_sover_sött.jpg' och ligger i mappen C:\MinaBilder\Semester_2023\.
                Plötsligt kom det upp en varning från mitt antivirusprogram, F-Secure SAFE. Den sa: 'Hot blockerat! Filen C:\MinaBilder\Semester_2023\Måns_sover_sött.jpg har identifierats som misstänkt och har satts i karantän.'
                Nu kan jag inte se bilden längre i fotoprogrammet, den är bara borta från albumet! Måns favoritbild!
                Men jag vet att den bilden är helt ofarlig, jag tog den ju själv med min egen kamera! Det måste vara programmet som har blivit tokigt. Vad menas med karantän, är min bild sjuk nu? Jag har inte laddat ner något konstigt eller klickat på några skumma länkar.
            """,
            "losning_nyckelord": ["Antivirusprogram ('F-Secure SAFE') visar varning 'Hot blockerat! Filen C:\\MinaBilder\\Semester_2023\\Måns_sover_sött.jpg har identifierats som misstänkt och har satts i karantän'; fotoprogram kan ej visa bilden", "antivirusprogrammet har felaktigt identifierat en ofarlig fil som ett hot (falskt positivt)", "lägg till ett undantag för filen eller mappen i F-Secure SAFE:s inställningar", "kontrollera F-Secure SAFE:s karantän och återställ filen därifrån om den är ofarlig"],
            "start_prompt": "Hjälp! Mitt skyddsprogram på datorn, det där F-Secure, har blivit helt tokigt! Det säger att en av mina bästa bilder på Måns när han sover så sött är farlig och nu kan jag inte se den längre! Men jag vet att den är snäll!"
        },
        {
            "id": "L2_P009",
            "beskrivning": """
                Jag ville lyssna på lite musik i mina fina hörlurar, Philips SHP2000, för att inte störa Måns som låg och sov så sött i soffan. Jag kopplade in dem i det gröna 3.5mm ljuduttaget på framsidan av min stationära dator.
                Jag startade mitt musikprogram, Foobar2000, men ljudet fortsatte att komma ur de stora högtalarna som är inbyggda i min datorskärm (en Dell S2421H som är kopplad med en HDMI-sladd)!
                Jag tittade i Windows Ljudinställningar under fliken Uppspelning. Där står det att 'Högtalare (Realtek High Definition Audio)' är standardenhet. Mina hörlurar finns med i listan, men de är inte valda som standard.
                Det är ju inte klokt, ljudet ska ju komma i lurarna när jag har dem i! Jag har provat att klicka lite här och var i ljudinställningarna men vågar inte ändra för mycket.
            """,
            "losning_nyckelord": ["Ljud från 'Foobar2000' spelas via datorns monitorhögtalare ('Dell S2421H' via HDMI) trots att hörlurar ('Philips SHP2000') är anslutna till grönt 3.5mm ljuduttag; Windows Ljudinställningar visar 'Högtalare (Realtek High Definition Audio)' som standardenhet, 'Hörlurar' listas men är inte standard", "hörlurarna är inte valda som standardljudenhet i Windows", "ändra standarduppspelningsenhet till hörlurarna i ljudinställningarna", "högerklicka på hörlurarna i ljudpanelen och välj 'Ange som standardenhet'"],
            "start_prompt": "Jag sätter i mina fina hörlurar för att inte störa Måns när han sover, men ljudet fortsätter ändå att komma ur de stora högtalarna! Det är ju inte klokt."
        },
        {
            "id": "L2_P010",
            "beskrivning": """
                Jag skulle logga in på min bank, Swedbank, och tog fram min lilla bankdosa, en sån där gammal Vasco Digipass 260.
                Men när jag skulle börja knappa in koden såg jag att det stod 'LOW BATT' på den lilla LCD-displayen. Och precis när jag höll på att mata in engångskoden så stängde den av sig!
                Nu kommer jag ju inte åt mina pengar till fikat! Jag vet att den använder ett sånt där platt, runt batteri, ett CR2032, och det går att byta, för det har jag gjort förut för länge sen.
                Kan det vara så enkelt att batteriet är slut igen? Den har känts lite trög att starta på sistone också.
            """,
            "losning_nyckelord": ["Bankdosa ('Vasco Digipass 260', Swedbank) visar 'LOW BATT' på LCD-displayen och stängs av under inmatning av engångskod; använder CR2032-batteri", "batteriet i bankdosan är slut", "byt ut det gamla CR2032-batteriet i säkerhetsdosan mot ett nytt", "öppna batteriluckan och ersätt batteriet"],
            "start_prompt": "Min lilla bank-dosa blinkar något om 'LOW BATT' och stänger av sig mitt i när jag ska skriva in koden. Nu kommer jag väl inte åt mina pengar till fikat!"
        }
    ],
    # --- LEVEL 3 PROBLEMS (Index 2) - Based on "Svårighetsgrad 3" ---
    [
        {
            "id": "L3_P001",
            "beskrivning": """
                Jag satt och skrev på mina memoarer om Måns när min dator, en Dell OptiPlex 7010 SFF, plötsligt visade en hemsk blå skärm!
                Det stod ':( Ditt system stötte på ett problem... Stoppkod: MEMORY_MANAGEMENT' med en massa annan teknisk text. Sen startade den om sig själv. Det här har hänt flera gånger de senaste dagarna, helt slumpmässigt.
                Jag har två minneskort i datorn, Kingston KVR13N9S6/2, som är 2GB styck. Min son sa att man kunde köra något som heter Windows Minnesdiagnostik, och jag provade det (standardtestet), men det visade inga fel direkt.
                Det är som att datorn har tappat minnet, stackarn. Jag är så rädd att allt jag skrivit ska försvinna. Datorn känns också allmänt lite instabil.
            """,
            "losning_nyckelord": ["Slumpmässig blåskärm (BSOD) med text 'Stoppkod: MEMORY_MANAGEMENT' på dator 'Dell OptiPlex 7010 SFF' med 2x2GB DDR3 RAM ('Kingston KVR13N9S6/2'); Windows Minnesdiagnostik (standardtest) visar inga fel", "problem med RAM-minnet (arbetsminnet)", "kör en grundligare minnesdiagnostik som MemTest86 från USB", "prova med en minnesmodul i taget i olika platser för att isolera felet", "kontrollera RAM-modulernas kompatibilitet"],
            "start_prompt": "Hemska apparat! Skärmen blir alldeles blå med ett ledset ansikte och en massa text om 'MEMORY', sen startar den om sig själv. Det är som att den har tappat minnet, stackarn."
        },
        {
            "id": "L3_P002",
            "beskrivning": """
                Barnbarnen var här och lämnade en film på en sån där .MKV-fil. Jag försöker titta på den i mitt vanliga filmprogram, VLC Media Player 3.0.8. Det är en H.264 codec och 1080p, vad nu det betyder.
                Men när jag spelar upp filmen fylls bilden med gröna och rosa fyrkantiga fläckar och pixelfel, särskilt när det är snabba rörelser i filmen. Ljudet fortsätter dock att spelas upp normalt.
                Mitt grafikkort är ett NVIDIA GeForce GT 710 2GB, och drivrutinen är version 391.35 från 2018, sa min son.
                Det ser ut som Måns har lekt med färgburkarna på skärmen! Det går ju inte att titta så här. Andra filmer jag har fungerar bra.
            """,
            "losning_nyckelord": ["Uppspelning av '.MKV'-fil (H.264, 1080p) i VLC Media Player 3.0.8 ger gröna/rosa fyrkantiga artefakter och pixelfel; ljud normalt; Grafikkort NVIDIA GeForce GT 710 2GB, drivrutin 391.35 (2018)", "grafikkortets drivrutiner är föråldrade eller korrupta", "uppdatera grafikkortets drivrutiner till senaste stabila versionen från NVIDIA:s webbplats", "avinstallera gamla drivrutiner och installera nya rena drivrutiner"],
            "start_prompt": "När jag försöker titta på en film jag fått från barnbarnen så fylls hela skärmen av konstigt flimmer i alla möjliga färger, och bilden säger att den har hängt sig. Det ser ut som Måns har lekt med färgburkarna!"
        },
        {
            "id": "L3_P003",
            "beskrivning": """
                Jag skulle spara några nya bilder på Måns på mitt USB-minne, ett Kingston DataTraveler G4 8GB. Men det gick inte!
                Jag kan titta på filerna som redan finns på minnet, men när jag försöker radera något gammalt eller spara något nytt så säger Windows: 'Disken är skrivskyddad. Ta bort skrivskyddet eller använd en annan disk.'
                Jag tittade närmare på minnesstickan, och den har en liten fysisk knapp på sidan med en låsikon. Just nu är den knappen i 'låst' läge, alltså skjuten mot låsikonen. Kan det vara så enkelt?
                Jag har inte rört den där knappen med flit, Måns kanske kom åt den när han lekte på skrivbordet.
            """,
            "losning_nyckelord": ["USB-minne ('Kingston DataTraveler G4 8GB') med fysisk skrivskyddsbrytare i 'låst' läge tillåter läsning men inte radering/formatering; Windows fel 'Disken är skrivskyddad'", "USB-minnets fysiska skrivskydd är aktiverat", "skjut den lilla låsknappen på minnesstickans sida till olåst läge", "inaktivera 'write-protect' reglaget på USB-enheten"],
            "start_prompt": "Min lilla minnes-sticka går bra att titta på, men jag kan inte kasta något skräp från den – den säger att den är 'skriv-skyddad'. Har den fått någon form av skyddsvakt?"
        },
        {
            "id": "L3_P004",
            "beskrivning": """
                Jag har en bärbar dator, en HP Pavilion G6-2250so, och jag använder originalladdaren, en HP 65W Smart AC Adapter (modell PPP009L-E).
                Men nu visar batteriikonen i Windows aktivitetsfält '0% tillgängligt (nätansluten, laddar inte)'. Den lilla laddningslampan bredvid strömintaget på datorn lyser inte heller. Batteriet heter HP HSTNN-LB0W.
                Datorn fungerar så länge laddaren är i, men om jag drar ur sladden så stängs den av direkt. Det är som att den vägrar äta sin ström!
                Jag har provat att ta ut och sätta i batteriet igen, och även vickat på laddarsladden både vid datorn och vid vägguttaget.
            """,
            "losning_nyckelord": ["Bärbar dator ('HP Pavilion G6-2250so' med 'HP HSTNN-LB0W' batteri) visar '0% tillgängligt (nätansluten, laddar inte)'; laddningslampa lyser ej; stängs av om laddare (HP 65W Smart AC Adapter PPP009L-E) dras ur", "laddaren eller batteriet är defekt, eller dålig anslutning", "prova en annan kompatibel HP-laddare", "kontrollera om batteriet är korrekt isatt och överväg att byta batteri", "rengör kontaktytor för batteri och laddare"],
            "start_prompt": "Batteri-symbolen på min bärbara dator säger 'ansluten men laddas inte' fastän sladden sitter där den ska. Det är som att den vägrar äta sin ström!"
        },
        {
            "id": "L3_P005",
            "beskrivning": """
                Jag försöker skicka e-post till min syster om Måns tokigheter med mitt vanliga program, Microsoft Outlook 2016. Jag har ett Telia-konto, mailin.telia.com.
                Men programmet tjatar och frågar efter mitt nätverkslösenord för ulla.ulla@telia.com om och om igen. Jag skriver in det, men rutan kommer tillbaka.
                Alla e-postmeddelanden jag försöker skicka fastnar i 'Utkorgen' med status 'Väntar på att skickas (fel 0x800CCC0F)'.
                Jag bytte faktiskt lösenord på Telias webbmail för några dagar sedan, för jag tyckte det var dags. Det nya lösenordet fungerar utmärkt där på webbmailen. Kan det ha med saken att göra?
            """,
            "losning_nyckelord": ["E-postprogram ('Microsoft Outlook 2016' ansluten till Telia IMAP-konto mailin.telia.com) frågar upprepade gånger efter nätverkslösenord; e-post i 'Utkorgen' har status 'Väntar på att skickas (fel 0x800CCC0F)'; lösenord nyligen ändrat på webbmail och fungerar där", "sparat lösenord i Outlook är felaktigt efter byte på webbmailen", "uppdatera det sparade lösenordet i Outlooks kontoinställningar", "gå till Arkiv > Kontoinställningar, välj kontot och ange det nya lösenordet"],
            "start_prompt": "Mitt mejl-program frågar efter lösenordet om och om igen, och inga av mina brev till syrran om Måns tokigheter går iväg. Det är så frustrerande!"
        },
        {
            "id": "L3_P006",
            "beskrivning": """
                När jag pratar med barnbarnen i det där videosamtalsprogrammet Skype (version 8.96) på min bärbara dator, en Lenovo IdeaPad 3 15IIL05, så klagar de på att de hör sin egen röst som ett eko från min dator.
                Jag använder den inbyggda mikrofonen och högtalarna i datorn, inget headset. Jag har märkt att mikrofonsymbolen i Skype reagerar starkt även när bara de pratar, alltså på ljudet från mina högtalare.
                Det här händer även om jag sänker högtalarvolymen ganska mycket. Det låter som vi är i en stor kyrka! Det är ju inte så roligt för dem att höra sig själva hela tiden.
            """,
            "losning_nyckelord": ["Under videosamtal i Skype 8.96 på Lenovo IdeaPad 3 15IIL05 (inbyggd mikrofon/högtalare) rapporterar motparter tydligt eko av sin egen röst; mikrofon reagerar på ljud från datorns högtalare; inget headset används", "ljud från högtalarna plockas upp av mikrofonen (rundgång)", "använd ett headset (hörlurar med mikrofon) för att isolera ljudet", "sänk högtalarvolymen och mikrofonkänsligheten, eller använd Skypes ekoreducering om tillgängligt"],
            "start_prompt": "När jag pratar med barnbarnen på det där video-samtalet så hör alla sin egen röst som ett eko från min dator. Det låter som vi är i en stor kyrka!"
        },
        {
            "id": "L3_P007",
            "beskrivning": """
                Jag skriver ner mina memoarer om Måns i mitt skrivprogram, Microsoft Word 2013. Men på sista tiden har programmet börjat frysa hela tiden, särskilt när jag jobbar med stora dokument eller när det där autopsarandet sker.
                Hela fönstret visar '(Svarar inte)' och ibland kommer det ett meddelande 'Word försöker återskapa din information...'.
                Samtidigt har jag märkt att min datorlåda, eller snarare hårddisken inuti (en Seagate Barracuda 1TB ST1000DM003), ger ifrån sig konstiga klickande och höga arbetsljud, särskilt när programmet fryser.
                Min dotter installerade ett program som heter CrystalDiskInfo, och det visar en 'Varning' för disken, något om 'Reallocated Sectors Count'. Jag förstår inte vad det betyder, men det låter inte bra. Tänk om allt försvinner! Jag har inte gjort någon säkerhetskopia på länge.
            """,
            "losning_nyckelord": ["Textredigeringsprogram ('Microsoft Word 2013') fryser ofta ('(Svarar inte)'); hårddisk ('Seagate Barracuda 1TB ST1000DM003') ger återkommande klickljud; CrystalDiskInfo visar 'Varning' (t.ex. 'Reallocated Sectors Count')", "hårddisken har problem eller är på väg att gå sönder", "kör en fullständig diskkontroll (chkdsk /f /r) på systemdisken", "säkerhetskopiera viktiga filer omedelbart och överväg att byta ut hårddisken"],
            "start_prompt": "Mitt skriv-program, där jag skriver ner mina memoarer om Måns, fryser hela tiden och visar 'återskapar fil' medan datorlådan knastrar och låter konstigt. Tänk om allt försvinner!"
        },
        {
            "id": "L3_P008",
            "beskrivning": """
                Jag försöker skriva ut mitt goda kakrecept på båda sidor av pappret för att spara papper. Min skrivare är en Brother HL-L2350DW.
                Jag använder Word och väljer dubbelsidig utskrift med inställningen 'Vänd längs långa kanten (standard)'. Men när pappret kommer ut så är texten på baksidan (andra sidan) alldeles uppochnedvänd i förhållande till framsidan!
                Hur ska någon kunna läsa det? Det ser ju heltokigt ut. Jag ser att det finns ett annat alternativ som heter 'Vänd längs korta kanten' i skrivarens utskriftsdialog, men jag har inte vågat prova det än.
            """,
            "losning_nyckelord": ["Vid dubbelsidig utskrift från Word till Brother HL-L2350DW med inställning 'Vänd längs långa kanten (standard)' blir texten på baksidan uppochnedvänd", "fel inställning för pappersvändning vid dubbelsidig utskrift", "välj 'vänd längs korta kanten' i utskriftsinställningarna för korrekt orientering på baksidan", "justera duplex-inställningen för 'short-edge binding'"],
            "start_prompt": "När jag försöker skriva ut mitt kakrecept på båda sidor av pappret så kommer texten på baksidan alldeles upp-och-ned! Hur ska någon kunna läsa det?"
        },
        {
            "id": "L3_P009",
            "beskrivning": """
                Jag har en liten surfplatta, en Samsung Galaxy Tab A7 Lite (SM-T220) med Android 11, som jag brukar titta på Måns-videor på.
                Men nu har den blivit så envis! Bilden förblir i porträttläge, alltså stående, även om jag vrider på plattan för att titta på en film i liggande format.
                Jag har tittat i den där snabbinställningspanelen som man drar ner från toppen, och där finns en ikon för 'Automatisk rotering' (en rektangel med pilar runt). Den ikonen är gråtonad och det står 'Porträtt' under den. Det betyder väl att den är avstängd?
                Jag har provat att trycka på ikonen, men det verkar inte hända något. Den är fortfarande envis som en gammal get!
            """,
            "losning_nyckelord": ["Surfplatta ('Samsung Galaxy Tab A7 Lite (SM-T220)' med Android 11) förblir i porträttläge trots fysisk rotation; ikon för 'Automatisk rotering' i snabbinställningspanelen är gråtonad och visar 'Porträtt'", "automatisk skärmrotation är avstängd i systeminställningarna", "tryck på ikonen för skärmrotation i snabbinställningspanelen för att aktivera den", "gå till Inställningar > Skärm > och slå på 'Automatisk rotering'"],
            "start_prompt": "Min lilla surfplatta, som jag tittar på Måns-videor på, vägrar att vrida på bilden när jag vänder på plattan. Den är envis som en gammal get!"
        },
        {
            "id": "L3_P010",
            "beskrivning": """
                Jag skulle logga in på min bank, Handelsbanken, på datorn och behövde en engångskod som skickas via SMS till min telefon, en Doro 8080 (Android Go).
                Koden kom som den skulle, men när jag skrev in den på bankens webbplats så fick jag ett meddelande: 'Ogiltig kod. Koden kan vara för gammal eller redan använd.'
                Jag tittade på klockan på min telefon, och den visade 10:35. Men klockan på min dator, som jag vet går rätt för den synkas automatiskt, visade 10:32. Det är ju tre minuters skillnad!
                Jag har kollat i telefonens inställningar, och där är 'Använd nätverksbaserad tid' avstängd. Kan det vara det som spökar? Det är som att de lever i olika tidsåldrar!
            """,
            "losning_nyckelord": ["Engångskod via SMS till telefon ('Doro 8080') avvisas av bankens webbplats ('Handelsbanken') som 'Ogiltig kod... för gammal'; telefonens klocka (10:35) skiljer sig från datorns (10:32, NTP-synkad); 'Använd nätverksbaserad tid' avstängd på telefonen", "telefonens klocka är osynkroniserad vilket gör SMS-koden ogiltig för tidskänsliga system", "slå på 'Automatisk datum och tid' (nätverksbaserad tid) i telefonens inställningar", "kontrollera att telefonens tid och tidszon är korrekta och synkroniserade"],
            "start_prompt": "Bank-koden som kommer i ett SMS till min telefon avvisas direkt som 'för gammal' när jag skriver in den på datorn. Det är som att de lever i olika tidsåldrar!"
        }
    ],
    # --- LEVEL 4 PROBLEMS (Index 3) - Based on "Nivå B" ---
    [
        {
            "id": "L4_P001",
            "beskrivning": """
                Jag skulle starta min stationära dator, en HP Compaq Elite 8300 SFF, för att betala räkningar.
                Men när jag tryckte på startknappen så började den bara pipa tre gånger, kort och ilsket: pip-pip-pip. Strömlampan på datorn lyser grönt som den ska, men fönsterskärmen är helt svart. Det kommer ingen bild alls, inte ens den där första logotypen.
                Jag har två minneskort i datorn, Kingston KVR1333D3N9/2G heter de visst (2GB DDR3 PC3-10600). Min son sa att tre pip ofta betyder problem med minnet på HP-datorer.
                Jag har provat att stänga av den helt och försöka igen, men det är samma sak varje gång. Den verkar ha fått hicka och vägrar vakna! Jag har inte öppnat datorlådan eller rört något inuti.
            """,
            "losning_nyckelord": ["Stationär dator ('HP Compaq Elite 8300 SFF') ger tre korta ljudsignaler (beep code) vid startförsök; skärmen förblir svart; strömlampa lyser grönt; RAM 2x 'Kingston KVR1333D3N9/2G'", "fel på RAM-minnet eller dålig kontakt med minnesmodulerna", "ta ut och sätt tillbaka minneskorten ordentligt (reseat)", "prova med en minnesmodul i taget i olika minnesplatser för att identifiera felaktig modul eller plats"],
            "start_prompt": "När jag trycker på startknappen på min stora datorlåda piper den bara tre gånger, kort och ilsket, och fönsterskärmen är helt svart. Den verkar ha fått hicka!"
        },
        {
            "id": "L4_P002",
            "beskrivning": """
                Jag skulle skriva ut ett fint kort till Måns födelsedag och hade precis satt i nya bläckpatroner i min Epson Stylus DX4400 skrivare. En svart Epson T0711 och färgpatroner T0712, T0713 och T0714.
                Men när jag försökte skriva ut kom pappren ut alldeles blanka, inte en enda prick färg!
                Jag tittade närmare på en av de nya färgpatronerna som jag hade kvar i förpackningen, och jag såg att det satt en liten orange skyddstejp med texten 'PULL' på ovansidan. Den tejpen täcker ett litet lufthål eller en ventilationsöppning.
                Kan det vara så att jag har glömt att ta bort den tejpen på patronerna som sitter i skrivaren? Jag minns inte att jag drog bort någon tejp... Det är som att färgen har rymt!
            """,
            "losning_nyckelord": ["Nya bläckpatroner ('Epson T0711' svart, 'T0712/3/4' färg) installerade i 'Epson Stylus DX4400' matar fram blanka papper; orange skyddstejp ('PULL') observerad på ovansidan av ny patron täckande lufthål", "skyddstejp på bläckpatronerna blockerar bläcktillförseln eller ventilationen", "avlägsna all skyddstejp och plastremsor från nya bläckpatroner innan installation", "se till att lufthålen på patronerna är helt öppna"],
            "start_prompt": "Jag har satt i nya fina färgpatroner i skrivaren, men pappren kommer ut alldeles tomma, inte en prick! Det är som att färgen har rymt."
        },
        {
            "id": "L4_P003",
            "beskrivning": """
                Jag skulle ansluta min bärbara dator, en Acer Aspire 5 A515-54G med Windows 10, till mitt trådlösa nätverk för att läsa e-posten.
                Men istället för den vanliga WiFi-symbolen i aktivitetsfältet så visas det en liten flygplansikon. I Nätverksinställningar står det 'Flygplansläge: På'.
                Jag har provat att trycka på Fn-tangenten tillsammans med F3-tangenten (där det är en flygplanssymbol), men det händer ingenting. Det finns ingen särskild WiFi-knapp på sidan av datorn heller.
                Nu kan jag inte ansluta till några trådlösa nätverk alls. Den kanske vill flyga söderut med Måns? Jag har startat om datorn, men flygplanet är kvar.
            """,
            "losning_nyckelord": ["Bärbar dator ('Acer Aspire 5 A515-54G' med Windows 10) visar flygplansikon i aktivitetsfältet; Nätverksinställningar visar 'Flygplansläge: På'; Fn+F3 har ingen effekt; ingen WiFi-knapp på sidan", "flygplansläget är aktiverat i Windows och blockerar trådlösa anslutningar", "stäng av Flygplansläge via Nätverks- & Internetinställningar i Windows", "klicka på flygplansikonen i aktivitetsfältet och välj att stänga av läget därifrån"],
            "start_prompt": "Min bärbara dator har fått för sig att den är ett flygplan! Det har dykt upp en liten flygplansbild bredvid klockan, och nu ser jag inga trådlösa nät längre. Den kanske vill flyga söderut med Måns?"
        },
        {
            "id": "L4_P004",
            "beskrivning": """
                Jag har nyligen installerat om Windows 10 Home på min dator från en sån där generisk USB-sticka som min son gjorde åt mig. Allt verkar fungera, men det är en sak som stör mig.
                I nedre högra hörnet på skärmen visas en halvtransparent text, som en vattenstämpel. Det står: 'Aktivera Windows. Gå till Inställningar för att aktivera Windows.'
                Jag angav ingen produktnyckel under installationen, och jag tror inte jag har någon digital licens kopplad till mitt Microsoft-konto.
                Vad menar den med att jag måste 'aktivera' systemet? Ska jag klappa den lite? Det ser lite oproffsigt ut med den där texten där hela tiden.
            """,
            "losning_nyckelord": ["Halvtransparent text ('vattenstämpel') 'Aktivera Windows. Gå till Inställningar för att aktivera Windows.' visas på Windows 10 Home skärm efter ominstallation från generisk USB; produktnyckel ej angiven, ingen digital licens", "Windows-installationen är inte aktiverad med en giltig licens", "ange en giltig Windows 10 produktnyckel i Systeminställningar > Aktivering", "köp en Windows 10-licens eller använd en befintlig digital licens kopplad till ditt Microsoft-konto"],
            "start_prompt": "Det står en suddig text i hörnet på min fönsterskärm som säger att jag måste 'aktivera' systemet. Vad menar den med det? Ska jag klappa den lite?"
        },
        {
            "id": "L4_P005",
            "beskrivning": """
                Jag har en gammal stationär dator, en Fujitsu Siemens Scaleo P med ett ASUS P5KPL-AM moderkort. Den har börjat bli alldeles virrig i tiden!
                Varje gång jag stänger av den helt, alltså drar ur strömsladden en stund, och sen startar den igen, så har klockan i Windows hoppat tillbaka till den 1 januari 2002, klockan 00:00! Det händer också i den där BIOS-inställningen som kommer upp om man trycker på en knapp vid start.
                Det är ju väldigt opraktiskt, för då fungerar inte internet sidorna som de ska förrän jag ställt om klockan manuellt.
                Min son sa att det kunde vara ett litet batteri på moderkortet, ett sånt där platt runt CR2032, som har tagit slut. Kan det stämma? Datorn längtar kanske tillbaka till när Måns var kattunge.
            """,
            "losning_nyckelord": ["Systemklocka i BIOS och Windows på stationär dator ('Fujitsu Siemens Scaleo P', moderkort 'ASUS P5KPL-AM') återställs till 01-01-2002 00:00 efter att datorn varit strömlös; moderkortet använder CR2032-batteri", "CMOS-batteriet på moderkortet är urladdat eller defekt", "byt ut det lilla runda batteriet (CR2032) på datorns moderkort", "sätt i ett nytt, fräscht BIOS-batteri"],
            "start_prompt": "Min dator har blivit alldeles virrig i tiden! Varje gång jag stänger av den helt så hoppar klockan tillbaka till år 2001. Den kanske längtar tillbaka till när Måns var kattunge."
        },
        {
            "id": "L4_P006",
            "beskrivning": """
                Jag försöker skriva ut några bilder på Måns på min bläckstråleskrivare, en Canon PIXMA MG3650. Jag har PG-540 för svart och CL-541 för färgpatroner i den.
                Men utskrifterna blir alldeles randiga! Det är tjocka, jämnt fördelade mörka horisontella ränder som delvis täcker texten och bilderna. Det ser inte klokt ut!
                Jag har provat att köra den där 'Djuprengöring av skrivhuvud' som finns i skrivarens programvara flera gånger, jag lät den till och med vila en stund emellan, men det blir ingen märkbar förbättring.
                Det är som om någon har ritat med en bred svart tuschpenna över alltihop. Patronerna är inte nya, men de är inte helt tomma heller, tror jag.
            """,
            "losning_nyckelord": ["Bläckstråleskrivare ('Canon PIXMA MG3650' med PG-540/CL-541 patroner) producerar utskrifter med tjocka, jämnt fördelade mörka horisontella ränder; 'Djuprengöring av skrivhuvud' har körts utan förbättring", "skrivhuvudets munstycken är igentäppta och behöver rengöras", "kör skrivhuvudsrengöring (eventuellt flera gånger med paus emellan)", "om rengöring inte hjälper kan patronen eller skrivhuvudet vara defekt", "byt bläckpatroner"],
            "start_prompt": "Mina utskrifter från skrivaren får tjocka mörka ränder tvärs över texten, som om någon har ritat med en bred svart tuschpenna över alltihop. Det ser inte klokt ut!"
        },
        {
            "id": "L4_P007",
            "beskrivning": """
                Jag skulle spela min favoritmusik från Spotify på mitt högtalarsystem, ett Logitech Z313 2.1-system som är anslutet till det gröna ljuduttaget på datorn.
                Men ljudet kommer bara från den högra lilla högtalaren (satellithögtalaren), den vänstra är helt tyst! Den stora baslådan (subwoofern) fungerar dock, den brummar på som den ska.
                Jag tittade i Windows ljudinställningar, i den där Realtek HD Audio Manager, och där ser jag att ljudbalansen mellan höger och vänster kanal är helt fel. Det står: Höger kanal: 100%, Vänster kanal: 0%.
                Jag har inte rört den där inställningen med flit! Det är som att den vänstra högtalaren har tagit semester.
            """,
            "losning_nyckelord": ["Ljuduppspelning (från 'Spotify') via högtalarsystem ('Logitech Z313 2.1' anslutet till grönt ljuduttag) endast från höger satellithögtalare, vänster tyst, subwoofer fungerar; Windows ljudbalans visar Höger 100%, Vänster 0%", "ljudbalansen mellan höger och vänster kanal är felinställd", "justera ljudbalansen till mitten (50% för varje kanal) i ljudinställningarna", "centrera stereobalansen för uppspelningsenheten"],
            "start_prompt": "När jag spelar min favoritmusik så hörs den bara i den högra högtalaren – den vänstra är alldeles tyst! Det är som att den har tagit semester."
        },
        {
            "id": "L4_P008",
            "beskrivning": """
                Jag har en extern hårddisk, en WD Elements 2TB Portable (Modell: WDBU6Y0020BBK, P/N: WDBUZG0020BBK-WESN), där jag sparar alla mina bilder på Måns. Den ansluts med en enkel USB 3.0-kabel.
                Nu försökte jag koppla in den i en USB 2.0-port på min gamla dator för att visa bilderna för min syster. Men när jag ansluter den så börjar den avge ett repetitivt klickljud.
                Den syns kortvarigt i 'Den här datorn' och sen försvinner den igen. Det går inte att komma åt filerna.
                Min son sa att den här typen av disk kan kräva mer ström än vad en enskild gammal USB 2.0-port kan ge. Den kanske är hungrig? På min nya dator med USB 3.0 fungerar den fint.
            """,
            "losning_nyckelord": ["Extern hårddisk ('WD Elements 2TB Portable' med enkel USB 3.0 kabel) avger repetitivt klickljud vid anslutning till USB 2.0-port på äldre dator; syns kortvarigt och försvinner", "extern hårddisk får inte tillräckligt med ström från USB-porten", "använd en USB Y-kabel för att ansluta till två USB-portar för extra ström", "testa med en USB-hubb som har egen strömförsörjning", "anslut till en USB 3.0 port om möjligt"],
            "start_prompt": "Min yttre hårddisk, den där lilla lådan jag sparar bilder på Måns i, klickar och försvinner direkt när jag kopplar in den i den gamla datorn. Den kanske är hungrig?"
        },
        {
            "id": "L4_P009",
            "beskrivning": """
                Jag har kopplat min bärbara dator, en Dell Inspiron 15 5559 med Intel HD Graphics 520, till min stora Samsung UE40H6400 TV med en HDMI-kabel. Jag ville se på film på stor skärm.
                Bilden visas alldeles utmärkt på TV:n, men ljudet spelas fortfarande från datorns inbyggda högtalare! Det är ju inte meningen.
                Jag har tittat i Windows Ljudinställningar under fliken Uppspelning. Där visas 'Högtalare (Realtek High Definition Audio)' som standardenhet. Min Samsung TV (Intel(R) Display Audio) finns med i listan, men den är antingen 'Inaktiverad' eller i alla fall inte vald som standard.
                Jag har provat att högerklicka på TV:n i listan, men jag är osäker på vad jag ska välja.
            """,
            "losning_nyckelord": ["Bärbar dator ('Dell Inspiron 15 5559') ansluten till TV ('Samsung UE40H6400') via HDMI; bild visas på TV men ljud spelas från datorns högtalare; i Windows Ljudinställningar är 'Högtalare (Realtek High Definition Audio)' standard, 'Samsung TV (Intel(R) Display Audio)' listas men är inaktiverad/inte standard", "HDMI-ljudutgången är inte vald som standardenhet i Windows", "aktivera TV:n (HDMI) som ljudenhet och ställ in den som standard i ljudinställningarna", "högerklicka på HDMI-ljudenheten (Samsung TV) i ljudpanelen och välj 'Aktivera' och sedan 'Ange som standardenhet'"],
            "start_prompt": "Jag har kopplat min bärbara dator till den stora teven för att se på film, och jag får fin bild, men ljudet kommer fortfarande bara från den lilla datorn! Det är ju inte meningen."
        },
        {
            "id": "L4_P010",
            "beskrivning": """
                Jag har en iPad Air 2 (Modell A1566, MGKL2KN/A) med iOS 15, och den har börjat tjata om att 'Lagringsutrymme nästan fullt'.
                Jag har gått in under 'Inställningar > Allmänt > iPad-lagring' och där ser jag att hela 10GB upptas av 'Bilder > Nyligen raderade'. Detta trots att jag har raderat massor av gamla bilder och videor på Måns när han var liten från Bilder-appen!
                Jag har tittat i Bilder-appen, och mycket riktigt, i albumet 'Nyligen raderade' ligger alla de där bilderna kvar. Jag trodde de försvann direkt när man raderade dem.
                Var tar de vägen egentligen, de där raderade bilderna? De verkar ju inte raderas automatiskt direkt.
            """,
            "losning_nyckelord": ["Surfplatta ('iPad Air 2', iOS 15) meddelar 'Lagringsutrymme nästan fullt'; 10GB upptas av 'Bilder > Nyligen raderade' trots att bilder raderats från Bilder-appen; albumet 'Nyligen raderade' innehåller objekten", "raderade bilder/videor ligger kvar i albumet 'Nyligen raderade' och tar upp plats", "gå in i Bilder-appen > Album > Nyligen raderade och välj 'Välj' sedan 'Radera alla' för att permanent ta bort objekten", "töm papperskorgen för bilder manuellt"],
            "start_prompt": "Min platta säger att lagringen är full fast jag har raderat massor av gamla bilder på Måns när han var liten. Var tar de vägen egentligen, de där raderade bilderna?"
        }
    ],
    # --- LEVEL 5 PROBLEMS (Index 4) - Based on "Nivå A" ---
    [
        {
            "id": "L5_P001",
            "beskrivning": """
                Jag skulle just starta min dator, en Acer Veriton M2630G, för att titta på mina bilder på Måns.
                Men direkt efter den där första texten som alltid kommer upp (BIOS POST tror jag det heter), så blev skärmen svart och det stod med vit text: 'S.M.A.R.T. Status BAD, Backup and Replace. Press F1 to Resume.'
                Jag tryckte på F1-knappen som den sa, och då startade Windows till slut, men datorn är märkbart långsam nu och ibland hänger den sig helt. Hårddisken i datorn är en Toshiba DT01ACA100 på 1TB.
                Jag blir så orolig när det står 'BAD' och 'Replace'. Tänk om alla mina bilder och allt annat på datorn försvinner! Det känns inte bra alls. Datorn har också låtit lite mer än vanligt på sistone.
            """,
            "losning_nyckelord": ["Vid uppstart av dator ('Acer Veriton M2630G' med 'Toshiba DT01ACA100 1TB' HDD), efter BIOS POST, visas svart skärm med text: 'S.M.A.R.T. Status BAD, Backup and Replace. Press F1 to Resume.'; Windows startar efter F1 men är långsamt/hänger sig", "hårddisken rapporterar kritiska S.M.A.R.T.-fel och är på väg att gå sönder", "säkerhetskopiera alla viktiga data omedelbart och byt ut den felande hårddisken", "installera en ny hårddisk och återställ systemet från backup eller nyinstallation"],
            "start_prompt": "Min stackars dator varnar för att 'Hårddisken mår dåligt – byt snarast!' redan innan den hunnit starta ordentligt. Den ber mig trycka F1 för att fortsätta, men det känns inte bra alls. Tänk om alla mina bilder på Måns försvinner!"
        },
        {
            "id": "L5_P002",
            "beskrivning": """
                Jag skulle starta min fina nya bärbara dator, en Microsoft Surface Laptop 3 med Windows 10 Pro. Den har något som heter BitLocker-diskkryptering aktiverat på systemenheten, sa min son.
                Men nu när jag startar den visar den en blå skärm där det står: 'BitLocker-återställning. Ange återställningsnyckeln för den här enheten för att fortsätta.' Det visas också ett Nyckel-ID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX.
                Jag har ingen aning om var jag har en sådan återställningsnyckel! Jag minns inte att jag har sparat någon, och min son säger att den inte finns på mitt Microsoft-konto.
                Hjälp! Nu kommer jag inte in i datorn alls! Jag som skulle skriva ett viktigt brev.
            """,
            "losning_nyckelord": ["Bärbar dator ('Microsoft Surface Laptop 3' med Windows 10 Pro och BitLocker) visar blå skärm vid start: 'BitLocker-återställning. Ange återställningsnyckeln... Nyckel-ID: XXXXXXXX...'; användaren har inte sparat nyckeln, finns ej på Microsoft-konto", "BitLocker-diskkryptering kräver återställningsnyckel efter systemändring eller misstänkt manipulation", "leta efter en utskriven BitLocker-återställningsnyckel eller en som sparats på USB-minne vid installationen", "om nyckeln är förlorad kan data vara oåtkomliga utan ominstallation"],
            "start_prompt": "Hjälp! Min fina nya bärbara dator har fått fnatt! Den visar en blå skärm och ber mig skriva in en jättelång 'återställningskod' innan Windows vill öppnas. Jag har ingen aning om var jag har en sådan kod!"
        },
        {
            "id": "L5_P003",
            "beskrivning": """
                Jag försökte starta min gamla trotjänare till dator som kör Windows XP Professional. Den har ett Phoenix AwardBIOS v6.00PG.
                Efter den där första texten som kommer upp (BIOS POST), så blir skärmen bara svart och det står 'NTLDR is missing. Press Ctrl+Alt+Del to restart.' Jag har provat att trycka Ctrl+Alt+Del, men då startar den bara om och samma meddelande kommer igen.
                Jag kollade i BIOS-inställningarna, och där är CD-ROM-läsaren satt som första startenhet, och hårddisken (en Maxtor DiamondMax Plus 9 80GB ATA/133) som andra. Det har alltid varit så.
                Jag tänkte att jag kunde försöka starta från min gamla Windows XP installations-CD, men det verkar inte som att datorn ens försöker läsa från CD:n. Det händer ingenting när skivan är i, den bara snurrar lite och sen kommer felet igen.
                Det låter som en viktig del har sprungit bort. Kanske Måns har gömt den? Nu kommer jag inte åt mina gamla brev alls!
            """,
            "losning_nyckelord": ["Äldre dator (Windows XP Pro, Phoenix AwardBIOS v6.00PG) visar svart skärm med text: 'NTLDR is missing. Press Ctrl+Alt+Del to restart'; CD-ROM är första startenhet i BIOS, HDD ('Maxtor DiamondMax Plus 9 80GB ATA/133') andra; start från XP installations-CD misslyckas (CD läses ej)", "felaktig startenhetsordning (boot order) i BIOS eller problem med startfilerna på hårddisken", "gå in i BIOS-inställningarna och ställ in hårddisken (HDD) som första startenhet", "kontrollera att hårddisken detekteras korrekt i BIOS och försök reparera startsektorn med XP-CD (om CD-läsaren fungerar)", "kontrollera IDE/SATA-kabeln till hårddisken"],
            "start_prompt": "Min gamla trotjänare till dator säger bara 'NTLDR saknas' och vägrar gå vidare från en svart skärm. Det låter som en viktig del har sprungit bort. Kanske Måns har gömt den?"
        },
        {
            "id": "L5_P004",
            "beskrivning": """
                Det var ett kort strömavbrott här hemma, bara någon sekund. Efter det försökte jag starta min stationära dator (moderkort 'Gigabyte GA-Z97X-Gaming 5', CPU 'Intel Core i7-4790K').
                Datorn startar på så sätt att fläktarna börjar snurra på maxhastighet och LED-lamporna på moderkortet lyser, men fönsterskärmen får ingen signal alls, den är helt svart och säger 'No Input'.
                Jag såg att det finns en liten display på moderkortet, en Debug LED, och den visar '00'. Min son sa att '00' ofta kan indikera CPU-problem eller att BIOS har blivit korrupt.
                Jag har provat att göra en CMOS-reset med den där lilla jumpern på moderkortet som sonen visade mig, men det gjorde ingen skillnad. Det är som att den har blivit rädd för mörkret och vägrar vakna ordentligt.
            """,
            "losning_nyckelord": ["Stationär dator (moderkort 'Gigabyte GA-Z97X-Gaming 5', CPU 'Intel Core i7-4790K') startar efter strömavbrott (fläktar max, moderkorts-LEDs lyser) men skärmen får ingen signal ('No Input'); Debug LED på moderkort visar '00'; CMOS-reset via jumper utan effekt", "BIOS/CMOS-inställningarna är korrupta eller moderkortet har problem efter strömavbrott", "utför en grundlig CMOS-återställning genom att ta ur moderkortsbatteriet en stund medan datorn är strömlös", "kontrollera alla anslutningar på moderkortet och testa med minimal konfiguration (endast CPU, ett RAM, grafikkort)", "testa med annat nätaggregat"],
            "start_prompt": "Efter ett litet strömavbrott här hemma så snurrar fläktarna i datorn som tokiga, men fönsterskärmen tänds aldrig. Den är helt svart och säger 'Ingen signal'. Det är som att den har blivit rädd för mörkret."
        },
        {
            "id": "L5_P005",
            "beskrivning": """
                Jag skulle skriva ut mina dikter om Måns från WordPad i Windows 10. Jag har nyligen anslutit min HP LaserJet P1102w skrivare till datorn med en USB-kabel.
                Men när jag skriver ut så blir sidorna fyllda med helt obegripliga tecken och symboler! Det ser ut som 'ÿØÿà€JFIF€€Æ @#$!%^&*' och en massa annat krafs.
                Windows använde automatiskt något som heter 'Microsoft IPP Class Driver' när jag anslöt skrivaren. Jag minns att skrivaren fungerade alldeles utmärkt på min gamla dator, och då hade jag installerat HP:s egna, modellanpassade drivrutiner.
                Det ser ut som katten själv har varit framme och skrivit på pappret! Det går ju inte att läsa alls.
            """,
            "losning_nyckelord": ["Utskrift från WordPad (Windows 10) till HP LaserJet P1102w (nyligen USB-ansluten) resulterar i sidor fyllda med obegripliga tecken/symboler; Windows använde 'Microsoft IPP Class Driver'", "felaktig eller generisk skrivardrivrutin används av Windows", "ladda ner och installera den officiella, modellanpassade skrivardrivrutinen från HP:s webbplats för LaserJet P1102w", "avinstallera den nuvarande drivrutinen och installera rätt PCL- eller PostScript-drivrutin"],
            "start_prompt": "När jag försöker skriva ut mina dikter om Måns så blir all text på pappret bara en massa obegripliga krumelurer och konstiga tecken. Det ser ut som katten själv har varit framme och skrivit!"
        },
        {
            "id": "L5_P006",
            "beskrivning": """
                Min son hjälpte mig att installera om Windows 7 Ultimate (32-bitars, utan Service Pack) på en gammal dator. Allt verkar fungera, men jag kan inte komma åt några säkra webbplatser som google.com eller microsoft.com.
                När jag använder Internet Explorer 8 så står det bara 'Internet Explorer kan inte visa webbsidan' eller så kommer det upp ett fel om certifikat, 'Felkod: DLG_FLAGS_INVALID_CA / INET_E_SECURITY_PROBLEM'.
                Systemtiden och datumet på datorn är helt korrekta, det har jag kollat noga. Windows Update fungerar inte heller, det står att den 'kan inte söka efter nya uppdateringar' och ger felkod 80072EFE.
                Min son nämnde något om att det kunde bero på saknade rotcertifikat och stöd för TLS/SSL-protokoll. Det är som att alla dörrar på internet är låsta!
            """,
            "losning_nyckelord": ["Nyinstallerad Windows 7 Ultimate (utan SP, 32-bit) kan ej öppna HTTPS-webbplatser (IE8 visar 'kan inte visa webbsida' eller certifikatfel 'DLG_FLAGS_INVALID_CA / INET_E_SECURITY_PROBLEM'); Windows Update fungerar ej (felkod 80072EFE); systemtid/datum korrekt", "operativsystemet saknar uppdaterade rotcertifikat och modernt TLS/SSL-stöd", "installera Windows 7 Service Pack 1 och alla efterföljande kumulativa uppdateringar manuellt (t.ex. via Microsoft Update Catalog)", "importera aktuella rotcertifikat och aktivera TLS 1.2 stöd via registerändringar eller Microsoft Easy Fix"],
            "start_prompt": "Inga säkra sidor på internet vill öppnas på min nyinstallerade dator – allt bara klagar på ogiltiga 'certifikat' fast datumet på datorn stämmer. Det är som att alla dörrar är låsta!"
        },
        {
            "id": "L5_P007",
            "beskrivning": """
                Jag har en dator med 8GB RAM (Corsair Vengeance LPX DDR4 2400MHz) och det finns ungefär 50GB ledigt på min C-disk (en SSD, Samsung 860 EVO 250GB).
                Men när jag använder Google Chrome och har många flikar öppna samtidigt som jag försöker redigera bilder på Måns i Adobe Photoshop Elements 2021, så kommer det ofta upp ett meddelande från Windows: 'Datorn har ont om minne. Spara dina filer och stäng dessa program.'
                Ofta kraschar programmen strax efteråt. Jag har tittat på den där växlingsfilen (pagefile.sys), och den är systemhanterad och verkar ganska liten, kanske bara 2GB.
                Vad menar den med virtuellt minne, är det låtsasminne? Det är väldigt irriterande när allt bara stängs ner.
            """,
            "losning_nyckelord": ["System med 8GB RAM, 50GB ledigt på C: (SSD), Windows-meddelande 'Datorn har ont om minne' vid användning av Chrome (många flikar) och Photoshop Elements; program kraschar; växlingsfil (pagefile.sys) systemhanterad, liten (t.ex. 2GB)", "systemets växlingsfil (virtuellt minne) är för liten för den aktuella arbetsbelastningen", "öka storleken på växlingsfilen manuellt i Windows systeminställningar (t.ex. till 1.5x RAM eller systemhanterad med större initialstorlek)", "överväg att utöka det fysiska RAM-minnet om problemet kvarstår frekvent"],
            "start_prompt": "Min dator gnäller om att den har för lite 'virtuellt minne' och stänger ner mina program när jag försöker redigera bilder på Måns och ha många internetsidor öppna samtidigt. Vad menar den med virtuellt, är det låtsasminne?"
        },
        {
            "id": "L5_P008",
            "beskrivning": """
                Jag har köpt ett nytt fint USB-headset, ett Logitech H390, för att kunna prata med barnbarnen utan att störa Måns.
                Ljudet i själva hörlurarna fungerar alldeles utmärkt i Windows 10. Men när jag tittar i Ljudinställningarna under fliken 'Inspelning' (genom att högerklicka på ljudikonen och välja Ljud), så listas bara min gamla 'Mikrofon (Realtek High Definition Audio)' och något som heter 'Stereomix'.
                Jag ser ingen mikrofon från mitt Logitech USB Headset där, trots att headsetet visas korrekt i Enhetshanteraren under 'Ljud-, video- och spelenheter' utan några fel. Jag har också sett till att 'Visa inaktiverade enheter' är markerat i Ljudinställningarna.
                Det är ju tråkigt, för nu hör de inte mig! Jag har kollat så att mikrofonen inte är avstängd med knappen på sladden.
            """,
            "losning_nyckelord": ["Nytt USB-headset ('Logitech H390') ljud i hörlurar fungerar i Windows 10, men mikrofonen listas ej under 'Ljud > Inspelning' (endast 'Mikrofon (Realtek...)' och 'Stereomix' synliga); headset visas i Enhetshanteraren utan fel; 'Visa inaktiverade enheter' markerat", "headsetets mikrofon är inte aktiverad eller vald som standardinspelningsenhet, eller har sekretessproblem", "kontrollera att mikrofonen på headsetet inte är fysiskt avstängd (mute-knapp)", "gå till Enhetshanteraren, avinstallera headsetet och låt Windows installera om det; välj sedan som standard i Ljudinställningar", "kontrollera mikrofonens sekretessinställningar i Windows 10"],
            "start_prompt": "Jag har köpt en ny fin hörlur med mikrofon för att kunna prata med barnbarnen, men mikrofonen syns inte i listan i datorn! Ljudet i lurarna fungerar, men de hör inte mig. Det är ju tråkigt."
        },
        {
            "id": "L5_P009",
            "beskrivning": """
                Jag brukar titta på roliga kattklipp på YouTube och ibland på SVT Play i min webbläsare Mozilla Firefox 91 ESR på min Windows 10 dator (version 21H2).
                Men nu när jag försöker spela upp videor så hör jag bara ljudet – bildrutan är helt grå eller svart! Det gäller både på YouTube och SVT Play, och även i andra webbläsare har jag märkt.
                Problemet uppstod ganska nyligen, jag tror det var efter en Windows-uppdatering (något med KB500XXXX i namnet). Mitt grafikkort är ett Intel HD Graphics 4000 och drivrutinen är från 2017.
                Jag har kollat att maskinvaruacceleration i Firefox är aktiverad, det brukar den vara.
                Det är ju det roligaste som försvinner när bilden är borta! Måns blir också besviken, han brukar titta med mig.
            """,
            "losning_nyckelord": ["Videouppspelning ('YouTube HTML5 player', 'SVT Play') i Firefox 91 ESR på Windows 10 (21H2) visar endast ljud, bildrutan grå/svart; problem uppstod efter Windows-uppdatering (KB500XXXX); grafikkort Intel HD Graphics 4000 (drivrutin 2017); maskinvaruacceleration i Firefox aktiverad; problem i andra webbläsare också", "problem med videokodekar eller grafikdrivrutiner efter systemuppdatering", "installera ett omfattande kodekpaket (t.ex. K-Lite Codec Pack Full)", "försök att inaktivera/aktivera maskinvaruacceleration i webbläsarens inställningar eller systemets grafikinställningar; sök efter nyare (eller äldre stabila) grafikdrivrutiner"],
            "start_prompt": "När jag försöker titta på roliga kattklipp på internet så hör jag bara ljudet – bilden är alldeles grå! Det är ju det roligaste som försvinner. Måns blir också besviken."
        },
        {
            "id": "L5_P010",
            "beskrivning": """
                Jag skulle starta min stationära dator (moderkort 'ASUS P8P67 LE', CPU 'Intel Core i5-2500K', grafikkort 'NVIDIA GeForce GTX 560 Ti') för att sortera mina bilder.
                Men när jag tryckte på startknappen så pep den konstigt: ett långt pip och sedan två korta pip. Min son sa att det på AMI BIOS ofta indikerar problem med grafikkortet eller att ingen bildskärm är ansluten.
                Mycket riktigt, fönsterskärmen förblir alldeles svart, den säger att den inte får någon signal via DVI-porten. Fläktarna på grafikkortet snurrar dock som de ska.
                Kortet sitter i den översta stora porten (PCIe x16) och de där extra strömkablarna är anslutna till det.
                Den vill nog inte vakna idag. Jag har provat att starta om flera gånger, men det är samma ledsna fågel-pip varje gång.
            """,
            "losning_nyckelord": ["Stationär dator (moderkort 'ASUS P8P67 LE', CPU 'Intel Core i5-2500K', grafikkort 'NVIDIA GeForce GTX 560 Ti') avger en lång och två korta ljudsignaler (AMI BIOS beep code) vid start; skärmen svart (ingen signal via DVI); grafikkortsfläktar snurrar; kort i översta PCIe x16, extra ström ansluten", "grafikkortet har dålig kontakt, är felaktigt anslutet eller defekt", "ta ur och sätt tillbaka grafikkortet ordentligt i PCIe-porten (reseat)", "kontrollera att alla extra strömanslutningar till grafikkortet sitter fast; testa med ett annat grafikkort om möjligt", "testa med en annan bildskärmskabel eller bildskärmsport"],
            "start_prompt": "Min dator startar med ett långt pip och sedan två korta, som en ledsen fågel, och fönsterskärmen förblir alldeles svart. Den vill nog inte vakna idag."
        }
    ]
]

# Helper to get the number of levels
NUM_LEVELS = len(PROBLEM_CATALOGUES)