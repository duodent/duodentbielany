import time
import threading
from queue import PriorityQueue
import logging
from AppointmentRequest import AppointmentRequest

# Klasa zadania do wykonania przez daemon
class Task:
    def __init__(self, run_time, func, args=(), kwargs={}):
        self.run_time = run_time
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other):
        return self.run_time < other.run_time  # Kolejność w kolejce priorytetowej

# Klasa daemona zarządzającego zadaniami
class Daemon:
    def __init__(self):
        self.task_queue = PriorityQueue()
        self.running = True
        self.lock = threading.Lock()

    def add_task(self, delay, func, *args, **kwargs):
        """Dodaje zadanie do kolejki z opóźnieniem delay (w sekundach)."""
        run_time = time.time() + delay
        with self.lock:
            self.task_queue.put(Task(run_time, func, args, kwargs))
        
        # Sprawdzamy, czy zadanie ma argumenty
        task_info = f"(Zgłoszenie ID: {args[0].id})" if args and isinstance(args[0], AppointmentRequest) else ""

        logging.info(f"📌 Zadanie dodane: {func.__name__}, uruchomi się za {delay} sekund {task_info}")

    def remove_tasks_for_function(self, func, *args, arg_key="id"):
        """
        Usuwa wszystkie zaplanowane zadania dla danej funkcji (func), opcjonalnie filtrując po wartości w `arg_key`.
        
        :param func: Funkcja, której zadania mają zostać usunięte.
        :param args: Argumenty do sprawdzenia (np. obiekt visit).
        :param arg_key: Klucz do identyfikacji obiektu (np. "id" dla `visit.id`).
        """
        with self.lock:
            updated_queue = PriorityQueue()

            while not self.task_queue.empty():
                task = self.task_queue.get()

                # 1️⃣ Sprawdź, czy funkcja pasuje
                if task.func == func:
                    # 2️⃣ Jeśli przekazano `args`, próbujemy znaleźć klucz `arg_key` w argumentach zadania
                    if args:
                        for arg in args:
                            # Obsługa zarówno obiektów (np. `visit.id`), jak i słowników (np. `{"id": 50}`)
                            task_values = [getattr(a, arg_key, None) if hasattr(a, arg_key) else a.get(arg_key, None) for a in task.args]

                            if getattr(arg, arg_key, None) in task_values or arg.get(arg_key, None) in task_values:
                                logging.info(f"🗑 Usunięto zadanie {task.func.__name__} dla {arg_key} = {getattr(arg, arg_key, None) or arg.get(arg_key, None)}")
                                break  # Pomijamy to zadanie (nie dodajemy go z powrotem)
                    else:
                        logging.info(f"🗑 Usunięto WSZYSTKIE zadania {task.func.__name__}")
                        continue  # Usuwamy zadanie, jeśli `args` nie zostały przekazane (czyli usuwamy wszystkie instancje danej funkcji)

                # Jeśli zadanie nie pasuje do warunków, dodajemy je z powrotem do kolejki
                updated_queue.put(task)

            self.task_queue = updated_queue

    def run(self):
        """Główna pętla daemona, wykonuje zadania w odpowiednim czasie."""
        logging.info("🚀 Daemon uruchomiony!")
        while self.running:
            now = time.time()
            with self.lock:
                while not self.task_queue.empty():
                    task = self.task_queue.queue[0]
                    if task.run_time <= now:
                        self.task_queue.get()
                        threading.Thread(target=task.func, args=task.args, kwargs=task.kwargs).start()
                    else:
                        break
            time.sleep(1)

    def stop(self):
        """Zatrzymuje działanie daemona."""
        self.running = False
        logging.info("🛑 Daemon zatrzymany!")
