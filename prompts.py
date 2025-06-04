# prompts.py (Corrected L2_P008 with real AV name, and Ulla flair)

# --- START PHRASES PER LEVEL ---
START_PHRASES = [
    "starta övning", # Level 1 (index 0)
    "utmaning nivå 2",     # Level 2 (index 1)
    "expertläge nivå 3",    # Level 3 (index 2)
    "mästarprov nivå 4",    # Level 4 (index 3)
    "ulla special nivå 5"  # Level 5 (index 4)
]

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

EVALUATOR_SYSTEM_PROMPT = """
Du är en precis och logisk utvärderings-AI. Din uppgift är att strikt avgöra om studentens SENASTE meddelande innehåller en lösning som matchar de givna lösningsnyckelorden för det aktuella tekniska problemet.
Studentens meddelande kan innehålla annat än bara lösningen. Fokusera enbart på om kärnan i något av lösningsnyckelorden har föreslagits.
Svara ENDAST med `[LÖST]` på en egen rad om en korrekt lösning föreslås.
Svara ENDAST med `[EJ_LÖST]` på en egen rad om ingen korrekt lösning föreslås.
Ingen annan text, förklaring eller formatering.
"""

# --- PROBLEM CATALOGUES PER LEVEL ---
PROBLEM_CATALOGUES = [
    # --- LEVEL 1 PROBLEMS (Index 0) - Based on "Svårighetsgrad 1" ---
    [
        {
            "id": "L1_P001",
            "beskrivning": "Systemmeddelande i Windows Update: 'Viktig systemåtgärd krävs - Felkod WX0078'. Program 'Bildvisaren Deluxe 2.1' (som följde med kameran 'Kodak EasyShare C530') startar ej, visar 'Väntar på systemuppdatering'.",
            "losning_nyckelord": ["Systemet kräver uppdateringar för att program ska fungera", "kör Windows Update", "låta datorn installera uppdateringar klart"],
            "start_prompt": "Kära nån, nu tjatar datorn igen om en viktig uppdatering, och mitt fina fotoprogram där jag har alla bilder på Måns vill inte öppna sig längre. Det är ju förargligt!"
        },
        {
            "id": "L1_P002",
            "beskrivning": "USB-enhet: 'SanDisk Cruzer Blade 16GB' (röd/svart). Ingen aktivitetslampa tänds vid anslutning till främre USB-port (märkt med USB-symbol) på dator 'Fujitsu Esprimo P520'. Inget ljud från Windows vid anslutning.",
            "losning_nyckelord": ["USB-porten kanske inte fungerar eller ger tillräcklig kontakt", "prova ett annat USB-uttag", "sätta stickan i en annan USB-port"],
            "start_prompt": "Nu har jag stoppat in min lilla bild-sticka, du vet den jag fick av barnbarnet, men den hörs inte och syns inte någonstans på skärmen. Måns var precis här och nosade på den, men det hjälpte inte."
        },
        {
            "id": "L1_P003",
            "beskrivning": "Skärmmeddelande på 'Windows 7' inloggningsskärm: 'För många felaktiga lösenordsförsök. Kontot är låst. Försök igen om 15:00 minuter. Referens: LCK_USR_03'.",
            "losning_nyckelord": ["Kontot är temporärt låst på grund av för många felaktiga inloggningsförsök", "vänta tills kontot låses upp automatiskt", "ha tålamod femton minuter"],
            "start_prompt": "Åh, elände! Jag tror jag slog fel kod för många gånger när jag skulle logga in, för nu står det att jag måste vänta en hel kvart! Tänk om jag glömmer vad jag skulle göra under tiden?"
        },
        {
            "id": "L1_P004",
            "beskrivning": "Ljudprogram 'Winamp 5.6' indikerar uppspelning. Windows ljudinställningar (Kontrollpanelen > Ljud) visar 'Standardenhet för uppspelning: Hörlurar (Realtek High Definition Audio)' trots att inga hörlurar är anslutna till det gröna uttaget. Inget ljud från 'Logitech S120' högtalare (anslutna till samma gröna uttag).",
            "losning_nyckelord": ["Fel ljudenhet är vald som standard i Windows", "ändra standardljudenhet till högtalare i ljudinställningarna", "ställ in Windows att använda högtalarna"],
            "start_prompt": "Min musik går bara i de där hörsnäckorna, fast sladden är urdragen! Jag vill ju att det ska låta ur de vanliga högtalarna så Måns också kan höra. Han gillar Povel Ramel."
        },
        {
            "id": "L1_P005",
            "beskrivning": "Bildskärm 'Dell E2216H' (ansluten med VGA-kabel) visar plötsligt gröna/rosa flimrande artefakter och bildstörningar vid fysisk rörelse av skärmen eller när man rör vid VGA-kabeln ('den blåa sladden med små skruvarna') nära anslutningen.",
            "losning_nyckelord": ["Bildskärmskabeln har dålig kontakt eller är skadad", "tryck fast bild-sladden ordentligt i både skärm och dator", "kontrollera att skärmkabeln sitter åt"],
            "start_prompt": "Hjälp, om jag eller Måns råkar skaka lite på bordet så blinkar hela fönsterskärmen i alla möjliga konstiga färger! Det är som ett helt diskotek här hemma."
        },
        {
            "id": "L1_P006",
            "beskrivning": "Fotoprogram 'Picasa 3' (lokalt installerat) visar gråa platshållare med texten 'Bilden är offline. Status: Ingen internetanslutning. Kod: NC-002'. Nätverksikon (jordglob med rött kryss) vid klockan i Windows aktivitetsfält.",
            "losning_nyckelord": ["Datorn saknar internetanslutning", "aktivera nätverksanslutningen (WiFi eller kabel)", "kontrollera att internetkabeln sitter i eller anslut till trådlöst nätverk"],
            "start_prompt": "Alla mina fina moln-bilder, eller vad det nu heter, har blivit gråa rutor med något konstigt ord 'offline'. Det är som att de har rest bort utan att säga till!"
        },
        {
            "id": "L1_P007",
            "beskrivning": "Skrivare 'HP Deskjet 970Cxi' ger lågt brummande/klickande ljud, sedan blinkar orange 'Fel'-lampa (ikon med utropstecken). Ingen utskrift sker. Display visar 'Fel E05. Kontakta service'.",
            "losning_nyckelord": ["Skrivaren har ett internt fel som kan lösas med omstart", "stäng av och på skrivaren (power cycle)", "gör en kall omstart av skrivaren genom att dra ur strömsladden"],
            "start_prompt": "Min skrivar-apparat står bara och surrar lite tyst för sig själv, och sen kommer det ett ilsket felmeddelande. Den vill nog ha fika den också, precis som jag."
        },
        {
            "id": "L1_P008",
            "beskrivning": "Webbsida 'Skatteverket.se' för deklaration. Interaktion med 'Nästa'-knapp resulterar i ingen åtgärd. Webbläsare 'Internet Explorer 9' visar ibland notis 'Ett popup-fönster blockerades. För att se detta popup-fönster eller ytterligare alternativ klickar du här...'.",
            "losning_nyckelord": ["Webbläsarens popup-blockerare hindrar sidan från att fungera korrekt", "tillåt pop-up-fönster för den specifika webbplatsen", "inaktivera popup-blockeraren tillfälligt för skatteverket.se"],
            "start_prompt": "Jag försöker göra rätt för mig på den där myndighetssidan, men det händer absolut ingenting när jag trycker på knapparna! Det är som att den ignorerar mig totalt."
        },
        {
            "id": "L1_P009",
            "beskrivning": "PDF-fil 'Telia_Faktura_Mars.pdf' öppnas i 'Adobe Reader X (10.1.0)'. Innehållet visas som en helt vit sida. Ibland visas felmeddelande 'Ett fel uppstod vid bearbetning av sidan. Ogiltig färgrymd.'",
            "losning_nyckelord": ["PDF-läsaren är för gammal eller har problem att rendera filen", "uppdatera Adobe Reader till senaste versionen", "prova att öppna PDF-filen med en annan PDF-visare (t.ex. webbläsare)"],
            "start_prompt": "Min el-räkning har kommit, men när jag öppnar den så är hela sidan alldeles kritvit! Jag ser inte ett enda öre av vad jag ska betala. Måns tycker det är jättekonstigt."
        },
        {
            "id": "L1_P010",
            "beskrivning": "Webbläsare 'Firefox ESR 52' visar röd varningssida 'Anslutningen är inte säker' med felkod 'SEC_ERROR_UNKNOWN_ISSUER' vid försök att nå bankens (Swedbank) webbplats. Adressfältet visar 'http://www.swedbank.se' och ett överstruket hänglås.",
            "losning_nyckelord": ["Webbplatsen försöker nås via en osäker anslutning (HTTP istället för HTTPS)", "skriv https:// före webbadressen (t.ex. https://www.swedbank.se)", "klicka på lås-ikonen (om det finns en varning) och välj att fortsätta till säker anslutning"],
            "start_prompt": "När jag ska logga in på min bank så säger datorn att anslutningen inte är säker och stänger ner hela rasket! Jag blir så nervös av sånt här."
        }
    ],
    # --- LEVEL 2 PROBLEMS (Index 1) - Based on "Svårighetsgrad 2" ---
    [
        {
            "id": "L2_P001",
            "beskrivning": "Dator 'Packard Bell iMedia S2883' chassi blir mycket varmt vid beröring. Systemet stängs plötsligt av efter ca 30 minuters användning. Vid omstart, ibland meddelande 'CPU Fan Error' i BIOS. Fläktljudet är högt och damm synligt i ventilationsgaller bak och på sidan.",
            "losning_nyckelord": ["Datorn överhettas på grund av damm och dålig kylning", "rengör datorns fläktar och kylflänsar från damm", "blås bort dammet ur datorn med tryckluft"],
            "start_prompt": "Min datorlåda blir så varm att man nästan kan koka ägg på den, och fläktarna låter som en hårtork! Sen stänger den av sig mitt i allt, precis när Måns har lagt sig tillrätta i knät."
        },
        {
            "id": "L2_P002",
            "beskrivning": "E-postprogram 'Mozilla Thunderbird 60.9.1' visar statusfältmeddelande: 'Kvoten överskriden för kontot ulla.andersson@gmail.com (105% av 15GB). Felkod: MBX_FULL_001'. Nya e-postmeddelanden mottas inte. Utkorgen visar 'Skickar...'.",
            "losning_nyckelord": ["E-postlådan på servern är full", "logga in på webbmailen och ta bort gamla/stora mejl", "töm skräpposten och radera meddelanden med stora bilagor från servern"],
            "start_prompt": "Nu säger min e-post att brevlådan är proppfull och nya brev kommer inte in! Jag som väntar på ett recept på sockerkaka från min syster."
        },
        {
            "id": "L2_P003",
            "beskrivning": "Försök att öppna 'Försäkringskassan_Beslut.pdf' (nedladdad fil) i 'Windows 7' resulterar i dialogruta: 'Windows kan inte öppna den här filtypen (.pdf). För att öppna filen behöver Windows veta vilket program du vill använda...'. Inget PDF-program installerat.",
            "losning_nyckelord": ["Program för att visa PDF-filer saknas på datorn", "installera Adobe Acrobat Reader eller annan PDF-läsare", "ladda hem ett gratisprogram för att öppna PDF-dokument"],
            "start_prompt": "Jag har fått ett viktigt dokument från myndigheten, men datorn säger att den inte vet hur den ska öppna det. Det är som att den inte har rätt glasögon på sig!"
        },
        {
            "id": "L2_P004",
            "beskrivning": "Webbsida 'Blomsterlandet.se' i 'Internet Explorer 11'. Knappar ('Lägg i varukorg', 'Visa mer') är utgråade/inaktiva och reagerar inte på klick. Gul varningstriangel i statusfältet med text 'Fel på sidan. Detaljer: Objekt stöder inte egenskapen eller metoden 'addEventListener''.",
            "losning_nyckelord": ["Webbläsaren blockerar eller kan inte köra nödvändiga skript (JavaScript) på sidan", "aktivera JavaScript i webbläsarens inställningar", "kontrollera säkerhetsinställningar för skript i Internet Explorer"],
            "start_prompt": "Jag skulle beställa nya penséer på en webbsida, men alla knappar är alldeles grå och går inte att trycka på. Det är som att de har somnat!"
        },
        {
            "id": "L2_P005",
            "beskrivning": "Systemvarning i 'Windows 10' aktivitetsfält: 'Lågt diskutrymme på Lokal Disk (C:). Du har nästan slut på utrymme på den här enheten (250MB ledigt av 120GB).' Försök att spara bild från kamera 'Canon PowerShot A590 IS' till 'Mina Bilder' ger felmeddelande 'Disken är full'.",
            "losning_nyckelord": ["Hårddisken (C:) är nästan full", "frigör diskutrymme genom att ta bort onödiga filer och program", "använd Diskrensning i Windows för att ta bort temporära filer"],
            "start_prompt": "Datorn plingar och piper och säger att lagringsutrymmet nästan är slut, och nu kan jag inte spara de nya bilderna på Måns när han jagade en fjäril. Det är ju katastrof!"
        },
        {
            "id": "L2_P006",
            "beskrivning": "Videosamtal i 'Skype 7.40' på bärbar 'Asus X550C'. WiFi-router 'Technicolor TG799vac' placerad i vardagsrum. WiFi-signalstyrka i Windows: 5/5 streck i kök/vardagsrum, 1/5 (rött) streck i sovrum. Samtal visar 'Anslutningen är svag. Återansluter...' och bryts ofta i sovrummet.",
            "losning_nyckelord": ["WiFi-signalen är för svag i sovrummet", "flytta datorn närmare WiFi-routern", "undvik fysiska hinder (väggar, möbler) mellan dator och router"],
            "start_prompt": "När jag pratar med barnbarnen i det där video-programmet så bryts det hela tiden om jag går in i sovrummet. De säger att jag bara blir en massa fyrkanter."
        },
        {
            "id": "L2_P007",
            "beskrivning": "Skrivare 'HP DeskJet 2710e' har stadig grön strömlampa och är ansluten via USB-kabel. I Windows 'Enheter och skrivare' är ikonen för 'HP DeskJet 2700 series' gråtonad med status 'Frånkopplad'. Utskriftsjobb fastnar i kön med status 'Fel - Skriver ut'.",
            "losning_nyckelord": ["Skrivaren är inte korrekt ansluten eller känns inte igen av Windows", "starta om både dator och skrivare", "kontrollera USB-kabeln och prova att ta bort och lägga till skrivaren igen i Windows"],
            "start_prompt": "Min skrivare är alldeles grå inne i datorn, fast lampan på själva apparaten lyser så snällt grönt. Det är som att de inte pratar med varandra!"
        },
        {
            "id": "L2_P008",
            "beskrivning": "Antivirusprogrammet 'F-Secure SAFE' visar en varning: 'Hot blockerat! Filen C:\\MinaBilder\\Semester_2023\\Måns_sover_sött.jpg har identifierats som misstänkt och har satts i karantän.' Fotoprogrammet kan inte längre visa bilden och Måns favoritbild är borta från albumet.",
            "losning_nyckelord": ["Antivirusprogrammet har felaktigt identifierat en ofarlig fil som ett hot (falskt positivt)", "lägg till ett undantag för filen eller mappen i F-Secure SAFE:s inställningar", "kontrollera F-Secure SAFE:s karantän och återställ filen därifrån om den är ofarlig"],
            "start_prompt": "Hjälp! Mitt skyddsprogram på datorn, det där F-Secure, har blivit helt tokigt! Det säger att en av mina bästa bilder på Måns när han sover så sött är farlig och nu kan jag inte se den längre! Men jag vet att den är snäll!"
        },
        {
            "id": "L2_P009",
            "beskrivning": "Hörlurar 'Philips SHP2000' anslutna till grönt 3.5mm ljuduttag på framsidan av stationär dator. Ljud från 'Foobar2000' spelas fortfarande via datorns monitorhögtalare ('Dell S2421H' via HDMI). Windows Ljudinställningar > Uppspelning: 'Högtalare (Realtek High Definition Audio)' är standardenhet, 'Hörlurar' listas men är inte standard.",
            "losning_nyckelord": ["Hörlurarna är inte valda som standardljudenhet i Windows", "ändra standarduppspelningsenhet till hörlurarna i ljudinställningarna", "högerklicka på hörlurarna i ljudpanelen och välj 'Ange som standardenhet'"],
            "start_prompt": "Jag sätter i mina fina hörlurar för att inte störa Måns när han sover, men ljudet fortsätter ändå att komma ur de stora högtalarna! Det är ju inte klokt."
        },
        {
            "id": "L2_P010",
            "beskrivning": "Bankdosa 'Vasco Digipass 260' (Swedbank, äldre modell) visar 'LOW BATT' på LCD-displayen. Stängs av under inmatning av engångskod för bankinloggning. Använder ett CR2032-batteri som går att byta.",
            "losning_nyckelord": ["Batteriet i bankdosan är slut", "byt ut det gamla CR2032-batteriet i säkerhetsdosan mot ett nytt", "öppna batteriluckan och ersätt batteriet"],
            "start_prompt": "Min lilla bank-dosa blinkar något om 'LOW BATT' och stänger av sig mitt i när jag ska skriva in koden. Nu kommer jag väl inte åt mina pengar till fikat!"
        }
    ],
    # --- LEVEL 3 PROBLEMS (Index 2) - Based on "Svårighetsgrad 3" ---
    [
        {
            "id": "L3_P001",
            "beskrivning": "Blåskärm (BSOD) visas slumpmässigt med text: ':( Ditt system stötte på ett problem... Stoppkod: MEMORY_MANAGEMENT'. Dator: 'Dell OptiPlex 7010 SFF' med 2x2GB DDR3 RAM-moduler ('Kingston KVR13N9S6/2'). Systemet startar om automatiskt. Körning av Windows Minnesdiagnostik (standardtest) visar inga fel direkt.",
            "losning_nyckelord": ["Problem med RAM-minnet (arbetsminnet)", "kör en grundligare minnesdiagnostik som MemTest86 från USB", "prova med en minnesmodul i taget i olika platser för att isolera felet"],
            "start_prompt": "Hemska apparat! Skärmen blir alldeles blå med ett ledset ansikte och en massa text om 'MEMORY', sen startar den om sig själv. Det är som att den har tappat minnet, stackarn."
        },
        {
            "id": "L3_P002",
            "beskrivning": "Vid uppspelning av '.MKV'-fil (H.264 codec, 1080p) i 'VLC Media Player 3.0.8' fylls bilden med gröna/rosa fyrkantiga artefakter och pixelfel, särskilt vid snabba scener. Ljudet fortsätter normalt. Grafikkort: 'NVIDIA GeForce GT 710 2GB'. Drivrutinsversion 391.35 (från 2018).",
            "losning_nyckelord": ["Grafikkortets drivrutiner är föråldrade eller korrupta", "uppdatera grafikkortets drivrutiner till senaste stabila versionen från NVIDIA:s webbplats", "avinstallera gamla drivrutiner och installera nya rena drivrutiner"],
            "start_prompt": "När jag försöker titta på en film jag fått från barnbarnen så fylls hela skärmen av konstigt flimmer i alla möjliga färger, och bilden säger att den har hängt sig. Det ser ut som Måns har lekt med färgburkarna!"
        },
        {
            "id": "L3_P003",
            "beskrivning": "USB-minne 'Kingston DataTraveler G4 8GB' har en liten fysisk skrivskyddsbrytare (låsikon) på sidan, som är i 'låst' läge. Tillåter läsning av filer men inte radering eller formatering. Windows felmeddelande: 'Disken är skrivskyddad. Ta bort skrivskyddet eller använd en annan disk.'",
            "losning_nyckelord": ["USB-minnets fysiska skrivskydd är aktiverat", "skjut den lilla låsknappen på minnesstickans sida till olåst läge", "inaktivera 'write-protect' reglaget på USB-enheten"],
            "start_prompt": "Min lilla minnes-sticka går bra att titta på, men jag kan inte kasta något skräp från den – den säger att den är 'skriv-skyddad'. Har den fått någon form av skyddsvakt?"
        },
        {
            "id": "L3_P004",
            "beskrivning": "Bärbar dator 'HP Pavilion G6-2250so' med originalladdare 'HP 65W Smart AC Adapter (modell PPP009L-E)'. Batteriikon i Windows aktivitetsfält visar '0% tillgängligt (nätansluten, laddar inte)'. Laddningslampan på datorn (bredvid strömintaget) lyser ej. Batteriet är 'HP HSTNN-LB0W'. Datorn fungerar med laddaren i men stängs av direkt om sladden dras ur.",
            "losning_nyckelord": ["Laddaren eller batteriet är defekt, eller dålig anslutning", "prova en annan kompatibel HP-laddare", "kontrollera om batteriet är korrekt isatt och överväg att byta batteri"],
            "start_prompt": "Batteri-symbolen på min bärbara dator säger 'ansluten men laddas inte' fastän sladden sitter där den ska. Det är som att den vägrar äta sin ström!"
        },
        {
            "id": "L3_P005",
            "beskrivning": "E-postprogram 'Microsoft Outlook 2016' (ansluten till Telia IMAP-konto: mailin.telia.com) uppvisar återkommande dialogruta: 'Ange nätverkslösenord för ulla.ulla@telia.com'. E-post i 'Utkorgen' har status 'Väntar på att skickas (fel 0x800CCC0F)'. Lösenordet är nyligen ändrat på Telias webbmail och fungerar där.",
            "losning_nyckelord": ["Sparat lösenord i Outlook är felaktigt efter byte på webbmailen", "uppdatera det sparade lösenordet i Outlooks kontoinställningar", "gå till Arkiv > Kontoinställningar, välj kontot och ange det nya lösenordet"],
            "start_prompt": "Mitt mejl-program frågar efter lösenordet om och om igen, och inga av mina brev till syrran om Måns tokigheter går iväg. Det är så frustrerande!"
        },
        {
            "id": "L3_P006",
            "beskrivning": "Under videosamtal i 'Skype 8.96' på 'Lenovo IdeaPad 3 15IIL05' (med inbyggd mikrofon och högtalare) rapporterar motparter tydligt eko av sin egen röst. Mikrofonsymbolen i Skype reagerar starkt på ljud från datorns högtalare. Ingen headset används. Problemet uppstår även vid låg högtalarvolym.",
            "losning_nyckelord": ["Ljud från högtalarna plockas upp av mikrofonen (rundgång)", "använd ett headset (hörlurar med mikrofon) för att isolera ljudet", "sänk högtalarvolymen och mikrofonkänsligheten, eller använd Skypes ekoreducering om tillgängligt"],
            "start_prompt": "När jag pratar med barnbarnen på det där video-samtalet så hör alla sin egen röst som ett eko från min dator. Det låter som vi är i en stor kyrka!"
        },
        {
            "id": "L3_P007",
            "beskrivning": "Textredigeringsprogram 'Microsoft Word 2013' fryser ofta (fönstret visar '(Svarar inte)') vid arbete med stora dokument eller när autopsarning sker. Meddelande 'Word försöker återskapa din information...' visas ibland. Hårddisk 'Seagate Barracuda 1TB ST1000DM003' ger ifrån sig återkommande klickande/höga arbetsljud. CrystalDiskInfo visar 'Varning' för disken (t.ex. 'Reallocated Sectors Count').",
            "losning_nyckelord": ["Hårddisken har problem eller är på väg att gå sönder", "kör en fullständig diskkontroll (chkdsk /f /r) på systemdisken", "säkerhetskopiera viktiga filer omedelbart och överväg att byta ut hårddisken"],
            "start_prompt": "Mitt skriv-program, där jag skriver ner mina memoarer om Måns, fryser hela tiden och visar 'återskapar fil' medan datorlådan knastrar och låter konstigt. Tänk om allt försvinner!"
        },
        {
            "id": "L3_P008",
            "beskrivning": "Skrivare 'Brother HL-L2350DW'. Vid dubbelsidig utskrift från Word med inställningen 'Vänd längs långa kanten (standard)' blir texten på baksidan (andra sidan) av pappret uppochnedvänd i förhållande till framsidan. Alternativet 'Vänd längs korta kanten' finns i skrivarens utskriftsdialog.",
            "losning_nyckelord": ["Fel inställning för pappersvändning vid dubbelsidig utskrift", "välj 'vänd längs korta kanten' i utskriftsinställningarna för korrekt orientering på baksidan", "justera duplex-inställningen för 'short-edge binding'"],
            "start_prompt": "När jag försöker skriva ut mitt kakrecept på båda sidor av pappret så kommer texten på baksidan alldeles upp-och-ned! Hur ska någon kunna läsa det?"
        },
        {
            "id": "L3_P009",
            "beskrivning": "Surfplatta 'Samsung Galaxy Tab A7 Lite (SM-T220)' med Android 11. Bilden förblir i porträttläge trots fysisk rotation av enheten. Ikon för 'Automatisk rotering' (rektangel med pilar runt) i snabbinställningspanelen är gråtonad och visar 'Porträtt' (vilket indikerar att automatisk rotering är avstängd).",
            "losning_nyckelord": ["Automatisk skärmrotation är avstängd i systeminställningarna", "tryck på ikonen för skärmrotation i snabbinställningspanelen för att aktivera den", "gå till Inställningar > Skärm > och slå på 'Automatisk rotering'"],
            "start_prompt": "Min lilla surfplatta, som jag tittar på Måns-videor på, vägrar att vrida på bilden när jag vänder på plattan. Den är envis som en gammal get!"
        },
        {
            "id": "L3_P010",
            "beskrivning": "Engångskod via SMS till telefon 'Doro 8080' (Android Go) avvisas av bankens (Handelsbanken) webbplats med meddelande 'Ogiltig kod. Koden kan vara för gammal eller redan använd.' Telefonens klocka visar 10:35, medan datorns klocka (synkad med NTP) visar 10:32. Inställningen 'Använd nätverksbaserad tid' är avstängd på telefonen.",
            "losning_nyckelord": ["Telefonens klocka är osynkroniserad vilket gör SMS-koden ogiltig för tidskänsliga system", "slå på 'Automatisk datum och tid' (nätverksbaserad tid) i telefonens inställningar", "kontrollera att telefonens tid och tidszon är korrekta och synkroniserade"],
            "start_prompt": "Bank-koden som kommer i ett SMS till min telefon avvisas direkt som 'för gammal' när jag skriver in den på datorn. Det är som att de lever i olika tidsåldrar!"
        }
    ],
    # --- LEVEL 4 PROBLEMS (Index 3) - Based on "Nivå B" ---
    [
        {
            "id": "L4_P001",
            "beskrivning": "Stationär dator 'HP Compaq Elite 8300 SFF' ger tre korta ljudsignaler (beep code) vid startförsök. Skärmen förblir svart (ingen BIOS-logotyp eller bild). Strömlampan på datorn lyser grönt. RAM-moduler: 2x 'Kingston KVR1333D3N9/2G' (2GB DDR3 PC3-10600). HP:s dokumentation för beep codes indikerar ofta minnesfel vid 3 korta pip.",
            "losning_nyckelord": ["Fel på RAM-minnet eller dålig kontakt med minnesmodulerna", "ta ut och sätt tillbaka minneskorten ordentligt (reseat)", "prova med en minnesmodul i taget i olika minnesplatser för att identifiera felaktig modul eller plats"],
            "start_prompt": "När jag trycker på startknappen på min stora datorlåda piper den bara tre gånger, kort och ilsket, och fönsterskärmen är helt svart. Den verkar ha fått hicka!"
        },
        {
            "id": "L4_P002",
            "beskrivning": "Nya bläckpatroner 'Epson T0711' (svart) och 'T0712/3/4' (färg) installerade i 'Epson Stylus DX4400' multifunktionsskrivare. Skrivaren matar fram helt blanka papper vid utskriftsförsök. En orange skyddstejp med texten 'PULL' observeras på ovansidan av en av de nyinstallerade färgpatronerna, täckande ett litet lufthål/ventilationsöppning.",
            "losning_nyckelord": ["Skyddstejp på bläckpatronerna blockerar bläcktillförseln eller ventilationen", "avlägsna all skyddstejp och plastremsor från nya bläckpatroner innan installation", "se till att lufthålen på patronerna är helt öppna"],
            "start_prompt": "Jag har satt i nya fina färgpatroner i skrivaren, men pappren kommer ut alldeles tomma, inte en prick! Det är som att färgen har rymt."
        },
        {
            "id": "L4_P003",
            "beskrivning": "På bärbar 'Acer Aspire 5 A515-54G' med Windows 10 visas en flygplansikon i aktivitetsfältet istället för WiFi-signalikonen. Nätverksinställningar visar 'Flygplansläge: På'. Fn+F3 (funktionstangent med flygplanssymbol) har ingen effekt. WiFi-knapp på sidan saknas. Datorn kan inte ansluta till några trådlösa nätverk.",
            "losning_nyckelord": ["Flygplansläget är aktiverat i Windows och blockerar trådlösa anslutningar", "stäng av Flygplansläge via Nätverks- & Internetinställningar i Windows", "klicka på flygplansikonen i aktivitetsfältet och välj att stänga av läget därifrån"],
            "start_prompt": "Min bärbara dator har fått för sig att den är ett flygplan! Det har dykt upp en liten flygplansbild bredvid klockan, och nu ser jag inga trådlösa nät längre. Den kanske vill flyga söderut med Måns?"
        },
        {
            "id": "L4_P004",
            "beskrivning": "Halvtransparent text ('vattenstämpel') i nedre högra hörnet på skärmen på en dator med 'Windows 10 Home': 'Aktivera Windows. Gå till Inställningar för att aktivera Windows.' Operativsystemet ominstallerades nyligen från en generisk USB-installationsmedia. Produktnyckel ej angiven under installation och ingen digital licens kopplad till Microsoft-konto.",
            "losning_nyckelord": ["Windows-installationen är inte aktiverad med en giltig licens", "ange en giltig Windows 10 produktnyckel i Systeminställningar > Aktivering", "köp en Windows 10-licens eller använd en befintlig digital licens kopplad till ditt Microsoft-konto"],
            "start_prompt": "Det står en suddig text i hörnet på min fönsterskärm som säger att jag måste 'aktivera' systemet. Vad menar den med det? Ska jag klappa den lite?"
        },
        {
            "id": "L4_P005",
            "beskrivning": "Stationär dator 'Fujitsu Siemens Scaleo P' (moderkort 'ASUS P5KPL-AM'). Systemklockan i BIOS (och därmed Windows) återställs konsekvent till 01-01-2002 00:00 vid varje omstart efter att datorn varit helt strömlös (strömkabel urdragen). Moderkortet använder ett 'CR2032' 3V litiumbatteri för att bibehålla CMOS-inställningar.",
            "losning_nyckelord": ["CMOS-batteriet på moderkortet är urladdat eller defekt", "byt ut det lilla runda batteriet (CR2032) på datorns moderkort", "sätt i ett nytt, fräscht BIOS-batteri"],
            "start_prompt": "Min dator har blivit alldeles virrig i tiden! Varje gång jag stänger av den helt så hoppar klockan tillbaka till år 2001. Den kanske längtar tillbaka till när Måns var kattunge."
        },
        {
            "id": "L4_P006",
            "beskrivning": "Bläckstråleskrivare 'Canon PIXMA MG3650' (patroner 'PG-540' svart / 'CL-541' färg) producerar utskrifter med tjocka, jämnt fördelade mörka horisontella ränder som delvis täcker texten, vilket tyder på igentäppta munstycken. 'Djuprengöring av skrivhuvud' via skrivarens programvara har körts flera gånger utan märkbar förbättring.",
            "losning_nyckelord": ["Skrivhuvudets munstycken är igentäppta och behöver rengöras", "kör skrivhuvudsrengöring (eventuellt flera gånger med paus emellan)", "om rengöring inte hjälper kan patronen eller skrivhuvudet vara defekt"],
            "start_prompt": "Mina utskrifter från skrivaren får tjocka mörka ränder tvärs över texten, som om någon har ritat med en bred svart tuschpenna över alltihop. Det ser inte klokt ut!"
        },
        {
            "id": "L4_P007",
            "beskrivning": "Ljuduppspelning (från 'Spotify') via högtalarsystem 'Logitech Z313 2.1' (anslutet till grönt ljuduttag). Ljud endast från höger satellithögtalare, vänster är helt tyst. Subwoofern fungerar. Windows ljudbalans i 'Realtek HD Audio Manager' (eller Windows ljudinställningar) visar: Höger kanal: 100%, Vänster kanal: 0%.",
            "losning_nyckelord": ["Ljudbalansen mellan höger och vänster kanal är felinställd", "justera ljudbalansen till mitten (50% för varje kanal) i ljudinställningarna", "centrera stereobalansen för uppspelningsenheten"],
            "start_prompt": "När jag spelar min favoritmusik så hörs den bara i den högra högtalaren – den vänstra är alldeles tyst! Det är som att den har tagit semester."
        },
        {
            "id": "L4_P008",
            "beskrivning": "Extern hårddisk 'WD Elements 2TB Portable' (Modell: WDBU6Y0020BBK, P/N: WDBUZG0020BBK-WESN, ansluten med enkel USB 3.0 kabel) avger repetitivt klickljud vid anslutning till USB 2.0-port på äldre dator. Syns kortvarigt i 'Den här datorn' och försvinner. Denna typ av disk kan kräva mer ström än vad en enskild USB 2.0-port kan leverera.",
            "losning_nyckelord": ["Extern hårddisk får inte tillräckligt med ström från USB-porten", "använd en USB Y-kabel för att ansluta till två USB-portar för extra ström", "testa med en USB-hubb som har egen strömförsörjning"],
            "start_prompt": "Min yttre hårddisk, den där lilla lådan jag sparar bilder på Måns i, klickar och försvinner direkt när jag kopplar in den i den gamla datorn. Den kanske är hungrig?"
        },
        {
            "id": "L4_P009",
            "beskrivning": "Bärbar dator 'Dell Inspiron 15 5559' (med Intel HD Graphics 520) ansluten till 'Samsung UE40H6400' TV via HDMI-kabel. Bild visas korrekt på TV:n, men ljud spelas fortfarande från datorns inbyggda högtalare. I Windows Ljudinställningar > Uppspelning visas 'Högtalare (Realtek High Definition Audio)' som standardenhet, medan 'Samsung TV (Intel(R) Display Audio)' listas men är 'Inaktiverad' eller 'Inte standard'.",
            "losning_nyckelord": ["HDMI-ljudutgången är inte vald som standardenhet i Windows", "aktivera TV:n (HDMI) som ljudenhet och ställ in den som standard i ljudinställningarna", "högerklicka på HDMI-ljudenheten (Samsung TV) i ljudpanelen och välj 'Aktivera' och sedan 'Ange som standardenhet'"],
            "start_prompt": "Jag har kopplat min bärbara dator till den stora teven för att se på film, och jag får fin bild, men ljudet kommer fortfarande bara från den lilla datorn! Det är ju inte meningen."
        },
        {
            "id": "L4_P010",
            "beskrivning": "Surfplatta 'iPad Air 2 (Modell A1566, MGKL2KN/A)' med iOS 15 meddelar 'Lagringsutrymme nästan fullt'. Under 'Inställningar > Allmänt > iPad-lagring' upptas 10GB av 'Bilder > Nyligen raderade' trots att många bilder och videor har raderats från Bilder-appen. Albumet 'Nyligen raderade' i Bilder-appen innehåller dessa objekt och de raderas inte automatiskt direkt.",
            "losning_nyckelord": ["Raderade bilder/videor ligger kvar i albumet 'Nyligen raderade' och tar upp plats", "gå in i Bilder-appen > Album > Nyligen raderade och välj 'Välj' sedan 'Radera alla' för att permanent ta bort objekten", "töm papperskorgen för bilder manuellt"],
            "start_prompt": "Min platta säger att lagringen är full fast jag har raderat massor av gamla bilder på Måns när han var liten. Var tar de vägen egentligen, de där raderade bilderna?"
        }
    ],
    # --- LEVEL 5 PROBLEMS (Index 4) - Based on "Nivå A" ---
    [
        {
            "id": "L5_P001",
            "beskrivning": "Vid uppstart, direkt efter BIOS POST, visas svart skärm med text: 'S.M.A.R.T. Status BAD, Backup and Replace. Press F1 to Resume.' Hårddisk: 'Toshiba DT01ACA100 1TB' i 'Acer Veriton M2630G'. Windows startar efter F1-tryckning men är märkbart långsamt och systemet hänger sig ibland.",
            "losning_nyckelord": ["Hårddisken rapporterar kritiska S.M.A.R.T.-fel och är på väg att gå sönder", "säkerhetskopiera alla viktiga data omedelbart och byt ut den felande hårddisken", "installera en ny hårddisk och återställ systemet från backup eller nyinstallation"],
            "start_prompt": "Min stackars dator varnar för att 'Hårddisken mår dåligt – byt snarast!' redan innan den hunnit starta ordentligt. Den ber mig trycka F1 för att fortsätta, men det känns inte bra alls. Tänk om alla mina bilder på Måns försvinner!"
        },
        {
            "id": "L5_P002",
            "beskrivning": "Bärbar dator 'Microsoft Surface Laptop 3' (med Windows 10 Pro och BitLocker-diskkryptering aktiverad på systemenheten) visar blå skärm vid start: 'BitLocker-återställning. Ange återställningsnyckeln för den här enheten för att fortsätta.' Nyckel-ID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX visas. Användaren har inte sparat återställningsnyckeln och den finns inte på Microsoft-kontot.",
            "losning_nyckelord": ["BitLocker-diskkryptering kräver återställningsnyckel efter systemändring eller misstänkt manipulation", "leta efter en utskriven BitLocker-återställningsnyckel eller en som sparats på USB-minne vid installationen", "om nyckeln är förlorad kan data vara oåtkomliga utan ominstallation"],
            "start_prompt": "Hjälp! Min fina nya bärbara dator har fått fnatt! Den visar en blå skärm och ber mig skriva in en jättelång 'återställningskod' innan Windows vill öppnas. Jag har ingen aning om var jag har en sådan kod!"
        },
        {
            "id": "L5_P003",
            "beskrivning": "Äldre dator med 'Windows XP Professional'. Efter BIOS POST (Phoenix AwardBIOS v6.00PG), visas svart skärm med text: 'NTLDR is missing. Press Ctrl+Alt+Del to restart.' CD-ROM är satt som första startenhet i BIOS, hårddisk 'Maxtor DiamondMax Plus 9 80GB ATA/133' som andra. Försök att starta från Windows XP installations-CD misslyckas också; CD:n verkar inte läsas.",
            "losning_nyckelord": ["Felaktig startenhetsordning (boot order) i BIOS eller problem med startfilerna på hårddisken", "gå in i BIOS-inställningarna och ställ in hårddisken (HDD) som första startenhet", "kontrollera att hårddisken detekteras korrekt i BIOS och försök reparera startsektorn med XP-CD (om CD-läsaren fungerar)"],
            "start_prompt": "Min gamla trotjänare till dator säger bara 'NTLDR saknas' och vägrar gå vidare från en svart skärm. Det låter som en viktig del har sprungit bort. Kanske Måns har gömt den?"
        },
        {
            "id": "L5_P004",
            "beskrivning": "Stationär dator (moderkort 'Gigabyte GA-Z97X-Gaming 5', CPU 'Intel Core i7-4790K'). Efter kort strömavbrott startar datorn (fläktar snurrar på maxhastighet, LED-lampor på moderkortet lyser) men skärmen får ingen signal ('No Input'). Debug LED på moderkort visar '00' (vilket ofta indikerar CPU-problem eller BIOS-korruption). Försök med CMOS-reset via jumper har gjorts utan effekt.",
            "losning_nyckelord": ["BIOS/CMOS-inställningarna är korrupta eller moderkortet har problem efter strömavbrott", "utför en grundlig CMOS-återställning genom att ta ur moderkortsbatteriet en stund medan datorn är strömlös", "kontrollera alla anslutningar på moderkortet och testa med minimal konfiguration"],
            "start_prompt": "Efter ett litet strömavbrott här hemma så snurrar fläktarna i datorn som tokiga, men fönsterskärmen tänds aldrig. Den är helt svart och säger 'Ingen signal'. Det är som att den har blivit rädd för mörkret."
        },
        {
            "id": "L5_P005",
            "beskrivning": "Utskrift från 'WordPad' i 'Windows 10' till 'HP LaserJet P1102w' (nyligen ansluten via USB) resulterar i sidor fyllda med obegripliga tecken och symboler (t.ex. 'ÿØÿà€JFIF€€Æ @#$!%^&*'). Windows använde automatiskt 'Microsoft IPP Class Driver' vid installationen. Skrivaren fungerade korrekt på en tidigare dator med HP:s egna, modellanpassade drivrutiner.",
            "losning_nyckelord": ["Felaktig eller generisk skrivardrivrutin används av Windows", "ladda ner och installera den officiella, modellanpassade skrivardrivrutinen från HP:s webbplats för LaserJet P1102w", "avinstallera den nuvarande drivrutinen och installera rätt PCL- eller PostScript-drivrutin"],
            "start_prompt": "När jag försöker skriva ut mina dikter om Måns så blir all text på pappret bara en massa obegripliga krumelurer och konstiga tecken. Det ser ut som katten själv har varit framme och skrivit!"
        },
        {
            "id": "L5_P006",
            "beskrivning": "Nyinstallerad 'Windows 7 Ultimate (utan Service Pack, 32-bitars)'. HTTPS-webbplatser (t.ex. google.com, microsoft.com) kan ej öppnas. 'Internet Explorer 8' visar 'Internet Explorer kan inte visa webbsidan' eller certifikatfel 'Felkod: DLG_FLAGS_INVALID_CA / INET_E_SECURITY_PROBLEM'. Systemtid/datum är korrekt. Windows Update fungerar inte ('kan inte söka efter nya uppdateringar', felkod 80072EFE). Detta beror på saknade rotcertifikat och TLS/SSL-protokollstöd.",
            "losning_nyckelord": ["Operativsystemet saknar uppdaterade rotcertifikat och modernt TLS/SSL-stöd", "installera Windows 7 Service Pack 1 och alla efterföljande kumulativa uppdateringar manuellt (t.ex. via Microsoft Update Catalog)", "importera aktuella rotcertifikat och aktivera TLS 1.2 stöd via registerändringar eller Microsoft Easy Fix"],
            "start_prompt": "Inga säkra sidor på internet vill öppnas på min nyinstallerade dator – allt bara klagar på ogiltiga 'certifikat' fast datumet på datorn stämmer. Det är som att alla dörrar är låsta!"
        },
        {
            "id": "L5_P007",
            "beskrivning": "System med 8GB RAM ('Corsair Vengeance LPX DDR4 2400MHz'), 50GB ledigt på C: (SSD 'Samsung 860 EVO 250GB'). Vid användning av 'Google Chrome' (många flikar) och 'Adobe Photoshop Elements 2021' samtidigt, visas Windows-meddelande: 'Datorn har ont om minne. Spara dina filer och stäng dessa program.' Program kraschar. Växlingsfil (pagefile.sys) är systemhanterad, aktuell storlek är liten (t.ex. 2GB).",
            "losning_nyckelord": ["Systemets växlingsfil (virtuellt minne) är för liten för den aktuella arbetsbelastningen", "öka storleken på växlingsfilen manuellt i Windows systeminställningar (t.ex. till 1.5x RAM)", "överväg att utöka det fysiska RAM-minnet om problemet kvarstår frekvent"],
            "start_prompt": "Min dator gnäller om att den har för lite 'virtuellt minne' och stänger ner mina program när jag försöker redigera bilder på Måns och ha många internetsidor öppna samtidigt. Vad menar den med virtuellt, är det låtsasminne?"
        },
        {
            "id": "L5_P008",
            "beskrivning": "Nytt USB-headset 'Logitech H390'. Ljud i hörlurar fungerar korrekt i 'Windows 10'. Under 'Ljud > Inspelning' (högerklicka på ljudikonen > Ljud) listas endast 'Mikrofon (Realtek High Definition Audio)' och 'Stereomix'. Ingen 'Logitech USB Headset' mikrofon synlig trots att headsetet visas i Enhetshanteraren under 'Ljud-, video- och spelenheter' utan fel. 'Visa inaktiverade enheter' är markerat.",
            "losning_nyckelord": ["Headsetets mikrofon är inte aktiverad eller vald som standardinspelningsenhet", "kontrollera att mikrofonen på headsetet inte är fysiskt avstängd (mute-knapp)", "gå till Enhetshanteraren, avinstallera headsetet och låt Windows installera om det; välj sedan som standard i Ljudinställningar"],
            "start_prompt": "Jag har köpt en ny fin hörlur med mikrofon för att kunna prata med barnbarnen, men mikrofonen syns inte i listan i datorn! Ljudet i lurarna fungerar, men de hör inte mig. Det är ju tråkigt."
        },
        {
            "id": "L5_P009",
            "beskrivning": "Videouppspelning ('YouTube HTML5 player', 'SVT Play') i 'Mozilla Firefox 91 ESR' på 'Windows 10' (version 21H2) visar endast ljud; bildrutan är helt grå eller svart. Problem uppstod efter en Windows-uppdatering ('KB500XXXX'). Grafikkort: 'Intel HD Graphics 4000' (drivrutin från 2017). Maskinvaruacceleration i Firefox är aktiverad. Problemet kvarstår i andra webbläsare.",
            "losning_nyckelord": ["Problem med videokodekar eller grafikdrivrutiner efter systemuppdatering", "installera ett omfattande kodekpaket (t.ex. K-Lite Codec Pack Full)", "försök att inaktivera/aktivera maskinvaruacceleration i webbläsarens inställningar eller systemets grafikinställningar; sök efter nyare (eller äldre stabila) grafikdrivrutiner"],
            "start_prompt": "När jag försöker titta på roliga kattklipp på internet så hör jag bara ljudet – bilden är alldeles grå! Det är ju det roligaste som försvinner. Måns blir också besviken."
        },
        {
            "id": "L5_P010",
            "beskrivning": "Stationär dator (moderkort 'ASUS P8P67 LE', CPU 'Intel Core i5-2500K', grafikkort 'NVIDIA GeForce GTX 560 Ti') avger en lång och två korta ljudsignaler (AMI BIOS beep code som indikerar grafikkortsfel/ingen bildskärm ansluten eller felaktigt kort) vid start. Skärmen förblir svart (ingen signal detekteras via DVI-port). Grafikkortets fläktar snurrar. Kortet sitter i översta PCIe x16-porten och har extra strömkablar anslutna.",
            "losning_nyckelord": ["Grafikkortet har dålig kontakt, är felaktigt anslutet eller defekt", "ta ur och sätt tillbaka grafikkortet ordentligt i PCIe-porten (reseat)", "kontrollera att alla extra strömanslutningar till grafikkortet sitter fast; testa med ett annat grafikkort om möjligt"],
            "start_prompt": "Min dator startar med ett långt pip och sedan två korta, som en ledsen fågel, och fönsterskärmen förblir alldeles svart. Den vill nog inte vakna idag."
        }
    ]
]

# Helper to get the number of levels
NUM_LEVELS = len(PROBLEM_CATALOGUES)