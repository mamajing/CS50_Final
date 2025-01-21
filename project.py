import sys
import re
import random
import inflect
import copy
import math
from os import system, name
from PIL import Image, ImageDraw, ImageFont

p = inflect.engine()



# store the different lists indicating the current card collection and positions
class System_state:
    def __init__(self):
        self.selected = []                      # names of cards in the current selection
        self.remaining = []                     # names of cards in the card deck, which is not shown to the user
        self.positions = []                     # 0s and 1s indicating the position of the selected cards. 0 = horizontal, 1 = vertical
        self.covers = []                        # 0s and 1s indicating the position of the selected cards. 0 = face-up, 1 = face-down
        self.favourites = []                    # names of cards in the favourite list

    def set_state(self, selected, remaining, positions, covers, favourites):
        self.selected = selected
        self.remaining = remaining
        self.positions = positions
        self.covers = covers
        self.favourites = favourites

    def __str__(self):
        return f"selected: {self.selected},  remaining: {self.remaining},  positions: {self.positions},  covers: {self.covers},  favourites: {self.favourites}"

    def is_equal_to(self, other):
        for i in range(len(self.selected)):
            if (self.selected[i] != other.selected[i]):
                return False
        for i in range(len(self.remaining)):
            if (self.remaining[i] != other.remaining[i]):
                return False
        for i in range(len(self.covers)):
            if (self.covers[i] != other.covers[i]):
                return False
        for i in range(len(self.positions)):
            if (self.positions[i] != other.positions[i]):
                return False
        for i in range(len(self.favourites)):
            if (self.favourites[i] != other.favourites[i]):
                return False
        return True



#The txt file containing all card names, found in Folder: All_Cards
All_Cards_File_Name = "All_Cards.txt"       # file name where all card names are found
try:
    cover_image = Image.open("All_Cards/" + "Cover.png")        #load card cover image
except FileNotFoundError:
    sys.exit("'" + "Cover.png" + "' is missing in the folder 'All_Cards'.")
try:
    hearts_image = Image.open("Other_Files/" + "Hearts.png")        #load hearts image for background_fav
except FileNotFoundError:
    sys.exit("'" + "Hearts.png" + "' is missing in the folder 'Other_Files'.")
try:
    love_image = Image.open("Other_Files/" + "Love.png")        #load hearts image for background_fav
except FileNotFoundError:
    sys.exit("'" + "Love.png" + "' is missing in the folder 'Other_Files'.")
card_h = cover_image.height                 # height of all cards (each card should have the same dimensions)
card_w = cover_image.width                  # width of all cards (each card should have the same dimensions)
border_w = int(0.1*card_h)                  # make a border area strip of this width between the background edges and each overlaid card image on the background
default_card_amount = 6                     # initially deals this quantity of cards to a user
max_fav_amount = 3                          # maximum allowable cards in the favourite card list
max_select_amount = 8                       # maximum allowable cards in the selected card list
# possible commands and their equivalent values, for example, 0 = zero = exit
commands = {"exit":["0", "zero", "exit"], "rotate":["1", "one", "rotate"], "flip":["2", "two", "rotate"],
            "add":["3", "three", "add"], "discard":["4", "four", "discard"], "undo":["5", "five", "undo"],
            "favourite":["6", "six", "favourite"], "gif":["7", "seven", "gif"], "shuffle":["8", "eight", "shuffle"],
            "restore":["9", "nine", "restore"]}



