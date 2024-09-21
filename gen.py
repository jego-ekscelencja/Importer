import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext, simpledialog
import shutil
import datetime
import subprocess
from PIL import Image, ExifTags


# Funkcja do pobierania daty z EXIF
def get_exif_date_taken(filepath):
    try:
        image = Image.open(filepath)
        exif_data = getattr(image, '_getexif', None)
        if exif_data:
            for tag, value in exif_data.items():
                decoded_tag = ExifTags.TAGS.get(tag, tag)
                if decoded_tag == "DateTimeOriginal":
                    return datetime.datetime.strptime(value, "%Y:%m:%d %H:%M:%S").date()
    except (IOError, AttributeError):
        return None
    return None


# Funkcja do pobierania daty z nazwy pliku
def get_date_from_filename(filename):
    patterns = [
        r"(\d{4})[_-](\d{2})[_-](\d{2})",  # format 2024_05-10
        r"(\d{4})(\d{2})(\d{2})",  # format 20240510
        r"(\d{2})(\d{2})(\d{2})",  # format 240510
        r"(\d{2})[_-](\d{2})[_-](\d{2})",  # format 24-05-10
    ]

    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            if len(match.groups()) == 3:
                try:
                    return datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                except ValueError:
                    pass
    return None


# Funkcja do pobierania daty utworzenia pliku z systemu plików
def get_creation_date(filepath):
    try:
        timestamp = os.path.getctime(filepath)
        return datetime.date.fromtimestamp(timestamp)
    except (OSError, ValueError):
        return None


