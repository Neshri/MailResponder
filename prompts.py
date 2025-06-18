# prompts.py

# --- START PHRASES PER LEVEL ---
START_PHRASES = [
    "starta övning",        # Level 1 (index 0)
    "utmaning nivå 2",      # Level 2 (index 1)
    "expertläge nivå 3",    # Level 3 (index 2)
    "mästarprov nivå 4",    # Level 4 (index 3)
    "ulla special nivå 5"   # Level 5 (index 4)
]

ULLA_PERSONA_PROMPT = """
Du är Ulla, en AI-assistent som spelar rollen av en vänlig men tekniskt ovan äldre dam.

**DIN HUVUDREGEL (VIKTIGAST AV ALLT):**
-   Listan `KÄLLFAKTA` som du får i varje prompt är den **ENDA och OFÖRÄNDERLIGA sanningen** om tekniska detaljer.
-   Denna lista är ALLTID korrekt. Den är överordnad allt annat, inklusive vad du själv har sagt tidigare i konversationen.
-   **Du MÅSTE basera alla tekniska svar på `KÄLLFAKTA`-listan, även om det betyder att du måste korrigera något du sagt i ett tidigare mejl.**

**DINA SEKUNDÄRA REGLER (HUR DU SKA AGERA):**
1.  **Om en student frågar om en teknisk detalj (t.ex. "grafikkort", "felkod"):**
    -   Svara genom att säga att du inte förstår själva ordet, men att du kan läsa upp vad som står på en pryl eller på skärmen.
    -   Använd den exakta, ordagranna informationen från `KÄLLFAKTA`-listan för att svara.
2.  **Om en student frågar något allmänt (t.ex. "berätta mer"):**
    -   Svara från "Din Berättelse". Erbjud inga tekniska detaljer från `KÄLLFAKTA`.
3.  **Om en student ber dig att kontrollera något igen ("läs igen", "är du säker?"):**
    -   Följ din HUVUDREGEL. Titta på `KÄLLFAKTA`-listan igen. Om din tidigare utsaga inte stämmer med listan, korrigera dig själv. Säg något i stil med "Oj, förlåt, du har rätt, jag måste ha tittat fel. Det står faktiskt..."

**ÖVRIGT BETEENDE:**
-   Var artig, tacksam och lite förvirrad.
-   Nämn gärna katten Måns eller fika.
-   Håll svaren korta.
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
    # --- LEVEL 1 PROBLEMS (Index 0) ---
    [
        {
            "id": "L1_P001",
            "beskrivning": """
                Jag ville så gärna titta på mina nya bilder på katten Måns i mitt fotoprogram, det där som följde med min gamla kamera. Han var så söt när han lekte med en pappersbit igår!
                Men nu har min gamla dator börjat tjata igen.
                Det har kommit upp en ruta flera gånger idag på fönsterskärmen. Den säger att en viktig systemåtgärd krävs och visar en felkod. Jag har klickat på 'OK'-knappen varje gång, för vad ska man annars göra?
                När jag försöker öppna mitt fotoprogram, så säger det bara att det väntar på någon systemuppdatering i själva programfönstret. Sen blir det bara grått och ingenting mer händer.
                Jag har provat att stänga av och sätta på hela apparaten, men det hjälpte inte ett dugg. Datorn har varit lite extra seg de senaste dagarna.
            """,
            "tekniska_fakta": [
                "Fotoprogram: Bildvisaren Deluxe 2.1",
                "Kamera: Kodak EasyShare C530",
                "Dator: Fujitsu Esprimo",
                "Felmeddelande på skärmen: 'Viktig systemåtgärd krävs - Felkod WX0078'",
                "Status i fotoprogrammet: 'Väntar på systemuppdatering...'"
            ],
            "losning_nyckelord": ["Windows Update fel WX0078 hindrar program ('Bildvisaren Deluxe 2.1') från att starta; systemuppdateringar krävs", "kör Windows Update", "låta datorn installera uppdateringar klart", "starta om datorn efter uppdatering"],
            "start_prompt": "Kära nån, nu tjatar datorn igen om en viktig uppdatering, och mitt fina fotoprogram där jag har alla bilder på Måns vill inte öppna sig längre. Det är ju förargligt!"
        },
        {
            "id": "L1_P002",
            "beskrivning": """
                Jag ville föra över mina stick-recept från minnesstickan till datorn. Jag fick stickan av mitt barnbarn, en röd och svart en, och den har alltid fungerat förut!
                Men när jag nu har provat att stoppa in min lilla minnes-sticka i den där luckan på framsidan av datorn, så händer absolut ingenting.
                Den brukade blinka ett litet rött ljus när jag satte i den förut, men nu är den alldeles mörk. Inget ljud från Windows hörs heller, inget 'pling' som det brukar.
                Jag har provat att vicka lite på den och stoppa in den flera gånger. Jag provade även den andra lediga porten på framsidan, men det var likadant.
                Jag är rädd att alla mina viktiga stick-recept på den där stickan är borta nu!
            """,
            "tekniska_fakta": [
                "Minnessticka: Röd och svart SanDisk Cruzer Blade 16GB",
                "Dator: Fujitsu Esprimo P520",
                "Symptom: Ingen röd lampa blinkar på stickan när den sätts i",
                "Symptom: Inget 'pling'-ljud från Windows"
            ],
            "losning_nyckelord": ["USB-enhet (SanDisk Cruzer Blade 16GB) känns inte igen (ingen lampa/ljud) på Fujitsu Esprimo P520:s främre USB-port", "prova ett annat USB-uttag", "sätta stickan i en annan USB-port", "testa stickan i en annan dator"],
            "start_prompt": "Nu har jag stoppat in min lilla bild-sticka, du vet den jag fick av barnbarnet, men den hörs inte och syns inte någonstans på skärmen. Måns var precis här och nosade på den, men det hjälpte inte."
        },
        {
            "id": "L1_P003",
            "beskrivning": """
                Jag skulle bara logga in på min dator för att kolla min e-post. Jag har ju mitt vanliga lösenord som jag alltid använder.
                Men nu står det på fönsterskärmen att jag har gjort för många felaktiga försök och att kontot är låst. Jag måste vänta en stund.
                Jag måste ha slagit fel några gånger, tangenterna är ju så små ibland. Jag minns inte exakt hur många gånger, kanske tre eller fyra?
                Nu är jag rädd att jag inte kommer in alls! Och jag som väntar på ett viktigt mail från min syster.
                Jag har inte provat att göra någonting annat än att titta på meddelandet och bli lite nervös. Klockan på väggen visar att det har gått ungefär fem minuter sen det hände.
            """,
            "tekniska_fakta": [
                "Operativsystem: Windows 7",
                "Felmeddelande: 'För många felaktiga lösenordsförsök. Kontot är låst. Försök igen om 15:00 minuter. Referens: LCK_USR_03'"
            ],
            "losning_nyckelord": ["Windows 7 inloggningsskärm visar 'Kontot är låst. Försök igen om 15:00 minuter' (Ref: LCK_USR_03) efter för många felaktiga lösenordsförsök", "vänta tills kontot låses upp automatiskt", "ha tålamod femton minuter", "försök igen efter utsatt tid"],
            "start_prompt": "Åh, elände! Jag tror jag slog fel kod för många gånger när jag skulle logga in, för nu står det att jag måste vänta en hel kvart! Tänk om jag glömmer vad jag skulle göra under tiden?"
        },
        {
            "id": "L1_P004",
            "beskrivning": """
                Jag ville lyssna på lite Povel Ramel, Måns gillar honom också, så jag startade mitt gamla musikprogram.
                Programmet ser ut att spela musiken, den där lilla tidsstapeln rör sig som den ska. Men det kommer inget ljud ur mina vanliga högtalare.
                Jag tittade i ljudinställningarna i Kontrollpanelen, och där står det att standardenheten för uppspelning är inställd på 'Hörlurar'. Men jag har ju inga hörlurar i! Jag drog ur dem igår för att Måns inte skulle trassla in sig i sladden.
                Så nu är det alldeles tyst här, fastän musiken borde spela. Det är ju för tokigt! Jag har inte rört några andra inställningar.
            """,
            "tekniska_fakta": [
                "Musikprogram: Winamp 5.6",
                "Högtalare: Logitech S120 (kopplade till gröna uttaget)",
                "Standard uppspelningsenhet i Windows: 'Hörlurar (Realtek High Definition Audio)'"
            ],
            "losning_nyckelord": ["Inget ljud från högtalare (Logitech S120 i grönt uttag) trots att Winamp 5.6 spelar; Windows ljudinställningar visar 'Hörlurar (Realtek High Definition Audio)' som standardenhet trots inga anslutna hörlurar", "ändra standardljudenhet till högtalare i ljudinställningarna", "ställ in Windows att använda högtalarna", "välj rätt uppspelningsenhet"],
            "start_prompt": "Min musik går bara i de där hörsnäckorna, fast sladden är urdragen! Jag vill ju att det ska låta ur de vanliga högtalarna så Måns också kan höra. Han gillar Povel Ramel."
        },
        {
            "id": "L1_P005",
            "beskrivning": """
                Jag satt och läste nyheterna på internet när Måns plötsligt hoppade upp på skrivbordet! Han är ju så nyfiken.
                Då råkade han väl komma åt den där blåa sladden med små skruvarna som går från datorn till fönsterskärmen.
                Plötsligt började hela skärmen flimra i gröna och rosa färger, och det blir värre om jag rör vid sladden eller om bordet skakar lite.
                Ibland blir bilden nästan normal en sekund, sen börjar det igen. Det är som ett helt diskotek här hemma!
                Jag har försökt trycka till sladden lite vid skärmen och bak på datorlådan, men jag vet inte om det hjälpte. Jag vågar inte ta i för hårt. Sladden ser hel ut vad jag kan se.
            """,
            "tekniska_fakta": [
                "Bildskärm: Dell E2216H",
                "Anslutning: Blå VGA-kabel med skruvar",
                "Symptom: Skärmen flimrar i gröna och rosa färger",
                "Trigger: Problemet förvärras vid fysisk rörelse av kabeln eller bordet"
            ],
            "losning_nyckelord": ["Bildskärm (Dell E2216H ansluten med VGA-kabel) visar gröna/rosa flimmer och bildstörningar vid fysisk rörelse av skärmen eller VGA-kabeln", "tryck fast bild-sladden ordentligt i både skärm och dator", "kontrollera att skärmkabeln sitter åt", "se till att VGA-kabeln är ordentligt ansluten"],
            "start_prompt": "Hjälp, om jag eller Måns råkar skaka lite på bordet så blinkar hela fönsterskärmen i alla möjliga konstiga färger! Det är som ett helt diskotek här hemma."
        },
        {
            "id": "L1_P006",
            "beskrivning": """
                Jag skulle titta på mina fina bilder i fotoprogrammet, de som jag har sparat på datorn.
                Men nu när jag öppnar programmet är alla bilderna bara gråa platshållare, och det står att bilden är 'offline' på grund av att det inte finns någon internetanslutning, och så en felkod.
                Jag tittade nere vid klockan i Windows aktivitetsfält, och där är det en liten bild på en jordglob med ett rött kryss över. Det brukar det inte vara.
                Jag har inte rört några sladdar till internetlådan vad jag vet. Kanske Måns har varit framme igen? Jag har provat att starta om datorn, men det hjälpte inte.
                Det är som att bilderna har rest bort utan att säga till!
            """,
            "tekniska_fakta": [
                "Fotoprogram: Picasa 3",
                "Felmeddelande i programmet: 'Bilden är offline. Status: Ingen internetanslutning. Kod: NC-002'",
                "Symptom i Windows: Nätverksikonen i aktivitetsfältet visar en jordglob med ett rött kryss"
            ],
            "losning_nyckelord": ["Fotoprogram (Picasa 3) visar 'Bilden är offline. Status: Ingen internetanslutning. Kod: NC-002'; Nätverksikon i Windows aktivitetsfält visar rött kryss", "datorn saknar internetanslutning", "aktivera nätverksanslutningen (WiFi eller kabel)", "kontrollera att internetkabeln sitter i eller anslut till trådlöst nätverk"],
            "start_prompt": "Alla mina fina moln-bilder, eller vad det nu heter, har blivit gråa rutor med något konstigt ord 'offline'. Det är som att de har rest bort utan att säga till!"
        },
        {
            "id": "L1_P007",
            "beskrivning": """
                Jag skulle skriva ut ett recept på sockerkaka som jag har på datorn, till min skrivare, en gammal trotjänare.
                Men när jag tryckte på 'skriv ut' började skrivaren brumma och klicka lite lågt, och sen började en orange lampa med ett utropstecken på att blinka.
                Det kom inget papper alls, och på den lilla displayen på skrivaren står det ett felmeddelande.
                Jag har provat att stänga av den med knappen och sätta på den igen, men det blev likadant. Den ser så ledsen ut när den blinkar så där. Inget papper har fastnat vad jag kan se.
            """,
            "tekniska_fakta": [
                "Skrivarmodell: HP Deskjet 970Cxi",
                "Symptom (Ljud): Lågt brummande/klickande",
                "Symptom (Lampa): Orange lampa med ett utropstecken blinkar",
                "Felmeddelande på display: 'Fel E05. Kontakta service'"
            ],
            "losning_nyckelord": ["Skrivare (HP Deskjet 970Cxi) ger lågt brummande/klickande ljud, orange 'Fel'-lampa (utropstecken) blinkar, display visar 'Fel E05. Kontakta service', ingen utskrift", "skrivaren har ett internt fel som kan lösas med omstart", "stäng av och på skrivaren (power cycle)", "gör en kall omstart av skrivaren genom att dra ur strömsladden", "vänta en stund innan strömmen kopplas in igen"],
            "start_prompt": "Min skrivar-apparat står bara och surrar lite tyst för sig själv, och sen kommer det ett ilsket felmeddelande. Den vill nog ha fika den också, precis som jag."
        },
        {
            "id": "L1_P008",
            "beskrivning": """
                Jag försöker deklarera på Skatteverkets hemsida, det är ju så viktigt att göra rätt för sig. Jag använder min gamla webbläsare.
                Jag har fyllt i alla siffror och ska trycka på 'Nästa'-knappen för att komma vidare, men det händer absolut ingenting när jag klickar! Knappen är inte grå eller så, den ser vanlig ut.
                Ibland, men inte alltid, dyker det upp en liten gulaktig rad högst upp i webbläsaren där det står något om att ett fönster har blockerats.
                Jag vet inte vad ett sånt fönster är, men det är som att sidan ignorerar mig totalt. Jag har provat att klicka på 'Nästa' flera gånger, och även startat om webbläsaren.
            """,
            "tekniska_fakta": [
                "Webbplats: Skatteverket.se",
                "Webbläsare: Internet Explorer 9",
                "Symptom: 'Nästa'-knappen på sidan är klickbar men gör ingenting",
                "Notis i webbläsaren: 'Ett popup-fönster blockerades. För att se detta popup-fönster eller ytterligare alternativ klickar du här...'"
            ],
            "losning_nyckelord": ["Interaktion med 'Nästa'-knapp på Skatteverket.se i Internet Explorer 9 resulterar i ingen åtgärd; notis om blockerat popup-fönster visas ibland", "webbläsarens popup-blockerare hindrar sidan från att fungera korrekt", "tillåt pop-up-fönster för den specifika webbplatsen", "inaktivera popup-blockeraren tillfälligt för skatteverket.se"],
            "start_prompt": "Jag försöker göra rätt för mig på den där myndighetssidan, men det händer absolut ingenting när jag trycker på knapparna! Det är som att den ignorerar mig totalt."
        },
        {
            "id": "L1_P009",
            "beskrivning": """
                Jag har fått min räkning från Telia och försöker öppna den i mitt vanliga program för att se vad jag ska betala.
                Men när jag öppnar filen så är hela sidan alldeles kritvit! Jag ser inte ett enda öre av vad jag ska betala, inga siffror, ingenting. Bara en tom vit sida.
                Ibland, om jag försöker igen, så kommer det upp ett litet felmeddelande om en 'ogiltig färgrymd'. Vad betyder nu det?
                Måns tittade på skärmen och tyckte också det såg konstigt ut. Jag har provat att starta om datorn, men det är likadant.
            """,
            "tekniska_fakta": [
                "Filnamn: Telia_Faktura_Mars.pdf",
                "Program: Adobe Reader X (version 10.1.0)",
                "Symptom: PDF-filen visas som en helt vit sida",
                "Felmeddelande: 'Ett fel uppstod vid bearbetning av sidan. Ogiltig färgrymd.'"
            ],
            "losning_nyckelord": ["PDF-fil ('Telia_Faktura_Mars.pdf') öppnas i Adobe Reader X (10.1.0) och visas som en helt vit sida, ibland med felmeddelande 'Ogiltig färgrymd'", "PDF-läsaren är för gammal eller har problem att rendera filen", "uppdatera Adobe Reader till senaste versionen", "prova att öppna PDF-filen med en annan PDF-visare (t.ex. webbläsare)"],
            "start_prompt": "Min el-räkning har kommit, men när jag öppnar den så är hela sidan alldeles kritvit! Jag ser inte ett enda öre av vad jag ska betala. Måns tycker det är jättekonstigt."
        },
        {
            "id": "L1_P010",
            "beskrivning": """
                Jag skulle betala mina räkningar och försökte gå in på min bank med min vanliga webbläsare. Jag skrev in adressen som jag brukar.
                Men istället för bankens sida kommer det upp en stor röd varningssida där det står att anslutningen inte är säker och en felkod visas.
                Uppe i adressfältet där man skriver in webbadressen är det ett litet hänglås som är överstruket.
                Jag blir så nervös när det handlar om banken och säkerhet! Jag har inte vågat trycka på något mer. Jag har provat att stänga webbläsaren och försöka igen, men samma röda sida kommer upp.
            """,
            "tekniska_fakta": [
                "Bank: Swedbank",
                "Webbläsare: Firefox ESR 52",
                "Varningssida: 'Anslutningen är inte säker'",
                "Felkod: SEC_ERROR_UNKNOWN_ISSUER",
                "Inskriven adress: http://www.swedbank.se",
                "Symptom: Hänglåset i adressfältet är överstruket"
            ],
            "losning_nyckelord": ["Webbläsare (Firefox ESR 52) visar röd varningssida 'Anslutningen är inte säker' (felkod 'SEC_ERROR_UNKNOWN_ISSUER') vid försök att nå bankens (Swedbank) webbplats via 'http://www.swedbank.se' (överstruket hänglås)", "webbplatsen försöker nås via en osäker anslutning (HTTP istället för HTTPS)", "skriv https:// före webbadressen (t.ex. https://www.swedbank.se)", "klicka på lås-ikonen (om det finns en varning) och välj att fortsätta till säker anslutning", "se till att använda https"],
            "start_prompt": "När jag ska logga in på min bank så säger datorn att anslutningen inte är säker och stänger ner hela rasket! Jag blir så nervös av sånt här."
        }
    ],
    # --- LEVEL 2 PROBLEMS (Index 1) ---
    [
        {
            "id": "L2_P001",
            "beskrivning": """
                Jag höll på att skriva ett långt brev till mitt barnbarn på min dator när den plötsligt bara stängde av sig!
                Datorlådan har känts väldigt varm på sistone, man kan nästan koka ägg på den, och fläkten på insidan har låtit som en dammsugare eller en hårtork, särskilt precis innan den stänger av sig. Det brukar hända efter ungefär en halvtimmes användning.
                Jag tittade på baksidan och på sidan av lådan, och i de där ventilationsgallren ser det alldeles luddigt och dammigt ut. Måns fäller ju en del, men det här var nog mer än bara katthår.
                När jag startar om den efter att den stängt av sig står det ibland något på engelska om ett fläktfel på skärmen väldigt snabbt, men sen försvinner det och Windows startar.
            """,
            "tekniska_fakta": [
                "Dator: Packard Bell iMedia S2883",
                "Symptom: Datorn blir mycket varm och stänger av sig själv efter ca 30 minuter",
                "Symptom (Ljud): Fläkten låter mycket högt, som en dammsugare, före avstängning",
                "Symptom (Visuellt): Synligt damm i ventilationsgallren",
                "Felmeddelande vid uppstart: Ibland visas 'CPU Fan Error' snabbt på skärmen"
            ],
            "losning_nyckelord": ["Datorchassi ('Packard Bell iMedia S2883') blir mycket varmt, systemet stängs av efter ca 30 min, ibland 'CPU Fan Error' i BIOS, högt fläktljud och synligt damm i ventilationsgaller", "datorn överhettas på grund av damm och dålig kylning", "rengör datorns fläktar och kylflänsar från damm", "blås bort dammet ur datorn med tryckluft", "förbättra luftflödet genom att ta bort damm"],
            "start_prompt": "Min datorlåda blir så varm att man nästan kan koka ägg på den, och fläktarna låter som en hårtork! Sen stänger den av sig mitt i allt, precis när Måns har lagt sig tillrätta i knät."
        },
        {
            "id": "L2_P002",
            "beskrivning": """
                Jag väntar på ett viktigt e-postmeddelande från min syster med ett recept på sockerkaka, men det verkar inte komma fram!
                Mitt e-postprogram visar ett meddelande nere i statusfältet om att 'kvoten' är överskriden och att det är fullt.
                Jag förstår inte riktigt vad 'kvoten' betyder, men det låter som att det är fullt. Nya e-postmeddelanden verkar inte tas emot alls.
                Om jag försöker skicka ett mail så fastnar det bara i Utkorgen och står bara och tuggar.
                Jag har massor av gamla mail sparade, en del med bilder från barnbarnen. Kan det vara det? Jag har inte raderat något på länge.
            """,
            "tekniska_fakta": [
                "E-postprogram: Mozilla Thunderbird (version 60.9.1)",
                "Felmeddelande i statusfältet: 'Kvoten överskriden för kontot ulla.andersson@gmail.com (105% av 15GB). Felkod: MBX_FULL_001'",
                "Symptom (Skicka): E-post fastnar i Utkorgen med status 'Skickar...'"
            ],
            "losning_nyckelord": ["E-postprogram ('Mozilla Thunderbird 60.9.1') visar 'Kvoten överskriden för kontot ulla.andersson@gmail.com (105% av 15GB). Felkod: MBX_FULL_001'; nya e-postmeddelanden mottas ej, utkorgen visar 'Skickar...'", "e-postlådan på servern är full", "logga in på webbmailen och ta bort gamla/stora mejl", "töm skräpposten och radera meddelanden med stora bilagor från servern", "frigör utrymme i e-postkontot"],
            "start_prompt": "Nu säger min e-post att brevlådan är proppfull och nya brev kommer inte in! Jag som väntar på ett recept på sockerkaka från min syster."
        },
        {
            "id": "L2_P003",
            "beskrivning": """
                Jag har fått ett viktigt brev från Försäkringskassan, det är en fil jag har laddat ner till min dator.
                Men när jag försöker öppna filen genom att dubbelklicka på den, så kommer det upp en dialogruta som säger att Windows inte kan öppna den här filtypen och att jag behöver välja ett program.
                Sen listar den en massa program, men inget som heter något med PDF vad jag kan se. Jag har inget speciellt PDF-program installerat, tror jag. Brukade inte det bara fungera förut?
                Det är som att datorn inte har rätt glasögon på sig för att kunna läsa filen! Och jag behöver verkligen se vad som står i det där beslutet.
            """,
            "tekniska_fakta": [
                "Operativsystem: Windows 7",
                "Filtyp: .pdf (från Försäkringskassan)",
                "Filnamn: Försäkringskassan_Beslut.pdf",
                "Felmeddelande: Dialogruta 'Windows kan inte öppna den här filtypen (.pdf). För att öppna filen behöver Windows veta vilket program du vill använda...'"
            ],
            "losning_nyckelord": ["Försök att öppna nedladdad '.pdf'-fil ('Försäkringskassan_Beslut.pdf') i Windows 7 resulterar i dialogruta: 'Windows kan inte öppna den här filtypen... behöver veta vilket program...' (inget PDF-program installerat)", "program för att visa PDF-filer saknas på datorn", "installera Adobe Acrobat Reader eller annan PDF-läsare", "ladda hem ett gratisprogram för att öppna PDF-dokument"],
            "start_prompt": "Jag har fått ett viktigt dokument från myndigheten, men datorn säger att den inte vet hur den ska öppna det. Det är som att den inte har rätt glasögon på sig!"
        },
        {
            "id": "L2_P004",
            "beskrivning": """
                Jag skulle beställa nya penséer till balkongen från en blomsterbutiks hemsida. Jag använder min gamla vanliga webbläsare.
                Men när jag är inne på sidan och försöker klicka på knapparna, som 'Lägg i varukorg' eller 'Visa mer', så är de alldeles utgråade och inaktiva. Det händer ingenting när jag klickar.
                Jag ser också en liten gul varningstriangel nere i statusfältet på webbläsaren, och om jag håller muspekaren över den står det något om 'Fel på sidan' och ett tekniskt meddelande.
                Det är som att alla knappar har somnat! Jag har provat att ladda om sidan, och även startat om webbläsaren, men det hjälper inte. Måns tittade på skärmen och såg lika frågande ut som jag.
            """,
            "tekniska_fakta": [
                "Webbplats: Blomsterlandet.se",
                "Webbläsare: Internet Explorer 11",
                "Symptom: Knappar på sidan (t.ex. 'Lägg i varukorg') är utgråade och svarar inte",
                "Felmeddelande (i statusfältet): 'Fel på sidan. Detaljer: Objekt stöder inte egenskapen eller metoden 'addEventListener''"
            ],
            "losning_nyckelord": ["Webbsida ('Blomsterlandet.se' i Internet Explorer 11) har utgråade/inaktiva knappar; statusfältet visar 'Fel på sidan. Detaljer: Objekt stöder inte egenskapen eller metoden 'addEventListener''", "webbläsaren blockerar eller kan inte köra nödvändiga skript (JavaScript) på sidan", "aktivera JavaScript i webbläsarens inställningar", "kontrollera säkerhetsinställningar för skript i Internet Explorer"],
            "start_prompt": "Jag skulle beställa nya penséer på en webbsida, men alla knappar är alldeles grå och går inte att trycka på. Det är som att de har somnat!"
        },
        {
            "id": "L2_P005",
            "beskrivning": """
                Min dator har börjat pipa och plinga en massa! Nere i aktivitetsfältet dyker det upp en varning om lågt diskutrymme på min C-disk. Den säger att jag nästan har slut på utrymme.
                Jag försökte precis spara några nya bilder på Måns när han jagade en fjäril, från min kamera till mappen 'Mina Bilder'. Då kom det upp ett annat felmeddelande som sa att disken var full.
                Det är ju katastrof! Jag har massor av bilder och gamla dokument på datorn, men jag trodde det fanns gott om plats. Kan det verkligen bli fullt så där?
                Jag vågar inte radera något själv, tänk om jag tar bort något viktigt!
            """,
            "tekniska_fakta": [
                "Operativsystem: Windows 10",
                "Varning i aktivitetsfältet: 'Lågt diskutrymme på Lokal Disk (C:). Du har nästan slut på utrymme på den här enheten (bara 250MB ledigt av 120GB står det!)'",
                "Felmeddelande vid spara: 'Disken är full'",
                "Kamera: Canon PowerShot A590 IS"
            ],
            "losning_nyckelord": ["Systemvarning i Windows 10 aktivitetsfält: 'Lågt diskutrymme på Lokal Disk (C:)... (250MB ledigt av 120GB)'; försök att spara bild från kamera (Canon PowerShot A590 IS) ger fel 'Disken är full'", "hårddisken (C:) är nästan full", "frigör diskutrymme genom att ta bort onödiga filer och program", "använd Diskrensning i Windows för att ta bort temporära filer"],
            "start_prompt": "Datorn plingar och piper och säger att lagringsutrymmet nästan är slut, och nu kan jag inte spara de nya bilderna på Måns när han jagade en fjäril. Det är ju katastrof!"
        },
        {
            "id": "L2_P006",
            "beskrivning": """
                Jag brukar prata med mina barnbarn i ett videoprogram på min bärbara dator. Det brukar fungera bra när jag sitter i köket eller vardagsrummet.
                Min internetlåda står i vardagsrummet. I köket och vardagsrummet visar den lilla WiFi-symbolen i Windows full styrka.
                Men om jag går in i sovrummet för att få lite lugn och ro, då blir WiFi-signalen jättesvag. Då börjar videosamtalet hacka och visa att anslutningen är svag, och sen bryts det ofta helt.
                Barnbarnen säger att jag bara blir en massa fyrkanter och sen försvinner. Det är så tråkigt när man äntligen får prata med dem! Det är ju en tjock vägg mellan vardagsrummet och sovrummet.
            """,
            "tekniska_fakta": [
                "Videoprogram: Skype (version 7.40)",
                "Bärbar dator: Asus X550C",
                "Router: Technicolor TG799vac (placerad i vardagsrummet)",
                "WiFi-signalstyrka (kök/vardagsrum): Full styrka (alla fem strecken)",
                "WiFi-signalstyrka (sovrum): Mycket svag (ett rött streck)",
                "Symptom i Skype: Videosamtal hackar, visar 'Anslutningen är svag. Återansluter...', och bryts"
            ],
            "losning_nyckelord": ["Videosamtal i Skype 7.40 på bärbar (Asus X550C) har svag WiFi-signal (1/5 streck, rött) och bryts i sovrum; starkare signal (5/5) i rum närmare WiFi-router (Technicolor TG799vac i vardagsrum)", "WiFi-signalen är för svag i sovrummet", "flytta datorn närmare WiFi-routern", "undvik fysiska hinder (väggar, möbler) mellan dator och router", "använd en WiFi-förstärkare/repeater"],
            "start_prompt": "När jag pratar med barnbarnen i det där video-programmet så bryts det hela tiden om jag går in i sovrummet. De säger att jag bara blir en massa fyrkanter."
        },
        {
            "id": "L2_P007",
            "beskrivning": """
                Jag skulle skriva ut ett brev till min väninna Agda på min skrivare, som är kopplad till datorn med en USB-sladd.
                Lampan på skrivaren lyser stadigt grönt, så den verkar ju vara på och må bra.
                Men inne i datorn, i Windows under 'Enheter och skrivare', så är ikonen för min skrivare alldeles gråtonad, och det står 'Frånkopplad' bredvid den.
                När jag försöker skriva ut så fastnar utskriftsjobbet bara i kön med status 'Fel'. Det kommer ingenting alls.
                Det är som att datorn och skrivaren inte pratar med varandra längre! Jag har provat att dra ur USB-sladden och sätta i den igen, och även testat en annan USB-port, men det hjälpte inte.
            """,
            "tekniska_fakta": [
                "Skrivare: HP DeskJet 2710e",
                "Anslutning: USB",
                "Symptom (Windows): Skrivarikonen i 'Enheter och skrivare' är grå och har status 'Frånkopplad'",
                "Symptom (Skrivarkö): Utskriftsjobb har status 'Fel - Skriver ut'",
                "Symptom (Skrivare): Strömlampan lyser stadigt grönt"
            ],
            "losning_nyckelord": ["Skrivare (HP DeskJet 2710e ansluten via USB) har stadig grön strömlampa men visas som 'Frånkopplad' i Windows 'Enheter och skrivare'; utskriftsjobb fastnar med status 'Fel - Skriver ut'", "skrivaren är inte korrekt ansluten eller känns inte igen av Windows", "starta om både dator och skrivare", "kontrollera USB-kabeln och prova att ta bort och lägga till skrivaren igen i Windows", "installera om skrivardrivrutinerna"],
            "start_prompt": "Min skrivare är alldeles grå inne i datorn, fast lampan på själva apparaten lyser så snällt grönt. Det är som att de inte pratar med varandra!"
        },
        {
            "id": "L2_P008",
            "beskrivning": """
                Jag satt och tittade på mina semesterbilder från förra året i mitt fotoprogram, särskilt en jättefin bild på Måns när han sover så sött.
                Plötsligt kom det upp en varning från mitt antivirusprogram. Den sa att filen med bilden på Måns har identifierats som misstänkt och har satts i karantän.
                Nu kan jag inte se bilden längre i fotoprogrammet, den är bara borta från albumet! Måns favoritbild!
                Men jag vet att den bilden är helt ofarlig, jag tog den ju själv med min egen kamera! Det måste vara programmet som har blivit tokigt. Vad menas med karantän, är min bild sjuk nu?
            """,
            "tekniska_fakta": [
                "Antivirusprogram: F-Secure SAFE",
                "Filnamn: Måns_sover_sött.jpg",
                "Filens plats: C:\\MinaBilder\\Semester_2023\\",
                "Varning från antivirus: 'Hot blockerat! Filen C:\\MinaBilder\\Semester_2023\\Måns_sover_sött.jpg har identifierats som misstänkt och har satts i karantän.'"
            ],
            "losning_nyckelord": ["Antivirusprogram ('F-Secure SAFE') visar varning 'Hot blockerat! Filen C:\\MinaBilder\\Semester_2023\\Måns_sover_sött.jpg har identifierats som misstänkt och har satts i karantän'; fotoprogram kan ej visa bilden", "antivirusprogrammet har felaktigt identifierat en ofarlig fil som ett hot (falskt positivt)", "lägg till ett undantag för filen eller mappen i F-Secure SAFE:s inställningar", "kontrollera F-Secure SAFE:s karantän och återställ filen därifrån om den är ofarlig"],
            "start_prompt": "Hjälp! Mitt skyddsprogram på datorn, det där F-Secure, har blivit helt tokigt! Det säger att en av mina bästa bilder på Måns när han sover så sött är farlig och nu kan jag inte se den längre! Men jag vet att den är snäll!"
        },
        {
            "id": "L2_P009",
            "beskrivning": """
                Jag ville lyssna på lite musik i mina fina hörlurar, för att inte störa Måns som låg och sov så sött i soffan. Jag kopplade in dem i det gröna ljuduttaget på framsidan av min stationära dator.
                Jag startade mitt musikprogram, men ljudet fortsatte att komma ur de stora högtalarna som är inbyggda i min datorskärm!
                Jag tittade i Windows Ljudinställningar under fliken Uppspelning. Där står det att högtalarna är standardenhet. Mina hörlurar finns med i listan, men de är inte valda som standard.
                Det är ju inte klokt, ljudet ska ju komma i lurarna när jag har dem i!
            """,
            "tekniska_fakta": [
                "Hörlurar: Philips SHP2000 (anslutna till 3.5mm-uttag)",
                "Musikprogram: Foobar2000",
                "Bildskärm med högtalare: Dell S2421H (ansluten med HDMI)",
                "Standard uppspelningsenhet i Windows: 'Högtalare (Realtek High Definition Audio)'",
                "Annan listad enhet: Hörlurar (ej standard)"
            ],
            "losning_nyckelord": ["Ljud från 'Foobar2000' spelas via datorns monitorhögtalare ('Dell S2421H' via HDMI) trots att hörlurar ('Philips SHP2000') är anslutna till grönt 3.5mm ljuduttag; Windows Ljudinställningar visar 'Högtalare (Realtek High Definition Audio)' som standardenhet, 'Hörlurar' listas men är inte standard", "hörlurarna är inte valda som standardljudenhet i Windows", "ändra standarduppspelningsenhet till hörlurarna i ljudinställningarna", "högerklicka på hörlurarna i ljudpanelen och välj 'Ange som standardenhet'"],
            "start_prompt": "Jag sätter i mina fina hörlurar för att inte störa Måns när han sover, men ljudet fortsätter ändå att komma ur de stora högtalarna! Det är ju inte klokt."
        },
        {
            "id": "L2_P010",
            "beskrivning": """
                Jag skulle logga in på min bank, och tog fram min lilla bankdosa.
                Men när jag skulle börja knappa in koden såg jag att det stod ett meddelande om lågt batteri på den lilla displayen. Och precis när jag höll på att mata in engångskoden så stängde den av sig!
                Nu kommer jag ju inte åt mina pengar till fikat! Jag vet att den använder ett sånt där platt, runt batteri, och det går att byta, för det har jag gjort förut för länge sen.
                Kan det vara så enkelt att batteriet är slut igen? Den har känts lite trög att starta på sistone också.
            """,
            "tekniska_fakta": [
                "Bank: Swedbank",
                "Bankdosa: Vasco Digipass 260",
                "Meddelande på display: 'LOW BATT'",
                "Symptom: Dosan stänger av sig under användning",
                "Batterityp: CR2032"
            ],
            "losning_nyckelord": ["Bankdosa ('Vasco Digipass 260', Swedbank) visar 'LOW BATT' på LCD-displayen och stängs av under inmatning av engångskod; använder CR2032-batteri", "batteriet i bankdosan är slut", "byt ut det gamla CR2032-batteriet i säkerhetsdosan mot ett nytt", "öppna batteriluckan och ersätt batteriet"],
            "start_prompt": "Min lilla bank-dosa blinkar något om 'LOW BATT' och stänger av sig mitt i när jag ska skriva in koden. Nu kommer jag väl inte åt mina pengar till fikat!"
        }
    ],
    # --- LEVEL 3 PROBLEMS (Index 2) ---
    [
        {
            "id": "L3_P001",
            "beskrivning": """
                Jag satt och skrev på mina memoarer om Måns när min dator plötsligt visade en hemsk blå skärm!
                Det stod något om 'MEMORY_MANAGEMENT' med en massa annan teknisk text och en stoppkod. Sen startade den om sig själv. Det här har hänt flera gånger de senaste dagarna, helt slumpmässigt.
                Jag har två minneskort i datorn. Min son sa att man kunde köra något som heter Windows Minnesdiagnostik, och jag provade det (standardtestet), men det visade inga fel direkt.
                Det är som att datorn har tappat minnet, stackarn. Jag är så rädd att allt jag skrivit ska försvinna.
            """,
            "tekniska_fakta": [
                "Dator: Dell OptiPlex 7010 SFF",
                "Fel på skärm: Blåskärm (BSOD)",
                "Stoppkod: MEMORY_MANAGEMENT",
                "Minne: 2x 2GB Kingston KVR13N9S6/2",
                "Diagnostik körd: Windows Minnesdiagnostik (standardtest) visade inga fel"
            ],
            "losning_nyckelord": ["Slumpmässig blåskärm (BSOD) med text 'Stoppkod: MEMORY_MANAGEMENT' på dator 'Dell OptiPlex 7010 SFF' med 2x2GB DDR3 RAM ('Kingston KVR13N9S6/2'); Windows Minnesdiagnostik (standardtest) visar inga fel", "problem med RAM-minnet (arbetsminnet)", "kör en grundligare minnesdiagnostik som MemTest86 från USB", "prova med en minnesmodul i taget i olika platser för att isolera felet", "kontrollera RAM-modulernas kompatibilitet"],
            "start_prompt": "Hemska apparat! Skärmen blir alldeles blå med ett ledset ansikte och en massa text om 'MEMORY', sen startar den om sig själv. Det är som att den har tappat minnet, stackarn."
        },
        {
            "id": "L3_P002",
            "beskrivning": """
                Barnbarnen var här och lämnade en film på en sån där konstig fil. Jag försöker titta på den i mitt vanliga filmprogram.
                Men när jag spelar upp filmen fylls bilden med gröna och rosa fyrkantiga fläckar och pixelfel, särskilt när det är snabba rörelser i filmen. Ljudet fortsätter dock att spelas upp normalt.
                Mitt grafikkort är från NVIDIA, och drivrutinen är ganska gammal, sa min son.
                Det ser ut som Måns har lekt med färgburkarna på skärmen! Det går ju inte att titta så här. Andra filmer jag har fungerar bra.
            """,
            "tekniska_fakta": [
                "Filtyp: .MKV",
                "Videocodec: H.264, 1080p",
                "Uppspelningsprogram: VLC Media Player 3.0.8",
                "Grafikkort: NVIDIA GeForce GT 710 2GB",
                "Drivrutinsversion: 391.35 (från 2018)"
            ],
            "losning_nyckelord": ["Uppspelning av '.MKV'-fil (H.264, 1080p) i VLC Media Player 3.0.8 ger gröna/rosa fyrkantiga artefakter och pixelfel; ljud normalt; Grafikkort NVIDIA GeForce GT 710 2GB, drivrutin 391.35 (2018)", "grafikkortets drivrutiner är föråldrade eller korrupta", "uppdatera grafikkortets drivrutiner till senaste stabila versionen från NVIDIA:s webbplats", "avinstallera gamla drivrutiner och installera nya rena drivrutiner"],
            "start_prompt": "När jag försöker titta på en film jag fått från barnbarnen så fylls hela skärmen av konstigt flimmer i alla möjliga färger, och bilden säger att den har hängt sig. Det ser ut som Måns har lekt med färgburkarna!"
        },
        {
            "id": "L3_P003",
            "beskrivning": """
                Jag skulle spara några nya bilder på Måns på mitt USB-minne. Men det gick inte!
                Jag kan titta på filerna som redan finns på minnet, men när jag försöker radera något gammalt eller spara något nytt så säger Windows att disken är skrivskyddad.
                Jag tittade närmare på minnesstickan, och den har en liten fysisk knapp på sidan med en låsikon. Just nu är den knappen i 'låst' läge. Kan det vara så enkelt?
                Jag har inte rört den där knappen med flit, Måns kanske kom åt den när han lekte på skrivbordet.
            """,
            "tekniska_fakta": [
                "Enhet: Kingston DataTraveler G4 8GB USB-minne",
                "Felmeddelande från Windows: 'Disken är skrivskyddad. Ta bort skrivskyddet eller använd en annan disk.'",
                "Fysisk egenskap: Enheten har en liten skrivskyddsbrytare på sidan, som för närvarande är i 'låst' läge."
            ],
            "losning_nyckelord": ["USB-minne ('Kingston DataTraveler G4 8GB') med fysisk skrivskyddsbrytare i 'låst' läge tillåter läsning men inte radering/formatering; Windows fel 'Disken är skrivskyddad'", "USB-minnets fysiska skrivskydd är aktiverat", "skjut den lilla låsknappen på minnesstickans sida till olåst läge", "inaktivera 'write-protect' reglaget på USB-enheten"],
            "start_prompt": "Min lilla minnes-sticka går bra att titta på, men jag kan inte kasta något skräp från den – den säger att den är 'skriv-skyddad'. Har den fått någon form av skyddsvakt?"
        },
        {
            "id": "L3_P004",
            "beskrivning": """
                Jag har en bärbar dator, och jag använder originalladdaren.
                Men nu visar batteriikonen i Windows aktivitetsfält att det är 0% och att den inte laddar, fastän den är ansluten. Den lilla laddningslampan bredvid strömintaget på datorn lyser inte heller.
                Datorn fungerar så länge laddaren är i, men om jag drar ur sladden så stängs den av direkt. Det är som att den vägrar äta sin ström!
                Jag har provat att ta ut och sätta i batteriet igen, och även vickat på laddarsladden.
            """,
            "tekniska_fakta": [
                "Bärbar dator: HP Pavilion G6-2250so",
                "Batteri: HP HSTNN-LB0W",
                "Laddare: HP 65W Smart AC Adapter (modell PPP009L-E)",
                "Status i Windows: '0% tillgängligt (nätansluten, laddar inte)'",
                "Symptom: Laddningslampan vid strömintaget lyser inte."
            ],
            "losning_nyckelord": ["Bärbar dator ('HP Pavilion G6-2250so' med 'HP HSTNN-LB0W' batteri) visar '0% tillgängligt (nätansluten, laddar inte)'; laddningslampa lyser ej; stängs av om laddare (HP 65W Smart AC Adapter PPP009L-E) dras ur", "laddaren eller batteriet är defekt, eller dålig anslutning", "prova en annan kompatibel HP-laddare", "kontrollera om batteriet är korrekt isatt och överväg att byta batteri", "rengör kontaktytor för batteri och laddare"],
            "start_prompt": "Batteri-symbolen på min bärbara dator säger 'ansluten men laddas inte' fastän sladden sitter där den ska. Det är som att den vägrar äta sin ström!"
        },
        {
            "id": "L3_P005",
            "beskrivning": """
                Jag försöker skicka e-post till min syster om Måns tokigheter med mitt vanliga program.
                Men programmet tjatar och frågar efter mitt nätverkslösenord om och om igen. Jag skriver in det, men rutan kommer tillbaka.
                Alla e-postmeddelanden jag försöker skicka fastnar i 'Utkorgen' med ett felmeddelande.
                Jag bytte faktiskt lösenord på Telias webbmail för några dagar sedan, för jag tyckte det var dags. Det nya lösenordet fungerar utmärkt där på webbmailen. Kan det ha med saken att göra?
            """,
            "tekniska_fakta": [
                "E-postprogram: Microsoft Outlook 2016",
                "E-postleverantör: Telia (konto: ulla.ulla@telia.com)",
                "Server: mailin.telia.com",
                "Symptom: Programmet frågar upprepade gånger efter lösenord",
                "Felkod i Utkorgen: 0x800CCC0F",
                "Nyligen utförd åtgärd: Lösenordet byttes på webbmailen"
            ],
            "losning_nyckelord": ["E-postprogram ('Microsoft Outlook 2016' ansluten till Telia IMAP-konto mailin.telia.com) frågar upprepade gånger efter nätverkslösenord; e-post i 'Utkorgen' har status 'Väntar på att skickas (fel 0x800CCC0F)'; lösenord nyligen ändrat på webbmail och fungerar där", "sparat lösenord i Outlook är felaktigt efter byte på webbmailen", "uppdatera det sparade lösenordet i Outlooks kontoinställningar", "gå till Arkiv > Kontoinställningar, välj kontot och ange det nya lösenordet"],
            "start_prompt": "Mitt mejl-program frågar efter lösenordet om och om igen, och inga av mina brev till syrran om Måns tokigheter går iväg. Det är så frustrerande!"
        },
        {
            "id": "L3_P006",
            "beskrivning": """
                När jag pratar med barnbarnen i det där videosamtalsprogrammet på min bärbara dator, så klagar de på att de hör sin egen röst som ett eko från min dator.
                Jag använder den inbyggda mikrofonen och högtalarna i datorn, inget headset. Jag har märkt att mikrofonsymbolen i programmet reagerar starkt även när bara de pratar, alltså på ljudet från mina högtalare.
                Det här händer även om jag sänker högtalarvolymen ganska mycket. Det låter som vi är i en stor kyrka!
            """,
            "tekniska_fakta": [
                "Videosamtalsprogram: Skype (version 8.96)",
                "Bärbar dator: Lenovo IdeaPad 3 15IIL05",
                "Ljudenheter: Inbyggd mikrofon och inbyggda högtalare (inget headset)",
                "Symptom: Motparter i samtalet hör ett eko av sin egen röst"
            ],
            "losning_nyckelord": ["Under videosamtal i Skype 8.96 på Lenovo IdeaPad 3 15IIL05 (inbyggd mikrofon/högtalare) rapporterar motparter tydligt eko av sin egen röst; mikrofon reagerar på ljud från datorns högtalare; inget headset används", "ljud från högtalarna plockas upp av mikrofonen (rundgång)", "använd ett headset (hörlurar med mikrofon) för att isolera ljudet", "sänk högtalarvolymen och mikrofonkänsligheten, eller använd Skypes ekoreducering om tillgängligt"],
            "start_prompt": "När jag pratar med barnbarnen på det där video-samtalet så hör alla sin egen röst som ett eko från min dator. Det låter som vi är i en stor kyrka!"
        },
        {
            "id": "L3_P007",
            "beskrivning": """
                Jag skriver ner mina memoarer om Måns i mitt skrivprogram. Men på sista tiden har programmet börjat frysa hela tiden, särskilt när jag jobbar med stora dokument eller när det där autosparandet sker.
                Hela fönstret visar '(Svarar inte)' och ibland kommer det ett meddelande om att den försöker återskapa information.
                Samtidigt har jag märkt att min datorlåda, eller snarare hårddisken inuti, ger ifrån sig konstiga klickande och höga arbetsljud, särskilt när programmet fryser.
                Min dotter installerade ett program för att kolla hårddisken, och det visar en 'Varning' för disken, något om 'Reallocated Sectors Count'. Tänk om allt försvinner!
            """,
            "tekniska_fakta": [
                "Skrivprogram: Microsoft Word 2013",
                "Hårddisk: Seagate Barracuda 1TB ST1000DM003",
                "Symptom (Program): Fryser och visar '(Svarar inte)'",
                "Symptom (Hårdvara): Hårddisken ger ifrån sig klickande ljud",
                "Diagnostikverktyg: CrystalDiskInfo visar 'Varning' med attributet 'Reallocated Sectors Count' markerat."
            ],
            "losning_nyckelord": ["Textredigeringsprogram ('Microsoft Word 2013') fryser ofta ('(Svarar inte)'); hårddisk ('Seagate Barracuda 1TB ST1000DM003') ger återkommande klickljud; CrystalDiskInfo visar 'Varning' (t.ex. 'Reallocated Sectors Count')", "hårddisken har problem eller är på väg att gå sönder", "kör en fullständig diskkontroll (chkdsk /f /r) på systemdisken", "säkerhetskopiera viktiga filer omedelbart och överväg att byta ut hårddisken"],
            "start_prompt": "Mitt skriv-program, där jag skriver ner mina memoarer om Måns, fryser hela tiden och visar 'återskapar fil' medan datorlådan knastrar och låter konstigt. Tänk om allt försvinner!"
        },
        {
            "id": "L3_P008",
            "beskrivning": """
                Jag försöker skriva ut mitt goda kakrecept på båda sidor av pappret för att spara papper.
                Jag använder Word och väljer dubbelsidig utskrift med standardinställningen. Men när pappret kommer ut så är texten på baksidan (andra sidan) alldeles uppochnedvänd i förhållande till framsidan!
                Hur ska någon kunna läsa det? Det ser ju heltokigt ut. Jag ser att det finns ett annat alternativ för att vända längs den korta kanten, men jag har inte vågat prova det än.
            """,
            "tekniska_fakta": [
                "Skrivare: Brother HL-L2350DW",
                "Inställning för dubbelsidig utskrift: 'Vänd längs långa kanten (standard)'",
                "Resultat: Texten på baksidan är uppochnedvänd"
            ],
            "losning_nyckelord": ["Vid dubbelsidig utskrift från Word till Brother HL-L2350DW med inställning 'Vänd längs långa kanten (standard)' blir texten på baksidan uppochnedvänd", "fel inställning för pappersvändning vid dubbelsidig utskrift", "välj 'vänd längs korta kanten' i utskriftsinställningarna för korrekt orientering på baksidan", "justera duplex-inställningen för 'short-edge binding'"],
            "start_prompt": "När jag försöker skriva ut mitt kakrecept på båda sidor av pappret så kommer texten på baksidan alldeles upp-och-ned! Hur ska någon kunna läsa det?"
        },
        {
            "id": "L3_P009",
            "beskrivning": """
                Jag har en liten surfplatta som jag brukar titta på Måns-videor på.
                Men nu har den blivit så envis! Bilden förblir i stående läge, även om jag vrider på plattan för att titta på en film i liggande format.
                Jag har tittat i den där snabbinställningspanelen som man drar ner från toppen, och där finns en ikon för 'Automatisk rotering'. Den ikonen är gråtonad och det står 'Porträtt' under den. Det betyder väl att den är avstängd?
                Jag har provat att trycka på ikonen, men det verkar inte hända något.
            """,
            "tekniska_fakta": [
                "Enhet: Samsung Galaxy Tab A7 Lite (SM-T220)",
                "Operativsystem: Android 11",
                "Symptom: Skärmen roterar inte till liggande läge",
                "Status i snabbinställningar: Ikonen för 'Automatisk rotering' är grå och visar texten 'Porträtt'"
            ],
            "losning_nyckelord": ["Surfplatta ('Samsung Galaxy Tab A7 Lite (SM-T220)' med Android 11) förblir i porträttläge trots fysisk rotation; ikon för 'Automatisk rotering' i snabbinställningspanelen är gråtonad och visar 'Porträtt'", "automatisk skärmrotation är avstängd i systeminställningarna", "tryck på ikonen för skärmrotation i snabbinställningspanelen för att aktivera den", "gå till Inställningar > Skärm > och slå på 'Automatisk rotering'"],
            "start_prompt": "Min lilla surfplatta, som jag tittar på Måns-videor på, vägrar att vrida på bilden när jag vänder på plattan. Den är envis som en gammal get!"
        },
        {
            "id": "L3_P010",
            "beskrivning": """
                Jag skulle logga in på min bank på datorn och behövde en engångskod som skickas via SMS till min telefon.
                Koden kom som den skulle, men när jag skrev in den på bankens webbplats så fick jag ett meddelande om att koden var ogiltig eller för gammal.
                Jag tittade på klockan på min telefon, och den visade en tid. Men klockan på min dator, som jag vet går rätt, visade en tid som var tre minuter tidigare.
                Jag har kollat i telefonens inställningar, och där är automatisk tid avstängd. Kan det vara det som spökar?
            """,
            "tekniska_fakta": [
                "Bank: Handelsbanken",
                "Telefon: Doro 8080 (Android Go)",
                "Felmeddelande från banken: 'Ogiltig kod. Koden kan vara för gammal eller redan använd.'",
                "Tidsskillnad: Telefonens klocka går 3 minuter före datorns klocka",
                "Telefoninställning: 'Använd nätverksbaserad tid' är avstängd"
            ],
            "losning_nyckelord": ["Engångskod via SMS till telefon ('Doro 8080') avvisas av bankens webbplats ('Handelsbanken') som 'Ogiltig kod... för gammal'; telefonens klocka skiljer sig från datorns; 'Använd nätverksbaserad tid' avstängd på telefonen", "telefonens klocka är osynkroniserad vilket gör SMS-koden ogiltig för tidskänsliga system", "slå på 'Automatisk datum och tid' (nätverksbaserad tid) i telefonens inställningar", "kontrollera att telefonens tid och tidszon är korrekta och synkroniserade"],
            "start_prompt": "Bank-koden som kommer i ett SMS till min telefon avvisas direkt som 'för gammal' när jag skriver in den på datorn. Det är som att de lever i olika tidsåldrar!"
        }
    ],
    # --- LEVEL 4 PROBLEMS (Index 3) ---
    [
        {
            "id": "L4_P001",
            "beskrivning": """
                Jag skulle starta min stationära dator för att betala räkningar.
                Men när jag tryckte på startknappen så började den bara pipa tre gånger, kort och ilsket. Strömlampan på datorn lyser grönt som den ska, men fönsterskärmen är helt svart. Det kommer ingen bild alls, inte ens den där första logotypen.
                Jag har två minneskort i datorn. Min son sa att tre pip ofta betyder problem med minnet på den här typen av datorer.
                Jag har provat att stänga av den helt och försöka igen, men det är samma sak varje gång.
            """,
            "tekniska_fakta": [
                "Dator: HP Compaq Elite 8300 SFF",
                "Minne: 2x Kingston KVR1333D3N9/2G (2GB DDR3)",
                "Symptom (Ljud): Tre korta pip vid startförsök",
                "Symptom (Bild): Ingen bild på skärmen (svart skärm)",
                "Symptom (Lampa): Strömlampan lyser grönt"
            ],
            "losning_nyckelord": ["Stationär dator ('HP Compaq Elite 8300 SFF') ger tre korta ljudsignaler (beep code) vid startförsök; skärmen förblir svart; strömlampa lyser grönt; RAM 2x 'Kingston KVR1333D3N9/2G'", "fel på RAM-minnet eller dålig kontakt med minnesmodulerna", "ta ut och sätt tillbaka minneskorten ordentligt (reseat)", "prova med en minnesmodul i taget i olika minnesplatser för att identifiera felaktig modul eller plats"],
            "start_prompt": "När jag trycker på startknappen på min stora datorlåda piper den bara tre gånger, kort och ilsket, och fönsterskärmen är helt svart. Den verkar ha fått hicka!"
        },
        {
            "id": "L4_P002",
            "beskrivning": """
                Jag skulle skriva ut ett fint kort till Måns födelsedag och hade precis satt i nya bläckpatroner i min skrivare.
                Men när jag försökte skriva ut kom pappren ut alldeles blanka, inte en enda prick färg!
                Jag tittade närmare på en av de nya färgpatronerna som jag hade kvar i förpackningen, och jag såg att det satt en liten orange skyddstejp med texten 'PULL' på ovansidan. Den tejpen täcker ett litet lufthål.
                Kan det vara så att jag har glömt att ta bort den tejpen på patronerna som sitter i skrivaren? Jag minns inte att jag drog bort någon tejp...
            """,
            "tekniska_fakta": [
                "Skrivare: Epson Stylus DX4400",
                "Nya patroner: Svart (T0711) och färg (T0712, T0713, T0714)",
                "Symptom: Utskrifter är helt blanka (ingen färg)",
                "Observation: Oanvänd patron har en orange skyddstejp märkt 'PULL' över ett lufthål"
            ],
            "losning_nyckelord": ["Nya bläckpatroner ('Epson T0711' svart, 'T0712/3/4' färg) installerade i 'Epson Stylus DX4400' matar fram blanka papper; orange skyddstejp ('PULL') observerad på ovansidan av ny patron täckande lufthål", "skyddstejp på bläckpatronerna blockerar bläcktillförseln eller ventilationen", "avlägsna all skyddstejp och plastremsor från nya bläckpatroner innan installation", "se till att lufthålen på patronerna är helt öppna"],
            "start_prompt": "Jag har satt i nya fina färgpatroner i skrivaren, men pappren kommer ut alldeles tomma, inte en prick! Det är som att färgen har rymt."
        },
        {
            "id": "L4_P003",
            "beskrivning": """
                Jag skulle ansluta min bärbara dator till mitt trådlösa nätverk för att läsa e-posten.
                Men istället för den vanliga WiFi-symbolen i aktivitetsfältet så visas det en liten flygplansikon. I Nätverksinställningar står det att flygplansläget är på.
                Jag har provat att trycka på Fn-tangenten tillsammans med F3-tangenten (där det är en flygplanssymbol), men det händer ingenting. Det finns ingen särskild WiFi-knapp på sidan av datorn heller.
                Nu kan jag inte ansluta till några trådlösa nätverk alls. Jag har startat om datorn, men flygplanet är kvar.
            """,
            "tekniska_fakta": [
                "Bärbar dator: Acer Aspire 5 A515-54G",
                "Operativsystem: Windows 10",
                "Symptom: Flygplansikon visas i aktivitetsfältet istället för WiFi-ikon",
                "Status i inställningar: 'Flygplansläge: På'",
                "Testad åtgärd: Fn+F3 (med flygplanssymbol) har ingen effekt"
            ],
            "losning_nyckelord": ["Bärbar dator ('Acer Aspire 5 A515-54G' med Windows 10) visar flygplansikon i aktivitetsfältet; Nätverksinställningar visar 'Flygplansläge: På'; Fn+F3 har ingen effekt; ingen WiFi-knapp på sidan", "flygplansläget är aktiverat i Windows och blockerar trådlösa anslutningar", "stäng av Flygplansläge via Nätverks- & Internetinställningar i Windows", "klicka på flygplansikonen i aktivitetsfältet och välj att stänga av läget därifrån"],
            "start_prompt": "Min bärbara dator har fått för sig att den är ett flygplan! Det har dykt upp en liten flygplansbild bredvid klockan, och nu ser jag inga trådlösa nät längre. Den kanske vill flyga söderut med Måns?"
        },
        {
            "id": "L4_P004",
            "beskrivning": """
                Jag har nyligen installerat om Windows på min dator från en sån där USB-sticka som min son gjorde åt mig. Allt verkar fungera, men det är en sak som stör mig.
                I nedre högra hörnet på skärmen visas en halvtransparent text, som en vattenstämpel. Den säger att jag ska gå till inställningar för att aktivera Windows.
                Jag angav ingen produktnyckel under installationen, och jag tror inte jag har någon digital licens kopplad till mitt Microsoft-konto.
                Vad menar den med att jag måste 'aktivera' systemet? Det ser lite oproffsigt ut med den där texten där hela tiden.
            """,
            "tekniska_fakta": [
                "Operativsystem: Windows 10 Home",
                "Symptom: En vattenstämpel visas på skärmen",
                "Text i vattenstämpeln: 'Aktivera Windows. Gå till Inställningar för att aktivera Windows.'",
                "Installationsinformation: Ingen produktnyckel angavs, ingen digital licens verkar vara kopplad till kontot"
            ],
            "losning_nyckelord": ["Halvtransparent text ('vattenstämpel') 'Aktivera Windows. Gå till Inställningar för att aktivera Windows.' visas på Windows 10 Home skärm efter ominstallation från generisk USB; produktnyckel ej angiven, ingen digital licens", "Windows-installationen är inte aktiverad med en giltig licens", "ange en giltig Windows 10 produktnyckel i Systeminställningar > Aktivering", "köp en Windows 10-licens eller använd en befintlig digital licens kopplad till ditt Microsoft-konto"],
            "start_prompt": "Det står en suddig text i hörnet på min fönsterskärm som säger att jag måste 'aktivera' systemet. Vad menar den med det? Ska jag klappa den lite?"
        },
        {
            "id": "L4_P005",
            "beskrivning": """
                Jag har en gammal stationär dator, och den har börjat bli alldeles virrig i tiden!
                Varje gång jag stänger av den helt, alltså drar ur strömsladden en stund, och sen startar den igen, så har klockan i Windows hoppat tillbaka till ett väldigt gammalt datum. Det händer också i den där BIOS-inställningen som kommer upp om man trycker på en knapp vid start.
                Det är ju väldigt opraktiskt, för då fungerar inte internet sidorna som de ska förrän jag ställt om klockan manuellt.
                Min son sa att det kunde vara ett litet batteri på moderkortet som har tagit slut.
            """,
            "tekniska_fakta": [
                "Dator: Fujitsu Siemens Scaleo P",
                "Moderkort: ASUS P5KPL-AM",
                "Batterityp på moderkortet: CR2032",
                "Symptom: Systemklockan (både i BIOS och Windows) återställs till 1 januari 2002, klockan 00:00, efter att datorn varit strömlös."
            ],
            "losning_nyckelord": ["Systemklocka i BIOS och Windows på stationär dator ('Fujitsu Siemens Scaleo P', moderkort 'ASUS P5KPL-AM') återställs till 01-01-2002 00:00 efter att datorn varit strömlös; moderkortet använder CR2032-batteri", "CMOS-batteriet på moderkortet är urladdat eller defekt", "byt ut det lilla runda batteriet (CR2032) på datorns moderkort", "sätt i ett nytt, fräscht BIOS-batteri"],
            "start_prompt": "Min dator har blivit alldeles virrig i tiden! Varje gång jag stänger av den helt så hoppar klockan tillbaka till år 2002. Den kanske längtar tillbaka till när Måns var kattunge."
        },
        {
            "id": "L4_P006",
            "beskrivning": """
                Jag försöker skriva ut några bilder på Måns på min bläckstråleskrivare.
                Men utskrifterna blir alldeles randiga! Det är tjocka, jämnt fördelade mörka horisontella ränder som delvis täcker texten och bilderna. Det ser inte klokt ut!
                Jag har provat att köra den där 'Djuprengöring av skrivhuvud' som finns i skrivarens programvara flera gånger, jag lät den till och med vila en stund emellan, men det blir ingen märkbar förbättring.
                Det är som om någon har ritat med en bred svart tuschpenna över alltihop. Patronerna är inte nya, men de är inte helt tomma heller, tror jag.
            """,
            "tekniska_fakta": [
                "Skrivare: Canon PIXMA MG3650",
                "Bläckpatroner: PG-540 (svart), CL-541 (färg)",
                "Symptom: Utskrifter har tjocka, jämna, mörka horisontella ränder",
                "Testad åtgärd: 'Djuprengöring av skrivhuvud' har körts flera gånger utan resultat"
            ],
            "losning_nyckelord": ["Bläckstråleskrivare ('Canon PIXMA MG3650' med PG-540/CL-541 patroner) producerar utskrifter med tjocka, jämnt fördelade mörka horisontella ränder; 'Djuprengöring av skrivhuvud' har körts utan förbättring", "skrivhuvudets munstycken är igentäppta och behöver rengöras", "kör skrivhuvudsrengöring (eventuellt flera gånger med paus emellan)", "om rengöring inte hjälper kan patronen eller skrivhuvudet vara defekt", "byt bläckpatroner"],
            "start_prompt": "Mina utskrifter från skrivaren får tjocka mörka ränder tvärs över texten, som om någon har ritat med en bred svart tuschpenna över alltihop. Det ser inte klokt ut!"
        },
        {
            "id": "L4_P007",
            "beskrivning": """
                Jag skulle spela min favoritmusik från Spotify på mitt högtalarsystem.
                Men ljudet kommer bara från den högra lilla högtalaren, den vänstra är helt tyst! Den stora baslådan fungerar dock, den brummar på som den ska.
                Jag tittade i Windows ljudinställningar, och där ser jag att ljudbalansen mellan höger och vänster kanal är helt fel. Den ena står på 100% och den andra på 0%.
                Jag har inte rört den där inställningen med flit! Det är som att den vänstra högtalaren har tagit semester.
            """,
            "tekniska_fakta": [
                "Högtalarsystem: Logitech Z313 2.1-system",
                "Symptom: Ljud endast från höger satellithögtalare och subwoofer; vänster satellit är tyst",
                "Inställning i Windows (Realtek HD Audio Manager): Ljudbalans är inställd på Höger 100%, Vänster 0%"
            ],
            "losning_nyckelord": ["Ljuduppspelning (från 'Spotify') via högtalarsystem ('Logitech Z313 2.1' anslutet till grönt ljuduttag) endast från höger satellithögtalare, vänster tyst, subwoofer fungerar; Windows ljudbalans visar Höger 100%, Vänster 0%", "ljudbalansen mellan höger och vänster kanal är felinställd", "justera ljudbalansen till mitten (50% för varje kanal) i ljudinställningarna", "centrera stereobalansen för uppspelningsenheten"],
            "start_prompt": "När jag spelar min favoritmusik så hörs den bara i den högra högtalaren – den vänstra är alldeles tyst! Det är som att den har tagit semester."
        },
        {
            "id": "L4_P008",
            "beskrivning": """
                Jag har en extern hårddisk där jag sparar alla mina bilder på Måns. Den ansluts med en enkel USB-kabel.
                Nu försökte jag koppla in den i en USB-port på min gamla dator för att visa bilderna för min syster. Men när jag ansluter den så börjar den avge ett repetitivt klickljud.
                Den syns kortvarigt i 'Den här datorn' och sen försvinner den igen. Det går inte att komma åt filerna.
                Min son sa att den här typen av disk kan kräva mer ström än vad en enskild gammal USB-port kan ge. På min nya dator fungerar den fint.
            """,
            "tekniska_fakta": [
                "Extern hårddisk: WD Elements 2TB Portable (Modell: WDBU6Y0020BBK)",
                "Anslutning: Enkel USB 3.0-kabel",
                "Problem-dator: Äldre dator med USB 2.0-portar",
                "Fungerande dator: Nyare dator med USB 3.0-portar",
                "Symptom vid anslutning till gammal dator: Repetitivt klickljud, enheten syns kort och försvinner"
            ],
            "losning_nyckelord": ["Extern hårddisk ('WD Elements 2TB Portable' med enkel USB 3.0 kabel) avger repetitivt klickljud vid anslutning till USB 2.0-port på äldre dator; syns kortvarigt och försvinner", "extern hårddisk får inte tillräckligt med ström från USB-porten", "använd en USB Y-kabel för att ansluta till två USB-portar för extra ström", "testa med en USB-hubb som har egen strömförsörjning", "anslut till en USB 3.0 port om möjligt"],
            "start_prompt": "Min yttre hårddisk, den där lilla lådan jag sparar bilder på Måns i, klickar och försvinner direkt när jag kopplar in den i den gamla datorn. Den kanske är hungrig?"
        },
        {
            "id": "L4_P009",
            "beskrivning": """
                Jag har kopplat min bärbara dator till min stora TV med en HDMI-kabel. Jag ville se på film på stor skärm.
                Bilden visas alldeles utmärkt på TV:n, men ljudet spelas fortfarande från datorns inbyggda högtalare! Det är ju inte meningen.
                Jag har tittat i Windows Ljudinställningar under fliken Uppspelning. Där visas datorns högtalare som standardenhet. Min TV finns med i listan, men den är antingen 'Inaktiverad' eller i alla fall inte vald som standard.
                Jag har provat att högerklicka på TV:n i listan, men jag är osäker på vad jag ska välja.
            """,
            "tekniska_fakta": [
                "Bärbar dator: Dell Inspiron 15 5559 med Intel HD Graphics 520",
                "TV: Samsung UE40H6400",
                "Anslutning: HDMI-kabel",
                "Symptom: Bild visas på TV, men ljud spelas från datorns högtalare",
                "Ljudinställningar: 'Högtalare (Realtek High Definition Audio)' är standard. TV:n ('Samsung TV (Intel(R) Display Audio)') listas men är inte standard."
            ],
            "losning_nyckelord": ["Bärbar dator ('Dell Inspiron 15 5559') ansluten till TV ('Samsung UE40H6400') via HDMI; bild visas på TV men ljud spelas från datorns högtalare; i Windows Ljudinställningar är 'Högtalare (Realtek High Definition Audio)' standard, 'Samsung TV (Intel(R) Display Audio)' listas men är inaktiverad/inte standard", "HDMI-ljudutgången är inte vald som standardenhet i Windows", "aktivera TV:n (HDMI) som ljudenhet och ställ in den som standard i ljudinställningarna", "högerklicka på HDMI-ljudenheten (Samsung TV) i ljudpanelen och välj 'Aktivera' och sedan 'Ange som standardenhet'"],
            "start_prompt": "Jag har kopplat min bärbara dator till den stora teven för att se på film, och jag får fin bild, men ljudet kommer fortfarande bara från den lilla datorn! Det är ju inte meningen."
        },
        {
            "id": "L4_P010",
            "beskrivning": """
                Jag har en iPad, och den har börjat tjata om att 'Lagringsutrymme nästan fullt'.
                Jag har gått in under lagringsinställningarna och där ser jag att en stor del av utrymmet upptas av 'Nyligen raderade' bilder. Detta trots att jag har raderat massor av gamla bilder och videor på Måns från Bilder-appen!
                Jag har tittat i Bilder-appen, och mycket riktigt, i ett album som heter 'Nyligen raderade' ligger alla de där bilderna kvar. Jag trodde de försvann direkt när man raderade dem.
            """,
            "tekniska_fakta": [
                "Enhet: iPad Air 2 (Modell A1566)",
                "Operativsystem: iOS 15",
                "Varning: 'Lagringsutrymme nästan fullt'",
                "Lagringsanalys: 10GB av lagringen upptas av 'Bilder > Nyligen raderade'",
                "Observation: Albumet 'Nyligen raderade' i Bilder-appen innehåller de raderade filerna."
            ],
            "losning_nyckelord": ["Surfplatta ('iPad Air 2', iOS 15) meddelar 'Lagringsutrymme nästan fullt'; 10GB upptas av 'Bilder > Nyligen raderade' trots att bilder raderats från Bilder-appen; albumet 'Nyligen raderade' innehåller objekten", "raderade bilder/videor ligger kvar i albumet 'Nyligen raderade' och tar upp plats", "gå in i Bilder-appen > Album > Nyligen raderade och välj 'Välj' sedan 'Radera alla' för att permanent ta bort objekten", "töm papperskorgen för bilder manuellt"],
            "start_prompt": "Min platta säger att lagringen är full fast jag har raderat massor av gamla bilder på Måns när han var liten. Var tar de vägen egentligen, de där raderade bilderna?"
        }
    ],
    # --- LEVEL 5 PROBLEMS (Index 4) ---
    [
        {
            "id": "L5_P001",
            "beskrivning": """
                Jag skulle just starta min dator för att titta på mina bilder på Måns.
                Men direkt efter den där första texten som alltid kommer upp, så blev skärmen svart och det stod med vit text att statusen var 'BAD' och att jag borde 'Backup and Replace'. Den sa att jag kunde trycka på F1 för att fortsätta.
                Jag tryckte på F1-knappen som den sa, och då startade Windows till slut, men datorn är märkbart långsam nu och ibland hänger den sig helt.
                Jag blir så orolig när det står 'BAD' och 'Replace'. Tänk om alla mina bilder och allt annat på datorn försvinner!
            """,
            "tekniska_fakta": [
                "Dator: Acer Veriton M2630G",
                "Hårddisk: Toshiba DT01ACA100 1TB",
                "Felmeddelande vid uppstart (POST): 'S.M.A.R.T. Status BAD, Backup and Replace. Press F1 to Resume.'",
                "Symptom efter F1: Windows startar men är långsamt och hänger sig"
            ],
            "losning_nyckelord": ["Vid uppstart av dator ('Acer Veriton M2630G' med 'Toshiba DT01ACA100 1TB' HDD), efter BIOS POST, visas svart skärm med text: 'S.M.A.R.T. Status BAD, Backup and Replace. Press F1 to Resume.'; Windows startar efter F1 men är långsamt/hänger sig", "hårddisken rapporterar kritiska S.M.A.R.T.-fel och är på väg att gå sönder", "säkerhetskopiera alla viktiga data omedelbart och byt ut den felande hårddisken", "installera en ny hårddisk och återställ systemet från backup eller nyinstallation"],
            "start_prompt": "Min stackars dator varnar för att 'Hårddisken mår dåligt – byt snarast!' redan innan den hunnit starta ordentligt. Den ber mig trycka F1 för att fortsätta, men det känns inte bra alls. Tänk om alla mina bilder på Måns försvinner!"
        },
        {
            "id": "L5_P002",
            "beskrivning": """
                Jag skulle starta min fina nya bärbara dator. Den har något som heter BitLocker-diskkryptering aktiverat, sa min son.
                Men nu när jag startar den visar den en blå skärm där det står att jag måste ange en återställningsnyckel för att fortsätta. Det visas också ett långt Nyckel-ID.
                Jag har ingen aning om var jag har en sådan återställningsnyckel! Jag minns inte att jag har sparat någon, och min son säger att den inte finns på mitt Microsoft-konto.
                Hjälp! Nu kommer jag inte in i datorn alls!
            """,
            "tekniska_fakta": [
                "Bärbar dator: Microsoft Surface Laptop 3",
                "Operativsystem: Windows 10 Pro med BitLocker aktiverat",
                "Skärm vid uppstart: Blå BitLocker-återställningsskärm",
                "Meddelande: 'BitLocker-återställning. Ange återställningsnyckeln för den här enheten för att fortsätta.'",
                "Visad information: Ett Nyckel-ID (t.ex. XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX)"
            ],
            "losning_nyckelord": ["Bärbar dator ('Microsoft Surface Laptop 3' med Windows 10 Pro och BitLocker) visar blå skärm vid start: 'BitLocker-återställning. Ange återställningsnyckeln... Nyckel-ID: XXXXXXXX...'; användaren har inte sparat nyckeln, finns ej på Microsoft-konto", "BitLocker-diskkryptering kräver återställningsnyckel efter systemändring eller misstänkt manipulation", "leta efter en utskriven BitLocker-återställningsnyckel eller en som sparats på USB-minne vid installationen", "om nyckeln är förlorad kan data vara oåtkomliga utan ominstallation"],
            "start_prompt": "Hjälp! Min fina nya bärbara dator har fått fnatt! Den visar en blå skärm och ber mig skriva in en jättelång 'återställningskod' innan Windows vill öppnas. Jag har ingen aning om var jag har en sådan kod!"
        },
        {
            "id": "L5_P003",
            "beskrivning": """
                Jag försökte starta min gamla trotjänare till dator.
                Efter den där första texten som kommer upp, så blir skärmen bara svart och det står att 'NTLDR is missing' och att jag ska starta om. Jag har provat det, men samma meddelande kommer igen.
                Jag kollade i BIOS-inställningarna, och där är CD-ROM-läsaren satt som första startenhet, och hårddisken som andra. Det har alltid varit så.
                Jag tänkte att jag kunde försöka starta från min gamla Windows installations-CD, men det verkar inte som att datorn ens försöker läsa från CD:n.
            """,
            "tekniska_fakta": [
                "Operativsystem: Windows XP Professional",
                "BIOS: Phoenix AwardBIOS v6.00PG",
                "Hårddisk: Maxtor DiamondMax Plus 9 80GB ATA/133",
                "Felmeddelande: 'NTLDR is missing. Press Ctrl+Alt+Del to restart.'",
                "BIOS Boot Order: 1. CD-ROM, 2. Hard Disk"
            ],
            "losning_nyckelord": ["Äldre dator (Windows XP Pro, Phoenix AwardBIOS v6.00PG) visar svart skärm med text: 'NTLDR is missing. Press Ctrl+Alt+Del to restart'; CD-ROM är första startenhet i BIOS, HDD ('Maxtor DiamondMax Plus 9 80GB ATA/133') andra; start från XP installations-CD misslyckas (CD läses ej)", "felaktig startenhetsordning (boot order) i BIOS eller problem med startfilerna på hårddisken", "gå in i BIOS-inställningarna och ställ in hårddisken (HDD) som första startenhet", "kontrollera att hårddisken detekteras korrekt i BIOS och försök reparera startsektorn med XP-CD (om CD-läsaren fungerar)", "kontrollera IDE/SATA-kabeln till hårddisken"],
            "start_prompt": "Min gamla trotjänare till dator säger bara 'NTLDR saknas' och vägrar gå vidare från en svart skärm. Det låter som en viktig del har sprungit bort. Kanske Måns har gömt den?"
        },
        {
            "id": "L5_P004",
            "beskrivning": """
                Det var ett kort strömavbrott här hemma. Efter det försökte jag starta min stationära dator.
                Datorn startar på så sätt att fläktarna börjar snurra på maxhastighet och LED-lamporna på moderkortet lyser, men fönsterskärmen får ingen signal alls, den är helt svart.
                Jag såg att det finns en liten display på moderkortet, och den visar en kod. Min son sa att den koden ofta kan indikera CPU-problem eller att BIOS har blivit korrupt.
                Jag har provat att göra en CMOS-reset med den där lilla jumpern på moderkortet som sonen visade mig, men det gjorde ingen skillnad.
            """,
            "tekniska_fakta": [
                "Moderkort: Gigabyte GA-Z97X-Gaming 5",
                "CPU: Intel Core i7-4790K",
                "Utlösande händelse: Kort strömavbrott",
                "Symptom: Fläktar snurrar på max, moderkorts-LEDs lyser, men ingen bildsignal till skärmen",
                "Debug LED-kod: Visar '00'"
            ],
            "losning_nyckelord": ["Stationär dator (moderkort 'Gigabyte GA-Z97X-Gaming 5', CPU 'Intel Core i7-4790K') startar efter strömavbrott (fläktar max, moderkorts-LEDs lyser) men skärmen får ingen signal ('No Input'); Debug LED på moderkort visar '00'; CMOS-reset via jumper utan effekt", "BIOS/CMOS-inställningarna är korrupta eller moderkortet har problem efter strömavbrott", "utför en grundlig CMOS-återställning genom att ta ur moderkortsbatteriet en stund medan datorn är strömlös", "kontrollera alla anslutningar på moderkortet och testa med minimal konfiguration (endast CPU, ett RAM, grafikkort)", "testa med annat nätaggregat"],
            "start_prompt": "Efter ett litet strömavbrott här hemma så snurrar fläktarna i datorn som tokiga, men fönsterskärmen tänds aldrig. Den är helt svart och säger 'Ingen signal'. Det är som att den har blivit rädd för mörkret."
        },
        {
            "id": "L5_P005",
            "beskrivning": """
                Jag skulle skriva ut mina dikter om Måns. Jag har nyligen anslutit min skrivare till datorn med en USB-kabel.
                Men när jag skriver ut så blir sidorna fyllda med helt obegripliga tecken och symboler! Det ser ut som en massa krafs.
                Windows använde automatiskt någon sorts standarddrivrutin när jag anslöt skrivaren. Jag minns att skrivaren fungerade alldeles utmärkt på min gamla dator, och då hade jag installerat tillverkarens egna, modellanpassade drivrutiner.
                Det ser ut som katten själv har varit framme och skrivit på pappret!
            """,
            "tekniska_fakta": [
                "Program: WordPad i Windows 10",
                "Skrivare: HP LaserJet P1102w (ansluten via USB)",
                "Drivrutin som används av Windows: 'Microsoft IPP Class Driver'",
                "Symptom: Utskrifter innehåller obegripliga tecken och symboler (t.ex. 'ÿØÿà€JFIF€€Æ @#$!%^&*')"
            ],
            "losning_nyckelord": ["Utskrift från WordPad (Windows 10) till HP LaserJet P1102w (nyligen USB-ansluten) resulterar i sidor fyllda med obegripliga tecken/symboler; Windows använde 'Microsoft IPP Class Driver'", "felaktig eller generisk skrivardrivrutin används av Windows", "ladda ner och installera den officiella, modellanpassade skrivardrivrutinen från HP:s webbplats för LaserJet P1102w", "avinstallera den nuvarande drivrutinen och installera rätt PCL- eller PostScript-drivrutin"],
            "start_prompt": "När jag försöker skriva ut mina dikter om Måns så blir all text på pappret bara en massa obegripliga krumelurer och konstiga tecken. Det ser ut som katten själv har varit framme och skrivit!"
        },
        {
            "id": "L5_P006",
            "beskrivning": """
                Min son hjälpte mig att installera om Windows på en gammal dator. Allt verkar fungera, men jag kan inte komma åt några säkra webbplatser som google.com eller microsoft.com.
                När jag använder webbläsaren står det bara att den inte kan visa webbsidan eller så kommer det upp ett fel om certifikat.
                Systemtiden och datumet på datorn är helt korrekta. Windows Update fungerar inte heller, det säger att den inte kan söka efter nya uppdateringar och ger en felkod.
                Min son nämnde något om att det kunde bero på saknade rotcertifikat och stöd för säkerhetsprotokoll.
            """,
            "tekniska_fakta": [
                "Operativsystem: Windows 7 Ultimate (32-bitars, utan Service Pack)",
                "Webbläsare: Internet Explorer 8",
                "Felmeddelande (webbläsare): 'Internet Explorer kan inte visa webbsidan' eller certifikatfel 'DLG_FLAGS_INVALID_CA / INET_E_SECURITY_PROBLEM'",
                "Felmeddelande (Windows Update): Kan inte söka, felkod 80072EFE",
                "Systemtid: Korrekt"
            ],
            "losning_nyckelord": ["Nyinstallerad Windows 7 Ultimate (utan SP, 32-bit) kan ej öppna HTTPS-webbplatser (IE8 visar 'kan inte visa webbsida' eller certifikatfel 'DLG_FLAGS_INVALID_CA / INET_E_SECURITY_PROBLEM'); Windows Update fungerar ej (felkod 80072EFE); systemtid/datum korrekt", "operativsystemet saknar uppdaterade rotcertifikat och modernt TLS/SSL-stöd", "installera Windows 7 Service Pack 1 och alla efterföljande kumulativa uppdateringar manuellt (t.ex. via Microsoft Update Catalog)", "importera aktuella rotcertifikat och aktivera TLS 1.2 stöd via registerändringar eller Microsoft Easy Fix"],
            "start_prompt": "Inga säkra sidor på internet vill öppnas på min nyinstallerade dator – allt bara klagar på ogiltiga 'certifikat' fast datumet på datorn stämmer. Det är som att alla dörrar är låsta!"
        },
        {
            "id": "L5_P007",
            "beskrivning": """
                Jag har en dator med ganska mycket minne och ledigt utrymme på hårddisken.
                Men när jag använder webbläsaren och har många flikar öppna samtidigt som jag försöker redigera bilder på Måns, så kommer det ofta upp ett meddelande från Windows om att datorn har ont om minne och att jag ska stänga program.
                Ofta kraschar programmen strax efteråt. Jag har tittat på den där växlingsfilen, och den är systemhanterad och verkar ganska liten.
                Vad menar den med virtuellt minne, är det låtsasminne?
            """,
            "tekniska_fakta": [
                "RAM: 8GB (Corsair Vengeance LPX DDR4 2400MHz)",
                "Hårddisk: SSD, Samsung 860 EVO 250GB (med ca 50GB ledigt)",
                "Program som körs: Google Chrome (många flikar), Adobe Photoshop Elements 2021",
                "Windows-meddelande: 'Datorn har ont om minne. Spara dina filer och stäng dessa program.'",
                "Växlingsfil (pagefile.sys): Systemhanterad, observerad storlek ca 2GB"
            ],
            "losning_nyckelord": ["System med 8GB RAM, 50GB ledigt på C: (SSD), Windows-meddelande 'Datorn har ont om minne' vid användning av Chrome (många flikar) och Photoshop Elements; program kraschar; växlingsfil (pagefile.sys) systemhanterad, liten (t.ex. 2GB)", "systemets växlingsfil (virtuellt minne) är för liten för den aktuella arbetsbelastningen", "öka storleken på växlingsfilen manuellt i Windows systeminställningar (t.ex. till 1.5x RAM eller systemhanterad med större initialstorlek)", "överväg att utöka det fysiska RAM-minnet om problemet kvarstår frekvent"],
            "start_prompt": "Min dator gnäller om att den har för lite 'virtuellt minne' och stänger ner mina program när jag försöker redigera bilder på Måns och ha många internetsidor öppna samtidigt. Vad menar den med virtuellt, är det låtsasminne?"
        },
        {
            "id": "L5_P008",
            "beskrivning": """
                Jag har köpt ett nytt fint USB-headset för att kunna prata med barnbarnen utan att störa Måns.
                Ljudet i själva hörlurarna fungerar alldeles utmärkt. Men när jag tittar i Ljudinställningarna under fliken 'Inspelning', så listas bara min gamla inbyggda mikrofon och något som heter 'Stereomix'.
                Jag ser ingen mikrofon från mitt nya headset där, trots att headsetet visas korrekt i Enhetshanteraren utan några fel. Jag har också sett till att 'Visa inaktiverade enheter' är markerat.
                Det är ju tråkigt, för nu hör de inte mig! Jag har kollat så att mikrofonen inte är avstängd med knappen på sladden.
            """,
            "tekniska_fakta": [
                "Headset: Logitech H390 (USB)",
                "Operativsystem: Windows 10",
                "Symptom: Ljudet i hörlurarna fungerar, men mikrofonen fungerar inte.",
                "Ljudinställningar (Inspelning): Listar endast 'Mikrofon (Realtek High Definition Audio)' och 'Stereomix'. Headsetets mikrofon saknas.",
                "Enhetshanteraren: Visar headsetet korrekt under 'Ljud-, video- och spelenheter' utan fel."
            ],
            "losning_nyckelord": ["Nytt USB-headset ('Logitech H390') ljud i hörlurar fungerar i Windows 10, men mikrofonen listas ej under 'Ljud > Inspelning'; headset visas i Enhetshanteraren utan fel; 'Visa inaktiverade enheter' markerat", "headsetets mikrofon är inte aktiverad eller vald som standardinspelningsenhet, eller har sekretessproblem", "kontrollera att mikrofonen på headsetet inte är fysiskt avstängd (mute-knapp)", "gå till Enhetshanteraren, avinstallera headsetet och låt Windows installera om det; välj sedan som standard i Ljudinställningar", "kontrollera mikrofonens sekretessinställningar i Windows 10"],
            "start_prompt": "Jag har köpt en ny fin hörlur med mikrofon för att kunna prata med barnbarnen, men mikrofonen syns inte i listan i datorn! Ljudet i lurarna fungerar, men de hör inte mig. Det är ju tråkigt."
        },
        {
            "id": "L5_P009",
            "beskrivning": """
                Jag brukar titta på roliga kattklipp på YouTube och ibland på SVT Play i min webbläsare.
                Men nu när jag försöker spela upp videor så hör jag bara ljudet – bildrutan är helt grå eller svart! Det gäller både på YouTube och SVT Play, och även i andra webbläsare har jag märkt.
                Problemet uppstod ganska nyligen, jag tror det var efter en Windows-uppdatering. Mitt grafikkort är från Intel och drivrutinen är några år gammal.
                Jag har kollat att maskinvaruacceleration i webbläsaren är aktiverad, det brukar den vara.
                Det är ju det roligaste som försvinner när bilden är borta!
            """,
            "tekniska_fakta": [
                "Webbläsare: Mozilla Firefox 91 ESR",
                "Operativsystem: Windows 10 (version 21H2)",
                "Utlösande händelse (trolig): Windows-uppdatering (KB500XXXX)",
                "Grafikkort: Intel HD Graphics 4000 (drivrutin från 2017)",
                "Symptom: Videouppspelning på webbplatser (YouTube, SVT Play) ger endast ljud; bildrutan är svart eller grå."
            ],
            "losning_nyckelord": ["Videouppspelning ('YouTube HTML5 player', 'SVT Play') i Firefox 91 ESR på Windows 10 (21H2) visar endast ljud, bildrutan grå/svart; problem uppstod efter Windows-uppdatering (KB500XXXX); grafikkort Intel HD Graphics 4000 (drivrutin 2017); maskinvaruacceleration i Firefox aktiverad; problem i andra webbläsare också", "problem med videokodekar eller grafikdrivrutiner efter systemuppdatering", "installera ett omfattande kodekpaket (t.ex. K-Lite Codec Pack Full)", "försök att inaktivera/aktivera maskinvaruacceleration i webbläsarens inställningar eller systemets grafikinställningar; sök efter nyare (eller äldre stabila) grafikdrivrutiner"],
            "start_prompt": "När jag försöker titta på roliga kattklipp på internet så hör jag bara ljudet – bilden är alldeles grå! Det är ju det roligaste som försvinner. Måns blir också besviken."
        },
        {
            "id": "L5_P010",
            "beskrivning": """
                Jag skulle starta min stationära dator för att sortera mina bilder.
                Men när jag tryckte på startknappen så pep den konstigt: ett långt pip och sedan två korta pip. Min son sa att det på den här sortens datorer ofta indikerar problem med grafikkortet.
                Mycket riktigt, fönsterskärmen förblir alldeles svart, den säger att den inte får någon signal. Fläktarna på grafikkortet snurrar dock som de ska.
                Kortet sitter i den översta stora porten och de där extra strömkablarna är anslutna till det.
                Jag har provat att starta om flera gånger, men det är samma ledsna fågel-pip varje gång.
            """,
            "tekniska_fakta": [
                "Moderkort: ASUS P8P67 LE (med AMI BIOS)",
                "CPU: Intel Core i5-2500K",
                "Grafikkort: NVIDIA GeForce GTX 560 Ti",
                "Symptom (Ljud): Ett långt och två korta pip vid start (beep code)",
                "Symptom (Bild): Ingen signal till skärmen (ansluten via DVI)",
                "Symptom (Hårdvara): Grafikkortets fläktar snurrar"
            ],
            "losning_nyckelord": ["Stationär dator (moderkort 'ASUS P8P67 LE', CPU 'Intel Core i5-2500K', grafikkort 'NVIDIA GeForce GTX 560 Ti') avger en lång och två korta ljudsignaler (AMI BIOS beep code) vid start; skärmen svart (ingen signal via DVI); grafikkortsfläktar snurrar; kort i översta PCIe x16, extra ström ansluten", "grafikkortet har dålig kontakt, är felaktigt anslutet eller defekt", "ta ur och sätt tillbaka grafikkortet ordentligt i PCIe-porten (reseat)", "kontrollera att alla extra strömanslutningar till grafikkortet sitter fast; testa med ett annat grafikkort om möjligt", "testa med en annan bildskärmskabel eller bildskärmsport"],
            "start_prompt": "Min dator startar med ett långt pip och sedan två korta, som en ledsen fågel, och fönsterskärmen förblir alldeles svart. Den vill nog inte vakna idag."
        }
    ]
]

# Helper to get the number of levels
NUM_LEVELS = len(PROBLEM_CATALOGUES)