def main():
    intro_msg()
    image_names = initialize()                           # initialize all data

    # create the three system states: state0 - the oldest; state1 - previous; stateC - current
    system_state0 = System_state()
    system_state1 = System_state()
    system_state2 = System_state()
    system_stateC = System_state()

    # initiatlize first system state = current system state
    system_stateC.selected, system_stateC.remaining = random_select(image_names, default_card_amount)     # randomly select default_card_amount of images
    system_stateC.positions = [1 for x in system_stateC.selected]       # initially all cards in vertical position
    system_stateC.covers = [0 for x in system_stateC.selected]          # initially all cards in face-up position
    system_stateC.favourites = []                                       # initially no favourite cards

    # create background and draw the initial system condition
    background = create_background(max_select_amount)                   # superimpose images on it
    background.save("Outputs/"+"selected.png")                                       # initialize output image for background
    background_blank = create_background(max_select_amount)             # restore the background
    background_fav = create_background(max_fav_amount)                  # superimpose images on it
    background_fav.save("Outputs/"+"favourites.png")                                   # initialize output image for background_fav
    background_fav_blank = create_background(max_fav_amount)            # restore the background_fav

    # initialize all backup states to be equal to the very initial state of the system
    system_state0 = copy.deepcopy(system_stateC)
    system_state1 = copy.deepcopy(system_stateC)
    system_state2 = copy.deepcopy(system_stateC)

    output_changed = True                 # assumed after each loop, the output is changed
    saving_gif = False                    # assumed after each loop, the user does not save a gif
    undo_count = 0                        # only 2 system backups are available, maximum possible undos in a row = 2 times

    # start of main while loop
    while True:
        # create output with current stage of the system if the output is changed
        if output_changed == True or saving_gif == True:
            selected_images = []
            fav_images = []

            for card_name in system_stateC.selected:
                selected_images.append(Image.open("All_Cards/" + card_name).resize([card_w, card_h]))
            for card_name in system_stateC.favourites:
                fav_images.append(Image.open("All_Cards/" + card_name).resize([card_w, card_h]))

            background = overlay_images(selected_images, background, system_stateC.positions, system_stateC.covers)
            background = output_card_amount(background, len(system_stateC.remaining), "remaining")
            background.save("Outputs/"+"selected.png")
            background = background_blank.copy()
            background_fav = overlay_images(fav_images, background_fav, [1 for y in system_stateC.favourites], [0 for y in system_stateC.favourites])
            background_fav = output_card_amount(background_fav, len(system_stateC.favourites), "favourites")
            background_fav.save("Outputs/"+"favourites.png")
            background_fav = background_fav_blank.copy()

            if saving_gif == True:
                save_fav_gif(fav_images, background_fav)

            del selected_images
            del fav_images

        output_changed = True                       # reset the default value to True
        saving_gif = False                          # reset the default value to False

        print("Please input your command:")
        print("0=exit  1=rotate  2=flip  3=add  4=discard  5=undo  6=favourite  7=gif  8=shuffle  9=restore  H=help")
        word = input().strip().lower()
        if word == "h" or word == "help":
            clear_terminal()
            print("0 - Exit the program.")
            print("1 - Rotate all or some selected cards.")
            print("2 - Flip all or some selected cards.")
            print("3 - Add one or more cards to the selected cards.")
            print("4 - Discard all or one selected cards.")
            print("5 - Undo the last change. Maximum 2 undos available.")
            print("6 - Transfer one selected card to your favourite cards.")
            print("7 - Make an interesting GIF using your favourite cards. Try it.")
            print("8 - Shuffle your cards in different areas.")
            print("9 - Restore all selected cards into the default position - face-up and vertical.")
            print("\nPlease input your command using the number digits.")
            word = input().strip().lower()

        clear_terminal()

        # if there are no selected cards, ignore certain commands, continue to the next loop to ask for a new input
        if len(system_stateC.selected) == 0 and is_command(word, "rotate", "flip", "discard", "favourite"):
            print("There are no selected cards. No change can be performed. Please select another command.")
            output_changed = False
            continue

        # user exits the program
        if is_command(word, "exit"):
            break

        # user wants to rotate some cards
        elif is_command(word, "rotate"):
            print("Do you want to rotate all cards?  Y/N")
            word = input().strip().lower()
            if word == "y" or word == "yes":
                for i in range(len(system_stateC.selected)):
                    system_stateC.positions[i] = not(system_stateC.positions[i])
            else:
                output_changed = False
                for i in range(len(system_stateC.selected)):
                    print("Do you want to rotate card no. ", (i+1), "?  Y/N", sep="")
                    word = input().strip().lower()
                    if word == "y" or word == "yes":
                        system_stateC.positions[i] = not(system_stateC.positions[i])
                        output_changed = True
                if output_changed == False:
                    continue

        # user wants to flip some cards
        elif is_command(word, "flip"):
            print("Do you want to flip all cards?  Y/N")
            word = input().strip().lower()
            if word == "y" or word == "yes":
                for i in range(len(system_stateC.selected)):
                    system_stateC.covers[i] = not(system_stateC.covers[i])
            else:
                output_changed = False
                for i in range(len(system_stateC.selected)):
                    print("Do you want to flip card no. ", (i+1), "?  Y/N", sep="")
                    word = input().strip().lower()
                    if word == "y" or word == "yes":
                        system_stateC.covers[i] = not(system_stateC.covers[i])
                        output_changed = True
                if output_changed == False:
                    continue

        # user wants to add one card
        elif word == "add" or word == "3" or word == "three":
            if len(system_stateC.selected) < max_select_amount and len(system_stateC.remaining) > 0:
                print("Do you want to add as many cards as possible to your selected cards?  Y/N")
                word = input().strip().lower()
                if word == "y" or word == "yes":
                    num_card_to_add = max_select_amount - len(system_stateC.selected)
                else:
                    num_card_to_add = 1
                for z in range(num_card_to_add):
                    if len(system_stateC.remaining) == 0:
                        break
                    else:
                        selected_new, system_stateC.remaining = random_select(system_stateC.remaining, 1)
                        system_stateC.selected.extend(selected_new)
                        system_stateC.positions.extend([1])
                        system_stateC.covers.extend([0])
            elif len(system_stateC.selected) >= max_select_amount:
                print("Selected cards at maxmimum capacity. Cannot add any cards.")
                output_changed = False
                continue
            else:
                print("No more remaining cards. Cannot add any cards.")
                output_changed = False
                continue

        # user wants to discard on card
        elif is_command(word, "discard"):
            print("Do you want to discard all cards?  Y/N")
            word = input().strip().lower()
            if word == "y" or word == "yes":
                system_stateC.selected = []
                system_stateC.positions = []
                system_stateC.covers = []
            else:
                print("Select the card number to be discarded, from number 1 to ", len(system_stateC.selected), ".", sep="")
                word = input().strip().lower()
                if is_integer_between(word, 1, len(system_stateC.selected)):
                    del system_stateC.selected[int(word)-1]
                    del system_stateC.positions[int(word)-1]
                    del system_stateC.covers[int(word)-1]
                else:
                    print("Input is not valid.")
                    output_changed = False
                    continue

        # user wants to undo an action, restore the system to a previous state
        elif is_command(word, "undo"):
            if undo_count == 2:
                print("No further undo is possible. Only 2 versions of backup are supported.")
                output_changed = False
                continue
            else:
                system_stateC = copy.deepcopy(system_state1)
                system_state2 = copy.deepcopy(system_state1)
                system_state1 = copy.deepcopy(system_state0)
                undo_count += 1
                continue

        # user wants to save a card to the favourite list
        elif is_command(word, "favourite"):
            if len(system_stateC.favourites) >= max_fav_amount:
                print("There are already ", p.no("card", max_fav_amount), " in the favourite list. No further addition is possible.", sep="")
                output_changed = False
                continue
            else:
                print("Select the card number to be added to your favourite, from number 1 to ", len(system_stateC.selected), ".", sep="")
                word = input().strip().lower()
                if is_integer_between(word, 1, len(system_stateC.selected)):
                    system_stateC.favourites.append(system_stateC.selected[int(word)-1])
                    del system_stateC.selected[int(word)-1]
                    del system_stateC.covers[int(word)-1]
                    del system_stateC.positions[int(word)-1]
                else:
                    print("Input is not valid.")
                    output_changed = False
                    continue

        # user wants to save all cards in the favourite list to a gif file
        elif is_command(word, "gif"):
            if len(system_stateC.favourites) == 0:
                print("There are no favourite cards. Do you really want to make a gif?  Y/N")
                word = input().strip().lower()
                if word == "n" or word == "no":
                    output_changed = False
                    continue
            output_changed = False
            saving_gif = True
            continue

        # user wants to shuffle some cards
        elif is_command(word, "shuffle"):
            output_changed, skip_backup = shuffle_list(system_stateC)
            if skip_backup == True:
                continue

        elif is_command(word, "restore"):
            sum_of_pos_values = 0
            sum_of_cover_values = 0
            for value in system_stateC.positions:
                sum_of_pos_values += value
            for value in system_stateC.covers:
                sum_of_cover_values += value

            if sum_of_pos_values == len(system_stateC.positions) and sum_of_cover_values == 0:
                output_changed = False
                continue
            else:
                system_stateC.positions = [1 for value in system_stateC.selected]
                system_stateC.covers = [0 for value in system_stateC.selected]

        # when no input is recognised
        else:
            print("Input is not valid.")
            output_changed = False
            continue

        # system state advanced and backup is done if undo was not selected
        system_state0 = copy.deepcopy(system_state1)
        system_state1 = copy.deepcopy(system_state2)
        system_state2 = copy.deepcopy(system_stateC)
        undo_count = max(0, undo_count-1)
    # end of main while loop

    background.close()
    background_fav.close()
    global cover_image
    cover_image.close()

    clear_terminal()
    print("Thank you for trying the program written by a 🐭!")



