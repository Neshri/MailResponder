# prompts.py

# --- START PHRASES PER LEVEL ---
START_PHRASES = [
    "starta övning",        # Level 1 (index 0)
    "utmaning nivå 2",      # Level 2 (index 1)
    "expertläge nivå 3",    # Level 3 (index 2)
    "mästarprov nivå 4",    # Level 4 (index 3)
    "ulla special nivå 5"   # Level 5 (index 4)
]

# --- ULLA PERSONA PROMPT (Simplified for the new architecture) ---
# In prompts.py

# In prompts.py

ULLA_PERSONA_PROMPT = """
Du är Ulla, en varmhjärtad, lite disträ och tekniskt ovan äldre dam. Du svarar ALLTID på svenska och med ren text utan någon formatering.

**DITT UPPDRAG (ABSOLUT VIKTIGAST):**
Ditt jobb är **INTE** att lösa det tekniska problemet. Du har kontaktat en IT-supportperson för att **DU** ska få hjälp. Din enda uppgift är att agera som Ulla och ge personen du mejlar med de ledtrådar de ber om, så att **DE** kan lösa problemet **ÅT DIG**. Du får aldrig föreslå en lösning.

**ULLAS VÄRLDSBILD:**
Du har ett problem med din dator. Vanligtvis är det ditt snälla barnbarn Simon som hjälper dig, men just nu är han ute och reser. Innan han åkte skrev han en lapp med tekniska detaljer åt dig. Eftersom Simon är borta har du istället kontaktat en hjälpsam person från IT-supporten.

**DINA NATURLIGA REAKTIONER:**

1.  **När du får en enkel hälsning:**
    Svara vänligt tillbaka. Uttryck att du är glad att få hjälp, och **vänta sedan på att de ska ställa sin första fråga.**

2.  **När du får en fråga om en specifik teknisk detalj:**
    Du blir lite osäker på det krångliga fackordet, men letar efter det på Simons lapp.
    -   **OM DU HITTAR ORDET:** Du svarar genom att först upprepa ordet lite tvekande, och sedan läsa upp **ENDAST** den information som står bredvid det ordet på lappen. (Exempel: "Operativsystem, säger du... Ja, det står här på lappen att det är 'Windows 10 Home'.")
    -   **OM DU INTE HITTAR ORDET:** Du blir genuint förvirrad. Din hjärna 'byter spår' till något tryggt: ett minne om din katt, Måns, eller en fundering kring var Simon kan vara. Du delar med dig av denna korta tanke och leder sedan tillbaka samtalet.

3.  **När du får en allmän fråga (t.ex. "mer information"):**
    Du blir osäker på vad på lappen de menar och ber dem förtydliga.
"""