# Główna klasa aplikacji
class ImporterApp:
    def __init__(self, master):
        self.root = master
        self.root.title("Importer")
        self.root.configure(padx=10, pady=5, background="#D3D3D3")  # Zmniejszamy padding

        # Definiowanie wszystkich atrybutów instancji w __init__
        self.source_var = tk.StringVar()
        self.use_exif_var = tk.BooleanVar(value=True)
        self.media_path_var = tk.StringVar()
        self.operation_var = tk.StringVar(value="Kopiowanie")
        self.buffer_var = tk.StringVar(value="Dynamiczny")  # Domyślnie dynamiczny
        self.naming_var = tk.StringVar(value="Data i źródło")
        self.suffix_var = tk.BooleanVar()
        self.subfolder_var = tk.StringVar(value="Wszystkie pliki w jednym katalogu")
        self.dest_path_var = tk.StringVar()
        self.open_folder_var = tk.BooleanVar()
        self.log_file_var = tk.BooleanVar()
        self.sources = []

        self.source_combobox = None
        self.media_path_entry = None
        self.file_info_label = None
        self.date_source_var = tk.StringVar(value="EXIF")  # Domyślnie EXIF
        self.file_list_text = None
        self.use_exif_radio = None
        self.use_filename_radio = None
        self.date_source_frame = None
        self.date_source_label = None
        self.date_source_dynamic = None
        self.footer_text = None

        # Media Source Section
        self.create_media_source_section()

        # Path Selection Section
        self.create_path_selection_section()

        # Operation Selection Section
        self.create_operation_selection_section()

        # Buffer Size Selection Section
        self.create_buffer_size_section()

        # Naming Format Section with EXIF or Filename Date
        self.create_naming_format_section()

        # Suffix Options
        self.create_suffix_options_section()

        # Subfolder Options Section
        self.create_subfolder_options_section()

        # Destination Path Section
        self.create_destination_path_section()

        # Additional Options Section
        self.create_additional_options_section()

        # File List Output Section
        self.create_file_list_output_section()

        # Action Buttons Section
        self.create_action_buttons_section()

        # Footer Section
        self.create_footer_section()

    def create_media_source_section(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=0, columnspan=2, pady=2, sticky="ew")

        label = ttk.Label(frame, text="Źródło multimediów:", font=("Calibri", 12))
        label.grid(row=0, column=0, sticky="w")

        self.load_sources()
        self.source_combobox = ttk.Combobox(frame, textvariable=self.source_var, values=self.sources, state="readonly")
        self.source_combobox.grid(row=0, column=1, padx=5)

        add_button = ttk.Button(frame, text="Dodaj nowe źródło", command=self.add_source)
        add_button.grid(row=0, column=2, padx=5)

        remove_button = ttk.Button(frame, text="Usuń wybrane źródło", command=self.remove_source)
        remove_button.grid(row=0, column=3, padx=5)

    def create_path_selection_section(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=1, column=0, columnspan=2, pady=2, sticky="ew")

        label = ttk.Label(frame, text="Ścieżka do karty z multimediami:", font=("Calibri", 12))
        label.grid(row=0, column=0, sticky="w")

        self.media_path_entry = ttk.Entry(frame, textvariable=self.media_path_var, width=50)
        self.media_path_entry.grid(row=0, column=1, padx=5)

        browse_button = ttk.Button(frame, text="Wybierz ścieżkę", command=self.browse_media_path)
        browse_button.grid(row=0, column=2, padx=5)

        self.file_info_label = ttk.Label(frame, text="Zawartość:")
        self.file_info_label.grid(row=1, column=0, columnspan=3, sticky="w")

    def create_operation_selection_section(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=2, column=0, columnspan=2, pady=2, sticky="ew")

        label = ttk.Label(frame, text="Operacja:", font=("Calibri", 12))
        label.grid(row=0, column=0, sticky="w")

        copy_radio = ttk.Radiobutton(frame, text="Kopiowanie", variable=self.operation_var, value="Kopiowanie")
        copy_radio.grid(row=0, column=1, padx=5)
        move_radio = ttk.Radiobutton(frame, text="Przenoszenie", variable=self.operation_var, value="Przenoszenie")
        move_radio.grid(row=0, column=2, padx=5)

    def create_buffer_size_section(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=3, column=0, columnspan=2, pady=2, sticky="ew")

        label = ttk.Label(frame, text="Rozmiar bufora:", font=("Calibri", 12))
        label.grid(row=0, column=0, sticky="w")

        buffer_small = ttk.Radiobutton(frame, text="Mały (128 KB)", variable=self.buffer_var, value="Mały (128 KB)")
        buffer_small.grid(row=0, column=1, padx=5)
        buffer_medium = ttk.Radiobutton(frame, text="Średni (512 KB)", variable=self.buffer_var,
                                        value="Średni (512 KB)")
        buffer_medium.grid(row=0, column=2, padx=5)
        buffer_large = ttk.Radiobutton(frame, text="Duży (1 MB)", variable=self.buffer_var, value="Duży (1 MB)")
        buffer_large.grid(row=0, column=3, padx=5)
        buffer_dynamic = ttk.Radiobutton(frame, text="Dynamiczny", variable=self.buffer_var, value="Dynamiczny")
        buffer_dynamic.grid(row=0, column=4, padx=5)

        dynamic_tooltip = tk.Label(frame, text="(automatycznie dopasuje się do rozmiaru plików)", font=("Calibri", 8),
                                   foreground="gray")
        dynamic_tooltip.grid(row=1, column=4, padx=5)

    def create_naming_format_section(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=4, column=0, columnspan=2, pady=2, sticky="ew")

        label = ttk.Label(frame, text="Format nazwy folderu:", font=("Calibri", 12))
        label.grid(row=0, column=0, sticky="w")

        date_source_radio = ttk.Radiobutton(frame, text="Data i źródło", variable=self.naming_var,
                                            value="Data i źródło")
        date_source_radio.grid(row=0, column=1, padx=5)
        date_range_radio = ttk.Radiobutton(frame, text="Zakres dat i źródło", variable=self.naming_var,
                                           value="Zakres dat i źródło")
        date_range_radio.grid(row=0, column=2, padx=5)

        self.use_exif_radio = ttk.Radiobutton(frame, text="Odczytaj datę z EXIF", variable=self.use_exif_var,
                                              value=True)
        self.use_exif_radio.grid(row=1, column=1, padx=5)

        self.use_filename_radio = ttk.Radiobutton(frame, text="Odczytaj datę z nazwy pliku", variable=self.use_exif_var,
                                                  value=False)
        self.use_filename_radio.grid(row=1, column=2, padx=5)

        self.date_source_frame = ttk.Frame(frame)
        self.date_source_frame.grid(row=2, column=0, columnspan=3, sticky="w")

        self.date_source_label = ttk.Label(self.date_source_frame, text="Daty:", font=("Calibri", 12))
        self.date_source_label.grid(row=0, column=0, sticky="w")

        self.date_source_dynamic = ttk.Label(self.date_source_frame, textvariable=self.date_source_var,
                                             font=("Calibri", 12))
        self.date_source_dynamic.grid(row=0, column=1, sticky="w")

    def create_suffix_options_section(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=5, column=0, columnspan=2, pady=2, sticky="ew")

        suffix_checkbox = ttk.Checkbutton(frame, text="Dodaj P, M, PM do nazwy katalogu", variable=self.suffix_var)
        suffix_checkbox.grid(row=0, column=0, sticky="w")

    def create_subfolder_options_section(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=6, column=0, columnspan=2, pady=2, sticky="ew")

        single_folder_radio = ttk.Radiobutton(frame, text="Wszystkie pliki w jednym katalogu",
                                              variable=self.subfolder_var,
                                              value="Wszystkie pliki w jednym katalogu")
        single_folder_radio.grid(row=0, column=0, padx=5)
        daily_subfolder_radio = ttk.Radiobutton(frame, text="Twórz podkatalogi na każdy dzień",
                                                variable=self.subfolder_var,
                                                value="Twórz podkatalogi na każdy dzień")
        daily_subfolder_radio.grid(row=0, column=1, padx=5)

    def create_destination_path_section(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=7, column=0, columnspan=2, pady=2, sticky="ew")

        label = ttk.Label(frame, text="Lokalizacja wygenerowanego katalogu:", font=("Calibri", 12))
        label.grid(row=0, column=0, sticky="w")

        dest_path_entry = ttk.Entry(frame, textvariable=self.dest_path_var, width=50)
        dest_path_entry.grid(row=0, column=1, padx=5)

        browse_button = ttk.Button(frame, text="Wybierz lokalizację", command=self.browse_dest_path)
        browse_button.grid(row=0, column=2, padx=5)

    def create_additional_options_section(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=8, column=0, columnspan=2, pady=2, sticky="ew")

        open_folder_checkbox = ttk.Checkbutton(frame, text="Otwórz folder po zakończeniu",
                                               variable=self.open_folder_var)
        open_folder_checkbox.grid(row=0, column=0, sticky="w")

        log_file_checkbox = ttk.Checkbutton(frame, text="Generuj plik log", variable=self.log_file_var)
        log_file_checkbox.grid(row=0, column=1, sticky="w")

    def create_file_list_output_section(self):
        label = ttk.Label(self.root, text="Lista skopiowanych plików:", font=("Calibri", 12))
        label.grid(row=9, column=0, sticky="w")

        self.file_list_text = scrolledtext.ScrolledText(self.root, width=60, height=10, wrap=tk.WORD)
        self.file_list_text.grid(row=10, column=0, columnspan=2, pady=2, sticky="ew")

    def create_action_buttons_section(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=11, column=0, columnspan=2, pady=2, sticky="ew")

        action_button = ttk.Button(frame, text="Utwórz i kopiuj multimedia", command=self.start_file_operation)
        action_button.grid(row=0, column=1, padx=5)

    def create_footer_section(self):
        canvas = tk.Canvas(self.root, height=40, bg="#D3D3D3", highlightthickness=0)
        canvas.grid(row=12, column=1, sticky="se")

        self.footer_text = canvas.create_text(250, 20, text="Jarek J.", font=("Calibri", 10), anchor="e")

        canvas.tag_bind(self.footer_text, '<Double-1>', self.show_footer_popup)

    @staticmethod
    def show_footer_popup(_):
        messagebox.showinfo("Info", "Jarosław Jankowski - 2024r")

    def load_sources(self):
        try:
            with open("source.txt", "r", encoding="utf-8") as file:
                self.sources = [line.strip() for line in file.readlines()]
        except FileNotFoundError:
            self.sources = []

    def add_source(self):
        new_source = simpledialog.askstring("Dodaj nowe źródło", "Wprowadź nazwę źródła (np. Telewizor Pokój):")
        if new_source:
            short_name = simpledialog.askstring("Skrót", "Podaj skróconą nazwę (np. Tel_Pok):")
            if short_name:
                source_entry = f"{new_source} ({short_name})"
                self.sources.append(source_entry)
                self.source_combobox["values"] = self.sources
                self.save_sources()

    def remove_source(self):
        selected_source = self.source_combobox.get()
        confirm = messagebox.askyesno("Potwierdzenie", f"Czy na pewno chcesz usunąć źródło '{selected_source}'?")
        if confirm:
            if selected_source in self.sources:
                self.sources.remove(selected_source)
                self.source_combobox.set('')
                self.source_combobox["values"] = self.sources
                self.save_sources()
                messagebox.showinfo("Sukces", f"Źródło '{selected_source}' zostało usunięte.")
            else:
                messagebox.showwarning("Błąd", "Nie wybrano źródła lub źródło nie istnieje na liście.")

    def save_sources(self):
        with open("source.txt", "w", encoding="utf-8") as file:
            for source in self.sources:
                file.write(source + "\n")

    def browse_media_path(self):
        path = filedialog.askdirectory()
        if path:
            self.media_path_var.set(path)
            self.display_file_info(path)
            self.analyze_files(path)

    def display_file_info(self, path):
        total_size = 0
        file_count = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for file in filenames:
                file_path = os.path.join(dirpath, file)
                total_size += os.path.getsize(file_path)
                file_count += 1
        self.file_info_label.config(text=f"Zawartość: Liczba plików: {file_count}, Łączny rozmiar: "
                                         f"{total_size / (1024 * 1024):.2f} MB")

    def analyze_files(self, source_path):
        exif_count = 0
        filename_count = 0
        creation_date_count = 0
        total_files = 0
        unique_dates = set()

        for dirpath, dirnames, filenames in os.walk(source_path):
            for file in filenames:
                total_files += 1
                src_file = os.path.join(dirpath, file)

                date_taken = get_exif_date_taken(src_file)
                if date_taken:
                    exif_count += 1
                else:
                    date_taken = get_date_from_filename(file)
                    if date_taken:
                        filename_count += 1
                    else:
                        date_taken = get_creation_date(src_file)
                        if date_taken:
                            creation_date_count += 1

                if date_taken:
                    unique_dates.add(date_taken)

        if len(unique_dates) > 1:
            self.naming_var.set("Zakres dat i źródło")
            self.subfolder_var.set("Twórz podkatalogi na każdy dzień")
        else:
            self.naming_var.set("Data i źródło")

        if exif_count > 0:
            self.date_source_var.set("EXIF")
        elif filename_count > 0:
            self.date_source_var.set("Nazwa pliku")
        else:
            self.date_source_var.set("Właściwości pliku")

        dates_info = ", ".join(sorted([date.strftime("%Y-%m-%d") for date in unique_dates]))
        messagebox.showinfo("Analiza plików",
                            f"Liczba plików: {total_files}\n"
                            f"Pliki z datą EXIF: {exif_count}\n"
                            f"Pliki z datą w nazwie: {filename_count}\n"
                            f"Pliki z datą utworzenia: {creation_date_count}\n"
                            f"Unikalne daty plików: {dates_info}")

    def browse_dest_path(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_path_var.set(path)

    def start_file_operation(self):
        source_path = self.media_path_var.get()
        dest_path = self.dest_path_var.get()

        if not source_path or not dest_path:
            messagebox.showwarning("Błąd", "Ścieżki muszą być wybrane.")
            return

        copied_files = []
        total_size = 0

        main_folder_name = "backup"

        first_file_date = None
        latest_file_date = None
        for dirpath, dirnames, filenames in os.walk(source_path):
            for file in filenames:
                src_file = os.path.join(dirpath, file)
                date_taken = None
                if self.use_exif_var.get():
                    date_taken = get_exif_date_taken(src_file)
                    if not date_taken:
                        date_taken = get_date_from_filename(file)
                else:
                    date_taken = get_date_from_filename(file)

                if not date_taken:
                    date_taken = get_creation_date(src_file)

                if date_taken:
                    if not first_file_date or date_taken < first_file_date:
                        first_file_date = date_taken
                    if not latest_file_date or date_taken > latest_file_date:
                        latest_file_date = date_taken

        if not first_file_date:
            messagebox.showerror("Błąd", "Nie można ustalić dat dla plików w katalogu źródłowym.")
            return

        if self.naming_var.get() == "Data i źródło":
            source_name_short = self.get_short_name_from_source(self.source_var.get())
            main_folder_name = f"{first_file_date.strftime('%Y-%m-%d')}_{source_name_short}"
        elif self.naming_var.get() == "Zakres dat i źródło":
            source_name_short = self.get_short_name_from_source(self.source_var.get())
            main_folder_name = f"{first_file_date.strftime('%Y-%m-%d')}_do_{latest_file_date.strftime('%Y-%m-%d')}_{source_name_short}"

        main_dest_folder = os.path.join(dest_path, main_folder_name)

        os.makedirs(main_dest_folder, exist_ok=True)

        try:
            for dirpath, dirnames, filenames in os.walk(source_path):
                for file in filenames:
                    src_file = os.path.join(dirpath, file)

                    date_taken = None
                    if self.use_exif_var.get():
                        date_taken = get_exif_date_taken(src_file)
                        if not date_taken:
                            date_taken = get_date_from_filename(file)
                    else:
                        date_taken = get_date_from_filename(file)

                    if not date_taken:
                        date_taken = get_creation_date(src_file)

                    if not date_taken:
                        messagebox.showerror("Błąd", f"Nie można pobrać daty z pliku {file}")
                        return

                    formatted_date = date_taken.strftime("%Y-%m-%d")

                    dest_dir_name = os.path.join(main_dest_folder, formatted_date)

                    os.makedirs(dest_dir_name, exist_ok=True)

                    dest_file = os.path.join(dest_dir_name, file)

                    if self.operation_var.get() == "Kopiowanie":
                        shutil.copy2(src_file, dest_file)
                    elif self.operation_var.get() == "Przenoszenie":
                        shutil.move(src_file, dest_file)

                    copied_files.append(dest_file)
                    total_size += os.path.getsize(dest_file)
                    self.file_list_text.insert(tk.END, f"Skopiowano: {dest_file}\n")

            final_dest_path = self.add_suffix(main_dest_folder)

            if self.log_file_var.get():
                self.generate_log(copied_files, final_dest_path)

            self.show_summary(copied_files, total_size, source_path)

            if self.open_folder_var.get():
                self.open_folder(final_dest_path)

            messagebox.showinfo("Sukces", "Operacja zakończona pomyślnie.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd: {e}")

    @staticmethod
    def get_short_name_from_source(source_entry):
        match = re.search(r"\((.*?)\)", source_entry)
        if match:
            return match.group(1)
        return ""

    def add_suffix(self, dest_folder):
        if not self.suffix_var.get():
            return dest_folder

        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.raw'}
        video_extensions = {'.mp4', '.mov', '.avi'}

        image_found = False
        video_found = False

        for dirpath, dirnames, filenames in os.walk(dest_folder):
            for file in filenames:
                ext = os.path.splitext(file)[1].lower()
                if ext in image_extensions:
                    image_found = True
                elif ext in video_extensions:
                    video_found = True

        new_folder_name = dest_folder

        if image_found and video_found:
            new_folder_name = f"{dest_folder}_PM"
        elif image_found:
            new_folder_name = f"{dest_folder}_P"
        elif video_found:
            new_folder_name = f"{dest_folder}_M"

        if new_folder_name != dest_folder:
            os.rename(dest_folder, new_folder_name)

        return new_folder_name

    def generate_log(self, copied_files, dest_folder):
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder, exist_ok=True)

        log_file_name = f"LOG-kopiowania do katalogu {os.path.basename(dest_folder)}.txt"
        log_file_path = os.path.join(dest_folder, log_file_name)

        try:
            with open(log_file_path, "w", encoding="utf-8") as log_file:
                log_file.write(f"Operacja: {self.operation_var.get()}\n")
                log_file.write(f"Rozmiar bufora: {self.buffer_var.get()}\n")
                log_file.write(f"Format nazwy folderu: {self.naming_var.get()}\n")
                log_file.write(f"Dodaj sufiks: {self.suffix_var.get()}\n")
                log_file.write(f"Twórz podkatalogi: {self.subfolder_var.get()}\n\n")
                log_file.write("Lista skopiowanych plików:\n")
                for file in copied_files:
                    log_file.write(f"{file}\n")
            self.file_list_text.insert(tk.END, f"\nLog zapisany: {log_file_path}\n")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać pliku logu: {e}")

    @staticmethod
    def show_summary(copied_files, total_size, source_path):
        source_file_count = sum([len(files) for r, d, files in os.walk(source_path)])
        source_total_size = sum(
            [os.path.getsize(os.path.join(r, file)) for r, d, files in os.walk(source_path) for file in files])

        messagebox.showinfo("Podsumowanie",
                            f"Skopiowano plików: {len(copied_files)}\n"
                            f"Łączny rozmiar: {total_size / (1024 * 1024):.2f} MB\n\n"
                            f"W katalogu źródłowym: {source_file_count} plików\n"
                            f"Łączny rozmiar: {source_total_size / (1024 * 1024):.2f} MB")

    @staticmethod
    def open_folder(path):
        if os.name == 'nt':  # Windows
            os.startfile(path)
        elif os.name == 'posix':  # macOS or Linux
            subprocess.Popen(['xdg-open', path])


if __name__ == "__main__":
    root_window = tk.Tk()
    app = ImporterApp(root_window)
    root_window.mainloop()
