import configparser
import datetime
import os
import sys
import math

import pygame
from dateutil.relativedelta import relativedelta

pygame.init()
pygame.font.init()

# Initialize the three fonts used in this program
large_font = pygame.font.SysFont('Lucida Console', 70)
small_font = pygame.font.SysFont('Lucida Console', 15)
medium_font = pygame.font.SysFont('Lucida Console', 28)

# f_rate is the framerate of the countdown timer. The actual countdown could
# function perfectly fine at less than 10 FPS but a framerate of 60 ensures
# that user input from the get_input() function is handled smoothly
f_rate = 60
clock = pygame.time.Clock()
surface = pygame.display.set_mode((516, 90))

# Target defaults to Christmas Day of the current year
# Year, Month, Day, Hours, Minutes, Seconds
tt = []
default = f"{datetime.datetime.now().year}, 12, 25, 0, 0, 0"


def save_load(save=True):
    # Loads the stored target date when starting the program, and saves
    # the new target date when the get_input() function is called
    config = configparser.ConfigParser()

    # Create a settings.cfg file if one does not already exist
    if not os.path.isfile("settings.cfg"):
        with open("settings.cfg", mode='w') as f:
            f.write(f"[settings]\ntarget_datetime = {default}")

    if save:
        config.read("settings.cfg")
        config.set("settings", "target_datetime", ', '.join([str(x) for x in tt]))

        with open("settings.cfg", mode="w") as g:
            config.write(g)

    else:
        config.read("settings.cfg")
        config = config['settings']
        return [int(x) for x in config["target_datetime"].split(", ")]


def get_delta():
    # Gets the difference between the current time and the target date.
    # Delta probably isn't the correct word because this function doesn't calculate
    # any form of change. But get_delta() is way cooler sounding than
    # get_difference() so whatever.

    # c_date is the current datetime, t_date is the target date that is being counted towards
    c_date = datetime.datetime.now()
    t_date = datetime.datetime(year=tt[0], month=tt[1], day=tt[2], hour=tt[3], minute=tt[4], second=tt[5])

    # relativedelta() does not track years, months, and days independently - all three must be added up to equal
    # the number of days. This would be very complicated due to differing month and year lengths, so we just
    # use the built-in subtraction operator which does calculate days independently.
    delta = relativedelta(t_date, c_date)
    delta2 = t_date - c_date
    delta = [delta2.days, delta.hours, delta.minutes, delta.seconds]

    # If the target date has been reached, lock the timer at 0 days, 00:00:00
    # Otherwise the display would show negative numbers and cause everything to be offset weird
    if c_date >= t_date:
        delta = [0, 0, 0, 0]

    # Pad the hours, minutes, and seconds to always have at least two digits
    delta = [str(delta[0])] + [f"0{x}" if x < 10 else str(x) for x in delta[1:]]

    return delta


def create_timer(digits):
    # This formula finds the number of digits in the days counter, minus 1.
    # It's used to pad the labels and set the window size to fit the entire timer.
    # log 0 is undefined, so if the time remaining is less than 1 day, we just manually set the padding to 1
    if digits[0]:
        padding = int(math.log10(int(digits[0])))

    else:
        padding = 0

    timer_string = f"{digits[0]} {digits[1]}:{digits[2]}:{digits[3]}"
    day_string = "DAYS"
    hour_string = "HOURS"
    minute_string = "MINUTES"
    second_string = "SECONDS"

    # Adjust the window size to fit the timer. We have to check to make sure that
    # the window isn't already set correctly, because ALL calls to pygame.display.set_mode()
    # trigger a Windows alert. The program becomes near-unusable and always has an orange
    # highlight on its icon unless we do this.
    if surface.get_size() != (43*padding + 435, 90):
        pygame.display.set_mode((43*padding + 435, 90))

    # Days, Hours, Minutes, and Seconds are rendered separately so that we can offset them
    # to the correct pixel, instead of having to use spaces.
    timer = large_font.render(timer_string, True, (0, 0, 0))
    days = small_font.render(day_string, True, (0, 0, 0))
    hours = small_font.render(hour_string, True, (0, 0, 0))
    minutes = small_font.render(minute_string, True, (0, 0, 0))
    seconds = small_font.render(second_string, True, (0, 0, 0))

    surface.blit(timer, (8, 10))
    surface.blit(days, (20*padding + 13, 75))
    surface.blit(hours, (42*padding + 115, 75))
    surface.blit(minutes, (42*padding + 230, 75))
    surface.blit(seconds, (42*padding + 355, 75))


