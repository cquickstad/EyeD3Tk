#!/usr/bin/env python3

from argparse import ArgumentParser
from eyed3 import load
from eyed3.id3 import Genre
from eyed3.id3.frames import ImageFrame
from tkinter import Tk, Label, Button, Entry, Frame, StringVar, filedialog, LEFT, CENTER, RIGHT, X, END, DISABLED, \
    NORMAL
from PIL import ImageTk, Image
from io import BytesIO
from os.path import isfile
from magic import Magic

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

    def __init__(self, root, cmd_line_mp3_file):
        self.master = root
        self.master.title(app_title)

        self.file_frame = Frame(self.master)
        self.file_frame.pack(fill=X)

        self.file_button = Button(self.file_frame, text="MP3 File...", command=self.file_select_button_action)
        self.file_button.pack(side=LEFT)

        self.mp3_file_sv = StringVar()
        self.file_entry = Entry(self.file_frame, width=75, textvariable=self.mp3_file_sv)
        self.file_entry.bind('<Return>', lambda _: self.file_entry_return_key_action())
        self.file_entry.pack(fill=X)
        self.mp3_file_sv.set("...select a file...")

        self.id3_section_frame = Frame(self.master)
        self.id3_section_frame.pack(fill=X)

        self.id3_section_label = Label(self.id3_section_frame, text="--- ID3 Tag ---", justify=CENTER)
        self.id3_section_label.pack(fill=X)

        self.id3_frame = dict()
        self.id3_entry = dict()
        self.id3_label = dict()

        self.create_ide_element('title', "Title:")
        self.create_ide_element('artist', "Artist:")
        self.create_ide_element('composer', "Composer:")
        self.create_ide_element('album', "Album:")
        self.create_ide_element('album_artist', "Album Artist:")
        self.create_ide_element('original_release_date', "Original Release Date:")
        self.create_ide_element('release_date', "Release Date:")
        self.create_ide_element('recording_date', "Recording Date:")
        self.create_ide_element('track_num', "Track:")
        self.create_ide_element('num_tracks', "Tracks in Album:")
        self.create_ide_element('genre', "Genre:")
        self.create_ide_element('comments', "Comments:")

        self.front_cover_frame = Frame(self.master)
        self.front_cover_frame.pack(fill=X)

        self.front_cover_img = None

        self.image_description_sv = StringVar()
        self.image_description_sv.set(self.no_img_txt)
        self.image_dimension_label = Label(self.front_cover_frame, textvariable=self.image_description_sv)
        self.image_dimension_label.pack()
        self.extract_image_button = Button(self.front_cover_frame, text="Extract All Images to Files",
                                           state=DISABLED, command=self.extract_images_action)
        self.extract_image_button.pack()

        self.new_front_cover_frame = Frame(self.master)
        self.new_front_cover_frame.pack(fill=X)

        self.new_front_cover_button = Button(self.new_front_cover_frame, text="New Front Cover ...",
                                             command=self.new_front_cover_button_action)
        self.new_front_cover_button.pack(side=LEFT)
        self.remove_button = Button(self.new_front_cover_frame, text="Remove All Images",
                                    command=self.remove_button_action)
        self.remove_button.pack(side=RIGHT)
        self.new_front_cover_sv = StringVar()
        self.new_front_cover_sv.set("... select a file ...")
        self.new_front_cover_entry = Entry(self.new_front_cover_frame, width=50, textvariable=self.new_front_cover_sv)
        self.new_front_cover_entry.bind('<Return>', lambda _: self.img_entry_return_key_action())
        self.new_front_cover_entry.pack(fill=X)

        self.save_button = Button(self.master, text="Save to MP3 File", command=self.save_button_action)
        self.save_button.pack(fill=X)

        self.audio_file = None
        self.tk_img = None
        self.image_file = None

        if len(cmd_line_mp3_file) > 0:
            if isfile(cmd_line_mp3_file):
                self.mp3_file_sv.set(cmd_line_mp3_file)
                self.open_mp3_file()
            else:
                self.mp3_file_sv.set("Invalid file path: " + cmd_line_mp3_file)

    def create_ide_element(self, name, text):
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

    def extract_images_action(self):
        try:
            for info in self.audio_file.tag.images:
                image_io_stream = BytesIO(info.image_data)
                img = Image.open(image_io_stream)
                extension = "." + str(img.format).lower()
                id3_img_name = ID3_IMG_TYPES[info.picture_type]
                if info.description != "":
                    id3_img_name = info.description + '.' + id3_img_name
                image_save_path = filedialog.asksaveasfilename(parent=self.front_cover_frame,
                                                               defaultextension=extension, initialfile=id3_img_name)
                if image_save_path is None or image_save_path == "":
                    continue

                with open(image_save_path, 'wb') as img_file:
                    img_file.write(info.image_data)
        except AttributeError:
            pass

    def open_mp3_file(self):
        self.clear_elements()
        try:
            self.audio_file = load(self.file_entry.get())
        except IOError:
            self.mp3_file_sv.set("No file selected!")
            return
        self.put_tag_fields_in_entries()
        self.open_id3_tag_image_as_file_io()
        if self.image_file is None:
            self.clear_image()
        else:
            self.display_image_file()

    def tag_to_str(self, tag_element):
        if tag_element is None:
            tag_element = ""
        tag_element = str(tag_element)
        return tag_element

    def save_button_action(self):
        assert self.audio_file is not None
        if self.audio_file.tag is None:
            self.audio_file.initTag()
        tag = self.audio_file.tag
        assert tag is not None

        title = self.id3_entry['title'].get()
        artist = self.id3_entry['artist'].get()
        composer = self.id3_entry['composer'].get()
        album = self.id3_entry['album'].get()
        album_artist = self.id3_entry['album_artist'].get()
        track_num = self.id3_entry['track_num'].get()
        num_tracks = self.id3_entry['num_tracks'].get()
        original_release_date = self.id3_entry['original_release_date'].get()
        release_date = self.id3_entry['release_date'].get()
        recording_date = self.id3_entry['recording_date'].get()
        comments = self.id3_entry['comments'].get()
        genre = self.id3_entry['genre'].get()

        tag.version = (2, 4, 0)
        tag.title = None if len(title) == 0 else title
        tag.artist = None if len(artist) == 0 else artist
        tag.composer = None if len(composer) == 0 else composer
        tag.album = None if len(album) == 0 else album
        tag.album_artist = None if len(album_artist) == 0 else album_artist
        tag.genre = None if len(genre) == 0 else Genre(genre)

        track_num = None if len(track_num) == 0 else int(track_num)
        num_tracks = None if len(num_tracks) == 0 else int(num_tracks)
        if track_num == 0:
            track_num = None
        if num_tracks == 0:
            num_tracks = None
        tag.track_num = (track_num, num_tracks)

        tag.original_release_date = None if len(original_release_date) == 0 else original_release_date
        tag.release_date = None if len(release_date) == 0 else release_date
        tag.release_date = None if len(release_date) == 0 else release_date
        tag.recording_date = None if len(recording_date) == 0 else recording_date

        tag.comments.set(None if len(comments) == 0 else comments)

        tag.save()

    def clear_elements(self):
        for key, entry in self.id3_entry.items():
            entry.delete(0, END)
        self.clear_image()

    def clear_image(self):
        self.image_description_sv.set(self.no_img_txt)
        self.extract_image_button['state'] = DISABLED
        if self.front_cover_img is not None:
            self.front_cover_img.pack_forget()

    def put_tag_fields_in_entries(self):
        tag = self.audio_file.tag
        if tag is None:
            return
        self.id3_entry['title'].insert(0, self.tag_to_str(tag.title))
        self.id3_entry['artist'].insert(0, self.tag_to_str(tag.artist))
        self.id3_entry['composer'].insert(0, self.tag_to_str(tag.composer))
        self.id3_entry['album'].insert(0, self.tag_to_str(tag.album))
        self.id3_entry['album_artist'].insert(0, self.tag_to_str(tag.album_artist))
        self.id3_entry['genre'].insert(0, tag.genre.name if tag.genre is not None else "")
        if len(tag.track_num) > 1:
            self.id3_entry['track_num'].insert(0, self.tag_to_str(tag.track_num[0]))
            self.id3_entry['num_tracks'].insert(0, self.tag_to_str(tag.track_num[1]))
        self.id3_entry['original_release_date'].insert(0, self.tag_to_str(tag.original_release_date))
        self.id3_entry['release_date'].insert(0, self.tag_to_str(tag.release_date))
        self.id3_entry['recording_date'].insert(0, self.tag_to_str(tag.recording_date))
        comments_accessor = tag.comments.get(description="")
        if comments_accessor is not None:
            self.id3_entry['comments'].insert(0, self.tag_to_str(comments_accessor.text))

    def display_image_file(self):
        img = Image.open(self.image_file)
        original_dimensions = img.size
        img = img.resize((200, 200), Image.ANTIALIAS)
        self.tk_img = ImageTk.PhotoImage(img)
        if self.front_cover_img is None:
            self.front_cover_img = Label(self.front_cover_frame, image=self.tk_img)
        else:
            self.front_cover_img.configure(image=self.tk_img)
        self.front_cover_img.pack()
        self.image_description_sv.set("FRONT_COVER: {} x {}".format(original_dimensions[0], original_dimensions[1]))
        self.extract_image_button['state'] = NORMAL

    def file_entry_return_key_action(self):
        self.open_mp3_file()

    def open_id3_tag_image_as_file_io(self):
        self.image_file = None
        try:
            for info in self.audio_file.tag.images:
                if info.picture_type == ImageFrame.FRONT_COVER:
                    self.image_file = BytesIO(info.image_data)
                    break
        except AttributeError:
            pass

    def img_entry_return_key_action(self):
        new_path = self.new_front_cover_sv.get()
        with open(new_path, 'rb') as self.image_file:
            self.display_image_file()
        self.put_new_image_into_tag()

    def remove_button_action(self):
        self.image_file = None
        self.clear_image()
        self.remove_all_images_from_tag()

    def remove_all_images_from_tag(self):
        descriptions = list()
        for info in self.audio_file.tag.images:
            descriptions.append(info.description)
        for description in descriptions:
            self.audio_file.tag.images.remove(description)

    def put_new_image_into_tag(self):
        f = self.new_front_cover_sv.get()
        if isfile(f):
            mime = Magic(mime=True)
            mime_type = mime.from_file(f)
            image_data = open(self.new_front_cover_sv.get(), 'rb').read()
            self.audio_file.tag.images.set(ImageFrame.FRONT_COVER, image_data, mime_type)


def parse_arguments():
    ap = ArgumentParser(description=app_title)
    ap.add_argument('mp3_file', nargs='?', type=str, default="", help="MP3 file to edit")
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    root = Tk()
    mw = MainWindow(root, args.mp3_file)
    root.mainloop()
