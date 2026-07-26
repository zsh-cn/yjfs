import os
from dotenv import load_dotenv
import customtkinter as ctk
from main_window import MainWindow


def main():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()