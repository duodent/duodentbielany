from datetime import datetime

def handle_error_old(exception, retry_count=3, log_path="../logs/errors.log"):
    try:
        with open(log_path, "a") as log:
            now = str(datetime.now())
            message = "{0} {1}\n".format(now, exception)
            log.write(message)
    except Exception as e:
        if retry_count > 0:
            print(f"Błąd podczas zapisywania do pliku: {e}. Ponawiam próbę...")
            handle_error(exception, retry_count - 1, log_path)
        else:
            print("Nieudana próba zapisu do pliku. Przekroczono limit ponawiania.")


def handle_error(exception, retry_count=3, log_path="../logs/errors.log"):
    try:
        # Upewnij się, że retry_count to liczba całkowita
        retry_count = int(retry_count) if isinstance(retry_count, str) else retry_count

        # Zapisywanie do pliku logów
        with open(log_path, "a") as log:
            now = str(datetime.now())
            message = f"{now} {exception}\n"
            log.write(message)

    except Exception as e:
        # Obsługa błędów podczas zapisu do pliku
        if retry_count > 0:
            print(f"Błąd podczas zapisywania do pliku: {e}. Ponawiam próbę... ({retry_count} próby pozostały)")
            handle_error(exception, retry_count - 1, log_path)
        else:
            print("Nieudana próba zapisu do pliku. Przekroczono limit ponawiania.")