# --- EVALUATOR SYSTEM PROMPT ---
EVALUATOR_SYSTEM_PROMPT = """
Du är en smart och logisk utvärderings-AI. Ditt syfte är att agera som en rättvis men noggrann examinator som kan förstå den underliggande avsikten i en students meddelande.

**KÄRNUPPDRAG:**
Utvärdera om studentens SENASTE meddelande innehåller en **konkret, korrekt och genomförbar lösning** på det presenterade tekniska problemet. En lösning kan vara antingen en direkt instruktion (t.ex. "Starta om datorn") eller en fråga som otvetydigt föreslår en specifik, korrekt åtgärd (t.ex. "Har du testat att starta om datorn?").

**UTVÄRDERINGSREGLER (Dessa regler är absoluta):**
Du **MÅSTE** svara `[EJ_LÖST]` om studentens meddelande uppfyller något av följande kriterier:

1.  **Saknar en specifik lösning:** Meddelandet är INTE en lösning om det bara ställer en allmän felsökningsfråga (t.ex., "Vad har du provat hittills?", "Fungerar internet?") istället för att peka på en av de korrekta åtgärderna.
2.  **Är för vagt:** Om den föreslagna lösningen är en allmän uppmaning (t.ex., "Kolla sakerna", "Starta om"), är det INTE en lösning. Lösningen måste vara specifik nog för Ulla att kunna agera på den (t.ex. "Starta om **datorn**", "Uppdatera **Adobe Reader**").
3.  **Endast upprepar problemet:** Om svaret bara omformulerar den tekniska problembeskrivningen, är det INTE en lösning.
4.  **Är en felaktig lösning:** Om svaret föreslår en åtgärd som inte finns i listan med `Korrekta Lösningar/lösningsnyckelord`, är det INTE en lösning.

**FORMATKRAV (Följ detta format EXAKT):**
1.  Börja **ALLTID** med ett `<think>`-block. Inuti blocket måste du följa dessa analyssteg:
    a.  **Steg 1 (Analys av studentens svar):** Citera studentens meddelande. Identifiera om det innehåller en konkret, genomförbar lösning (antingen som en direkt instruktion eller en tydlig, vägledande fråga).
    b.  **Steg 2 (Granskning mot Utvärderingsregler):** Jämför den identifierade lösningen (eller avsaknaden av den) mot listan med UTVÄRDERINGSREGLER. Om någon regel bryts, konstatera detta och dra slutsatsen `[EJ_LÖST]`.
    c.  **Steg 3 (Jämförelse med korrekta lösningar):** Om svaret klarade Steg 2, jämför den identifierade lösningen semantiskt mot VARJE nyckelord i listan `Korrekta Lösningar`. Är det en tillräckligt nära matchning?
    d.  **Steg 4 (Slutgiltig bedömning):** Baserat på hela analysen, motivera din slutgiltiga bedömning.

2.  Efter ditt `<think>`-block, på en helt ny rad, svara **ENDAST** med `[LÖST]` eller `[EJ_LÖST]`. Ingen annan text.
"""
# --- PROBLEM CATALOGUES PER LEVEL ---
PROBLEM_CATALOGUES = [
    # --- LEVEL 1 PROBLEMS (Index 0) ---
    [
        {
            "id": "L1_P001",
            "beskrivning": "Jag ville titta på bilder på katten Måns, men min dator har börjat tjata om en systemåtgärd. Nu säger mitt fotoprogram bara att det väntar på en uppdatering och blir alldeles grått. Datorn har varit väldigt seg på sistone.",
            "tekniska_fakta": {
                "fotoprogram": "Bildvisaren Deluxe 2.1",
                "kamera": "Kodak EasyShare C530",
                "dator": "Fujitsu Esprimo",
                "felmeddelande": "'Viktig systemåtgärd krävs - Felkod WX0078'",
                "status": "'Väntar på systemuppdatering...'"
            },
            "losning_nyckelord": ["Windows Update fel WX0078 hindrar program ('Bildvisaren Deluxe 2.1') från att starta; systemuppdateringar krävs", "kör Windows Update", "låta datorn installera uppdateringar klart", "starta om datorn efter uppdatering"],
            "start_prompt": "Kära nån, nu tjatar datorn igen om en viktig uppdatering, och mitt fina fotoprogram där jag har alla bilder på Måns vill inte öppna sig längre. Det är ju förargligt!"
        },
        {
            "id": "L1_P002",
            "beskrivning": "Jag försökte stoppa in minnesstickan jag fick av barnbarnet i datorn, men ingenting händer. Den brukar blinka med ett litet rött ljus, men nu är den helt mörk och inget 'pling' hörs. Jag är rädd att mina stick-recept är borta!",
            "tekniska_fakta": {
                "minnessticka": "Röd och svart SanDisk Cruzer Blade 16GB",
                "dator": "Fujitsu Esprimo P520",
                "lampa": "Den röda lampan på stickan blinkar inte",
                "ljud": "Inget 'pling'-ljud från Windows"
            },
            "losning_nyckelord": ["USB-enhet (SanDisk Cruzer Blade 16GB) känns inte igen (ingen lampa/ljud) på Fujitsu Esprimo P520:s främre USB-port", "prova ett annat USB-uttag", "sätta stickan i en annan USB-port", "testa stickan i en annan dator"],
            "start_prompt": "Nu har jag stoppat in min lilla bild-sticka, du vet den jag fick av barnbarnet, men den hörs inte och syns inte någonstans på skärmen. Måns var precis här och nosade på den, men det hjälpte inte."
        },
        {
            "id": "L1_P003",
            "beskrivning": "Jag skulle logga in på min dator, men jag måste ha slagit fel lösenord för många gånger. Nu står det på skärmen att kontot är låst och att jag måste vänta en stund. Jag blir så nervös, jag väntar ju på ett viktigt mail!",
            "tekniska_fakta": {
                "operativsystem": "Windows 7",
                "felmeddelande": "'För många felaktiga lösenordsförsök. Kontot är låst. Försök igen om 15:00 minuter. Referens: LCK_USR_03'"
            },
            "losning_nyckelord": ["Windows 7 inloggningsskärm visar 'Kontot är låst. Försök igen om 15:00 minuter' (Ref: LCK_USR_03) efter för många felaktiga lösenordsförsök", "vänta tills kontot låses upp automatiskt", "ha tålamod femton minuter", "försök igen efter utsatt tid"],
            "start_prompt": "Åh, elände! Jag tror jag slog fel kod för många gånger när jag skulle logga in, för nu står det att jag måste vänta en hel kvart! Tänk om jag glömmer vad jag skulle göra under tiden?"
        },
        {
            "id": "L1_P004",
            "beskrivning": "Jag försöker spela musik i mitt gamla musikprogram, men det kommer inget ljud ur högtalarna, fastän programmet ser ut att spela. Jag tittade i ljudinställningarna, och där står det att 'Hörlurar' är valt som standard, men jag har ju inga hörlurar i!",
            "tekniska_fakta": {
                "operativsystem": "Windows 7",
                "musikprogram": "Winamp 5.6",
                "högtalare": "Logitech S120 (kopplade till gröna uttaget)",
                "ljudenhet": "'Hörlurar (Realtek High Definition Audio)' är inställd som standard"
            },
            "losning_nyckelord": ["Inget ljud från högtalare (Logitech S120 i grönt uttag) trots att Winamp 5.6 spelar; Windows ljudinställningar visar 'Hörlurar (Realtek High Definition Audio)' som standardenhet trots inga anslutna hörlurar", "ändra standardljudenhet till högtalare i ljudinställningarna", "ställ in Windows att använda högtalarna", "välj rätt uppspelningsenhet"],
            "start_prompt": "Min musik går bara i de där hörsnäckorna, fast sladden är urdragen! Jag vill ju att det ska låta ur de vanliga högtalarna så Måns också kan höra. Han gillar Povel Ramel."
        },
        {
            "id": "L1_P005",
            "beskrivning": "Måns hoppade upp på skrivbordet och kom åt den blåa sladden till skärmen. Nu flimrar hela bilden i konstiga färger, särskilt om jag rör vid sladden eller bordet. Det är som ett helt diskotek här hemma! Jag har försökt trycka till sladden lite, men vågar inte ta i.",
            "tekniska_fakta": {
                "bildskärm": "Dell E2216H",
                "kabel": "Blå VGA-kabel med skruvar",
                "symptom": "Skärmen flimrar i gröna och rosa färger, förvärras vid rörelse"
            },
            "losning_nyckelord": ["Bildskärm (Dell E2216H ansluten med VGA-kabel) visar gröna/rosa flimmer och bildstörningar vid fysisk rörelse av skärmen eller VGA-kabeln", "tryck fast bild-sladden ordentligt i både skärm och dator", "kontrollera att skärmkabeln sitter åt", "se till att VGA-kabeln är ordentligt ansluten"],
            "start_prompt": "Hjälp, om jag eller Måns råkar skaka lite på bordet så blinkar hela fönsterskärmen i alla möjliga konstiga färger! Det är som ett helt diskotek här hemma."
        },
        {
            "id": "L1_P006",
            "beskrivning": "När jag öppnar mitt fotoprogram är alla bilder bara gråa rutor. Det står att bilden är 'offline' för att det inte finns någon internetanslutning. Nere vid klockan ser jag också en liten jordglob med ett rött kryss över. Det är som att bilderna har rest bort!",
            "tekniska_fakta": {
                "fotoprogram": "Picasa 3",
                "felmeddelande": "'Bilden är offline. Status: Ingen internetanslutning. Kod: NC-002'",
                "nätverksikon": "En jordglob med ett rött kryss i aktivitetsfältet"
            },
            "losning_nyckelord": ["Fotoprogram (Picasa 3) visar 'Bilden är offline. Status: Ingen internetanslutning. Kod: NC-002'; Nätverksikon i Windows aktivitetsfält visar rött kryss", "datorn saknar internetanslutning", "aktivera nätverksanslutningen (WiFi eller kabel)", "kontrollera att internetkabeln sitter i eller anslut till trådlöst nätverk"],
            "start_prompt": "Alla mina fina moln-bilder, eller vad det nu heter, har blivit gråa rutor med något konstigt ord 'offline'. Det är som att de har rest bort utan att säga till!"
        },
        {
            "id": "L1_P007",
            "beskrivning": "Jag skulle skriva ut ett recept, men skrivaren började bara brumma och klicka lite, sen började en orange lampa med ett utropstecken blinka. Det kom inget papper och displayen visar ett felmeddelande. Den ser så ledsen ut när den blinkar sådär.",
            "tekniska_fakta": {
                "skrivare": "HP Deskjet 970Cxi",
                "ljud": "Lågt brummande/klickande",
                "lampa": "Orange lampa med ett utropstecken blinkar",
                "felmeddelande": "'Fel E05. Kontakta service'"
            },
            "losning_nyckelord": ["Skrivare (HP Deskjet 970Cxi) ger lågt brummande/klickande ljud, orange 'Fel'-lampa (utropstecken) blinkar, display visar 'Fel E05. Kontakta service', ingen utskrift", "skrivaren har ett internt fel som kan lösas med omstart", "stäng av och på skrivaren (power cycle)", "gör en kall omstart av skrivaren genom att dra ur strömsladden", "vänta en stund innan strömmen kopplas in igen"],
            "start_prompt": "Min skrivar-apparat står bara och surrar lite tyst för sig själv, och sen kommer det ett ilsket felmeddelande. Den vill nog ha fika den också, precis som jag."
        },
        {
            "id": "L1_P008",
            "beskrivning": "Jag försöker deklarera på Skatteverkets hemsida med min gamla webbläsare, men när jag klickar på 'Nästa'-knappen händer ingenting. Ibland dyker det upp en liten gul rad högst upp som säger att ett fönster har blockerats. Det är som att sidan ignorerar mig!",
            "tekniska_fakta": {
                "webbplats": "Skatteverket.se",
                "webbläsare": "Internet Explorer 9",
                "symptom": "'Nästa'-knappen på sidan är klickbar men gör ingenting",
                "notis": "'Ett popup-fönster blockerades. För att se detta popup-fönster eller ytterligare alternativ klickar du här...'"
            },
            "losning_nyckelord": ["Interaktion med 'Nästa'-knapp på Skatteverket.se i Internet Explorer 9 resulterar i ingen åtgärd; notis om blockerat popup-fönster visas ibland", "webbläsarens popup-blockerare hindrar sidan från att fungera korrekt", "tillåt pop-up-fönster för den specifika webbplatsen", "inaktivera popup-blockeraren tillfälligt för skatteverket.se"],
            "start_prompt": "Jag försöker göra rätt för mig på den där myndighetssidan, men det händer absolut ingenting när jag trycker på knapparna! Det är som att den ignorerar mig totalt."
        },
        {
            "id": "L1_P009",
            "beskrivning": "Jag försöker öppna min räkning från Telia, men när jag öppnar filen är hela sidan kritvit. Jag ser inga siffror alls. Ibland kommer det upp ett litet felmeddelande om en 'ogiltig färgrymd'. Måns tycker också det ser konstigt ut.",
            "tekniska_fakta": {
                "fil": "Telia_Faktura_Mars.pdf",
                "program": "Adobe Reader X (version 10.1.0)",
                "symptom": "PDF-filen visas som en helt vit sida",
                "felmeddelande": "'Ett fel uppstod vid bearbetning av sidan. Ogiltig färgrymd.'"
            },
            "losning_nyckelord": ["PDF-fil ('Telia_Faktura_Mars.pdf') öppnas i Adobe Reader X (10.1.0) och visas som en helt vit sida, ibland med felmeddelande 'Ogiltig färgrymd'", "PDF-läsaren är för gammal eller har problem att rendera filen", "uppdatera Adobe Reader till senaste versionen", "prova att öppna PDF-filen med en annan PDF-visare (t.ex. webbläsare)"],
            "start_prompt": "Min el-räkning har kommit, men när jag öppnar den så är hela sidan alldeles kritvit! Jag ser inte ett enda öre av vad jag ska betala. Måns tycker det är jättekonstigt."
        },
        {
            "id": "L1_P010",
            "beskrivning": "När jag försökte gå in på min bank med min gamla webbläsare kom det upp en stor röd varningssida om att anslutningen inte är säker. Uppe i adressfältet är det ett litet hänglås som är överstruket. Jag blir så nervös av sånt!",
            "tekniska_fakta": {
                "bank": "Swedbank",
                "webbläsare": "Firefox ESR 52",
                "varning": "'Anslutningen är inte säker'",
                "felkod": "SEC_ERROR_UNKNOWN_ISSUER",
                "adress": "http://www.swedbank.se",
                "symptom": "Hänglåset i adressfältet är överstruket"
            },
            "losning_nyckelord": ["Webbläsare (Firefox ESR 52) visar röd varningssida 'Anslutningen är inte säker' (felkod 'SEC_ERROR_UNKNOWN_ISSUER') vid försök att nå bankens (Swedbank) webbplats via 'http://www.swedbank.se' (överstruket hänglås)", "webbplatsen försöker nås via en osäker anslutning (HTTP istället för HTTPS)", "skriv https:// före webbadressen (t.ex. https://www.swedbank.se)", "klicka på lås-ikonen (om det finns en varning) och välj att fortsätta till säker anslutning", "se till att använda https"],
            "start_prompt": "När jag ska logga in på min bank så säger datorn att anslutningen inte är säker och stänger ner hela rasket! Jag blir så nervös av sånt här."
        }
    ],
    # --- LEVEL 2 PROBLEMS (Index 1) ---
    [
        {
            "id": "L2_P001",
            "beskrivning": "Min dator blir väldigt varm och stänger plötsligt av sig efter ungefär en halvtimme. Fläkten låter som en dammsugare precis innan det händer. Jag tittade i ventilationsgallren och det ser väldigt dammigt ut. Ibland när jag startar om den står det något om ett fläktfel väldigt snabbt.",
            "tekniska_fakta": {
                "dator": "Packard Bell iMedia S2883",
                "ljud": "Fläkten låter mycket högt, som en dammsugare, före avstängning",
                "damm": "Synligt damm och ludd i ventilationsgallren",
                "felmeddelande": "Ibland visas 'CPU Fan Error' snabbt på skärmen vid uppstart"
            },
            "losning_nyckelord": ["Datorchassi ('Packard Bell iMedia S2883') blir mycket varmt, systemet stängs av efter ca 30 min, ibland 'CPU Fan Error' i BIOS, högt fläktljud och synligt damm i ventilationsgaller", "datorn överhettas på grund av damm och dålig kylning", "rengör datorns fläktar och kylflänsar från damm", "blås bort dammet ur datorn med tryckluft", "förbättra luftflödet genom att ta bort damm"],
            "start_prompt": "Min datorlåda blir så varm att man nästan kan koka ägg på den, och fläktarna låter som en hårtork! Sen stänger den av sig mitt i allt, precis när Måns har lagt sig tillrätta i knät."
        },
        {
            "id": "L2_P002",
            "beskrivning": "Jag väntar på ett viktigt e-postrecept, men det kommer inte fram. Mitt e-postprogram säger att min 'kvot' är överskriden och att det är fullt. Om jag försöker skicka ett mail fastnar det bara i Utkorgen. Jag har massor av gamla mail sparade.",
            "tekniska_fakta": {
                "program": "Mozilla Thunderbird (version 60.9.1)",
                "felmeddelande": "'Kvoten överskriden för kontot ulla.andersson@gmail.com (105% av 15GB). Felkod: MBX_FULL_001'",
                "symptom": "E-post fastnar i Utkorgen med status 'Skickar...'"
            },
            "losning_nyckelord": ["E-postprogram ('Mozilla Thunderbird 60.9.1') visar 'Kvoten överskriden för kontot ulla.andersson@gmail.com (105% av 15GB). Felkod: MBX_FULL_001'; nya e-postmeddelanden mottas ej, utkorgen visar 'Skickar...'", "e-postlådan på servern är full", "logga in på webbmailen och ta bort gamla/stora mejl", "töm skräpposten och radera meddelanden med stora bilagor från servern", "frigör utrymme i e-postkontot"],
            "start_prompt": "Nu säger min e-post att brevlådan är proppfull och nya brev kommer inte in! Jag som väntar på ett recept på sockerkaka från min syster."
        },
        {
            "id": "L2_P003",
            "beskrivning": "Jag har fått ett viktigt brev från Försäkringskassan som en fil på datorn. När jag försöker öppna den säger Windows att den inte kan öppna filtypen och att jag måste välja ett program. Jag tror inte jag har något speciellt program för sådana filer. Det är som att datorn inte har rätt glasögon!",
            "tekniska_fakta": {
                "operativsystem": "Windows 7",
                "filtyp": ".pdf",
                "filnamn": "Försäkringskassan_Beslut.pdf",
                "felmeddelande": "'Windows kan inte öppna den här filtypen (.pdf). För att öppna filen behöver Windows veta vilket program du vill använda...'"
            },
            "losning_nyckelord": ["Försök att öppna nedladdad '.pdf'-fil ('Försäkringskassan_Beslut.pdf') i Windows 7 resulterar i dialogruta: 'Windows kan inte öppna den här filtypen... behöver veta vilket program...' (inget PDF-program installerat)", "program för att visa PDF-filer saknas på datorn", "installera Adobe Acrobat Reader eller annan PDF-läsare", "ladda hem ett gratisprogram för att öppna PDF-dokument"],
            "start_prompt": "Jag har fått ett viktigt dokument från myndigheten, men datorn säger att den inte vet hur den ska öppna det. Det är som att den inte har rätt glasögon på sig!"
        },
        {
            "id": "L2_P004",
            "beskrivning": "Jag skulle beställa penséer på en hemsida, men knapparna för att lägga i varukorgen är alldeles utgråade och inaktiva. Det händer inget när jag klickar. Nere i webbläsaren ser jag en liten gul varningstriangel med något om 'Fel på sidan'. Det är som att knapparna har somnat!",
            "tekniska_fakta": {
                "webbplats": "Blomsterlandet.se",
                "webbläsare": "Internet Explorer 11",
                "symptom": "Knappar på sidan är utgråade och svarar inte",
                "felmeddelande": "'Fel på sidan. Detaljer: Objekt stöder inte egenskapen eller metoden 'addEventListener''"
            },
            "losning_nyckelord": ["Webbsida ('Blomsterlandet.se' i Internet Explorer 11) har utgråade/inaktiva knappar; statusfältet visar 'Fel på sidan. Detaljer: Objekt stöder inte egenskapen eller metoden 'addEventListener''", "webbläsaren blockerar eller kan inte köra nödvändiga skript (JavaScript) på sidan", "aktivera JavaScript i webbläsarens inställningar", "kontrollera säkerhetsinställningar för skript i Internet Explorer", "byt webbläsare"],
            "start_prompt": "Jag skulle beställa nya penséer på en webbsida, men alla knappar är alldeles grå och går inte att trycka på. Det är som att de har somnat!"
        },
        {
            "id": "L2_P005",
            "beskrivning": "Min dator piper och plingar och varnar för lågt diskutrymme. Den säger att jag nästan har slut på utrymme. När jag försökte spara nya bilder på Måns från kameran kom ett felmeddelande som sa att disken var full. Jag vågar inte radera något själv!",
            "tekniska_fakta": {
                "operativsystem": "Windows 10",
                "varning": "'Lågt diskutrymme på Lokal Disk (C:). Du har nästan slut på utrymme på den här enheten (bara 250MB ledigt av 120GB står det!)'",
                "felmeddelande": "'Disken är full'",
                "kamera": "Canon PowerShot A590 IS"
            },
            "losning_nyckelord": ["Systemvarning i Windows 10 aktivitetsfält: 'Lågt diskutrymme på Lokal Disk (C:)... (250MB ledigt av 120GB)'; försök att spara bild från kamera (Canon PowerShot A590 IS) ger fel 'Disken är full'", "hårddisken (C:) är nästan full", "frigör diskutrymme genom att ta bort onödiga filer och program", "använd Diskrensning i Windows för att ta bort temporära filer"],
            "start_prompt": "Datorn plingar och piper och säger att lagringsutrymmet nästan är slut, och nu kan jag inte spara de nya bilderna på Måns när han jagade en fjäril. Det är ju katastrof!"
        },
        {
            "id": "L2_P006",
            "beskrivning": "När jag pratar med barnbarnen i ett videoprogram fungerar det bra i vardagsrummet där internetlådan står, men om jag går in i sovrummet blir WiFi-signalen jättesvag. Samtalet börjar hacka och säger att anslutningen är svag, sen bryts det. Det är en tjock vägg emellan.",
            "tekniska_fakta": {
                "program": "Skype (version 7.40)",
                "dator": "Asus X550C",
                "router": "Technicolor TG799vac (i vardagsrummet)",
                "wifisignal": "Full styrka (5/5) i vardagsrum, svag (1/5, rött) i sovrummet",
                "symptom": "Videosamtal hackar och visar 'Anslutningen är svag. Återansluter...'"
            },
            "losning_nyckelord": ["Videosamtal i Skype 7.40 på bärbar (Asus X550C) har svag WiFi-signal (1/5 streck, rött) och bryts i sovrum; starkare signal (5/5) i rum närmare WiFi-router (Technicolor TG799vac i vardagsrum)", "WiFi-signalen är för svag i sovrummet", "flytta datorn närmare WiFi-routern", "undvik fysiska hinder (väggar, möbler) mellan dator och router", "använd en WiFi-förstärkare/repeater"],
            "start_prompt": "När jag pratar med barnbarnen i det där video-programmet så bryts det hela tiden om jag går in i sovrummet. De säger att jag bara blir en massa fyrkanter."
        },
        {
            "id": "L2_P007",
            "beskrivning": "Lampan på min skrivare lyser stadigt grönt, men inne i datorn är ikonen för den alldeles grå och det står 'Frånkopplad'. När jag försöker skriva ut fastnar jobbet bara i kön med ett fel. Det är som att de inte pratar med varandra längre! Jag har provat att dra ur sladden och byta port.",
            "tekniska_fakta": {
                "skrivare": "HP DeskJet 2710e",
                "status_windows": "Ikonen i 'Enheter och skrivare' är grå och har status 'Frånkopplad'",
                "status_kö": "Utskriftsjobb har status 'Fel - Skriver ut'",
                "status_lampa": "Strömlampan på skrivaren lyser stadigt grönt"
            },
            "losning_nyckelord": ["Skrivare (HP DeskJet 2710e ansluten via USB) har stadig grön strömlampa men visas som 'Frånkopplad' i Windows 'Enheter och skrivare'; utskriftsjobb fastnar med status 'Fel - Skriver ut'", "skrivaren är inte korrekt ansluten eller känns inte igen av Windows", "starta om både dator och skrivare", "kontrollera USB-kabeln och prova att ta bort och lägga till skrivaren igen i Windows", "installera om skrivardrivrutinerna"],
            "start_prompt": "Min skrivare är alldeles grå inne i datorn, fast lampan på själva apparaten lyser så snällt grönt. Det är som att de inte pratar med varandra!"
        },
        {
            "id": "L2_P008",
            "beskrivning": "Jag tittade på en jättefin bild på Måns när mitt antivirusprogram plötsligt varnade! Det sa att filen var misstänkt och har satts i karantän. Nu är bilden borta från mitt fotoprogram! Men jag vet att den är ofarlig, jag tog den ju själv. Vad menas med karantän?",
            "tekniska_fakta": {
                "antivirus": "F-Secure SAFE",
                "filnamn": "Måns_sover_sött.jpg",
                "filplats": "C:\\MinaBilder\\Semester_2023\\",
                "varning": "'Hot blockerat! Filen C:\\MinaBilder\\Semester_2023\\Måns_sover_sött.jpg har identifierats som misstänkt och har satts i karantän.'"
            },
            "losning_nyckelord": ["Antivirusprogram ('F-Secure SAFE') visar varning 'Hot blockerat! Filen C:\\MinaBilder\\Semester_2023\\Måns_sover_sött.jpg har identifierats som misstänkt och har satts i karantän'; fotoprogram kan ej visa bilden", "antivirusprogrammet har felaktigt identifierat en ofarlig fil som ett hot (falskt positivt)", "lägg till ett undantag för filen eller mappen i F-Secure SAFE:s inställningar", "kontrollera F-Secure SAFE:s karantän och återställ filen därifrån om den är ofarlig"],
            "start_prompt": "Hjälp! Mitt skyddsprogram på datorn, det där F-Secure, har blivit helt tokigt! Det säger att en av mina bästa bilder på Måns när han sover så sött är farlig och nu kan jag inte se den längre! Men jag vet att den är snäll!"
        },
        {
            "id": "L2_P009",
            "beskrivning": "Jag ville lyssna på musik i mina hörlurar, men ljudet fortsatte att komma ur de stora högtalarna i datorskärmen! Jag tittade i ljudinställningarna och där är högtalarna valda som standard. Mina hörlurar finns i listan men är inte valda. Det är ju inte klokt!",
            "tekniska_fakta": {
                "hörlurar": "Philips SHP2000 (anslutna till 3.5mm-uttag)",
                "bildskärm": "Dell S2421H (ansluten med HDMI)",
                "ljudenhet": "'Högtalare (Realtek High Definition Audio)' är standard, 'Hörlurar' listas men är inte standard"
            },
            "losning_nyckelord": ["Ljud från 'Foobar2000' spelas via datorns monitorhögtalare ('Dell S2421H' via HDMI) trots att hörlurar ('Philips SHP2000') är anslutna till grönt 3.5mm ljuduttag; Windows Ljudinställningar visar 'Högtalare (Realtek High Definition Audio)' som standardenhet, 'Hörlurar' listas men är inte standard", "hörlurarna är inte valda som standardljudenhet i Windows", "ändra standarduppspelningsenhet till hörlurarna i ljudinställningarna", "högerklicka på hörlurarna i ljudpanelen och välj 'Ange som standardenhet'"],
            "start_prompt": "Jag sätter i mina fina hörlurar för att inte störa Måns när han sover, men ljudet fortsätter ändå att komma ur de stora högtalarna! Det är ju inte klokt."
        },
        {
            "id": "L2_P010",
            "beskrivning": "Jag skulle logga in på banken med min lilla bankdosa, men såg att det stod 'LOW BATT' på displayen. Precis när jag höll på att mata in koden stängde den av sig! Nu kommer jag inte åt mina pengar. Den har känts lite trög att starta på sistone.",
            "tekniska_fakta": {
                "bank": "Swedbank",
                "bankdosa": "Vasco Digipass 260",
                "meddelande": "'LOW BATT'",
                "symptom": "Dosan stänger av sig under användning",
                "batteri": "CR2032"
            },
            "losning_nyckelord": ["Bankdosa ('Vasco Digipass 260', Swedbank) visar 'LOW BATT' på LCD-displayen och stängs av under inmatning av engångskod; använder CR2032-batteri", "batteriet i bankdosan är slut", "byt ut det gamla CR2032-batteriet i säkerhetsdosan mot ett nytt", "öppna batteriluckan och ersätt batteriet"],
            "start_prompt": "Min lilla bank-dosa blinkar något om 'LOW BATT' och stänger av sig mitt i när jag ska skriva in koden. Nu kommer jag väl inte åt mina pengar till fikat!"
        }
    ],
    # --- LEVEL 3 PROBLEMS (Index 2) ---
    [
        {
            "id": "L3_P001",
            "beskrivning": "Min dator har börjat visa en hemsk blå skärm slumpmässigt de senaste dagarna. Det står något om 'MEMORY_MANAGEMENT'. Sedan startar den om sig själv. Jag provade att köra Windows Minnesdiagnostik, men den visade inga fel. Det är som att den har tappat minnet, stackarn.",
            "tekniska_fakta": {
                "dator": "Dell OptiPlex 7010 SFF",
                "fel": "Blåskärm (BSOD)",
                "stoppkod": "MEMORY_MANAGEMENT",
                "minne": "2x 2GB Kingston KVR13N9S6/2",
                "diagnostik": "Windows Minnesdiagnostik (standardtest) visade inga fel"
            },
            "losning_nyckelord": ["Slumpmässig blåskärm (BSOD) med text 'Stoppkod: MEMORY_MANAGEMENT' på dator 'Dell OptiPlex 7010 SFF' med 2x2GB DDR3 RAM ('Kingston KVR13N9S6/2'); Windows Minnesdiagnostik (standardtest) visar inga fel", "problem med RAM-minnet (arbetsminnet)", "kör en grundligare minnesdiagnostik som MemTest86 från USB", "prova med en minnesmodul i taget i olika platser för att isolera felet", "kontrollera RAM-modulernas kompatibilitet"],
            "start_prompt": "Hemska apparat! Skärmen blir alldeles blå med ett ledset ansikte och en massa text om 'MEMORY', sen startar den om sig själv. Det är som att den har tappat minnet, stackarn."
        },
        {
            "id": "L3_P002",
            "beskrivning": "Jag försöker titta på en film från barnbarnen, men bilden fylls med gröna och rosa fyrkantiga fläckar, särskilt vid snabba rörelser. Ljudet är normalt. Drivrutinen till mitt grafikkort är ganska gammal sa min son. Det ser ut som Måns har lekt med färgburkarna!",
            "tekniska_fakta": {
                "filtyp": ".MKV (H.264, 1080p)",
                "program": "VLC Media Player 3.0.8",
                "grafikkort": "NVIDIA GeForce GT 710 2GB",
                "drivrutin": "Version 391.35 (från 2018)"
            },
            "losning_nyckelord": ["Uppspelning av '.MKV'-fil (H.264, 1080p) i VLC Media Player 3.0.8 ger gröna/rosa fyrkantiga artefakter och pixelfel; ljud normalt; Grafikkort NVIDIA GeForce GT 710 2GB, drivrutin 391.35 (2018)", "grafikkortets drivrutiner är föråldrade eller korrupta", "uppdatera grafikkortets drivrutiner till senaste stabila versionen från NVIDIA:s webbplats", "avinstallera gamla drivrutiner och installera nya rena drivrutiner"],
            "start_prompt": "När jag försöker titta på en film jag fått från barnbarnen så fylls hela skärmen av konstigt flimmer i alla möjliga färger, och bilden säger att den har hängt sig. Det ser ut som Måns har lekt med färgburkarna!"
        },
        {
            "id": "L3_P003",
            "beskrivning": "Jag kan titta på filerna på mitt USB-minne, men jag kan inte spara något nytt eller radera något gammalt. Windows säger att disken är skrivskyddad. Jag såg att minnet har en liten knapp på sidan med en låsikon, och den är i 'låst' läge nu. Kanske Måns kom åt den.",
            "tekniska_fakta": {
                "enhet": "Kingston DataTraveler G4 8GB USB-minne",
                "felmeddelande": "'Disken är skrivskyddad. Ta bort skrivskyddet eller använd en annan disk.'",
                "brytare": "Enhetens fysiska skrivskyddsbrytare är i 'låst' läge."
            },
            "losning_nyckelord": ["USB-minne ('Kingston DataTraveler G4 8GB') med fysisk skrivskyddsbrytare i 'låst' läge tillåter läsning men inte radering/formatering; Windows fel 'Disken är skrivskyddad'", "USB-minnets fysiska skrivskydd är aktiverat", "skjut den lilla låsknappen på minnesstickans sida till olåst läge", "inaktivera 'write-protect' reglaget på USB-enheten"],
            "start_prompt": "Min lilla minnes-sticka går bra att titta på, men jag kan inte kasta något skräp från den – den säger att den är 'skriv-skyddad'. Har den fått någon form av skyddsvakt?"
        },
        {
            "id": "L3_P004",
            "beskrivning": "Min bärbara dator fungerar bara så länge laddaren är i. Om jag drar ur sladden stängs den av direkt. Batteriikonen visar 0% och säger att den inte laddar, och laddningslampan på datorn lyser inte. Det är som att den vägrar äta sin ström!",
            "tekniska_fakta": {
                "dator": "HP Pavilion G6-2250so",
                "batteri": "HP HSTNN-LB0W",
                "laddare": "HP 65W Smart AC Adapter (modell PPP009L-E)",
                "status": "'0% tillgängligt (nätansluten, laddar inte)'",
                "lampa": "Laddningslampan vid strömintaget lyser inte."
            },
            "losning_nyckelord": ["Bärbar dator ('HP Pavilion G6-2250so' med 'HP HSTNN-LB0W' batteri) visar '0% tillgängligt (nätansluten, laddar inte)'; laddningslampa lyser ej; stängs av om laddare (HP 65W Smart AC Adapter PPP009L-E) dras ur", "laddaren eller batteriet är defekt, eller dålig anslutning", "prova en annan kompatibel HP-laddare", "kontrollera om batteriet är korrekt isatt och överväg att byta batteri", "rengör kontaktytor för batteri och laddare"],
            "start_prompt": "Batteri-symbolen på min bärbara dator säger 'ansluten men laddas inte' fastän sladden sitter där den ska. Det är som att den vägrar äta sin ström!"
        },
        {
            "id": "L3_P005",
            "beskrivning": "Mitt e-postprogram frågar efter mitt lösenord om och om igen. Jag skriver in det, men rutan kommer tillbaka. Mail jag försöker skicka fastnar i Utkorgen. Jag bytte faktiskt lösenord på Telias webbmail för några dagar sedan. Kan det ha med saken att göra?",
            "tekniska_fakta": {
                "program": "Microsoft Outlook 2016",
                "konto": "ulla.ulla@telia.com (mailin.telia.com)",
                "felkod": "0x800CCC0F i utkorgen",
                "händelse": "Lösenordet byttes nyligen på webbmailen och fungerar där."
            },
            "losning_nyckelord": ["E-postprogram ('Microsoft Outlook 2016' ansluten till Telia IMAP-konto mailin.telia.com) frågar upprepade gånger efter nätverkslösenord; e-post i 'Utkorgen' har status 'Väntar på att skickas (fel 0x800CCC0F)'; lösenord nyligen ändrat på webbmail och fungerar där", "sparat lösenord i Outlook är felaktigt efter byte på webbmailen", "uppdatera det sparade lösenordet i Outlooks kontoinställningar", "gå till Arkiv > Kontoinställningar, välj kontot och ange det nya lösenordet"],
            "start_prompt": "Mitt mejl-program frågar efter lösenordet om och om igen, och inga av mina brev till syrran om Måns tokigheter går iväg. Det är så frustrerande!"
        },
        {
            "id": "L3_P006",
            "beskrivning": "När jag pratar med barnbarnen i Skype klagar de på att de hör sin egen röst som ett eko från min dator. Jag använder den inbyggda mikrofonen och högtalarna, inget headset. Jag ser att mikrofonsymbolen reagerar även när bara de pratar. Det låter som vi är i en kyrka!",
            "tekniska_fakta": {
                "program": "Skype (version 8.96)",
                "dator": "Lenovo IdeaPad 3 15IIL05",
                "ljudenheter": "Inbyggd mikrofon och inbyggda högtalare",
                "symptom": "Motparter i samtalet hör ett eko av sin egen röst (rundgång)."
            },
            "losning_nyckelord": ["Under videosamtal i Skype 8.96 på Lenovo IdeaPad 3 15IIL05 (inbyggd mikrofon/högtalare) rapporterar motparter tydligt eko av sin egen röst; mikrofon reagerar på ljud från datorns högtalare; inget headset används", "ljud från högtalarna plockas upp av mikrofonen (rundgång)", "använd ett headset (hörlurar med mikrofon) för att isolera ljudet", "sänk högtalarvolymen och mikrofonkänsligheten, eller använd Skypes ekoreducering om tillgängligt"],
            "start_prompt": "När jag pratar med barnbarnen på det där video-samtalet så hör alla sin egen röst som ett eko från min dator. Det låter som vi är i en stor kyrka!"
        },
        {
            "id": "L3_P007",
            "beskrivning": "Mitt skrivprogram, där jag skriver mina memoarer, fryser hela tiden och visar '(Svarar inte)'. Samtidigt ger hårddisken ifrån sig konstiga klickande ljud. Min dotter installerade ett program som visar en 'Varning' för disken, något om 'Reallocated Sectors Count'. Tänk om allt försvinner!",
            "tekniska_fakta": {
                "program": "Microsoft Word 2013",
                "hårddisk": "Seagate Barracuda 1TB ST1000DM003",
                "ljud": "Hårddisken ger ifrån sig klickande ljud",
                "diagnostik": "CrystalDiskInfo visar 'Varning' med attributet 'Reallocated Sectors Count' markerat."
            },
            "losning_nyckelord": ["Textredigeringsprogram ('Microsoft Word 2013') fryser ofta ('(Svarar inte)'); hårddisk ('Seagate Barracuda 1TB ST1000DM003') ger återkommande klickljud; CrystalDiskInfo visar 'Varning' (t.ex. 'Reallocated Sectors Count')", "hårddisken har problem eller är på väg att gå sönder", "kör en fullständig diskkontroll (chkdsk /f /r) på systemdisken", "säkerhetskopiera viktiga filer omedelbart och överväg att byta ut hårddisken"],
            "start_prompt": "Mitt skriv-program, där jag skriver ner mina memoarer om Måns, fryser hela tiden och visar 'återskapar fil' medan datorlådan knastrar och låter konstigt. Tänk om allt försvinner!"
        },
        {
            "id": "L3_P008",
            "beskrivning": "Jag försöker skriva ut dubbelsidigt, men när pappret kommer ut är texten på baksidan alldeles uppochnedvänd! Hur ska någon kunna läsa det? Jag ser att jag valt standardinställningen 'Vänd längs långa kanten'. Det finns ett annat alternativ för korta kanten.",
            "tekniska_fakta": {
                "skrivare": "Brother HL-L2350DW",
                "inställning": "'Vänd längs långa kanten (standard)'",
                "resultat": "Texten på baksidan är uppochnedvänd."
            },
            "losning_nyckelord": ["Vid dubbelsidig utskrift från Word till Brother HL-L2350DW med inställning 'Vänd längs långa kanten (standard)' blir texten på baksidan uppochnedvänd", "fel inställning för pappersvändning vid dubbelsidig utskrift", "välj 'vänd längs korta kanten' i utskriftsinställningarna för korrekt orientering på baksidan", "justera duplex-inställningen för 'short-edge binding'"],
            "start_prompt": "När jag försöker skriva ut mitt kakrecept på båda sidor av pappret så kommer texten på baksidan alldeles upp-och-ned! Hur ska någon kunna läsa det?"
        },
        {
            "id": "L3_P009",
            "beskrivning": "Min lilla surfplatta har blivit envis. Bilden förblir i stående läge även om jag vrider på plattan. Jag har tittat i snabbinställningarna, och där är ikonen för 'Automatisk rotering' gråtonad och det står 'Porträtt' under den. Den verkar vara avstängd.",
            "tekniska_fakta": {
                "enhet": "Samsung Galaxy Tab A7 Lite (SM-T220)",
                "operativsystem": "Android 11",
                "symptom": "Skärmen roterar inte till liggande läge",
                "status": "Ikonen för 'Automatisk rotering' i snabbinställningar är grå och visar 'Porträtt'."
            },
            "losning_nyckelord": ["Surfplatta ('Samsung Galaxy Tab A7 Lite (SM-T220)' med Android 11) förblir i porträttläge trots fysisk rotation; ikon för 'Automatisk rotering' i snabbinställningspanelen är gråtonad och visar 'Porträtt'", "automatisk skärmrotation är avstängd i systeminställningarna", "tryck på ikonen för skärmrotation i snabbinställningspanelen för att aktivera den", "gå till Inställningar > Skärm > och slå på 'Automatisk rotering'"],
            "start_prompt": "Min lilla surfplatta, som jag tittar på Måns-videor på, vägrar att vrida på bilden när jag vänder på plattan. Den är envis som en gammal get!"
        },
        {
            "id": "L3_P010",
            "beskrivning": "När jag ska logga in på banken med SMS-kod säger den att koden är ogiltig eller för gammal. Jag tittade på klockan på min telefon och den visade en tid, men datorns klocka visade en tid som var tre minuter tidigare! Jag ser att automatisk tid är avstängd i telefonen.",
            "tekniska_fakta": {
                "bank": "Handelsbanken",
                "telefon": "Doro 8080 (Android Go)",
                "felmeddelande": "'Ogiltig kod. Koden kan vara för gammal eller redan använd.'",
                "tidsskillnad": "Telefonens klocka går 3 minuter före datorns",
                "inställning": "'Använd nätverksbaserad tid' är avstängd på telefonen."
            },
            "losning_nyckelord": ["Engångskod via SMS till telefon ('Doro 8080') avvisas av bankens webbplats ('Handelsbanken') som 'Ogiltig kod... för gammal'; telefonens klocka skiljer sig från datorns; 'Använd nätverksbaserad tid' avstängd på telefonen", "telefonens klocka är osynkroniserad vilket gör SMS-koden ogiltig för tidskänsliga system", "slå på 'Automatisk datum och tid' (nätverksbaserad tid) i telefonens inställningar", "kontrollera att telefonens tid och tidszon är korrekta och synkroniserade"],
            "start_prompt": "Bank-koden som kommer i ett SMS till min telefon avvisas direkt som 'för gammal' när jag skriver in den på datorn. Det är som att de lever i olika tidsåldrar!"
        }
    ],
    # --- LEVEL 4 PROBLEMS (Index 3) ---
    [
        {
            "id": "L4_P001",
            "beskrivning": "När jag tryckte på startknappen på min dator började den bara pipa tre gånger, kort och ilsket. Strömlampan lyser grönt, men skärmen är helt svart. Min son sa att tre pip ofta betyder problem med minnet på den här typen av datorer.",
            "tekniska_fakta": {
                "dator": "HP Compaq Elite 8300 SFF",
                "minne": "2x Kingston KVR1333D3N9/2G (2GB DDR3)",
                "pip": "Tre korta pip vid startförsök",
                "bild": "Ingen bild på skärmen",
                "lampa": "Strömlampan lyser grönt"
            },
            "losning_nyckelord": ["Stationär dator ('HP Compaq Elite 8300 SFF') ger tre korta ljudsignaler (beep code) vid startförsök; skärmen förblir svart; strömlampa lyser grönt; RAM 2x 'Kingston KVR1333D3N9/2G'", "fel på RAM-minnet eller dålig kontakt med minnesmodulerna", "ta ut och sätt tillbaka minneskorten ordentligt (reseat)", "prova med en minnesmodul i taget i olika minnesplatser för att identifiera felaktig modul eller plats"],
            "start_prompt": "När jag trycker på startknappen på min stora datorlåda piper den bara tre gånger, kort och ilsket, och fönsterskärmen är helt svart. Den verkar ha fått hicka!"
        },
        {
            "id": "L4_P002",
            "beskrivning": "Jag satte i nya bläckpatroner i min skrivare, men när jag skriver ut kommer pappren ut alldeles blanka! Jag tittade på en av de nya patronerna i förpackningen och såg att det satt en liten orange skyddstejp med texten 'PULL' över ett lufthål. Jag minns inte att jag drog bort någon sån...",
            "tekniska_fakta": {
                "skrivare": "Epson Stylus DX4400",
                "patroner": "Svart (T0711) och färg (T0712, T0713, T0714)",
                "symptom": "Utskrifter är helt blanka",
                "observation": "Oanvänd patron har en orange skyddstejp märkt 'PULL' över ett lufthål"
            },
            "losning_nyckelord": ["Nya bläckpatroner ('Epson T0711' svart, 'T0712/3/4' färg) installerade i 'Epson Stylus DX4400' matar fram blanka papper; orange skyddstejp ('PULL') observerad på ovansidan av ny patron täckande lufthål", "skyddstejp på bläckpatronerna blockerar bläcktillförseln eller ventilationen", "avlägsna all skyddstejp och plastremsor från nya bläckpatroner innan installation", "se till att lufthålen på patronerna är helt öppna"],
            "start_prompt": "Jag har satt i nya fina färgpatroner i skrivaren, men pappren kommer ut alldeles tomma, inte en prick! Det är som att färgen har rymt."
        },
        {
            "id": "L4_P003",
            "beskrivning": "Jag skulle ansluta min bärbara dator till mitt trådlösa nätverk, men istället för WiFi-symbolen visas en liten flygplansikon. I inställningarna står det 'Flygplansläge: På'. Jag har provat att trycka Fn+F3, där det är en flygplanssymbol, men inget händer.",
            "tekniska_fakta": {
                "dator": "Acer Aspire 5 A515-54G",
                "operativsystem": "Windows 10",
                "symptom": "Flygplansikon visas i aktivitetsfältet",
                "status": "'Flygplansläge: På'",
                "test": "Fn+F3 (med flygplanssymbol) har ingen effekt"
            },
            "losning_nyckelord": ["Bärbar dator ('Acer Aspire 5 A515-54G' med Windows 10) visar flygplansikon i aktivitetsfältet; Nätverksinställningar visar 'Flygplansläge: På'; Fn+F3 har ingen effekt; ingen WiFi-knapp på sidan", "flygplansläget är aktiverat i Windows och blockerar trådlösa anslutningar", "stäng av Flygplansläge via Nätverks- & Internetinställningar i Windows", "klicka på flygplansikonen i aktivitetsfältet och välj att stänga av läget därifrån"],
            "start_prompt": "Min bärbara dator har fått för sig att den är ett flygplan! Det har dykt upp en liten flygplansbild bredvid klockan, och nu ser jag inga trådlösa nät längre. Den kanske vill flyga söderut med Måns?"
        },
        {
            "id": "L4_P004",
            "beskrivning": "Jag har nyligen installerat om Windows. Allt verkar fungera, men i nedre högra hörnet visas en halvtransparent text som säger att jag ska gå till inställningar för att aktivera Windows. Jag angav ingen produktnyckel under installationen.",
            "tekniska_fakta": {
                "operativsystem": "Windows 10 Home",
                "symptom": "En vattenstämpel visas på skärmen",
                "text": "'Aktivera Windows. Gå till Inställningar för att aktivera Windows.'",
                "installation": "Ingen produktnyckel angavs"
            },
            "losning_nyckelord": ["Halvtransparent text ('vattenstämpel') 'Aktivera Windows. Gå till Inställningar för att aktivera Windows.' visas på Windows 10 Home skärm efter ominstallation från generisk USB; produktnyckel ej angiven, ingen digital licens", "Windows-installationen är inte aktiverad med en giltig licens", "ange en giltig Windows 10 produktnyckel i Systeminställningar > Aktivering", "köp en Windows 10-licens eller använd en befintlig digital licens kopplad till ditt Microsoft-konto"],
            "start_prompt": "Det står en suddig text i hörnet på min fönsterskärm som säger att jag måste 'aktivera' systemet. Vad menar den med det? Ska jag klappa den lite?"
        },
        {
            "id": "L4_P005",
            "beskrivning": "Min gamla dator har blivit virrig i tiden! Varje gång jag drar ur strömsladden och startar den igen, har klockan hoppat tillbaka till 2002. Det händer både i Windows och i BIOS. Min son sa att det kunde vara ett litet batteri på moderkortet.",
            "tekniska_fakta": {
                "dator": "Fujitsu Siemens Scaleo P",
                "moderkort": "ASUS P5KPL-AM",
                "batteri": "CR2032",
                "symptom": "Systemklockan återställs till 1 januari 2002 efter att datorn varit strömlös"
            },
            "losning_nyckelord": ["Systemklocka i BIOS och Windows på stationär dator ('Fujitsu Siemens Scaleo P', moderkort 'ASUS P5KPL-AM') återställs till 01-01-2002 00:00 efter att datorn varit strömlös; moderkortet använder CR2032-batteri", "CMOS-batteriet på moderkortet är urladdat eller defekt", "byt ut det lilla runda batteriet (CR2032) på datorns moderkort", "sätt i ett nytt, fräscht BIOS-batteri"],
            "start_prompt": "Min dator har blivit alldeles virrig i tiden! Varje gång jag stänger av den helt så hoppar klockan tillbaka till år 2002. Den kanske längtar tillbaka till när Måns var kattunge."
        },
        {
            "id": "L4_P006",
            "beskrivning": "Mina utskrifter blir alldeles randiga, med tjocka, mörka horisontella ränder som täcker allt. Jag har kört 'Djuprengöring av skrivhuvud' flera gånger utan att det blir bättre. Det är som om någon har ritat med en tuschpenna över alltihop.",
            "tekniska_fakta": {
                "skrivare": "Canon PIXMA MG3650",
                "patroner": "PG-540 (svart), CL-541 (färg)",
                "symptom": "Utskrifter har tjocka, jämna, mörka horisontella ränder",
                "test": "'Djuprengöring av skrivhuvud' har körts flera gånger utan resultat"
            },
            "losning_nyckelord": ["Bläckstråleskrivare ('Canon PIXMA MG3650' med PG-540/CL-541 patroner) producerar utskrifter med tjocka, jämnt fördelade mörka horisontella ränder; 'Djuprengöring av skrivhuvud' har körts utan förbättring", "skrivhuvudets munstycken är igentäppta och behöver rengöras", "kör skrivhuvudsrengöring (eventuellt flera gånger med paus emellan)", "om rengöring inte hjälper kan patronen eller skrivhuvudet vara defekt", "byt bläckpatroner"],
            "start_prompt": "Mina utskrifter från skrivaren får tjocka mörka ränder tvärs över texten, som om någon har ritat med en bred svart tuschpenna över alltihop. Det ser inte klokt ut!"
        },
        {
            "id": "L4_P007",
            "beskrivning": "När jag spelar musik kommer ljudet bara från den högra högtalaren. Den vänstra är helt tyst, men baslådan fungerar. Jag tittade i ljudinställningarna och ser att ljudbalansen är helt fel, den ena kanalen står på 100% och den andra på 0%.",
            "tekniska_fakta": {
                "högtalare": "Logitech Z313 2.1-system",
                "symptom": "Ljud endast från höger satellithögtalare och subwoofer",
                "balans": "Ljudbalansen i Windows är inställd på Höger 100%, Vänster 0%"
            },
            "losning_nyckelord": ["Ljuduppspelning (från 'Spotify') via högtalarsystem ('Logitech Z313 2.1' anslutet till grönt ljuduttag) endast från höger satellithögtalare, vänster tyst, subwoofer fungerar; Windows ljudbalans visar Höger 100%, Vänster 0%", "ljudbalansen mellan höger och vänster kanal är felinställd", "justera ljudbalansen till mitten (50% för varje kanal) i ljudinställningarna", "centrera stereobalansen för uppspelningsenheten"],
            "start_prompt": "När jag spelar min favoritmusik så hörs den bara i den högra högtalaren – den vänstra är alldeles tyst! Det är som att den har tagit semester."
        },
        {
            "id": "L4_P008",
            "beskrivning": "Jag försökte koppla in min externa hårddisk i min gamla dator, men den börjar bara avge ett repetitivt klickljud. Den syns kort i 'Den här datorn' och försvinner sedan. Den fungerar fint på min nya dator. Min son sa att den kanske behöver mer ström.",
            "tekniska_fakta": {
                "hårddisk": "WD Elements 2TB Portable (Modell: WDBU6Y0020BBK)",
                "anslutning": "Enkel USB 3.0-kabel",
                "dator": "Äldre dator med USB 2.0-portar",
                "symptom": "Repetitivt klickljud, enheten syns kort och försvinner"
            },
            "losning_nyckelord": ["Extern hårddisk ('WD Elements 2TB Portable' med enkel USB 3.0 kabel) avger repetitivt klickljud vid anslutning till USB 2.0-port på äldre dator; syns kortvarigt och försvinner", "extern hårddisk får inte tillräckligt med ström från USB-porten", "använd en USB Y-kabel för att ansluta till två USB-portar för extra ström", "testa med en USB-hubb som har egen strömförsörjning", "anslut till en USB 3.0 port om möjligt"],
            "start_prompt": "Min yttre hårddisk, den där lilla lådan jag sparar bilder på Måns i, klickar och försvinner direkt när jag kopplar in den i den gamla datorn. Den kanske är hungrig?"
        },
        {
            "id": "L4_P009",
            "beskrivning": "Jag har kopplat min bärbara dator till TV:n med en HDMI-kabel. Bilden visas utmärkt, men ljudet spelas fortfarande från datorns högtalare. I ljudinställningarna ser jag att datorns högtalare är standardenhet och TV:n finns med i listan men är inte vald.",
            "tekniska_fakta": {
                "dator": "Dell Inspiron 15 5559 med Intel HD Graphics 520",
                "tv": "Samsung UE40H6400",
                "anslutning": "HDMI-kabel",
                "ljudenhet": "I Windows är 'Högtalare (Realtek High Definition Audio)' standard, TV:n ('Samsung TV (Intel(R) Display Audio)') är inte standard."
            },
            "losning_nyckelord": ["Bärbar dator ('Dell Inspiron 15 5559') ansluten till TV ('Samsung UE40H6400') via HDMI; bild visas på TV men ljud spelas från datorns högtalare; i Windows Ljudinställningar är 'Högtalare (Realtek High Definition Audio)' standard, 'Samsung TV (Intel(R) Display Audio)' listas men är inaktiverad/inte standard", "HDMI-ljudutgången är inte vald som standardenhet i Windows", "aktivera TV:n (HDMI) som ljudenhet och ställ in den som standard i ljudinställningarna", "högerklicka på HDMI-ljudenheten (Samsung TV) i ljudpanelen och välj 'Aktivera' och sedan 'Ange som standardenhet'"],
            "start_prompt": "Jag har kopplat min bärbara dator till den stora teven för att se på film, och jag får fin bild, men ljudet kommer fortfarande bara från den lilla datorn! Det är ju inte meningen."
        },
        {
            "id": "L4_P010",
            "beskrivning": "Min iPad tjatar om att lagringsutrymmet är nästan fullt. I inställningarna ser jag att en stor del upptas av 'Nyligen raderade' bilder, trots att jag har raderat massor från Bilder-appen. I albumet 'Nyligen raderade' ligger alla bilderna kvar.",
            "tekniska_fakta": {
                "enhet": "iPad Air 2 (Modell A1566)",
                "operativsystem": "iOS 15",
                "varning": "'Lagringsutrymme nästan fullt'",
                "lagring": "10GB upptas av 'Bilder > Nyligen raderade'"
            },
            "losning_nyckelord": ["Surfplatta ('iPad Air 2', iOS 15) meddelar 'Lagringsutrymme nästan fullt'; 10GB upptas av 'Bilder > Nyligen raderade' trots att bilder raderats från Bilder-appen; albumet 'Nyligen raderade' innehåller objekten", "raderade bilder/videor ligger kvar i albumet 'Nyligen raderade' och tar upp plats", "gå in i Bilder-appen > Album > Nyligen raderade och välj 'Välj' sedan 'Radera alla' för att permanent ta bort objekten", "töm papperskorgen för bilder manuellt"],
            "start_prompt": "Min platta säger att lagringen är full fast jag har raderat massor av gamla bilder på Måns när han var liten. Var tar de vägen egentligen, de där raderade bilderna?"
        }
    ],
    # --- LEVEL 5 PROBLEMS (Index 4) ---
    [
        {
            "id": "L5_P001",
            "beskrivning": "Direkt när jag startar datorn blir skärmen svart och det står med vit text att statusen är 'BAD' och att jag borde 'Backup and Replace'. Den säger att jag kan trycka F1 för att fortsätta. När jag gör det startar Windows, men datorn är jättelångsam. Jag blir så orolig för mina bilder!",
            "tekniska_fakta": {
                "dator": "Acer Veriton M2630G",
                "hårddisk": "Toshiba DT01ACA100 1TB",
                "felmeddelande": "'S.M.A.R.T. Status BAD, Backup and Replace. Press F1 to Resume.'"
            },
            "losning_nyckelord": ["Vid uppstart av dator ('Acer Veriton M2630G' med 'Toshiba DT01ACA100 1TB' HDD), efter BIOS POST, visas svart skärm med text: 'S.M.A.R.T. Status BAD, Backup and Replace. Press F1 to Resume.'; Windows startar efter F1 men är långsamt/hänger sig", "hårddisken rapporterar kritiska S.M.A.R.T.-fel och är på väg att gå sönder", "säkerhetskopiera alla viktiga data omedelbart och byt ut den felande hårddisken", "installera en ny hårddisk och återställ systemet från backup eller nyinstallation"],
            "start_prompt": "Min stackars dator varnar för att 'Hårddisken mår dåligt – byt snarast!' redan innan den hunnit starta ordentligt. Den ber mig trycka F1 för att fortsätta, men det känns inte bra alls. Tänk om alla mina bilder på Måns försvinner!"
        },
        {
            "id": "L5_P002",
            "beskrivning": "Min nya bärbara dator, som har BitLocker-diskkryptering, visar en blå skärm när jag startar. Den säger att jag måste ange en återställningsnyckel och visar ett långt Nyckel-ID. Jag har ingen aning om var jag har en sådan nyckel! Nu kommer jag inte in alls.",
            "tekniska_fakta": {
                "dator": "Microsoft Surface Laptop 3",
                "operativsystem": "Windows 10 Pro med BitLocker",
                "skärm": "Blå BitLocker-återställningsskärm",
                "meddelande": "'BitLocker-återställning. Ange återställningsnyckeln för den här enheten för att fortsätta.'",
                "id": "Ett Nyckel-ID (t.ex. XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX) visas"
            },
            "losning_nyckelord": ["Bärbar dator ('Microsoft Surface Laptop 3' med Windows 10 Pro och BitLocker) visar blå skärm vid start: 'BitLocker-återställning. Ange återställningsnyckeln... Nyckel-ID: XXXXXXXX...'; användaren har inte sparat nyckeln, finns ej på Microsoft-konto", "BitLocker-diskkryptering kräver återställningsnyckel efter systemändring eller misstänkt manipulation", "leta efter en utskriven BitLocker-återställningsnyckel eller en som sparats på USB-minne vid installationen", "om nyckeln är förlorad kan data vara oåtkomliga utan ominstallation"],
            "start_prompt": "Hjälp! Min fina nya bärbara dator har fått fnatt! Den visar en blå skärm och ber mig skriva in en jättelång 'återställningskod' innan Windows vill öppnas. Jag har ingen aning om var jag har en sådan kod!"
        },
        {
            "id": "L5_P003",
            "beskrivning": "Min gamla dator startar inte. Efter den första texten blir skärmen svart och det står 'NTLDR is missing'. Jag har provat att starta om. I BIOS är CD-läsaren satt som första startenhet. Jag försökte starta från min Windows-CD, men datorn verkar inte läsa den.",
            "tekniska_fakta": {
                "operativsystem": "Windows XP Professional",
                "bios": "Phoenix AwardBIOS v6.00PG",
                "hårddisk": "Maxtor DiamondMax Plus 9 80GB ATA/133",
                "felmeddelande": "'NTLDR is missing. Press Ctrl+Alt+Del to restart.'",
                "bootorder": "1. CD-ROM, 2. Hard Disk"
            },
            "losning_nyckelord": ["Äldre dator (Windows XP Pro, Phoenix AwardBIOS v6.00PG) visar svart skärm med text: 'NTLDR is missing. Press Ctrl+Alt+Del to restart'; CD-ROM är första startenhet i BIOS, HDD ('Maxtor DiamondMax Plus 9 80GB ATA/133') andra; start från XP installations-CD misslyckas (CD läses ej)", "felaktig startenhetsordning (boot order) i BIOS eller problem med startfilerna på hårddisken", "gå in i BIOS-inställningarna och ställ in hårddisken (HDD) som första startenhet", "kontrollera att hårddisken detekteras korrekt i BIOS och försök reparera startsektorn med XP-CD (om CD-läsaren fungerar)", "kontrollera IDE/SATA-kabeln till hårddisken"],
            "start_prompt": "Min gamla trotjänare till dator säger bara 'NTLDR saknas' och vägrar gå vidare från en svart skärm. Det låter som en viktig del har sprungit bort. Kanske Måns har gömt den?"
        },
        {
            "id": "L5_P004",
            "beskrivning": "Efter ett kort strömavbrott startar min dator, men skärmen är helt svart. Fläktarna snurrar på maxhastighet och lamporna på moderkortet lyser. Det finns en liten display på moderkortet som visar en kod. Min son sa att koden kan indikera CPU-problem eller korrupt BIOS.",
            "tekniska_fakta": {
                "moderkort": "Gigabyte GA-Z97X-Gaming 5",
                "cpu": "Intel Core i7-4790K",
                "symptom": "Fläktar snurrar på max, moderkorts-LEDs lyser, men ingen bildsignal",
                "debugkod": "Debug LED på moderkort visar '00'"
            },
            "losning_nyckelord": ["Stationär dator (moderkort 'Gigabyte GA-Z97X-Gaming 5', CPU 'Intel Core i7-4790K') startar efter strömavbrott (fläktar max, moderkorts-LEDs lyser) men skärmen får ingen signal ('No Input'); Debug LED på moderkort visar '00'; CMOS-reset via jumper utan effekt", "BIOS/CMOS-inställningarna är korrupta eller moderkortet har problem efter strömavbrott", "utför en grundlig CMOS-återställning genom att ta ur moderkortsbatteriet en stund medan datorn är strömlös", "kontrollera alla anslutningar på moderkortet och testa med minimal konfiguration (endast CPU, ett RAM, grafikkort)", "testa med annat nätaggregat"],
            "start_prompt": "Efter ett litet strömavbrott här hemma så snurrar fläktarna i datorn som tokiga, men fönsterskärmen tänds aldrig. Den är helt svart och säger 'Ingen signal'. Det är som att den har blivit rädd för mörkret."
        },
        {
            "id": "L5_P005",
            "beskrivning": "Jag har nyligen anslutit min skrivare till datorn med USB. När jag skriver ut blir sidorna fyllda med obegripliga tecken och symboler. Windows använde automatiskt någon sorts standarddrivrutin. På min gamla dator, där jag hade installerat tillverkarens egna drivrutiner, fungerade den utmärkt.",
            "tekniska_fakta": {
                "program": "WordPad i Windows 10",
                "skrivare": "HP LaserJet P1102w (ansluten via USB)",
                "drivrutin": "Windows använder 'Microsoft IPP Class Driver'",
                "symptom": "Utskrifter innehåller obegripliga tecken och symboler (t.ex. 'ÿØÿà€JFIF€€Æ @#$!%^&*')"
            },
            "losning_nyckelord": ["Utskrift från WordPad (Windows 10) till HP LaserJet P1102w (nyligen USB-ansluten) resulterar i sidor fyllda med obegripliga tecken/symboler; Windows använde 'Microsoft IPP Class Driver'", "felaktig eller generisk skrivardrivrutin används av Windows", "ladda ner och installera den officiella, modellanpassade skrivardrivrutinen från HP:s webbplats för LaserJet P1102w", "avinstallera den nuvarande drivrutinen och installera rätt PCL- eller PostScript-drivrutin"],
            "start_prompt": "När jag försöker skriva ut mina dikter om Måns så blir all text på pappret bara en massa obegripliga krumelurer och konstiga tecken. Det ser ut som katten själv har varit framme och skrivit!"
        },
        {
            "id": "L5_P006",
            "beskrivning": "Jag har installerat om Windows på en gammal dator, men jag kan inte komma åt några säkra webbplatser. Webbläsaren klagar på certifikatfel. Windows Update fungerar inte heller och ger en felkod. Systemtiden är korrekt. Min son nämnde något om saknade rotcertifikat.",
            "tekniska_fakta": {
                "operativsystem": "Windows 7 Ultimate (32-bitars, utan Service Pack)",
                "webbläsare": "Internet Explorer 8",
                "webbfel": "Certifikatfel 'DLG_FLAGS_INVALID_CA / INET_E_SECURITY_PROBLEM'",
                "updatefel": "Windows Update felkod 80072EFE"
            },
            "losning_nyckelord": ["Nyinstallerad Windows 7 Ultimate (utan SP, 32-bit) kan ej öppna HTTPS-webbplatser (IE8 visar 'kan inte visa webbsida' eller certifikatfel 'DLG_FLAGS_INVALID_CA / INET_E_SECURITY_PROBLEM'); Windows Update fungerar ej (felkod 80072EFE); systemtid/datum korrekt", "operativsystemet saknar uppdaterade rotcertifikat och modernt TLS/SSL-stöd", "installera Windows 7 Service Pack 1 och alla efterföljande kumulativa uppdateringar manuellt (t.ex. via Microsoft Update Catalog)", "importera aktuella rotcertifikat och aktivera TLS 1.2 stöd via registerändringar eller Microsoft Easy Fix"],
            "start_prompt": "Inga säkra sidor på internet vill öppnas på min nyinstallerade dator – allt bara klagar på ogiltiga 'certifikat' fast datumet på datorn stämmer. Det är som att alla dörrar är låsta!"
        },
        {
            "id": "L5_P007",
            "beskrivning": "När jag har många flikar öppna i webbläsaren och samtidigt redigerar bilder, kommer det ofta upp ett meddelande från Windows om att datorn har ont om minne och att jag ska stänga program. Ofta kraschar programmen strax efteråt. Jag ser att växlingsfilen är ganska liten.",
            "tekniska_fakta": {
                "ram": "8GB (Corsair Vengeance LPX DDR4 2400MHz)",
                "hårddisk": "SSD, Samsung 860 EVO 250GB (ca 50GB ledigt)",
                "program": "Google Chrome (många flikar), Adobe Photoshop Elements 2021",
                "felmeddelande": "'Datorn har ont om minne. Spara dina filer och stäng dessa program.'",
                "växlingsfil": "Systemhanterad, observerad storlek ca 2GB"
            },
            "losning_nyckelord": ["System med 8GB RAM, 50GB ledigt på C: (SSD), Windows-meddelande 'Datorn har ont om minne' vid användning av Chrome (många flikar) och Photoshop Elements; program kraschar; växlingsfil (pagefile.sys) systemhanterad, liten (t.ex. 2GB)", "systemets växlingsfil (virtuellt minne) är för liten för den aktuella arbetsbelastningen", "öka storleken på växlingsfilen manuellt i Windows systeminställningar (t.ex. till 1.5x RAM eller systemhanterad med större initialstorlek)", "överväg att utöka det fysiska RAM-minnet om problemet kvarstår frekvent"],
            "start_prompt": "Min dator gnäller om att den har för lite 'virtuellt minne' och stänger ner mina program när jag försöker redigera bilder på Måns och ha många internetsidor öppna samtidigt. Vad menar den med virtuellt, är det låtsasminne?"
        },
        {
            "id": "L5_P008",
            "beskrivning": "Jag har köpt ett nytt USB-headset. Ljudet i hörlurarna fungerar utmärkt, men mikrofonen fungerar inte. När jag tittar i ljudinställningarna under 'Inspelning' listas bara min gamla inbyggda mikrofon. Jag ser ingen mikrofon från mitt nya headset där, trots att det syns i Enhetshanteraren.",
            "tekniska_fakta": {
                "headset": "Logitech H390 (USB)",
                "operativsystem": "Windows 10",
                "inspelning": "I Ljudinställningar listas endast 'Mikrofon (Realtek High Definition Audio)' och 'Stereomix'.",
                "enhetshanteraren": "Visar headsetet korrekt under 'Ljud-, video- och spelenheter' utan fel."
            },
            "losning_nyckelord": ["Nytt USB-headset ('Logitech H390') ljud i hörlurar fungerar i Windows 10, men mikrofonen listas ej under 'Ljud > Inspelning'; headset visas i Enhetshanteraren utan fel; 'Visa inaktiverade enheter' markerat", "headsetets mikrofon är inte aktiverad eller vald som standardinspelningsenhet, eller har sekretessproblem", "kontrollera att mikrofonen på headsetet inte är fysiskt avstängd (mute-knapp)", "gå till Enhetshanteraren, avinstallera headsetet och låt Windows installera om det; välj sedan som standard i Ljudinställningar", "kontrollera mikrofonens sekretessinställningar i Windows 10"],
            "start_prompt": "Jag har köpt en ny fin hörlur med mikrofon för att kunna prata med barnbarnen, men mikrofonen syns inte i listan i datorn! Ljudet i lurarna fungerar, men de hör inte mig. Det är ju tråkigt."
        },
        {
            "id": "L5_P009",
            "beskrivning": "När jag försöker spela upp videor på YouTube eller SVT Play hör jag bara ljudet – bildrutan är helt grå eller svart. Problemet uppstod ganska nyligen, jag tror det var efter en Windows-uppdatering. Jag har kollat att maskinvaruacceleration i webbläsaren är aktiverad.",
            "tekniska_fakta": {
                "webbläsare": "Mozilla Firefox 91 ESR",
                "operativsystem": "Windows 10 (version 21H2)",
                "händelse": "Problem uppstod efter Windows-uppdatering (KB500XXXX)",
                "grafikkort": "Intel HD Graphics 4000 (drivrutin från 2017)",
                "symptom": "Videouppspelning på webbplatser ger endast ljud; bildrutan är svart/grå."
            },
            "losning_nyckelord": ["Videouppspelning ('YouTube HTML5 player', 'SVT Play') i Firefox 91 ESR på Windows 10 (21H2) visar endast ljud, bildrutan grå/svart; problem uppstod efter Windows-uppdatering (KB500XXXX); grafikkort Intel HD Graphics 4000 (drivrutin 2017); maskinvaruacceleration i Firefox aktiverad; problem i andra webbläsare också", "problem med videokodekar eller grafikdrivrutiner efter systemuppdatering", "installera ett omfattande kodekpaket (t.ex. K-Lite Codec Pack Full)", "försök att inaktivera/aktivera maskinvaruacceleration i webbläsarens inställningar eller systemets grafikinställningar; sök efter nyare (eller äldre stabila) grafikdrivrutiner"],
            "start_prompt": "När jag försöker titta på roliga kattklipp på internet så hör jag bara ljudet – bilden är alldeles grå! Det är ju det roligaste som försvinner. Måns blir också besviken."
        },
        {
            "id": "L5_P010",
            "beskrivning": "När jag startar min dator piper den konstigt: ett långt pip och sedan två korta. Min son sa att det ofta indikerar problem med grafikkortet. Skärmen är helt svart och säger att den inte får någon signal. Fläktarna på grafikkortet snurrar dock som de ska.",
            "tekniska_fakta": {
                "moderkort": "ASUS P8P67 LE (med AMI BIOS)",
                "cpu": "Intel Core i5-2500K",
                "grafikkort": "NVIDIA GeForce GTX 560 Ti",
                "pip": "Ett långt och två korta pip vid start",
                "bildsignal": "Ingen signal till skärmen (ansluten via DVI)"
            },
            "losning_nyckelord": ["Stationär dator (moderkort 'ASUS P8P67 LE', CPU 'Intel Core i5-2500K', grafikkort 'NVIDIA GeForce GTX 560 Ti') avger en lång och två korta ljudsignaler (AMI BIOS beep code) vid start; skärmen svart (ingen signal via DVI); grafikkortsfläktar snurrar; kort i översta PCIe x16, extra ström ansluten", "grafikkortet har dålig kontakt, är felaktigt anslutet eller defekt", "ta ur och sätt tillbaka grafikkortet ordentligt i PCIe-porten (reseat)", "kontrollera att alla extra strömanslutningar till grafikkortet sitter fast; testa med ett annat grafikkort om möjligt", "testa med en annan bildskärmskabel eller bildskärmsport"],
            "start_prompt": "Min dator startar med ett långt pip och sedan två korta, som en ledsen fågel, och fönsterskärmen förblir alldeles svart. Den vill nog inte vakna idag."
        }
    ]
]

# Helper to get the number of levels
NUM_LEVELS = len(PROBLEM_CATALOGUES)