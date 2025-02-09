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
        <body>
            <h2>Przypomnienie o zgłoszeniu</h2>
            <p>Pacjent: <strong>{{visit.name}}</strong></p>
            <p>To zgłoszenie wymaga obsługi.</p>
        </body>
        </html>
        """,
    
    'send_patient_reminder': """
        <html>
        <body>
            <h2>Przypomnienie o Twojej wizycie</h2>
            <p>Drogi {{visit.name}},</p>
            <p>Przypominamy, że Twoja wizyta odbędzie się: <strong>{{visit.confirmed_date}}</strong></p>
            <p>Jeśli masz pytania, skontaktuj się z naszą recepcją.</p>
        </body>
        </html>
        """,
    'send_reception_reminder': """
        <html>
        <body>
            <h2>Dzisiejsze wizyty</h2>
            <p>Prosimy o sprawdzenie grafiku wizyt na dziś.</p>
            <p>Pacjent: <strong>{{visit.name}}</strong></p>
            <p>Planowana godzina wizyty: <strong>{{visit.confirmed_date}}</strong></p>
        </body>
        </html>
        """,
    'send_cancellation_email': """
        <html>
        <body>
            <h2>Twoja wizyta została odwołana</h2>
            <p>Drogi {{visit.name}},</p>
            <p>Informujemy, że Twoja wizyta została odwołana przez recepcję.</p>
            <p>W razie pytań skontaktuj się z nami.</p>
        </body>
        </html>
        """,
    
}