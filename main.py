import tkinter as tk
from tkinter import Canvas, filedialog, BOTH
import os
import pygame
import configparser

pygame.init()

class MusicPlayerWindow:
    def __init__(self, root, width=1920, height=1080):
        self.__width = width
        self.__height = height
        self.__root = root
        self.__root.title("Music Playditor")

        self.__file_list = None
        self.__directory = None
        self.__paused = False
        self.__starting = True

        self.__play_button = tk.Button(self.__root, text="▶")
        self.__play_button.pack(side=tk.TOP, anchor=tk.N)
        self.__root.bind("<space>", self.on_space_press)

        self.__load_button = tk.Button(self.__root, text="Load", command=self.load_files)
        self.__load_button.pack(side=tk.TOP, anchor=tk.NW)

        self.__listbox_frame = tk.Frame(self.__root)
        self.__listbox_frame.pack(fill=BOTH, expand=True)

        self.__file_listbox = tk.Listbox(self.__listbox_frame, background="SystemButtonFace", width=int(self.__width * 0.17) , height=self.__height)
        self.__file_listbox.pack(side=tk.LEFT)
        self.__file_listbox.bind("<Double-Button-1>", self.play_selected_file)

        self.__listbox_scrollbar = tk.Scrollbar(self.__listbox_frame, orient=tk.VERTICAL, command=self.__file_listbox.yview)
        self.__listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.__file_listbox.config(yscrollcommand=self.__listbox_scrollbar.set)

        self.__canvas = Canvas(self.__root, width=self.__width, height=self.__height)
        self.__canvas.pack()
        self.__root.protocol("WM_DELETE_WINDOW", self.close)

        self.__config = configparser.ConfigParser()
        self.__config.read("config.ini")
        self.__last_directory = self.__config.get("Settings", "last_directory", fallback="")
        self.__last_played_file = self.__config.get("Settings", "last_played_file", fallback="")

        self.__current_index = None
        self.__audio_finished_event = pygame.USEREVENT + 1

        pygame.mixer.music.set_endevent(self.__audio_finished_event)

        if self.__config.has_section("Settings") and self.__config.has_option("Settings", "last_directory"):
            self.__last_directory = self.__config.get("Settings", "last_directory")
            self.load_files()
            if self.__last_played_file:
                index = self.__file_list.index(self.__last_played_file)
                self.__file_listbox.select_set(index)
                self.play_file_at_index(index)

        self.__root.after(100, self.check_audio_finished)

        if self.__config.has_option("Settings", "scrollbar_position"):
            scrollbar_position = float(self.__config.get("Settings", "scrollbar_position"))
            self.__file_listbox.yview_moveto(scrollbar_position)

    def on_space_press(self, event):
        if self.__paused:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()
        self.toggle_playback()

    def toggle_playback(self):
        self.__paused = not self.__paused
        current_text = self.__play_button.cget("text")
        new_text = "‖" if current_text == "▶" else "▶"
        self.__play_button.config(text=new_text)

    def load_files(self):
        if self.__last_directory == "" or not self.__starting:
            self.__directory = filedialog.askdirectory(initialdir=self.__last_directory)
        else:
            self.__directory = self.__last_directory

        if self.__directory:
            self.__last_directory = self.__directory

            if not self.__config.has_section("Settings"):
                self.__config.add_section("Settings")

            self.__config.set("Settings", "last_directory", self.__last_directory)
            with open("config.ini", "w") as configfile:
                self.__config.write(configfile)
            
            self.__file_listbox.delete(0, tk.END)
            self.__file_list = os.listdir(self.__directory)

        for file_name in self.__file_list:
            self.__file_listbox.insert(tk.END, file_name)

    def check_audio_finished(self):
        for event in pygame.event.get():
            if event.type == self.__audio_finished_event:
                self.play_next(None)
        self.__root.after(100, self.check_audio_finished)

    def play_selected_file(self, event):
        selected_index = self.__file_listbox.curselection()
        self.__current_index = selected_index[0]
        if selected_index:
            selected_file = self.__file_list[selected_index[0]]
            if selected_file.lower().endswith(('.mp3', '.wav')):
                self.__last_played_file = selected_file
                self.play_file(selected_file)

                self.__config.set("Settings", "last_played_file", self.__last_played_file)
                with open("config.ini", "w") as configfile:
                    self.__config.write(configfile)

    def play_file(self, file):
        pygame.mixer.music.load(os.path.join(self.__directory, file))
        pygame.mixer.music.play()

    def play_next(self, event):
        if self.__current_index is not None:
            next_index = (self.__current_index + 1) % len(self.__file_list)

            self.__file_listbox.selection_clear(0, tk.END)
            self.play_file_at_index(next_index)

            self.__last_played_file = self.__file_list[next_index]

            self.__config.set("Settings", "last_played_file", self.__last_played_file)
            with open("config.ini", "w") as configfile:
                self.__config.write(configfile)

    def play_file_at_index(self, index):
        if index < len(self.__file_list) and not self.__starting:
            self.play_file(self.__file_list[index])
            self.__current_index = index
            self.__file_listbox.select_set(index)
        else:
            self.__current_index = index
            self.__file_listbox.select_set(index)
            self.__starting = False

    def close(self):
        scrollbar_position = self.__listbox_scrollbar.get()[0]
        self.__config.set("Settings", "scrollbar_position", str(scrollbar_position))

        with open("config.ini", "w") as configfile:
            self.__config.write(configfile)

        self.__root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    music_player = MusicPlayerWindow(root)
    root.mainloop()