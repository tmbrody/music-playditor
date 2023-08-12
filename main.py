import tkinter as tk
from tkinter import Canvas, filedialog, BOTH
import os
import pygame
import configparser
import random

pygame.init()

class MusicPlayerWindow:
    def __init__(self, root, width=1920, height=1080):
        self.play_button = tk.PhotoImage(file="icons/play.png")
        self.pause_button = tk.PhotoImage(file="icons/pause.png")
        self.next_track_button = tk.PhotoImage(file="icons/next_track.png")
        self.previous_track_button = tk.PhotoImage(file="icons/previous_track.png")
        self.shuffle_button = tk.PhotoImage(file="icons/shuffle.png")
        self.no_shuffle_button = tk.PhotoImage(file="icons/no_shuffle.png")
        self.repeat_all_button = tk.PhotoImage(file="icons/repeat_all.png")
        self.repeat_one_button = tk.PhotoImage(file="icons/repeat_one.png")
        self.no_repeat_button = tk.PhotoImage(file="icons/no_repeat.png")
    
        self.__width = width
        self.__height = height
        self.__root = root
        self.__root.title("Music Playditor")

        self.__last_directory = None
        self.__current_index = None
        self.__last_played_file = None
        self.__file_list = None
        self.__directory = None
        self.__starting = True
        self.__play_state = {"paused": True,
                             "repeating": False,
                             "shuffle": False}

        self.__options_frame = tk.Frame(self.__root)
        self.__options_frame.pack(fill=tk.BOTH, expand=True)

        self.__load_button = HoverButton(self.__options_frame, text="Load", command=self.load_files, relief="flat")
        self.__load_button.pack(side=tk.LEFT, anchor=tk.NW)

        self.__edit_button = HoverButton(self.__options_frame, text="Edit", relief="flat")
        self.__edit_button.pack(side=tk.LEFT, anchor=tk.NW, padx=(0, 900))

        self.__shuffle_button = HoverButton(self.__options_frame, image=self.no_shuffle_button, relief="flat", 
                                            command=lambda: self.toggle_playback(self.__shuffle_button, self.no_shuffle_button, self.shuffle_button, "shuffle"))
        self.__shuffle_button.pack(side=tk.LEFT, anchor=tk.NW)

        self.__previous_track_button = HoverButton(self.__options_frame, image=self.previous_track_button, relief="flat", command=self.play_selected_file)
        self.__previous_track_button.pack(side=tk.LEFT, anchor=tk.NW)
        self.__root.bind("<p>", self.play_selected_file)

        self.__play_button = HoverButton(self.__options_frame, image=self.play_button, relief="flat", 
                                         command=lambda: self.pause_play_track(self.__play_button, self.pause_button, self.play_button, "paused"))
        self.__play_button.pack(side=tk.LEFT, anchor=tk.NW)
        self.__root.bind("<space>", lambda event: self.pause_play_track(self.__play_button, self.pause_button, self.play_button, "paused"))

        self.__next_track_button = HoverButton(self.__options_frame, image=self.next_track_button, command=self.play_next, relief="flat")
        self.__next_track_button.pack(side=tk.LEFT, anchor=tk.NW)
        self.__root.bind("<n>", self.play_next)

        self.__repeat_button = HoverButton(self.__options_frame, image=self.no_repeat_button, relief="flat", 
                                            command=lambda: self.toggle_playback(self.__repeat_button, self.no_repeat_button, self.repeat_one_button, "repeating"))
        self.__repeat_button.pack(side=tk.LEFT, anchor=tk.NW)


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
        self.__config.read("config.ini", encoding="utf-8")

        self.__audio_finished_event = pygame.USEREVENT + 1

        pygame.mixer.music.set_endevent(self.__audio_finished_event)

        if self.__config.has_section("Settings") and self.__config.has_option("Settings", "last_directory"):
            self.__last_directory = self.__config.get("Settings", "last_directory")
            self.__last_played_file = self.__config.get("Settings", "last_played_file", fallback="")
            self.load_files()
            if self.__last_played_file:
                index = self.__file_list.index(self.__last_played_file)
                self.__file_listbox.select_set(index)
                self.play_file_at_index(index)

        self.__root.after(100, self.check_audio_finished)

        if self.__config.has_option("Settings", "scrollbar_position"):
            scrollbar_position = float(self.__config.get("Settings", "scrollbar_position"))
            self.__file_listbox.yview_moveto(scrollbar_position)

        if self.__file_list:
            for index in range(len(self.__file_list)):
                if index % 2 == 0:
                    bg_color = "white"
                else:
                    bg_color = "light gray"
                self.__file_listbox.itemconfigure(index, background=bg_color)

    def pause_play_track(self, button, button_icon1, button_icon2, bool, event=None):
        if self.__play_state[bool]:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

        self.toggle_playback(button, button_icon1, button_icon2, bool)

    def toggle_playback(self, button, button_icon1, button_icon2, bool, event=None):
        self.__play_state[bool] = not self.__play_state[bool]
        current_image = button.cget("image")
        new_image = button_icon2 if str(current_image) == str(button_icon1) else button_icon1
        button.config(image=new_image)

    def load_files(self):
        if not self.__last_directory or not self.__starting:
            self.__directory = filedialog.askdirectory(initialdir=self.__last_directory)
        else:
            self.__directory = self.__last_directory

        if self.__directory:
            self.__last_directory = self.__directory

            if not self.__config.has_section("Settings"):
                self.__config.add_section("Settings")

            self.__config.set("Settings", "last_directory", self.__last_directory)
            with open("config.ini", "w", encoding="utf-8") as configfile:
                self.__config.write(configfile)
            
            self.__file_listbox.delete(0, tk.END)
            self.__file_list = os.listdir(self.__directory)

        if self.__file_list:
            for file_name in self.__file_list:
                self.__file_listbox.insert(tk.END, file_name)

    def check_audio_finished(self):
        for event in pygame.event.get():
            if event.type == self.__audio_finished_event:
                self.play_next(None)
        self.__root.after(100, self.check_audio_finished)

    def play_selected_file(self, event=None):
        self.__play_button.config(image=self.pause_button)
        if self.__play_state["paused"]:
            self.__play_state["paused"] = not self.__play_state["paused"]

        selected_index = self.__file_listbox.curselection()
        self.__current_index = selected_index[0]
        if selected_index:
            selected_file = self.__file_list[selected_index[0]]
            if selected_file.lower().endswith(('.mp3', '.wav')):
                self.__root.title(f"Music Playditor - {selected_file}")
                self.__last_played_file = selected_file
                self.play_file(selected_file)

                self.__config.set("Settings", "last_played_file", self.__last_played_file)
                with open("config.ini", "w", encoding="utf-8") as configfile:
                    self.__config.write(configfile)

    def play_file(self, file):
        pygame.mixer.music.load(os.path.join(self.__directory, file))
        pygame.mixer.music.play()

    def play_next(self, event=None):
        if self.__current_index is not None:
            if not self.__play_state["repeating"]:
                increase_by = 1
                if self.__play_state["shuffle"]:
                    increase_by = random.randint(1, len(self.__file_list) - 1)

                next_index = (self.__current_index + increase_by) % len(self.__file_list)
                self.__root.title(f"Music Playditor - {self.__file_list[next_index]}")

                self.__file_listbox.selection_clear(0, tk.END)
                self.play_file_at_index(next_index)

                self.__last_played_file = self.__file_list[next_index]

                self.__file_listbox.see(next_index)
            else:
                self.play_file_at_index(self.__current_index)

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
        if self.__config.has_section("Settings"):
            scrollbar_position = self.__listbox_scrollbar.get()[0]
            self.__config.set("Settings", "scrollbar_position", str(scrollbar_position))
            self.__config.set("Settings", "last_played_file", self.__last_played_file)

            with open("config.ini", "w", encoding="utf-8") as configfile:
                self.__config.write(configfile)

        self.__root.destroy()

class HoverButton(tk.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.transition_duration = 200
        self.transition_steps = 50

    def on_enter(self, event=None):
        self.transition_to_color("lightblue")

    def on_leave(self, event=None):
        self.transition_to_color("SystemButtonFace")

    def transition_to_color(self, target_color):
        current_color = self.cget("bg")
        target_rgb = self.winfo_rgb(target_color)
        current_rgb = self.winfo_rgb(current_color)
        step_rgb = [(target - current) / self.transition_steps for target, current in zip(target_rgb, current_rgb)]
        self.transition_step(current_rgb, step_rgb, 0)

    def transition_step(self, current_rgb, step_rgb, step):
        if step >= self.transition_steps:
            return
        new_rgb = tuple(int(current + step * step_value) for current, step_value in zip(current_rgb, step_rgb))
        new_color = "#%02x%02x%02x" % new_rgb
        self.config(bg=new_color)
        self.after(self.transition_duration // self.transition_steps, self.transition_step, current_rgb, step_rgb, step + 1)

if __name__ == "__main__":
    root = tk.Tk()
    music_player = MusicPlayerWindow(root)
    root.mainloop()