#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


# EyeD3Tk  <https://github.com/cquickstad/EyeD3Tk>
# Copyright (C) 2018  Chad Quickstad

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from argparse import ArgumentParser
from eyed3 import load
from eyed3.id3 import Genre, ID3_DEFAULT_VERSION
from eyed3.id3.frames import ImageFrame
from tkinter import Tk, Label, Button, Entry, Frame, StringVar, filedialog, \
    LEFT, CENTER, RIGHT, X, END, DISABLED, NORMAL
from PIL import ImageTk, Image
from io import BytesIO
from os.path import isfile
import magic

app_title = "EyeD3Tk"

# Too bad EydD3 library didn't use the Enum class for these values
ID3_IMG_TYPES = ("OTHER", "ICON", "OTHER_ICON", "FRONT_COVER", "BACK_COVER", "LEAFLET", "MEDIA", "LEAD_ARTIST",
                 "ARTIST", "CONDUCTOR", "BAND", "COMPOSER", "LYRICIST", "RECORDING_LOCATION", "DURING_RECORDING",
                 "DURING_PERFORMANCE", "VIDEO", "BRIGHT_COLORED_FISH", "ILLUSTRATION", "BAND_LOGO", "PUBLISHER_LOGO")


class MainWindow:
    no_img_txt = "FRONT_COVER: No Image"

    mp3_file_types = [('MP3 Audio Files', '*.mp3 *.MP3'),
                      ('All Files', "*")]

    img_file_types = [('ID3-Compatible Images', '*.jpg *.JPG *.jpeg *.JPEG *.png *.PNG'),
                      ('All Files', "*")]

    jpg_file_types = [('JPEG Image', '*.jpg *.JPG *.jpeg *.JPEG')]

    png_file_types = [('PNG Image', '*.png *.PNG')]

    id3_gui_fields = (('title', "Title:"),
                      ('artist', "Artist:"),
                      ('album', "Album:"),
                      ('album_artist', "Album Artist:"),
                      ('original_release_date', "Original Release Date:"),
                      ('release_date', "Release Date:"),
                      ('recording_date', "Recording Date:"),
                      ('track_num', "Track:"),
                      ('num_tracks', "Tracks in Album:"),
                      ('genre', "Genre:"),
                      ('comments', "Comments:"))

    def __init__(self, root, cmd_line_mp3_file):
        self.cmd_line_mp3_file = cmd_line_mp3_file
        self.master = root
        self.master.title(app_title)

        self.file_frame, self.file_button, self.mp3_file_sv, self.file_entry = None, None, None, None
        self.build_mp3_file_frame()

        self.id3_section_frame, self.id3_section_label = None, None
        self.build_id3_section_frame()

        self.id3_frame = dict()
        self.id3_entry = dict()
        self.id3_label = dict()
        for field, text in self.id3_gui_fields:
            self.create_id3_field_gui_element(field, text)

        self.front_cover_frame, self.image_description_sv = None, None
        self.image_dimension_label, self.extract_image_button = None, None
        self.build_front_cover_frame()

        self.new_front_cover_frame, self.new_front_cover_button, self.remove_button = None, None, None
        self.new_front_cover_sv, self.new_front_cover_entry = None, None
        self.build_new_front_cover_frame()

        self.save_button = None
        self.build_save_button()

        self.tk_label_for_img = None
        self.audio_file = None
        self.tk_img = None
        self.image_file = None

        self.fld_val = dict()

        self.open_cmd_line_file()

    def build_mp3_file_frame(self):
        self.file_frame = Frame(self.master)
        self.file_frame.pack(fill=X)

        self.file_button = Button(self.file_frame, text="MP3 File...", command=self.file_select_button_action)
        self.file_button.pack(side=LEFT)

        self.mp3_file_sv = StringVar()
        self.file_entry = Entry(self.file_frame, width=75, textvariable=self.mp3_file_sv)
        self.file_entry.bind('<Return>', lambda _: self.file_entry_return_key_action())
        self.file_entry.pack(fill=X)
        self.mp3_file_sv.set("...select a file...")

    def build_id3_section_frame(self):
        self.id3_section_frame = Frame(self.master)
        self.id3_section_frame.pack(fill=X)

        self.id3_section_label = Label(self.id3_section_frame, text="--- ID3 Tag ---", justify=CENTER)
        self.id3_section_label.pack(fill=X)

    def build_front_cover_frame(self):
        self.front_cover_frame = Frame(self.master)
        self.front_cover_frame.pack(fill=X)

        self.image_description_sv = StringVar()
        self.image_description_sv.set(self.no_img_txt)
        self.image_dimension_label = Label(self.front_cover_frame, textvariable=self.image_description_sv)
        self.image_dimension_label.pack()
        self.extract_image_button = Button(self.front_cover_frame, text="Extract All Images to Files",
                                           state=DISABLED, command=self.extract_images_button_action)
        self.extract_image_button.pack()

    def build_new_front_cover_frame(self):
        self.new_front_cover_frame = Frame(self.master)
        self.new_front_cover_frame.pack(fill=X)

        self.new_front_cover_button = Button(self.new_front_cover_frame, text="New Front Cover ...",
                                             command=self.new_front_cover_button_action)
        self.new_front_cover_button.pack(side=LEFT)
        self.remove_button = Button(self.new_front_cover_frame, text="Remove All Images",
                                    command=self.remove_button_action)
        self.remove_button.pack(side=RIGHT)
        self.new_front_cover_sv = StringVar()
        self.new_front_cover_entry = Entry(self.new_front_cover_frame, width=50, textvariable=self.new_front_cover_sv)
        self.new_front_cover_entry.bind('<Return>', lambda _: self.img_entry_return_key_action())
        self.new_front_cover_entry.pack(fill=X)

    def build_save_button(self):
        self.save_button = Button(self.master, text="Save to MP3 File", command=self.save_button_action)
        self.save_button.pack(fill=X)

    def open_cmd_line_file(self):
        if len(self.cmd_line_mp3_file) == 0:
            self.new_front_cover_sv.set("... select a file ...")
        else:
            if isfile(self.cmd_line_mp3_file):
                self.mp3_file_sv.set(self.cmd_line_mp3_file)
                self.open_mp3_file()
            else:
                self.mp3_file_sv.set("Invalid file path: '" + self.cmd_line_mp3_file + "'")

    def create_id3_field_gui_element(self, name, text):
        self.id3_frame[name] = Frame(self.master)
        self.id3_frame[name].pack(fill=X)
        self.id3_label[name] = Label(self.id3_frame[name], text=text, anchor='e', width=17)
        self.id3_label[name].pack(side=LEFT)
        self.id3_entry[name] = Entry(self.id3_frame[name])
        self.id3_entry[name].pack(fill=X)

    def file_select_button_action(self):
        new_path = filedialog.askopenfilename(parent=self.file_frame, filetypes=self.mp3_file_types)
        self.mp3_file_sv.set(new_path)
        self.open_mp3_file()

    def new_front_cover_button_action(self):
        new_path = filedialog.askopenfilename(parent=self.new_front_cover_frame, filetypes=self.img_file_types)
        self.new_front_cover_sv.set(new_path)
        with open(new_path, 'rb') as self.image_file:
            self.display_image_file()
        self.put_new_image_into_tag()

    def extract_images_button_action(self):
        self.try_to_extract_id3_images_to_files()

    def try_to_extract_id3_images_to_files(self):
        try:
            self.extract_id3_images_to_files()
        except AttributeError:
            pass

    def extract_id3_images_to_files(self):
        for info in self.audio_file.tag.images:
            self.extract_id3_image_to_file(info)

    def extract_id3_image_to_file(self, info):
        def_ext, ftypes = self.get_image_file_extension(info)
        path = filedialog.asksaveasfilename(parent=self.front_cover_frame,
                                            defaultextension=def_ext,
                                            initialfile=self.get_initial_image_file_name(info),
                                            filetypes=ftypes)
        if path is not None and path != "":
            with open(path, 'wb') as img_file:
                img_file.write(info.image_data)

    def get_image_file_extension(self, info):
        img = Image.open(BytesIO(info.image_data))
        default_extension = "." + str(img.format).lower()
        file_types = []
        if default_extension == ".jpeg":
            file_types = self.jpg_file_types
        elif default_extension == ".png":
            file_types = self.png_file_types
        return default_extension, file_types

    def get_initial_image_file_name(self, info):
        name = ID3_IMG_TYPES[info.picture_type]
        if info.description != "":
            name = info.description + '.' + name
        return name

    def open_mp3_file(self):
        self.clear_gui_tag_entry_elements()
        self.try_to_open_mp3_file()
        if self.audio_file:
            self.load_tag_into_gui()

    def try_to_open_mp3_file(self):
        try:
            self.audio_file = load(self.file_entry.get())
        except IOError:
            self.audio_file = None
            self.mp3_file_sv.set("No file selected!")

    def load_tag_into_gui(self):
        self.init_id3_tag()
        self.put_tag_fields_in_gui_entries()
        self.try_to_open_id3_tag_image_as_file_io()
        if self.image_file is None:
            self.clear_image_from_gui()
        else:
            self.display_image_file()

    def save_button_action(self):
        self.gui_fields_to_fld_val()

        for key, val in self.fld_val.items():
            print(key, ":", val)

        tag = self.audio_file.tag
        tag.version = ID3_DEFAULT_VERSION

        # These fields are assigned normally
        tag.title = self.fld_val['title']
        tag.artist = self.fld_val['artist']
        tag.album = self.fld_val['album']
        tag.album_artist = self.fld_val['album_artist']
        tag.original_release_date = self.fld_val['original_release_date']
        tag.release_date = self.fld_val['release_date']
        tag.recording_date = self.fld_val['recording_date']

        # These fields need some converting or special assignments
        tag.genre = Genre(self.fld_val['genre'])
        tag.track_num = (self.fld_val['track_num'], self.fld_val['num_tracks'])
        if self.fld_val['comments'] is not None and self.fld_val['comments'] != "":
            tag.comments.set(self.fld_val['comments'])

        tag.save(encoding="utf_8")

    def init_id3_tag(self):
        if self.audio_file.tag is None:
            self.audio_file.initTag()

    def clear_gui_tag_entry_elements(self):
        for key, entry in self.id3_entry.items():
            entry.delete(0, END)
        self.clear_image_from_gui()

    def clear_image_from_gui(self):
        self.image_description_sv.set(self.no_img_txt)
        self.extract_image_button['state'] = DISABLED
        if self.tk_label_for_img is not None:
            self.tk_label_for_img.pack_forget()

    def put_tag_fields_in_gui_entries(self):
        self.id3_tag_to_fld_val()
        self.fld_val_to_gui_fields()

    def id3_tag_to_fld_val(self):
        tag = self.audio_file.tag
        self.fld_val['title'] = self.tag_to_str(tag.title)
        self.fld_val['artist'] = self.tag_to_str(tag.artist)
        self.fld_val['album'] = self.tag_to_str(tag.album)
        self.fld_val['album_artist'] = self.tag_to_str(tag.album_artist)
        self.fld_val['original_release_date'] = self.tag_to_str(tag.original_release_date)
        self.fld_val['release_date'] = self.tag_to_str(tag.release_date)
        self.fld_val['recording_date'] = self.tag_to_str(tag.recording_date)

        self.fld_val['genre'] = "" if tag.genre is None else self.tag_to_str(tag.genre.name)
        self.fld_val['track_num'] = "" if tag.track_num is None or len(tag.track_num) < 1 \
            else self.tag_to_str(tag.track_num[0])
        self.fld_val['num_tracks'] = "" if tag.track_num is None or len(tag.track_num) < 2 \
            else self.tag_to_str(tag.track_num[1])
        self.id3_comments_to_fld_val()

    def tag_to_str(self, tag_element):
        return "" if tag_element is None else str(tag_element)

    def id3_comments_to_fld_val(self):
        self.fld_val['comments'] = ""
        for comment_accessor in self.audio_file.tag.comments:
            if comment_accessor.description != "":
                self.fld_val['comments'] += comment_accessor.description + ": "
            self.fld_val['comments'] += self.tag_to_str(comment_accessor.text)

    def fld_val_to_gui_fields(self):
        for field, _ in self.id3_gui_fields:
            self.id3_entry[field].insert(0, self.fld_val[field])

    def display_image_file(self):
        img = Image.open(self.image_file)
        original_dimensions = img.size
        img = img.resize((200, 200), Image.ANTIALIAS)
        self.tk_img = ImageTk.PhotoImage(img)
        if self.tk_label_for_img is None:
            self.tk_label_for_img = Label(self.front_cover_frame, image=self.tk_img)
        else:
            self.tk_label_for_img.configure(image=self.tk_img)
        self.tk_label_for_img.pack()
        self.image_description_sv.set("FRONT_COVER: {} x {}".format(original_dimensions[0], original_dimensions[1]))
        self.extract_image_button['state'] = NORMAL

    def file_entry_return_key_action(self):
        self.open_mp3_file()

    def try_to_open_id3_tag_image_as_file_io(self):
        try:
            self.open_id3_tag_image_as_file_io()
        except AttributeError:
            pass

    def open_id3_tag_image_as_file_io(self):
        self.image_file = None
        for i, info in enumerate(self.audio_file.tag.images):
            if self.should_display_image(i, info):
                self.image_file = BytesIO(info.image_data)
                break

    def img_entry_return_key_action(self):
        new_path = self.new_front_cover_sv.get()
        with open(new_path, 'rb') as self.image_file:
            self.display_image_file()
        self.put_new_image_into_tag()

    def remove_button_action(self):
        self.image_file = None
        self.clear_image_from_gui()
        self.remove_all_images_from_id3_tag()

    def remove_all_images_from_id3_tag(self):
        for description in [info.description for info in self.audio_file.tag.images]:
            self.audio_file.tag.images.remove(description)

    def put_new_image_into_tag(self):
        if isfile(self.new_front_cover_sv.get()):
            image_data = open(self.new_front_cover_sv.get(), 'rb').read()
            self.audio_file.tag.images.set(ImageFrame.FRONT_COVER, image_data, self.get_new_front_cover_mime_type())

    def should_display_image(self, image_idx, img_info):
        is_front_cover = img_info.picture_type == ImageFrame.FRONT_COVER
        is_last_picture = image_idx + 1 == len(self.audio_file.tag.images)
        return is_front_cover or is_last_picture

    def get_new_front_cover_mime_type(self):
        # return magic.detect_from_filename(self.new_front_cover_sv.get()).mime_type  # older magic version
        return magic.from_file(self.new_front_cover_sv.get(), mime=True)  # newer magic version

    def gui_fields_to_fld_val(self):
        for field, _ in self.id3_gui_fields:
            self.fld_val[field] = str(self.id3_entry[field].get())
            if "track" in field:
                if self.fld_val[field] in ("0", ""):
                    self.fld_val[field] = None
                else:
                    self.fld_val[field] = int(self.fld_val[field])
            if "date" in field:
                if self.fld_val[field] == "":
                    self.fld_val[field] = None


def parse_arguments():
    ap = ArgumentParser(description=app_title)
    ap.add_argument('mp3_file', nargs='?', type=str, default="", help="MP3 file to edit")
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    root = Tk()
    mw = MainWindow(root, args.mp3_file)
    root.mainloop()