def get_input():
    global tt

    # nt stands for new target. The number of elements in this list is used to determine
    # which step is currently active, the prompt for which is stored in c_step
    nt = []
    c_step = ("Enter target Month (mm): ",
              "Enter target Day (dd): ",
              "Enter target Year (yyyy): ",
              "Enter target Hour (hh): ",
              "Enter target Minute (mm): ",
              "Enter target Second (ss): ")

    max_chars = (2 + len(c_step[0]),  # Months can only be 2 digits long
                 2 + len(c_step[1]),  # Days can only be 2 digits long
                 4 + len(c_step[2]),  # Years can only be 4 digits long
                 2 + len(c_step[3]),  # Hours can only be 2 digits long
                 2 + len(c_step[4]),  # Minutes can only be 2 digits long
                 2 + len(c_step[5]))  # Seconds can only be 2 digits long

    error = None   # A string that is displayed telling the user what error occured when gathering input
    blink = False  # Toggles every 30 frames (0.5 seconds). When true, the text cursor is invisible.
    f_count = 0    # Used to trigger the blink variable to toggle.

    # The Window needs to be bigger to fit the text prompts
    pygame.display.set_mode((525, 90))
    current_input = c_step[0]

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # If the backspace key is pressed, chop off the last character in the current input
            if (event.type == pygame.KEYDOWN) and (event.key == pygame.K_BACKSPACE):
                # Check first to make sure there is actually a character to cut off.
                if len(current_input) > len(c_step[len(nt)]):
                    current_input = current_input[:-1]

            # Simulated real-time input. Polls for number-key presses and adds the keystroke
            # to the current input. Supports both number-pad and top-row.
            if (event.type == pygame.KEYDOWN) and (event.key in [pygame.K_KP0, pygame.K_0]):
                current_input += "0"
            if (event.type == pygame.KEYDOWN) and (event.key in [pygame.K_KP1, pygame.K_1]):
                current_input += "1"
            if (event.type == pygame.KEYDOWN) and (event.key in [pygame.K_KP2, pygame.K_2]):
                current_input += "2"
            if (event.type == pygame.KEYDOWN) and (event.key in [pygame.K_KP3, pygame.K_3]):
                current_input += "3"
            if (event.type == pygame.KEYDOWN) and (event.key in [pygame.K_KP4, pygame.K_4]):
                current_input += "4"
            if (event.type == pygame.KEYDOWN) and (event.key in [pygame.K_KP5, pygame.K_5]):
                current_input += "5"
            if (event.type == pygame.KEYDOWN) and (event.key in [pygame.K_KP6, pygame.K_6]):
                current_input += "6"
            if (event.type == pygame.KEYDOWN) and (event.key in [pygame.K_KP7, pygame.K_7]):
                current_input += "7"
            if (event.type == pygame.KEYDOWN) and (event.key in [pygame.K_KP8, pygame.K_8]):
                current_input += "8"
            if (event.type == pygame.KEYDOWN) and (event.key in [pygame.K_KP9, pygame.K_9]):
                current_input += "9"
            if (event.type == pygame.KEYDOWN) and (event.key == pygame.K_ESCAPE):
                return

            # Truncate any excess characters - cap the input length at the max_chars value.
            current_input = current_input[:max_chars[len(nt)]]

            # If the enter key is pressed, evaluate the input and move on to the next prompt if necessary
            if (event.type == pygame.KEYDOWN) and (event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]):

                # Evaluate the current input to make sure it's valid - for example, the number of seconds
                # can't be above 59. Will return an error message if it's not valid.
                valid_data = evaluate_input(current_input, c_step, nt)
                error_messages = ("Not a valid date!",
                                  "That date is in the past!",
                                  "Invalid value entered!")

                # Append the current input to the new target list if no error is triggered
                if valid_data not in error_messages:
                    error = None
                    nt.append(int(valid_data))

                    # If all prompts have been answered, do a final check to make sure that the new target
                    # date is valid. Prevents nonsensical dates (February 30th, for example) and target dates
                    # in the past.
                    if len(nt) == 6 and final_evaluate(nt) not in error_messages:

                        # Finally update the target date. Also save it to a file so that closing the program
                        # does not reset the target date.
                        tt[0], tt[1], tt[2], tt[3], tt[4], tt[5], = nt[2], nt[0], nt[1], nt[3], nt[4], nt[5]
                        save_load()

                        return

                    elif len(nt) != 6:
                        current_input = c_step[len(nt)]

                    else:
                        current_input = c_step[0]
                        error = final_evaluate(nt)
                        nt = []

                        continue

                else:
                    error = valid_data
                    current_input = c_step[len(nt)]

        # Blink the text cursor every 30 frames (0.5 seconds)
        if f_count == 30:
            f_count = 0
            blink = not blink

        surface.fill((255, 255, 255))

        # Prepare the current input, text cursor, and error message surfaces
        input_surface = medium_font.render(current_input, True, (0, 0, 0))
        blink_surface = medium_font.render("|", True, (0, 0, 0))
        error_surface = medium_font.render(error, True, (255, 0, 0))

        # Blit everything to the screen. The error message and text cursor are only visible if
        # certain conditions are met.
        surface.blit(input_surface, (5, 5))
        surface.blit(blink_surface, (3 + input_surface.get_width(), 5)) if not blink else ''
        surface.blit(error_surface, (5, 55)) if error else ''

        pygame.display.flip()

        f_count += 1
        clock.tick(f_rate)


