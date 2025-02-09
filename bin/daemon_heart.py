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
        with self.lock:
            updated_queue = PriorityQueue()

            while not self.task_queue.empty():
                task = self.task_queue.get()

                # Pobieramy wartość identyfikującą (np. `visit.id`)
                task_values = []
                for a in task.args:
                    if isinstance(a, dict):
                        task_values.append(a.get(arg_key, None))  # Jeśli to słownik, pobierz klucz
                    elif hasattr(a, arg_key):  
                        task_values.append(getattr(a, arg_key))  # Jeśli to obiekt, pobierz atrybut

                # Jeśli funkcja i argumenty pasują, usuwamy zadanie
                if task.func == func and any(value in task_values for value in args):
                    logging.info(f"🗑 Usunięto zadanie {task.func.__name__} dla ID {args}")
                else:
                    updated_queue.put(task)  # Przekładamy do nowej kolejki

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
