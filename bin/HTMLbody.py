html_body_dict = {
    'handle_visit_request': """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h1 style="color: #24363f;">Nowe zgłoszenie wizyty</h1>
                <p>
                    Otrzymaliśmy nowe zgłoszenie wizyty w placówce Duodent Bielany. Szczegóły zgłoszenia znajdują się poniżej:
                </p>
                <table style="border-collapse: collapse; width: 100%; margin-top: 20px;">
                    <tr style="background-color: #f9f9f9;">
                        <th style="border: 1px solid #ccc; padding: 10px; text-align: left;">Opis</th>
                        <th style="border: 1px solid #ccc; padding: 10px; text-align: left;">Dane</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ccc; padding: 10px;">Imię i nazwisko</td>
                        <td style="border: 1px solid #ccc; padding: 10px;">{{visit.name}}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="border: 1px solid #ccc; padding: 10px;">Adres e-mail</td>
                        <td style="border: 1px solid #ccc; padding: 10px;">{{visit.email}}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ccc; padding: 10px;">Numer telefonu</td>
                        <td style="border: 1px solid #ccc; padding: 10px;">{{visit.phone}}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="border: 1px solid #ccc; padding: 10px;">Data wizyty</td>
                        <td style="border: 1px solid #ccc; padding: 10px;">{{visit.visit_date}}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ccc; padding: 10px;">Typ pacjenta</td>
                        <td style="border: 1px solid #ccc; padding: 10px;">{{visit.patient_type}}</td>
                    </tr>
                </table>

                <p style="margin-top: 20px;">
                    Wybierz godzinę wizyty klikając w jeden z przycisków poniżej:
                </p>

                <div style="margin-top: 20px; text-align: center;">
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0800&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">08:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0830&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">08:30</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0900&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">09:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=0930&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">09:30</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1000&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">10:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1030&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">10:30</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1100&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">11:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1130&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">11:30</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1200&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">12:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1230&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">12:30</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1300&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">13:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1330&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">13:30</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1400&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">14:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1430&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">14:30</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1500&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">15:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1530&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">15:30</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1600&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">16:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1630&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">16:30</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1700&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">17:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1730&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">17:30</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1800&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">18:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1830&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">18:30</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1900&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">19:00</a>
                    <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}?date={{visit.visit_date}}&time=1930&emailtoconfirmverification={{visit.email}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">19:30</a>
                </div>
                <p style="margin-top: 20px;">
                    Ustaw datę i godzinę ręcznie klikając w ten link: <a href="https://duodentbielany.pl/reception/{{visit.link_hash}}" style="text-decoration: none; padding: 10px 15px; background-color: #24363f; color: #fff; border-radius: 5px; margin: 5px;">Zarządzaj terminem wizyty</a>
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