#load files, check the existence of import files and the validity of inputs in files
def initialize():
    #check the existence of the txt file
    try:
        with open("All_Cards/"+All_Cards_File_Name, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        sys.exit("'" + All_Cards_File_Name + "' is missing in the folder 'All_cards'.")

    #check the validity of inputs in files
    pattern = r"^(.+)\.(PNG|JPG|JPEG)$"

    for i in range(len(lines)):
        lines[i] = lines[i].strip()
        #if there is an empty line in the txt, just ignore
        if lines[i] == "":
            continue
        #check if each line in the txt matches with a valid file name pattern
        matches = re.search(pattern, lines[i], re.IGNORECASE)
        if not matches:
            sys.exit("Invalid card names found in " + All_Cards_File_Name +". All card names must be in the format name.png, name.jpg or name.jpeg.")
        else:
            #replace any capital letters in PNG, JPG and JPEG by their lower case equivalents
            lines[i] = matches.group(1) + "." + matches.group(2).lower()

    #remove empty entries in lines
    lines = [x for x in lines if x]

    #minimum 5 cards are required
    if len(lines) < default_card_amount:
        sys.exit("Not enough card names are found in " + All_Cards_File_Name + ". Minimum ", p.no("card", default_card_amount), " needed.", sep="")

    #check the presence of all card image files by loading all the images
    # if everything is alright, return the list of file names
    for line in lines:
        try:
            image = Image.open("All_Cards/" + line)
        except FileNotFoundError:
            sys.exit("The image file '" + line + "' is missing")
        else:
            image.close()
    return lines



#select n random cards from a list of cards, returning the list of selected cards and the list of remaining cards
def random_select(list_of_cards, n):
    if n > len(list_of_cards):
        print("Not enough cards to select " + p.no(" card", n) + " from")
        print("There " + p.plural_verb("is", len(list_of_cards)) + " only " + p.no(" card", len(list_of_cards)) + " left to select.")
        print("No cards are further selected randomly.")
        n = 0

    selected = []
    for i in range(n):
        rnum = random.randint(0, len(list_of_cards)-1)
        selected.append(list_of_cards[rnum])
        del list_of_cards[rnum]
    return [selected, list_of_cards]



#create a background for images to paste on, given a certain maximum number of cards in a row
def create_background(max_in_row):
    background = Image.new("RGBA", (card_h*max_in_row + border_w*2, card_h + border_w*2), (255,255,255,255))
    return background



# given a subset of list of card images, overlay them on the background
# positions as a list indicating how each card is overlaid, 0=horizontal position, 1=vertical position
# covers as a list indicating if each card is face-up or face-down, 0=face-up, 1=face-down
def overlay_images(list_of_images, background, positions, covers):
    for i in range(len(list_of_images)):
        if covers[i] == 0:
            card_image = list_of_images[i]
        else:
            card_image = cover_image
        if positions[i] == 0:
            card_image = card_image.rotate(90, expand=True)
            background.paste(card_image, (int(border_w + card_h*i), int(border_w + card_h/2 - card_w/2)))
        else:
            background.paste(card_image, (int(border_w + card_h/2 - card_w/2 + card_h*i), int(border_w)))
    return background



#display the card file names of a list of image objects, for checking and debugging purpose
def print_card_filenames(list_of_images):
    for card_image in list_of_images:
        card_name = card_image.filename.rpartition("/")[2]
        print(card_name, sep=" ", end=" ")




# check if the input string is equal to a command in a list of command words
def is_command(input_command, *command_words):
    for command_word in command_words:
        for keyword in commands[command_word]:
            if input_command == keyword:
                return True
    return False



# introduce the program, give basic instructions, set the card display parameters
def intro_msg():
    global card_w, card_h, border_w, cover_image, love_image
    temp_card_w = card_w
    temp_card_h = card_h
    temp_border_w = border_w
    print("Welcome to the program, where you can deal cards from a deck of cards.")
    print("")
    print("You can rotate the position of each card or all cards by 90 degrees.")
    print("You can flip each card or all cards face-up or face-down.")
    print("You can add cards from the deck.")
    print("You can discard cards from the selected cards.")
    print("You can transfer your selected cards into your favourite collection.")
    print("You can undo your changes.")
    print("You can shuffle the cards.")
    print("You can make a special gif for your favourite cards.")
    print("You can adjust the size of the cards.")
    print("")
    print("Note:")
    print("Initial amount of selected cards:", default_card_amount)
    print("Maximum allowable amount of cards in your favourite collection:", max_fav_amount)
    print("Maximum allowable amount of cards in your current selection:", max_select_amount)
    print("")
    print("Press any number key (0-9) to start using the programme or enter 'exit' to exit the program directly.")
    while True:
        word = input().strip().lower()
        if word.isdigit():
            clear_terminal()
            break
        elif word == "exit" or word == "e":
            sys.exit()

    while True:
        print("The designated card dimensions from the card cover are:", temp_card_w, "by", temp_card_h, "pixels.")
        print("")
        print("Do you want to reduce or restore the output dimensions of the cards?  Y/N")
        word = input().strip().lower()
        if word == "y" or word == "yes":
            while True:
                print("Select a scaling factor between 0 and 1, or enter R to restore the original card dimensions, or enter 'exit' to exit the program directly.")
                word = input().strip().lower()
                if is_float_between(word, 0, 1):
                    temp_card_w = max(1, int(temp_card_w * float(word)))
                    temp_card_h = max(1, int(temp_card_h * float(word)))
                    temp_border_w = int(max(1, 0.1*temp_card_h))
                    break
                elif word == "r":
                    temp_card_w = card_w
                    temp_card_h = card_h
                    temp_border_w = border_w
                    break
                elif word == "exit" or word == "e":
                    sys.exit()
        else:
            break

    cover_image = cover_image.resize([temp_card_w, temp_card_h])
    card_h = temp_card_h
    card_w = temp_card_w
    border_w = temp_border_w
    love_image = love_image.resize([int(temp_card_w/2.5), int(temp_card_w/2.5)])
    clear_terminal()



# overlay the background_fav_with hearts
def overlay_images_with_hearts(background_fav_blank, x_offset=0, y_offset=0):
    rep_h = math.ceil((background_fav_blank.width-x_offset)/hearts_image.width)
    rep_v = math.ceil((background_fav_blank.height-y_offset)/hearts_image.height)

    for j in range(rep_v):
        for i in range(rep_h):
            background_fav_blank.paste(hearts_image, (i*hearts_image.width + x_offset, j*hearts_image.height + y_offset), hearts_image)

    return background_fav_blank



# clear the terminal screen
def clear_terminal():
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')



# display the text regarding how many cards are remaining in a certain list
def output_card_amount(background, num_of_cards, text_type):
    try:
        myfont = ImageFont.truetype("Other_Files/"+"TextFont2.ttf", max(border_w-15, 20))
    except:
        sys.exit("'TextFont2.ttf' is missing in the folder 'Other_Files'.")
    draw_background = ImageDraw.Draw(background)
    green = (0,255,120)
    red = (255,0,0)

    if "remaining" in text_type:
        text_first = "Remaining no. of cards in the card deck: "
        if num_of_cards <= max_select_amount:
            text_second_color = red
        else:
            text_second_color = green
    else:
        text_first = "No. of favourite cards: "
        if num_of_cards >= max_fav_amount:
            text_second_color = red
        else:
            text_second_color = green

    dim_text = myfont.getbbox(text_first + str(num_of_cards))
    dim_text_first = myfont.getbbox(text_first)
    offset_num = int((dim_text[0] + dim_text[2])/2)

    draw_background.text((background.width/2 - offset_num, background.height - dim_text[3]), text_first , font=myfont, fill=green)
    draw_background.text((background.width/2 - offset_num + dim_text_first[2], background.height - dim_text[3]), str(num_of_cards), font=myfont, fill=text_second_color)

    return background



# shuffle a list of items
def shuffle_list(system_state):
    print("Enter 1 if you want to shuffle the selected cards.")
    print("Enter 2 if you want to shuffle the card deck.")
    print("Enter 3 if you want to shuffle the favourite cards.")
    print("Enter 4 if you want to shuffle everything.")
    print("Enter 5 if you want to return to the previous menu.")

    dict_for_selected = []
    for q in range(len(system_state.selected)):
        dict_for_selected.append({"card":system_state.selected[q], "position":system_state.positions[q],
            "cover":system_state.covers[q]})

    while True:
        skip_backup = False
        output_changed = False
        word = input().strip().lower()
        if word == "1" or word == "one":
            if len(system_state.selected) == 0:
                print("There are no selected cards to shuffle. No change has been performed.")
                skip_backup = True
            else:
                random.shuffle(dict_for_selected)
                system_state.selected = [q["card"] for q in dict_for_selected]
                system_state.positions = [q["position"] for q in dict_for_selected]
                system_state.covers = [q["cover"] for q in dict_for_selected]
                output_changed = True
            break
        elif word == "2" or word == "two":
            if len(system_state.remaining) == 0:
                print("There are no remaining cards to shuffle. No change has been performed.")
                skip_backup = True
            else:
                random.shuffle(system_state.remaining)
                output_changed = False
            break
        elif word == "3" or word == "three":
            if len(system_state.favourites) == 0:
                print("There are no favourites cards to shuffle. No change has been performed.")
                skip_backup = True
            else:
                random.shuffle(system_state.favourites)
                output_changed = True
            break
        elif word == "4" or word == "four":
            if (len(system_state.selected) + len(system_state.remaining) + len(system_state.favourites)) == 0 :
                print("There are no cards anywhere to shuffle. No change has been performed.")
                skip_backup = True
            else:
                random.shuffle(dict_for_selected)
                system_state.selected = [q["card"] for q in dict_for_selected]
                system_state.positions = [q["position"] for q in dict_for_selected]
                system_state.covers = [q["cover"] for q in dict_for_selected]
                random.shuffle(system_state.remaining)
                random.shuffle(system_state.favourites)
                output_changed = True
            break
        elif word == "5" or word == "five":
            skip_backup = True
            break
        else:
            print("Input is invalid.")

    return output_changed, skip_backup



# test if a string, word can be converted into an integer between a and b inclusive
def is_integer_between(word, a, b):
    try:
        n = int(word)
    except:
        return False
    else:
        if (a >= n >= b) or (a <= n <= b):
            return True
        else:
            return False


# create a gif of your favourite cards with hearts
def save_fav_gif(fav_images, plain_background):
    print("Please enter the file name. Do not enter the extension '.gif'. The extension is added automatically.")
    print("Please enter '_' to skip saving the favourite cards and return to the previous menu.")

    while True:
        word = input().strip()

        if word.startswith("_"):
            return

        pattern = r"^\w+( \w+)*$"
        match = re.search(pattern, word)
        if match:
            break
        else:
            print("Input is invalid. Please enter another file name.")

    constant_0 = 24
    love_dur = int(constant_0/6)
    cycle_time = 410
    background_gif = []
    delta_w = plain_background.width/constant_0
    delta_h = plain_background.height/constant_0
    background_fav_temp = plain_background.copy()

    x = [0 for _ in range(11)]
    y = copy.deepcopy(x)

    for i in range(constant_0):
        background_fav_temp = overlay_images_with_hearts(background_fav_temp, x_offset=int(-hearts_image.width+i*delta_w), y_offset=int(-hearts_image.height+i*delta_h))
        background_fav_temp = overlay_images(fav_images, background_fav_temp, [1 for y in range(len(fav_images))], [0 for y in range(len(fav_images))])

        for k in range(len(x)):
            if i % love_dur == 0:
                x[k] = random.randint(0, background_fav_temp.width)
                y[k] = random.randint(0, background_fav_temp.height)
            background_fav_temp.paste(love_image, (x[k]-love_image.width, y[k]-love_image.height), love_image)

        background_gif.append(background_fav_temp)
        background_fav_temp = plain_background.copy()

    background_gif[0].save("Outputs/"+word+".gif", save_all=True, append_images=[*background_gif[1:]], duration=cycle_time,loop=0)

    background_fav_temp.close()

    print("Wow! A new gif is saved!\n")



# test if a string, word can be converted into a float between a and b inclusive
def is_float_between(word, a, b):
    try:
        n = float(word)
    except:
        return False
    else:
        if (a >= n >= b) or (a <= n <= b):
            return True
        else:
            return False



# main() is invoked only if this .py file is called directly (not as an import)
if __name__ == "__main__":
    main()
