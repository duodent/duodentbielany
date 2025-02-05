class AppointmentRequest:
    """ Obiekt reprezentujący wizytę pacjenta """
    def __init__(self, id, name, email, phone, patient_type, visit_date, consent, status, created_at,
                 in_progress_date, in_progress_description, in_progress_flag, verified_date, verified_description,
                 verified_flag, confirmed_date, confirmed_description, confirmed_flag, cancelled_date,
                 cancelled_description, cancelled_flag, error_date, error_description, error_flag, link_hash,
                 reminder_count=0):

        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.patient_type = patient_type
        self.visit_date = visit_date
        self.consent = consent
        self.status = status
        self.created_at = created_at
        self.in_progress_date = in_progress_date
        self.in_progress_description = in_progress_description
        self.in_progress_flag = in_progress_flag
        self.verified_date = verified_date
        self.verified_description = verified_description
        self.verified_flag = verified_flag
        self.confirmed_date = confirmed_date
        self.confirmed_description = confirmed_description
        self.confirmed_flag = confirmed_flag
        self.cancelled_date = cancelled_date
        self.cancelled_description = cancelled_description
        self.cancelled_flag = cancelled_flag
        self.error_date = error_date
        self.error_description = error_description
        self.error_flag = error_flag
        self.link_hash = link_hash
        self.reminder_count = reminder_count  # ✅ Nowe pole

    @classmethod
    def from_tuple(cls, data):
        """ Tworzy obiekt `AppointmentRequest` z krotki (dane z MySQL) """
        return cls(*data)

    def to_dict(self):
        """ Konwertuje obiekt na słownik (przydatne do logowania/debugowania) """
        return self.__dict__