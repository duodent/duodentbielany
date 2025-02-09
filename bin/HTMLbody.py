html_body_dict = {
    'handle_visit_request': """
        <html>
            <style>
                .time_area {
                    display: flex;
                    flex-wrap: wrap; /* Elementy zawijają się do nowej linii */
                    gap: 0.5px; /* Bardzo mała przerwa między elementami */
                    justify-content: flex-start;
                    align-items: center;
                    border-radius: 5px;
                }

                .time_box {
                    display: inline-block; /* Kluczowe: pozwala na umieszczanie wielu elementów w linii */
                    color: #fff;
                    font-size: 11px; /* Trochę mniejsza czcionka */
                    margin: 0.5px; /* Bardzo małe marginesy */
                    white-space: nowrap; /* Zapobiega łamaniu się tekstu */
                }

                .time_link {
                    text-decoration: none !important; /* Usunięcie podkreślenia */
                    color: white !important; /* Biały kolor tekstu */
                    background-color: #24363f;
                    padding: 4px 6px; /* Zmniejszona wysokość i szerokość */
                    border-radius: 4px;
                    font-size: 11px;
                    width: 40px; /* Stała szerokość pasująca do 5 znaków */
                    height: 16px; /* Wysokość 2x mniejsza */
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    transition: color 0.3s ease-in-out, background 0.3s ease-in-out;
                }

                .time_link:visited {
                    color: white !important; /* Kolor linka po kliknięciu */
                }

                .time_link:hover {
                    color: orange !important; /* Kolor zmienia się na pomarańczowy */
                    background-color: #1a282f;
                }

                .time_link:active {
                    color: white !important; /* Kolor linka po kliknięciu */
                }

            </style>


            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h1 style="color: #24363f;">Nowe zgłoszenie wizyty</h1>
                <p>
                    Otrzymaliśmy nowy wniosek o rezerwację wizyty.
                </p>

                <p style="font-size: 16px; font-weight: bold; color: #24363f;">
                    Pacjent: <strong>{{visit.name}}</strong> | {{visit.patient_type}} | 
                    <a href="mailto:{{visit.email}}" style="color: #24363f; text-decoration: none;">{{visit.email}}</a> | 
                    <a href="tel:{{visit.phone}}" style="color: #24363f; text-decoration: none;">{{visit.phone}}</a>
                </p>

                <p>
                    Chce zarezerwować wizytę w dniu <strong>{{visit.visit_date}}</strong>.
                </p>

                <p style="margin-top: 20px;">
                    Należy ustalić godzinę z pacjentem.
                </p>

                <p style="margin-top: 20px;">
                    Wybierz godzinę wizyty klikając w jeden z przycisków poniżej:
                </p>

                <div class="time_area">
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0800&emailtoconfirmverification={{visit.email}}" class="time_link">
                            08:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0830&emailtoconfirmverification={{visit.email}}" class="time_link">
                            08:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0900&emailtoconfirmverification={{visit.email}}" class="time_link">
                            09:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0930&emailtoconfirmverification={{visit.email}}" class="time_link">
                            09:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1000&emailtoconfirmverification={{visit.email}}" class="time_link">
                            10:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1030&emailtoconfirmverification={{visit.email}}" class="time_link">
                            10:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1100&emailtoconfirmverification={{visit.email}}" class="time_link">
                            11:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1130&emailtoconfirmverification={{visit.email}}" class="time_link">
                            11:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1200&emailtoconfirmverification={{visit.email}}" class="time_link">
                            12:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1230&emailtoconfirmverification={{visit.email}}" class="time_link">
                            12:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1300&emailtoconfirmverification={{visit.email}}" class="time_link">
                            13:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1330&emailtoconfirmverification={{visit.email}}" class="time_link">
                            13:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1400&emailtoconfirmverification={{visit.email}}" class="time_link">
                            14:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1430&emailtoconfirmverification={{visit.email}}" class="time_link">
                            14:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1500&emailtoconfirmverification={{visit.email}}" class="time_link">
                            15:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1530&emailtoconfirmverification={{visit.email}}" class="time_link">
                            15:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1600&emailtoconfirmverification={{visit.email}}" class="time_link">
                            16:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1630&emailtoconfirmverification={{visit.email}}" class="time_link">
                            16:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1700&emailtoconfirmverification={{visit.email}}" class="time_link">
                            17:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1730&emailtoconfirmverification={{visit.email}}" class="time_link">
                            17:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1800&emailtoconfirmverification={{visit.email}}" class="time_link">
                            18:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1830&emailtoconfirmverification={{visit.email}}" class="time_link">
                            18:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1900&emailtoconfirmverification={{visit.email}}" class="time_link">
                            19:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1930&emailtoconfirmverification={{visit.email}}" class="time_link">
                            19:30
                        </a>
                    </div>
                </div>
                <p style="margin-top: 20px;">
                    Link do karty wizyty: <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}">Zarządzaj terminem wizyty</a>
                </p>

                <p style="margin-top: 20px;">
                    Prosimy o jak najszybsze potwierdzenie godziny wizyty pacjenta.
                </p>

                <p style="font-size: 12px; color: #686d71; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
                    Wiadomość wygenerowana automatycznie przez system rejestracji Duodent.
                </p>
            </body>
        </html>

        """,

    'remind_reception': """
        <html>
            <style>
                .time_area {
                    display: flex;
                    flex-wrap: wrap; /* Elementy zawijają się do nowej linii */
                    gap: 0.5px; /* Bardzo mała przerwa między elementami */
                    justify-content: flex-start;
                    align-items: center;
                    border-radius: 5px;
                }

                .time_box {
                    display: inline-block; /* Kluczowe: pozwala na umieszczanie wielu elementów w linii */
                    color: #fff;
                    font-size: 11px; /* Trochę mniejsza czcionka */
                    margin: 0.5px; /* Bardzo małe marginesy */
                    white-space: nowrap; /* Zapobiega łamaniu się tekstu */
                }

                .time_link {
                    text-decoration: none !important; /* Usunięcie podkreślenia */
                    color: white !important; /* Biały kolor tekstu */
                    background-color: #24363f;
                    padding: 4px 6px; /* Zmniejszona wysokość i szerokość */
                    border-radius: 4px;
                    font-size: 11px;
                    width: 40px; /* Stała szerokość pasująca do 5 znaków */
                    height: 16px; /* Wysokość 2x mniejsza */
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    transition: color 0.3s ease-in-out, background 0.3s ease-in-out;
                }

                .time_link:visited {
                    color: white !important; /* Kolor linka po kliknięciu */
                }

                .time_link:hover {
                    color: orange !important; /* Kolor zmienia się na pomarańczowy */
                    background-color: #1a282f;
                }

                .time_link:active {
                    color: white !important; /* Kolor linka po kliknięciu */
                }

            </style>


            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h1 style="color: #24363f;">🔔 Przypomnienie o zgłoszonej wizycie</h1>

                <p>
                    To zgłoszenie wymaga działania. Prosimy o potwierdzenie godziny wizyty pacjenta.
                </p>

                <p style="font-size: 16px; font-weight: bold; color: #24363f;">
                    Pacjent: <strong>{{visit.name}}</strong> | {{visit.patient_type}} | 
                    <a href="mailto:{{visit.email}}" style="color: #24363f; text-decoration: none;">{{visit.email}}</a> | 
                    <a href="tel:{{visit.phone}}" style="color: #24363f; text-decoration: none;">{{visit.phone}}</a>
                </p>

                <p>
                    Planowana data wizyty: <strong>{{visit.visit_date}}</strong>.
                </p>

                <p style="margin-top: 20px;">
                    Wybierz godzinę wizyty klikając w jeden z przycisków poniżej:
                </p>

                <div class="time_area">
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0800&emailtoconfirmverification={{visit.email}}" class="time_link">
                            08:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0830&emailtoconfirmverification={{visit.email}}" class="time_link">
                            08:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0900&emailtoconfirmverification={{visit.email}}" class="time_link">
                            09:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0930&emailtoconfirmverification={{visit.email}}" class="time_link">
                            09:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1000&emailtoconfirmverification={{visit.email}}" class="time_link">
                            10:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1030&emailtoconfirmverification={{visit.email}}" class="time_link">
                            10:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1100&emailtoconfirmverification={{visit.email}}" class="time_link">
                            11:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1130&emailtoconfirmverification={{visit.email}}" class="time_link">
                            11:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1200&emailtoconfirmverification={{visit.email}}" class="time_link">
                            12:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1230&emailtoconfirmverification={{visit.email}}" class="time_link">
                            12:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1300&emailtoconfirmverification={{visit.email}}" class="time_link">
                            13:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1330&emailtoconfirmverification={{visit.email}}" class="time_link">
                            13:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1400&emailtoconfirmverification={{visit.email}}" class="time_link">
                            14:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1430&emailtoconfirmverification={{visit.email}}" class="time_link">
                            14:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1500&emailtoconfirmverification={{visit.email}}" class="time_link">
                            15:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1530&emailtoconfirmverification={{visit.email}}" class="time_link">
                            15:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1600&emailtoconfirmverification={{visit.email}}" class="time_link">
                            16:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1630&emailtoconfirmverification={{visit.email}}" class="time_link">
                            16:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1700&emailtoconfirmverification={{visit.email}}" class="time_link">
                            17:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1730&emailtoconfirmverification={{visit.email}}" class="time_link">
                            17:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1800&emailtoconfirmverification={{visit.email}}" class="time_link">
                            18:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1830&emailtoconfirmverification={{visit.email}}" class="time_link">
                            18:30
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1900&emailtoconfirmverification={{visit.email}}" class="time_link">
                            19:00
                        </a>
                    </div>
                    <div class="time_box">
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1930&emailtoconfirmverification={{visit.email}}" class="time_link">
                            19:30
                        </a>
                    </div>
                </div>
                <p style="margin-top: 20px;">
                    Link do karty wizyty: <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}">Zarządzaj terminem wizyty</a>
                </p>

                <p style="margin-top: 20px;">
                    Prosimy o jak najszybsze potwierdzenie godziny wizyty pacjenta.
                </p>

                <p style="font-size: 12px; color: #686d71; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
                    Wiadomość wygenerowana automatycznie przez system rejestracji Duodent.
                </p>
            </body>
        </html>
        """,
    
    'send_patient_reminder': """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 15px;">

                <h1 style="color: #24363f; text-align: center;">📅 Przypomnienie o Twojej wizycie</h1>

                <p>Drogi/a <strong>{{visit.name}}</strong>,</p>

                <p>
                    Chcielibyśmy przypomnieć Ci o zaplanowanej wizycie w naszej przychodni. 
                </p>

                <p style="font-size: 16px; font-weight: bold; color: #24363f;">
                    ⏰ <strong>Data wizyty:</strong> {{visit.confirmed_date}}
                </p>

                <p>
                    Jeśli masz pytania lub chciałbyś dokonać zmian w rezerwacji, skontaktuj się z naszą recepcją.
                </p>

                <div style="margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px;">
                    <p style="font-size: 14px; font-weight: bold; color: #24363f;">
                        📞 Kontakt telefoniczny: 
                        <a href="tel:790777350" style="color: #24363f; text-decoration: none;">790 777 350</a>
                    </p>

                    <p style="font-size: 14px;">
                        ✉️ Kontakt e-mail: 
                        <a href="mailto:arkuszowa@duodent.com.pl" style="color: #24363f; text-decoration: none;">arkuszowa@duodent.com.pl</a>
                    </p>

                    <p>
                        Nasz zespół jest do Twojej dyspozycji w godzinach otwarcia przychodni i chętnie udzieli wszelkich informacji.
                    </p>
                </div>

                <hr style="border: 1px solid #ccc; margin: 20px 0;">

                <p>
                    ✅ <strong>Twoja wizyta została potwierdzona!</strong> 
                    Oczekujemy Cię w naszej placówce w dniu <strong>{{visit.confirmed_date}}</strong> .
                </p>

                <p>
                    Jeśli z jakiegokolwiek powodu godzina wizyty nie zgadza się z ustaleniami, prosimy o jak najszybszy kontakt 
                    z recepcją w celu skorygowania terminu.
                </p>

                <p style="text-align: center; margin-top: 20px;">
                    <a href="tel:790777350" style="text-decoration: none; background: #24363f; color: white; padding: 10px 15px; border-radius: 5px; font-weight: bold;">
                        📞 Zadzwoń do recepcji
                    </a>
                </p>

                <hr style="border: 1px solid #ccc; margin: 20px 0;">

                <p style="color: gray; font-size: 12px; font-weight: 300;">
                    ❗ Jeśli to nie Ty rejestrowałeś(-aś) wizytę, prosimy o niezwłoczny kontakt telefoniczny pod numerem 
                    <a href="tel:790777350" style="color: red; text-decoration: none;">790 777 350</a> 
                    lub mailowy na adres 
                    <a href="mailto:arkuszowa@duodent.com.pl" style="color: red; text-decoration: none;">arkuszowa@duodent.com.pl</a>.
                </p>

                <p style="font-size: 12px; color: #686d71; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px; text-align: center;">
                    Zespół Duodent Bielany  
                </p>

            </body>
        </html>


        """,
    'send_reception_reminder': """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">

                <h1 style="color: #24363f;">📅 Dzisiejsze wizyty – przypomnienie</h1>

                <p>
                    Przypominamy o zaplanowanej wizycie pacjenta, która odbędzie się dzisiaj w naszej przychodni.
                </p>

                <p style="font-size: 16px; font-weight: bold; color: #24363f;">
                    👤 <strong>Pacjent:</strong> {{visit.name}} | {{visit.patient_type}}<br>
                    ⏰ <strong>Data wizyty:</strong> {{visit.confirmed_date}}<br>
                    ✉️ <strong>Email:</strong> 
                    <a href="mailto:{{visit.email}}" style="color: #24363f; text-decoration: none;">{{visit.email}}</a><br>
                    📞 <strong>Telefon:</strong> 
                    <a href="tel:{{visit.phone}}" style="color: #24363f; text-decoration: none;">{{visit.phone}}</a>
                </p>

                <p>
                    Prosimy o potwierdzenie obecności pacjenta lub ewentualny kontakt telefoniczny w celu przypomnienia o wizycie.
                </p>

                <p style="margin-top: 20px;">
                    🔗 <strong>Link do karty wizyty:</strong> 
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}" style="color: #24363f; text-decoration: none; font-weight: bold;">
                        Zarządzaj terminem wizyty
                    </a>
                </p>

            </body>
        </html>

        """,
    'send_cancellation_email': """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: auto;">

                <h1 style="color: #c0392b; text-align: center;">❌ Twoja wizyta została odwołana</h1>

                <p>Drogi/a <strong>{{visit.name}}</strong>,</p>

                <p>
                    Informujemy, że Twoja wizyta zaplanowana na dzień <strong>{{visit.confirmed_date}}</strong> została odwołana przez recepcję.
                </p>

                <p>
                    Jeśli chcesz umówić się na nowy termin, skontaktuj się z nami.
                </p>

                <div style="margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px;">
                    <p style="font-size: 14px; font-weight: bold; color: #24363f;">
                        📞 Kontakt telefoniczny: 
                        <a href="tel:790777350" style="color: #24363f; text-decoration: none;">790 777 350</a>
                    </p>

                    <p style="font-size: 14px;">
                        ✉️ Kontakt e-mail: 
                        <a href="mailto:arkuszowa@duodent.com.pl" style="color: #24363f; text-decoration: none;">arkuszowa@duodent.com.pl</a>
                    </p>

                    <p>
                        Nasz zespół chętnie pomoże w znalezieniu nowego dogodnego terminu wizyty.
                    </p>
                </div>

                <p style="text-align: center; margin-top: 20px;">
                    <a href="tel:790777350" style="text-decoration: none; background: #c0392b; color: white; padding: 10px 15px; border-radius: 5px; font-weight: bold;">
                        📞 Zadzwoń do recepcji
                    </a>
                </p>

                <hr style="border: 1px solid #ccc; margin: 20px 0;">

                <p style="color: gray; font-size: 12px; font-weight: 300;">
                    ❗ Jeśli to nie Ty rejestrowałeś(-aś) wizytę, prosimy o niezwłoczny kontakt telefoniczny pod numerem 
                    <a href="tel:790777350" style="color: red; text-decoration: none;">790 777 350</a> 
                    lub mailowy na adres 
                    <a href="mailto:arkuszowa@duodent.com.pl" style="color: red; text-decoration: none;">arkuszowa@duodent.com.pl</a>.
                </p>

                <p style="font-size: 12px; color: #686d71; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px; text-align: center;">
                    Zespół Duodent Bielany  
                </p>

            </body>
        </html>

        """,
        'send_cancellation_reception': """
            <html>
                <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                    <h1 style="color: #d9534f;">📢 Odwołanie wizyty pacjenta</h1>

                    <p>
                        Informujemy, że pacjent <strong>{{visit.name}}</strong> odwołał swoją wizytę, która była zaplanowana na <strong>{{visit.confirmed_date}}</strong>.
                    </p>

                    <p>
                        Dane pacjenta:
                    </p>

                    <p style="font-size: 14px;">
                        👤 <strong>Imię i nazwisko:</strong> {{visit.name}} <br>
                        📧 <strong>Email:</strong> <a href="mailto:{{visit.email}}" style="color: #24363f; text-decoration: none;">{{visit.email}}</a> <br>
                        📞 <strong>Telefon:</strong> <a href="tel:{{visit.phone}}" style="color: #24363f; text-decoration: none;">{{visit.phone}}</a> <br>
                        🏷 <strong>Typ pacjenta:</strong> {{visit.patient_type}}
                    </p>

                    <hr style="border: 1px solid #ccc; margin: 20px 0;">

                    <p>
                        Możesz zarządzać wizytami pacjentów w systemie recepcji:
                    </p>

                    <p>
                        🔗 <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}" style="color: #d9534f; font-weight: bold; text-decoration: none;">Zarządzaj wizytami</a>
                    </p>

                    <p style="font-size: 12px; color: #686d71; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
                        Zespół Duodent Bielany
                    </p>
                </body>
            </html>
        """,
        'send_patient_info_visit': """
            <html>
                <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                    <h1 style="color: #24363f;">✅ Twoja wizyta została potwierdzona!</h1>
                    <p>Drogi/a <strong>{{visit.name}}</strong>,</p>
                    <p>Z radością informujemy, że Twoja wizyta w Duodent Bielany została potwierdzona.</p>
                    <p style="font-size: 16px; font-weight: bold; color: #24363f;">
                        📍 <strong>Data i godzina wizyty:</strong> {{visit.confirmed_date}}
                    </p>
                    <p>Jeśli masz jakiekolwiek pytania lub chcesz zmienić termin wizyty, skontaktuj się z naszą recepcją.</p>
                    <p style="font-size: 14px; font-weight: bold;">
                        📞 Telefon: <a href="tel:790777350" style="color: #24363f;">790 777 350</a><br>
                        ✉️ E-mail: <a href="mailto:arkuszowa@duodent.com.pl" style="color: #24363f;">arkuszowa@duodent.com.pl</a>
                    </p>
                    <hr style="border: 1px solid #ccc; margin: 20px 0;">
                    <p style="color: gray; font-size: 12px;">
                        Jeśli to nie Ty rejestrowałeś(-aś) wizytę, prosimy o niezwłoczny kontakt.
                    </p>
                </body>
            </html>
        """,

        'send_reception_info_visit': """
            <html>
                <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                    <h1 style="color: #24363f;">✅ Potwierdzona wizyta pacjenta</h1>
                    <p>Wizyta pacjenta <strong>{{visit.name}}</strong> została potwierdzona.</p>
                    <p style="font-size: 16px; font-weight: bold; color: #24363f;">
                        🕒 <strong>Godzina wizyty:</strong> {{visit.confirmed_date}}
                    </p>
                    <p>Proszę sprawdzić szczegóły wizyty w systemie.</p>
                    <p style="margin-top: 20px;">
                        📌 Link do karty wizyty: 
                        <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}" style="color: #24363f;">Zarządzaj wizytą</a>
                    </p>
                    <hr style="border: 1px solid #ccc; margin: 20px 0;">
                    <p style="color: gray; font-size: 12px;">
                        E-mail wygenerowany automatycznie.
                    </p>
                </body>
            </html>
        """
    
}