### 🛠 **Daemon do Zarządzania Zadaniami Asynchronicznymi**

🚀 **Daemon** to mechanizm do planowania i zarządzania zadaniami w tle. Działa na kolejce priorytetowej, pozwala na dodawanie, usuwanie i automatyczne wykonywanie zadań zgodnie z harmonogramem.

---

## 📌 **Funkcje Daemona**
✅ **Planowanie zadań** w przyszłości  
✅ **Usuwanie zaplanowanych zadań**  
✅ **Automatyczne zarządzanie kolejką**  
✅ **Obsługa wielowątkowa** dla płynnej pracy  
✅ **Bezpieczne zatrzymywanie** (np. przy zamykaniu aplikacji)

---

## 🚀 **Instalacja i Uruchomienie**
1. **Skopiuj pliki Daemona** do swojego projektu.
2. **Dodaj do aplikacji** i uruchom w tle:
   ```python
   daemon_thread = threading.Thread(target=daemon.run)
   daemon_thread.start()
   ```

---

## 🛠 **Użycie**
### 🔹 **Dodawanie zadania**
Dodajemy zadanie, które wykona się za określony czas:
```python
daemon.add_task(600, remind_reception, visit)
```
🕒 **Za 10 minut system przypomni recepcji o wizycie.**

---

### 🔹 **Usuwanie zadania**
Usuwamy wszystkie zadania danej funkcji powiązane z konkretną wizytą:
```python
daemon.remove_tasks_for_function(remind_reception, visit, arg_key="id")
```
❌ **Usuwa wszystkie przypomnienia dla tej wizyty.**

---

### 🔹 **Zatrzymywanie Daemona**
Jeśli chcesz zakończyć działanie Daemona:
```python
daemon.stop()
```
🛑 **Zatrzymuje kolejkę i kończy pracę Daemona.**

---

## 🏗 **Struktura kodu**
### **🔹 `Task` – Obiekt Zadania**
Reprezentuje pojedyncze zadanie do wykonania.
```python
class Task:
    def __init__(self, run_time, func, args=(), kwargs={}):
        self.run_time = run_time
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other):
        return self.run_time < other.run_time
```

### **🔹 `Daemon` – Główny Mechanizm**
Obsługuje kolejkę zadań i ich harmonogram.
```python
class Daemon:
    def __init__(self):
        self.task_queue = PriorityQueue()
        self.running = True
        self.lock = threading.Lock()
```

---

## 📌 **Obsługa `CTRL+C`**
Daemon obsługuje sygnał zatrzymania, co pozwala na jego bezpieczne wyłączenie.
```python
def stop_daemon(sig, frame):
    logging.info("🛑 Otrzymano sygnał zatrzymania! Zamykamy daemon...")
    daemon.stop()
    daemon_thread.join()
    logging.info("✅ Daemon został bezpiecznie zatrzymany!")

signal.signal(signal.SIGINT, stop_daemon)
```
✅ **Bezpieczne zamykanie Daemona przy zatrzymaniu aplikacji.**

---

## 📅 **Przykładowe Scenariusze**
🔹 **Przypomnienia dla recepcji**  
```python
daemon.add_task(300, remind_reception, visit)
```
🔹 **Powiadomienia e-mailowe**  
```python
daemon.add_task(10, send_email, visit, subject="Potwierdzenie wizyty")
```
🔹 **Obsługa anulowania wizyt**  
```python
daemon.remove_tasks_for_function(remind_reception, visit, arg_key="id")
```

---

## 🔥 **Podsumowanie**
✅ **Łatwa integracja** z każdą aplikacją  
✅ **Minimalne użycie zasobów**  
✅ **Automatyczne zarządzanie kolejką**  
✅ **Elastyczność** – działa dla różnych funkcji  

🔗 **Gotowy do użycia? Włącz Daemona i ciesz się automatyzacją!** 🚀