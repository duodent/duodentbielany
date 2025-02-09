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
        """Usuwa wszystkie zadania związane z daną funkcją i danym identyfikatorem."""

        # Pobieramy identyfikatory z przekazanych argumentów
        arg_values = set(getattr(a, arg_key, None) if hasattr(a, arg_key) else a for a in args)
        
        logging.info(f"🛠 Usuwam `{func.__name__}` dla ID: {arg_values}")

        with self.lock:
            updated_queue = PriorityQueue()
            removed_count = 0

            while not self.task_queue.empty():
                task = self.task_queue.get()

                # Pobieramy ID dla aktualnego zadania (obsługa różnych typów argumentów)
                task_values = set()
                for a in task.args:
                    if isinstance(a, (dict, AppointmentRequest)):
                        task_values.add(getattr(a, arg_key, None) if hasattr(a, arg_key) else a.get(arg_key, None))
                    elif isinstance(a, (int, str)):  # Obsługa ID podanych jako liczby lub stringi
                        task_values.add(a)

                # **Usuwamy tylko jeśli ID pasuje**
                if task.func == func and arg_values & task_values:
                    logging.info(f"🗑 Usunięto `{task.func.__name__}` dla ID {task_values}")
                    removed_count += 1
                else:
                    updated_queue.put(task)  # Przenosimy do nowej kolejki

            self.task_queue = updated_queue
            logging.info(f"✅ Usunięto {removed_count} zadań `{func.__name__}`")

            # 🔹 **Logowanie pozostałych zadań w kolejce**
            remaining_tasks = [f"{t.func.__name__} (ID: {getattr(t.args[0], arg_key, None) if t.args else 'Brak ID'})" for t in list(self.task_queue.queue)]
            logging.info(f"📌 Pozostałe zadania w kolejce: {remaining_tasks if remaining_tasks else 'Brak'}")




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
