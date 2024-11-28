import pyautogui
import threading
import tkinter as tk
from pynput import keyboard
import random
import requests
import time


class AutoClicker:
    def __init__(self):
        # Tracks whether the autoclicker is currently running
        self.clicking = False

        # Default key to toggle the autoclicker
        self.toggle_key = "f8"

        # Listener for detecting keypress events
        self.listener = None

        # Fetch a random seed for the pseudorandom generator
        self.seed = self.fetch_seed()

        # Initialize a pseudorandom number generator with the fetched seed
        self.rng = random.Random(self.seed)

        # Base delay between clicks to simulate 60 clicks per second (CPS)
        self.delay = 1 / 60

        # Lock object to ensure thread-safe changes to shared state
        # Multiple threads (click worker threads) may attempt to modify `self.clicking`.
        self.lock = threading.Lock()

        # List to keep track of active worker threads
        self.threads = []

    def fetch_seed(self):
        """
        Fetches a random integer from an online random number generator service
        to use as a seed for the pseudorandom generator. If the service fails,
        a fallback random seed is used.
        """
        try:
            response = requests.get(
                "https://www.random.org/integers/?num=1&min=0&max=100000&col=1&base=10&format=plain&rnd=new"
            )
            if response.status_code == 200:
                return int(response.text.strip())
            else:
                # Fallback if the online service is unavailable
                return random.randint(0, 100000)
        except Exception as e:
            print(f"Error fetching seed: {e}")
            return random.randint(0, 100000)

    def generate_random_offset(self):
        """
        Generates a small random delay offset to add slight variability
        between clicks, simulating human-like clicking behavior.
        """
        return self.rng.uniform(0.0005, 0.002)

    def click_worker(self):
        """
        A worker thread that continuously performs mouse clicks while
        `self.clicking` is True. Adding random jitter makes the autoclicker
        behavior appear less robotic.
        """
        while self.clicking:
            pyautogui.click()
            random_offset = self.generate_random_offset()
            time.sleep(self.delay + random_offset)

    def toggle_clicking(self):
        """
        Toggles the state of `self.clicking`. If toggled ON, multiple worker
        threads are started to perform rapid clicking. If toggled OFF, threads
        stop as they check `self.clicking` periodically.
        """
        with self.lock:
            self.clicking = not self.clicking
            if self.clicking:
                # Start multiple threads for parallel clicking
                for _ in range(5):  # Number of threads can be adjusted for performance
                    thread = threading.Thread(target=self.click_worker)
                    thread.daemon = True  # Daemon threads automatically stop when the program exits
                    self.threads.append(thread)
                    thread.start()
            else:
                # Stopping simply involves setting `self.clicking` to False;
                # worker threads will naturally exit their loops
                self.threads = []

    def set_toggle_key(self, key):
        """
        Updates the toggle key used to start/stop the autoclicker. Restarts the
        key listener to use the new key.
        """
        self.toggle_key = key.lower()
        if self.listener:
            self.listener.stop()
        self.start_listener()

    def start_listener(self):
        """
        Starts a key listener to detect when the toggle key is pressed.
        Pressing the toggle key will activate or deactivate the autoclicker.
        """

        def on_press(key):
            try:
                # Check if the pressed key matches the toggle key
                if key.char == self.toggle_key:
                    self.toggle_clicking()
            except AttributeError:
                pass

        # Launch the key listener in a separate thread
        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.start()


class AutoClickerUI:
    def __init__(self, root, autoclicker):
        """
        Initializes the graphical user interface for the autoclicker.
        The UI provides controls to toggle the autoclicker and customize the toggle key.
        """
        self.root = root
        self.autoclicker = autoclicker

        # Configure root window properties
        self.root.title("simpleclick")
        self.root.configure(bg="#1e1e1e")  # Dark background
        self.root.resizable(False, False)

        # Status Label
        self.status_label = tk.Label(
            root, text="Status: OFF", fg="red", bg="#1e1e1e", font=("Arial", 14)
        )
        self.status_label.pack(pady=10)

        # Toggle Button
        self.toggle_button = tk.Button(
            root,
            text="Toggle Autoclicker",
            command=self.toggle_clicking,
            font=("Arial", 12),
            bg="#444444",
            fg="white",
            activebackground="#555555",
        )
        self.toggle_button.pack(pady=10)

        # Keybind Label
        self.keybind_label = tk.Label(
            root, text="Set Keybind (current: F8):", bg="#1e1e1e", fg="white", font=("Arial", 12)
        )
        self.keybind_label.pack(pady=5)

        # Keybind Entry
        self.keybind_entry = tk.Entry(root, font=("Arial", 12), bg="#333333", fg="white")
        self.keybind_entry.pack(pady=5)

        # Set Keybind Button
        self.set_keybind_button = tk.Button(
            root,
            text="Set Keybind",
            command=self.set_keybind,
            font=("Arial", 12),
            bg="#444444",
            fg="white",
            activebackground="#555555",
        )
        self.set_keybind_button.pack(pady=10)

        self.update_status()

    def toggle_clicking(self):
        """
        Toggles the autoclicker and updates the status label to reflect the current state.
        """
        self.autoclicker.toggle_clicking()
        self.update_status()

    def set_keybind(self):
        """
        Updates the toggle key based on user input and updates the keybind label to show
        the new key.
        """
        key = self.keybind_entry.get()
        if key:
            self.autoclicker.set_toggle_key(key)
            self.keybind_label.config(text=f"Set Keybind (current: {key.upper()}):")

    def update_status(self):
        """
        Updates the status label to show whether the autoclicker is currently active.
        """
        if self.autoclicker.clicking:
            self.status_label.config(text="Status: ON", fg="green")
        else:
            self.status_label.config(text="Status: OFF", fg="red")


if __name__ == "__main__":
    # Initialize the autoclicker logic
    autoclicker = AutoClicker()
    print(f"Initialized with seed: {autoclicker.seed}")

    # Start listening for the toggle key
    autoclicker.start_listener()

    # Initialize the graphical interface
    root = tk.Tk()
    ui = AutoClickerUI(root, autoclicker)

    # Run the Tkinter main event loop
    root.mainloop()
