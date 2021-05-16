import datetime
import os
import time
from io import BytesIO

from tkinter import *

import requests
from PIL import ImageTk, Image

from parse_rest.connection import register
from parse_rest.user import User

import parsepy
import voice_command

register(APP_ID, API_KEY, master_key=None)
user = User.login(USER, PASSWORD)
current_item = parsepy.item()
last_name = " "


def start(barcode, wake, speaker, detected_object):
    # Root: Define the tkinter root.
    root = Tk()
    root.title('IRMA Refrigerator Management System')
    root.geometry("900x800")
    # root.attributes("-fullscreen", True)
    # root.columnconfigure(0, weight=1)
    # root.rowconfigure(0, weight=1)

    # Frame: Define a frame that covers the entire root window.
    root_frame = Frame(root, padx=3, pady=3)
    root_frame.grid(column=0, row=0, sticky=(N, W, E, S))

    # Style: Define some styling variables.
    label_font_style = ("Arial", 20)
    text_font_style = ("Arial", 10)
    dropdown_menu_font_style = ("Arial", 15)
    item_background_color = '#78D2F7'

    # Label: Product Inventory
    inventory_list_label = Label(root_frame, text='Product Inventory', font=label_font_style)
    inventory_list_label.grid(column=1, row=1, sticky=W)

    # Listbox: Product Inventory (fridge or freezer - listing of products in fridge or freezer)
    inventory_list_queryset = parsepy.item.Query.all()
    inventory_list_items = []
    inventory_item_name = StringVar(root, '')  # what is this var doing?
    inventory_list = Listbox(root_frame, font=label_font_style, width=40)
    for item in inventory_list_queryset:
        inventory_list_items.append(item)
        inventory_list.insert(len(inventory_list_items), inventory_list_items[len(inventory_list_items) - 1].name)
    inventory_list.grid(column=1, row=3, columnspan=3, sticky=NE)
    inventory_list.config(width=0, height=0)

    def raise_new_item_window():
        global current_item
        current_item = parsepy.item()
        new_item_window.deiconify()

    # Button: New Item Window Trigger
    new_item_button = Button(root_frame, text='Add Item', command=lambda: raise_new_item_window(),
                             font=label_font_style)
    new_item_button.grid(row=4, column=1, sticky=EW, padx=10, pady=5)

    def raise_edit_item_window():
        edit_item_window.deiconify()

    # Button: Edit Item Window Trigger
    edit_item_button = Button(root_frame, text='Edit Item', state='disabled', command=lambda: raise_edit_item_window(),
                              font=label_font_style)
    edit_item_button.grid(row=4, column=2, sticky=EW, padx=10, pady=5)

    def remove_item():
        index = inventory_list.curselection()[0]
        # print(index)
        delete_item = inventory_list_items[index]
        delete_item.delete()
        inventory_list_items.remove(delete_item)
        inventory_list.delete(index)

    # Button: Remove Item Window Trigger
    remove_item_button = Button(root_frame, text='Remove Item', command=lambda: remove_item(),
                                font=label_font_style)
    remove_item_button.grid(row=4, column=3, sticky=EW, padx=10, pady=5)

    # Toplevel: New Item Window
    # Hidden on startup with 'withdrawal()' and displayed with 'deiconify()'
    # Triggered via button on root_frame, voice command, or barcode read
    new_item_window = Toplevel(root, bg=item_background_color, borderwidth=2)
    new_item_window.title('IRMA - Item Management')
    new_item_window.geometry("900x800")
    new_item_window.attributes('-topmost', 'true')
    new_item_window.columnconfigure(0, weight=1)
    new_item_window.rowconfigure(0, weight=1)

    # Frame: Define a frame that covers the entire new item window frame.
    new_item_window_frame = Frame(new_item_window, bg=item_background_color)
    new_item_window_frame.grid(column=0, row=0, sticky=(N, W, E, S))

    # Label: New Item Window Label
    new_item_window_label = Label(new_item_window_frame, text='ADD ITEM', font=label_font_style,
                                  bg=item_background_color)
    new_item_window_label.grid(column=1, row=0, sticky=W)

    # Hide the new item window on startup.
    new_item_window.withdraw()

    # Toplevel: Edit Item Window
    # Hidden on startup with 'withdrawal()' and displayed with 'deiconify()'
    # Triggered via button on root_frame
    edit_item_window = Toplevel(root, bg=item_background_color, borderwidth=2)
    edit_item_window.title('IRMA - Item Management')
    edit_item_window.geometry("900x800")
    edit_item_window.attributes('-topmost', 'true')
    edit_item_window.columnconfigure(0, weight=1)
    edit_item_window.rowconfigure(0, weight=1)

    # Frame: Define a frame that covers the entire new item window frame.
    edit_item_window_frame = Frame(edit_item_window, bg=item_background_color)
    edit_item_window_frame.grid(column=0, row=0, sticky=(N, W, E, S))

    # Label: New Item Window Label
    edit_item_window_label = Label(edit_item_window_frame, text='EDIT ITEM', font=label_font_style,
                                   bg=item_background_color)
    edit_item_window_label.grid(column=1, row=0, sticky=W)

    # Hide the new item window on startup.
    edit_item_window.withdraw()

    # disable the 'x' in window upper right corner
    def disable_event():
        pass

    new_item_window.protocol("WM_DELETE_WINDOW", disable_event)

    # Menu: Favorites Menu
    favorites_list_queryset = parsepy.Favorite.Query.all()
    favorites_item_name_list = []
    for favorite in favorites_list_queryset:
        favorites_item_name_list.append(favorite.name)
    favorites_item_name = StringVar(root, value='Favorites')  # start with instruction

    def set_item_in_ui(ui_item, item_id='upc'):
        print('---0--')
        if item_id == 'name':
            image_file = 'favorites/' + ui_item.name.lower().replace(' ', '') + '.jpg'
        else:
            image_file = 'favorites/' + ui_item.upc + '.jpg'
        print("UPC Image File: ", image_file)
        print('UPC Image URL: ', ui_item.imageURL)
        if os.path.exists(image_file):
            print("Image Found")
            image_from_file = Image.open(image_file)
            image_width, image_height = image_from_file.size
            image_scale = 1
            if image_height > 150:
                image_scale = 150 / image_height
            print("Image Size: ", image_width, image_height, image_scale)
            image_from_file = image_from_file.resize((int(image_scale * image_width),
                                                      int(image_scale * image_height)),
                                                     Image.ANTIALIAS)
            image = ImageTk.PhotoImage(image_from_file)
            product_image_label.configure(image=image)
            product_image_label.image = image
        elif len(ui_item.imageURL) > 5:
            print('--1---')
            print("****GETTING Image from url", ui_item.imageURL)
            image_url_response = requests.get(ui_item.imageURL)
            try:
                url_image = ImageTk.PhotoImage(Image.open(BytesIO(image_url_response.content)))
            except TclError as e:
                print('ui: TclError', e)
            product_image_label.configure(image=url_image)
            product_image_label.image = url_image
        else:
            print("Image Not Found", )
            product_image_label.configure(image=product_image)
            product_image_label.image = PhotoImage(Image.new('RGB', (150, 150), 'gray'))
        product_name.set(ui_item.name)
        product_image_url.set(ui_item.imageURL)
        global current_item
        current_item = ui_item

    def set_favorite_item_in_ui():
        print("Selected Favorite Item")
        favorites_item = favorites_list_queryset.filter(name=favorites_item_name.get())
        favorites_item_selected = parsepy.item(
            name=favorites_item[0].name,
            upc=favorites_item[0].upc,
            imageURL=favorites_item[0].imageURL,
            category=favorites_item[0].category
        )
        print(favorites_item_selected, favorites_item_selected.name)
        set_item_in_ui(favorites_item_selected, 'upc')
        if len(favorites_item_selected.name) > 1:
            speaker.say(favorites_item_selected.name)

    favorites_menu = OptionMenu(new_item_window_frame, favorites_item_name, *favorites_item_name_list,
                                command=lambda x: set_favorite_item_in_ui())
    favorites_menu.grid(column=1, row=1, pady=8, sticky=(E, W))
    favorites_menu.configure(font=dropdown_menu_font_style, width=60)
    # TODO: create add to favorites button/function in add item window.
    # TODO: create delete button to remove items from inventory.

    # Radiobutton: Location Selection
    product_location = StringVar(value="Fridge")
    fridge_location_radiobutton = Radiobutton(new_item_window_frame,
                                              text='Fridge', variable=product_location, value="Fridge",
                                              font=label_font_style, bg=item_background_color, bd=0,
                                              highlightthickness=0)
    fridge_location_radiobutton.grid(column=1, row=3, sticky=W)
    freezer_location_radiobutton = Radiobutton(new_item_window_frame,
                                               text='Freezer', variable=product_location, value="Freezer",
                                               font=label_font_style, bg=item_background_color, bd=0,
                                               highlightthickness=0)
    freezer_location_radiobutton.grid(column=1, row=4, sticky=W)

    # Menu: Product Category
    # TODO: create label for category select.
    product_category = StringVar(root, value='Category')
    # Could eventually store categories in db to allow update with device access.
    product_category_menu = OptionMenu(new_item_window_frame, product_category,
                                       "Beverage",
                                       "Condiment",
                                       "Desert",
                                       "Fruit",
                                       "Leftover",
                                       "Meat",
                                       "Milk",
                                       "Other",
                                       "Vegetable")
    product_category_menu.grid(column=1, row=5, pady=8, sticky=W)
    product_category_menu.configure(font=label_font_style)

    # Entry: Product Addition Date
    product_addition_date = StringVar(root, datetime.date.today().strftime("%b %d, %Y"))
    product_addition_date_entry = Entry(new_item_window_frame, textvariable=product_addition_date, width=12,
                                        font=label_font_style)
    product_addition_date_entry.grid(column=1, pady=8, row=6, sticky=W)

    # Entry: Product Name
    product_name = StringVar(root, "")
    product_name_entry = Entry(new_item_window_frame, textvariable=product_name, width=35, font=label_font_style)
    product_name_entry.grid(column=1, row=7, pady=8, columnspan=2, sticky=W)

    # Image: Product Image
    # urllib.request.urlretrieve('https://images.barcodespider.com/upcimage/804879098249.jpg', 'sample.png')
    product_image = ImageTk.PhotoImage(Image.new('RGB', (150, 150), 'blue'))
    product_image_label = Label(new_item_window_frame, image=product_image)
    product_image_label.grid(column=1, row=3, rowspan=5, sticky=E, pady=15)

    def save_item():
        print("Save Called")
        current_item.name = product_name.get()
        current_item.location = product_location.get()
        current_item.dateEntered = datetime.datetime.now()
        current_item.imageURL = product_image_url.get()
        # current_item.image = product_image
        current_item.category = product_category.get()
        current_item.author = user
        current_item.save()
        inventory_item_name.set(current_item.name)
        inventory_list.insert(END, current_item.name)
        product_name.set("")
        product_location.set("")
        product_image_url.set("")
        product_category.set("None")
        product_image_label.image = PhotoImage(Image.new('RGB', (150, 150), 'gray'))
        favorites_item_name.set("Favorites")
        new_item_window.withdraw()

    # Button: Save Item
    save_item_button = Button(new_item_window_frame, text="Save", font=label_font_style, command=lambda: save_item())
    save_item_button.grid(column=1, row=10, sticky=W, pady=10)

    def cancel_item():
        print("Cancel Called")
        # inventory_item_name.set(product_name.get())  # why set the item name here?
        product_name.set("")
        product_location.set("")
        product_image_url.set("")
        product_category.set("None")
        favorites_item_name.set("Favorites")
        product_image_label.image = PhotoImage(Image.new('RGB', (150, 150), 'gray'))
        new_item_window.withdraw()

    # Button: Cancel Item
    cancel_item_button = Button(new_item_window_frame, text="Cancel", font=label_font_style,
                                command=lambda: cancel_item())
    cancel_item_button.grid(column=1, row=10, sticky=E, pady=10)

    # Label: Product Image URL
    product_image_url = StringVar(root, '//---')
    product_image_url_label = Label(new_item_window_frame, textvariable=product_image_url, font=text_font_style,
                                    bg=item_background_color)
    product_image_url_label.grid(column=1, row=15, sticky=SW)

    # Frame: System Status Frame
    system_status_frame = Frame(new_item_window, bd=3, bg=item_background_color, padx=2, pady=2)
    system_status_frame.grid(column=10, row=0, columnspan=100, rowspan=100, sticky=NE)

    # Label/Button: Microphone Status and Control
    microphone_status = StringVar(system_status_frame, 'ON')
    microphone_status_label = Label(system_status_frame, text="Microphone", bg=item_background_color)
    microphone_status_label.grid(column=2, row=1, sticky=NW)

    def mic_toggle():
        print("Microphone Toggle")
        if wake.running:
            wake.running = False
            microphone_status_button.config(bg="red")
            microphone_status.set("OFF")
        else:
            wake.running = True
            microphone_status_button.config(bg="green")
            microphone_status.set("ON")

    microphone_status_button = Button(system_status_frame, textvariable=microphone_status,
                                      bg="green", fg="white", command=lambda: mic_toggle(),
                                      width=3, height=1, font=text_font_style)
    microphone_status_button.grid(column=1, row=1, sticky=NE)

    # Label/Button: Barcode Scanner Status and Control
    barcode_scanner_status = StringVar(system_status_frame, 'ON')
    barcode_scanner_status_label = Label(system_status_frame, text="Barcode", bg=item_background_color)
    barcode_scanner_status_label.grid(column=2, row=2, sticky=NW)

    def barcode_scanner_toggle():
        print("Barcode Scanner Toggle")
        if barcode.running:
            barcode.running = False
            barcode_scanner_button.config(bg="red")
            barcode_scanner_status.set("OFF")
        else:
            barcode.running = True
            barcode_scanner_button.config(bg="green")
            barcode_scanner_status.set("ON")

    barcode_scanner_button = Button(system_status_frame, textvariable=barcode_scanner_status,
                                    bg="green", fg="white", command=lambda: barcode_scanner_toggle(),
                                    width=3, height=1, font=text_font_style)
    barcode_scanner_button.grid(column=1, row=2, sticky=NE)

    # Label/Button: Speaker Status and Control
    speaker_status = StringVar(system_status_frame, 'ON')
    speaker_status_label = Label(system_status_frame, text="Speaker", bg=item_background_color)
    speaker_status_label.grid(column=2, row=3, sticky=NW)

    def cfg_audio():
        print("Speaker Toggle")
        if speaker.is_on():
            speaker.turn_off()
            speaker_status_button.config(bg="red")
            speaker_status.set('OFF')
        else:
            speaker.turn_on()
            speaker_status_button.config(bg="green")
            speaker_status.set('ON')

    speaker_status_button = Button(system_status_frame, textvariable=speaker_status,
                                   bg="green", fg="white", command=lambda: cfg_audio(),
                                   width=3, height=1, font=text_font_style)
    speaker_status_button.grid(column=1, row=3, sticky=NE)

    # Check for input from voice and barcode scanner.

    def check_input():
        global last_name
        if wake.running and wake():  # Has the wake word been triggered
            print("ui Listening...")
            command, voice_item = wake.get_item()
            if len(voice_item.name) > 2:
                new_item_window.deiconify()
                set_item_in_ui(voice_item, 'name')
                speaker.say(voice_item.name)
            else:
                print('ui listen item too short')
        elif barcode.running and barcode.is_connected() and barcode():
            print("ui Scanning...")
            barcode_item = barcode.get_item()
            print("ui Scanned UPC: " + barcode_item.upc)
            new_item_window.deiconify()
            set_item_in_ui(barcode_item, 'upc')
            speaker.say(barcode_item.name)
        elif detected_object():
            object_item = detected_object.get_item()
            if last_name != object_item.name:
                last_name = object_item.name
                new_item_window.deiconify()
                set_item_in_ui(object_item, 'name')
                speaker.say(object_item.name)
        # if barcode.is_connected():
        #    barcode_scanner_status.set('ON')
        #    barcode_scanner_button.config(bg="green")
        if not barcode.is_connected():
            barcode_scanner_status.set('OFF')
            barcode_scanner_button.config(bg="red")
        # run again in 0.25 seconds
        root.after(50, lambda: check_input())

    root.after(50, lambda: check_input())
    root.mainloop()
    print('ui out of loop')



