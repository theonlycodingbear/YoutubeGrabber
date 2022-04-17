import math
import os
import sqlite3
from datetime import datetime

import pafy
import tkinter as tk
from tkinter import ttk, messagebox


class DefinitiveGrabber(tk.Tk):
    def __init__(self):
        super().__init__()
        # initial geometry----------------------------------------------------------------------------------------------
        self.title('Youtube grabber')
        self.attributes('-zoomed', True)  # full screen
        self.state('normal')
        self.resizable(width=True, height=True)
        self.config(background='antique white')
        # variables-----------------------------------------------------------------------------------------------------
        self.address = tk.StringVar()
        self.radio_button_type = tk.StringVar()
        self.radio_button_quality = tk.StringVar()
        self.titre_variable = tk.StringVar()
        self.length_variable = tk.StringVar()
        self.progress_value = tk.StringVar()
        self.stuff_to_download = None
        self.file_name = ""
        # database -----------------------------------------------------------------------------------------------------
        self.database = 'list_of_downloaded_stuff'
        # options for widgets-------------------------------------------------------------------------------------------
        opts_labelframe = {'ipadx': 10, 'ipady': 10, 'pady': 10, 'padx': 10, 'sticky': 'nw'}
        opts_widgets = {'ipadx': 5, 'ipady': 5, 'pady': 10, 'padx': 10, 'sticky': 'nw'}
        opts_canvas = {'ipadx': 10, 'ipady': 10, 'pady': 10, 'padx': 10, 'sticky': 'nsew'}
        # config columns------------------------------------------------------------------------------------------------
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        # canvases------------------------------------------------------------------------------------------------------
        canvas_user_input = tk.Canvas(self, bg="cyan")
        canvas_user_input.grid(column=0, row=0, **opts_canvas)

        canvas_file_table = tk.Canvas(self, bg="salmon")
        canvas_file_table.grid(column=1, row=0, rowspan=3, **opts_canvas)

        canvas_choice = tk.Canvas(self, bg="green")
        canvas_choice.grid(column=0, row=1, **opts_canvas)

        canvas_file_info = tk.Canvas(self, bg="pink")
        canvas_file_info.grid(column=0, row=2, **opts_canvas)

        # canvas_user_input - widgets-----------------------------------------------------------------------------------
        self.label_frame_address = tk.LabelFrame(canvas_user_input, text="Address")
        self.label_frame_address.grid(column=0, row=0, **opts_labelframe)
        self.web_address = tk.Entry(self.label_frame_address, textvariable=self.address)
        self.web_address.grid(row=0, column=2, sticky="we")

        label_frame_type = tk.LabelFrame(canvas_choice, text="Choose what to download")
        label_frame_type.grid(column=0, row=1, **opts_labelframe)
        radio_button_audio = tk.Radiobutton(label_frame_type, text="audio", variable=self.radio_button_type,
                                            value="audio")
        radio_button_audio.grid(column=0, row=2)
        radio_button_video = tk.Radiobutton(label_frame_type, text="video", variable=self.radio_button_type,
                                            value="video")
        radio_button_video.grid(column=1, row=2)
        radio_button_AV = tk.Radiobutton(label_frame_type, text="AV", variable=self.radio_button_type, value="AV")
        radio_button_AV.grid(column=2, row=2)

        grab_button = tk.Button(canvas_choice, text="Grab it", command=self.grab)
        grab_button.grid(column=1, row=1, sticky=tk.E)

        # file_info - widgets-----------------------------------------------------------------------------------
        self.label_frame_info = tk.LabelFrame(canvas_file_info, text="Details")
        self.label_frame_info.grid(column=0, row=0, **opts_labelframe)

        titre_label = tk.Label(self.label_frame_info, text="Title: ")
        titre_label.grid(column=0, row=0, **opts_widgets)
        self.titre = tk.Label(self.label_frame_info, textvariable=self.titre_variable)
        self.titre.grid(column=1, row=0, **opts_widgets)

        self.length_label = tk.Label(self.label_frame_info, text="Length")
        self.length_label.grid(column=0, row=1, **opts_widgets)
        self.song_length = tk.Label(self.label_frame_info, textvariable=self.length_variable)
        self.song_length.grid(column=1, row=1, **opts_widgets)

        # progress bar -------------------------------------------------------------------------------------------------
        self.progressbar_value = tk.Label(self, textvariable=self.progress_value)
        self.progressbar_value.grid(column=0, row=3, **opts_widgets)

        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.grid(columnspan=2, row=4, **opts_canvas)

        # tree ---------------------------------------------------------------------------------------------------------
        self.tree = ttk.Treeview(canvas_file_table, show='headings')  # height=15 takes 1/2 of the screen, that's enough
        self.tree.grid(column=0, row=0, sticky='ne', ipadx=10, ipady=10, padx=10, pady=10)
        self.tree.bind("<Double-Button-1>", self.on_double_click)
        namesColumns = ["index", "format", "definition", "size"]  # returns DB column headers
        namesColumnsTuple = tuple(namesColumns)  # casts the list into a tuple for the self.tree view headings
        self.tree["columns"] = namesColumnsTuple

        self.update_idletasks()
        width = self.tree.winfo_width()
        value = math.floor((width - 20 - 100) / 4)
        dimensionsOfColumns = {'index': 100, 'format': value, 'definition': value, 'size': value}

        for element in namesColumns:
            self.tree.heading(element, text=element, anchor=tk.W)
            self.tree.column(element, width=dimensionsOfColumns.get(element), stretch=True)

        # scrollbar-----------------------------------------------------------------------------------------------------
        vsb = ttk.Scrollbar(canvas_file_table, orient="vertical", command=self.tree.yview)
        vsb.grid(column=1, row=0, sticky="ns")
        self.tree.config(yscrollcommand=vsb.set)

        # buttons ------------------------------------------------------------------------------------------------------
        cancel_button = tk.Button(self, text="Cancel", command=self.cancel_download)
        cancel_button.grid(column=0, row=5)

        self.set_initial_values()

        #############################
        # end of def __init__(self) #
        #############################

    def check_if_already_downloaded(self, web_address, chosen_format):
        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()
        cursor.execute("SELECT web_address, type FROM downloaded_stuff")
        rows = cursor.fetchall()

        for row in rows:
            if row[0] == web_address and row[1] == chosen_format:
                question = messagebox.askquestion("Wait a bit!",
                                                  "You already downloaded that stuff.\nDo you wish to download anyway?")
                if question == "no":
                    exit()

                break
        cursor.close()

    def update_database(self, web_address, type_of_stuff, date):
        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()

        cmdParams = str("INSERT INTO downloaded_stuff (web_address, type, date) VALUES (?, ?, ?)")
        cursor.execute(cmdParams, (web_address, type_of_stuff, date))
        connection.commit()
        cursor.close()

    # button to click after choosing the type of file to DL (audio/video/AV)
    def grab(self):
        web_address = self.address.get()
        selected_option = self.radio_button_type.get()

        self.check_if_already_downloaded(web_address, selected_option)

        pafy_object = pafy.new(web_address)

        if selected_option == "audio":
            self.get_audio(pafy_object)
        elif selected_option == "video":
            self.get_video(pafy_object)
        else:
            self.get_AV(pafy_object)

    def get_audio(self, objet):
        self.stuff_to_download = objet.audiostreams
        self.get_details(objet, self.stuff_to_download)

    def get_video(self, objet):
        self.stuff_to_download = objet.videostreams
        self.get_details(objet, self.stuff_to_download)

    def get_AV(self, objet):
        self.stuff_to_download = objet.streams
        self.get_details(objet, self.stuff_to_download)

    # gets the details of the file to download and populates the tree
    def get_details(self, objet, stream):
        for child in self.tree.get_children():
            self.tree.delete(child)

        title = objet.title
        self.titre_variable.set(title)
        duration = objet.duration
        self.length_variable.set(duration)

        counter = 1  # not sure what it is, but is necessary
        tag = 'white'

        for i in range(len(stream)):
            values_to_insert = []
            resolution = stream[i].resolution
            extension = stream[i].extension
            size = stream[i].get_filesize()
            size_str = str(size / 1024 / 1024) + " MB"
            values_to_insert.append(counter)
            values_to_insert.append(extension)
            values_to_insert.append(resolution)
            values_to_insert.append(size_str)
            self.tree.insert("", "end", str(counter), text=str(counter), values=values_to_insert, tags=(tag,))
            if tag == 'white':
                self.tree.tag_configure(tag, background="#ffffff")  # white color
                tag = 'blue'
            else:
                self.tree.tag_configure(tag, background="#b3e5fc")  # blue color
                tag = 'white'
            counter += 1

    # starts DL when line double clicked in tree
    def on_double_click(self, event):
        row_id = event.widget.focus()
        item = event.widget.item(row_id)
        values = item['values']
        rowID = values[0] - 1

        web_address = self.address.get()
        type_of_file = self.radio_button_type.get()
        date = datetime.now()

        self.update_database(web_address, type_of_file, date)

        self.file_name = str(self.stuff_to_download[rowID].filename)
        # download to the current working directory
        self.stuff_to_download[rowID].download(callback=self.callback)
        # checks whether the file name contains problematic characters and removes them
        self.check_file_name()

    # indicates the progress of the DL, uses a progress bar
    def callback(self, total, received, ratio, rate, eta):
        portion = received / total
        self.update_idletasks()
        self.progress_value.set(portion * 100)
        self.progress['value'] = portion * 100

    def check_file_name(self):
        # the last 2 characters in the list below are NOT identical
        list_of_bad_characters = ["!", "'", "^", "%", "|", "@", ":", "<", ">", "-", "‘", "’"]
        # current directory
        cwd = os.getcwd()
        new_name = ""
        for file in os.listdir(cwd):
            if file == self.file_name:
                for char in self.file_name:
                    if char not in list_of_bad_characters:
                        new_name = new_name + char
                os.rename(self.file_name, new_name)
                break

    # resets the progress bar
    def set_initial_values(self):
        self.update_idletasks()
        self.progress["value"] = 0
        self.progress_value.set("0.0")

        width = math.floor((self.label_frame_address.winfo_width() - 40) * 0.55)
        self.web_address.config(width=width, bg="white")
        self.web_address.focus()

        width = math.floor((self.label_frame_info.winfo_width()) * 0.5)
        self.titre.config(width=width, bg="white")
        self.song_length.config(width=width, bg="white")

    def cancel_download(self):
        raise Exception


if __name__ == "__main__":
    app = DefinitiveGrabber()
    app.mainloop()