def evaluate_input(current_input, c_step, nt):
    # Check for obvious errors
    try:
        current_input = int(current_input[len(c_step[len(nt)]):])

    except ValueError:
        return "Invalid value entered!"

    if len(nt) == 0:
        if not (0 < current_input < 13):
            return "Invalid value entered!"
    if len(nt) == 1:
        if not (0 < current_input < 32):
            return "Invalid value entered!"
    if len(nt) == 3:
        if current_input >= 24:
            return "Invalid value entered!"
    if len(nt) == 4:
        if current_input >= 60:
            return "Invalid value entered!"
    if len(nt) == 5:
        if current_input >= 60:
            return "Invalid value entered!"

    return current_input


def final_evaluate(nt):
    # This will raise a ValueError if an invalid date is entered, such as February 30th.
    try:
        datetime.datetime(month=nt[0], day=nt[1], year=nt[2])

    except ValueError:
        return "Not a valid date!"

    new_time = datetime.datetime(month=nt[0], day=nt[1], year=nt[2], hour=nt[3], minute=nt[4], second=nt[5])

    # Do not allow times that are in the past - it would be a waste!
    if new_time < datetime.datetime.now():
        return "That date is in the past!"


def change_window_title(getting_input):
    if getting_input:
        ft = "Press ESC to cancel"

    else:
        if pygame.display.get_active() and pygame.key.get_focused():
            mouse_pos = pygame.mouse.get_pos()
            window_size = surface.get_size()

            if 0 < mouse_pos[0] < window_size[0] - 1 and 0 < mouse_pos[1] < window_size[1] - 1:
                ft = "Click to change target date"

            else:
                ft = [f"0{x}" if x < 10 else str(x) for x in tt]
                ft = f"Countdown to {ft[3]}:{ft[4]}:{ft[5]} on {ft[1]}/{ft[2]}/{ft[0]}"

        else:
            ft = "Countdown Timer"

    pygame.display.set_caption(ft)


def run_countdown():
    global tt

    f_count = 0
    tt = save_load(False)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Mouse-clicks are only registered if the window has been focused for at least 3 frames
            if (event.type == pygame.MOUSEBUTTONDOWN) and (pygame.mouse.get_pressed()[0]):
                if f_count == 3:
                    change_window_title(True)
                    get_input()

        change_window_title(False)
        surface.fill((255, 255, 255))
        create_timer(get_delta())
        pygame.display.flip()

        if pygame.key.get_focused():
            f_count += 1
            f_count = min(3, f_count)

        else:
            f_count = 0

        clock.tick(f_rate)
		
run_countdown()