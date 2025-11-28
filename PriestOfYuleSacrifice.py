#!/usr/bin/env python3
# region Comments and Imports
"""
Christmas CLI Challenge Game - Extensible Skeleton

How to use:
1. Save as christmas_challenge.py
2. Optionally install extras (see requirements below)
3. Run on Windows (desktop path is detected automatically)

Requirements (minimal):
 - Python 3.8+

Optional extras (recommended for advanced features):
 - PyPDF2==3.0.0        # for PDF page counting
 - Pillow               # for image handling
 - imagehash            # for perceptual image comparison
 - rich                 # prettier CLI
 - pyinstaller          # if you want to build an EXE

requirements.txt:
PyPDF2>=3.0.0
Pillow
imagehash
rich


Example:
    pip install PyPDF2 Pillow imagehash rich
    python christmas_challenge.py

Packaging (PyInstaller):
    pip install pyinstaller
    pyinstaller --onefile christmas_challenge.py
    # result: dist/christmas_challenge.exe

NOTE: This file is intentionally modular and each "OPTIONAL COMPONENT" is isolated under a clear comment block.
"""

from __future__ import annotations
import os
import sys
import time
import webbrowser
import subprocess
import random as r
import re
import threading
from pathlib import Path
from abc import ABC, abstractmethod
from binascii import unhexlify
from msvcrt import getch

import winsound
from google import genai
from google.genai import types
from google.genai import errors

# Optional imports guarded so the script still runs without them
try:
    from PyPDF2 import PdfReader  # PDF page counting (optional)
    HAS_PYPDF2 = True
except Exception:
    HAS_PYPDF2 = False

# try:
#     from PIL import Image         # image handling (optional advanced)
#     import imagehash             # perceptual hashing (optional advanced)
#     HAS_IMAGEHASH = True
# except Exception:
#     HAS_IMAGEHASH = False


from rich.console import Console
from rich.panel import Panel
HAS_RICH = True
console = Console()

# endregion

# -----------------------------
# region Configuration / Constants
# -----------------------------
POLL_INTERVAL = 1.0  # seconds between checks
ALTAR_FOLDER_NAME = "Sacrificial Altar"
WINNER_HEX = "68747470733a2f2f6368726973746d617332352e6c6c6f79642e626c61636b"
WINNER_WEBPAGE = unhexlify(WINNER_HEX).decode('UTF-8')
SCRIPT_DIR = "\\".join(os.path.realpath(__file__).split("\\")[:-1])
ICON_PATH = f"{SCRIPT_DIR}\\assets\\Sacrificial_Altar.ico"
GOOGLE_API_KEY = "AIzaSyArlI99Ivrw8b9aHXnCal8KNAj-RrnSKiE"
# endregion

# -----------------------------
# region Helper utilities
# -----------------------------
def print_good(text: str):
    if HAS_RICH:
        console.print(Panel(text, style="green"))
    else:
        print("[OK] " + text)


def print_info(text: str):
    if HAS_RICH:
        console.print(text)
    else:
        print("[..] " + text)


def print_error(text: str):
    if HAS_RICH:
        console.print(Panel(text, style="red"))
    else:
        print("[ERR] " + text)


def print_prompt(text: str, flush=False):
    if HAS_RICH:
        console.print(Panel(text, style="blue"))
    else:
        print("[PROMPT] " + text)


def gemini_eyeballs(prompt: str, candidate: Path):

    verdict = None
    VALID_EXTS = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }

    queries = 0
    model='gemini-2.5-flash'

    with open(candidate, 'rb') as img:
        image_bytes = img.read()

    print_info("Consulting with my stooge, who has eyes")

    try:
        if queries > 4:
            print_error("You've been asking a lot of my stooge. Please take a minute to reflect on your actions.")
            time.sleep(10)
            print_info("50...")
            time.sleep(10)
            print_info("40...")
            time.sleep(10)
            print_info("30...")
            time.sleep(10)
            print_info("20...")
            time.sleep(10)
            print_info("10...")
            time.sleep(10)
            queries = 0
            return False
        
        client = genai.Client(api_key=GOOGLE_API_KEY)
        response = client.models.generate_content(
            model = model,
            contents = [
                types.Part.from_bytes(data=image_bytes, mime_type=VALID_EXTS[candidate.suffix.lower()]),
                prompt
            ]
        )
    
        queries += 1
        # if response.text == "yes":
        #     return True
        # elif response.text != "no":
        #     print_info(f"My AI laborer is being unruly. They said {response.text} despite my clear instructions. Lemme try again.")
    except errors.APIError as e:
        if e.code == 429:
            print_error("You've exhausted my stooge. I take this as a personal affront and will be committing suicide as a result. Good day.")
            exit()
    
    except Exception as e:
        print_error(f"Image compare error for {candidate.name}: {e}")
        return None

    return response.text



def 



def play_sound_async(path):
    """Play a WAV file asynchronously on Windows using winsound."""
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(f"No such file: {p}")

    def _play():
        winsound.PlaySound(str(p), winsound.SND_FILENAME | winsound.SND_ASYNC)

    threading.Thread(target=_play, daemon=True).start()


def await_file_change(path: Path):
    
    mod_time = os.path.getmtime(path)

    while True:
        new_mod_time = os.path.getmtime(path)
        # print_info(str(new_mod_time))
        if new_mod_time != mod_time:
            return
        time.sleep(.5)



def get_desktop_path() -> Path:
    """Locate the current user's Desktop (Windows-friendly)."""
    home = Path.home()
    desktop = home / "Desktop"

    if desktop.exists():
        pass
    elif os.path.exists("C:\\Users\\mrllo\\OneDrive\\Desktop"): # For testing on my own dumb machine
        desktop = Path("C:\\Users\\mrllo\\OneDrive\\Desktop") # For testing on my own dumb machine
    else:
        # Fallbacks: sometimes "Desktop" localized; attempt environment variable
        env = os.environ.get("USERPROFILE") or os.environ.get("HOME")
        if env:
            candidate = Path(env) / "Desktop"
            if candidate.exists():
                return candidate
        # If still not found, just use home
        return home
    return desktop


def set_folder_icon(folder, icon_path):
    try:
        folder = os.path.abspath(folder)
        ini_path = os.path.join(folder, "desktop.ini")

        # desktop.ini contents
        ini = f"[.ShellClassInfo]\nIconResource={icon_path},0\n"

        # Write desktop.ini
        with open(ini_path, "w", encoding="utf-8") as f:
            f.write(ini)
        
        # Make folder a "system" folder
        subprocess.run(['attrib', '+s', folder], shell=True)

        # Make the ini file hidden + system
        subprocess.run(['attrib', '+h', '+s', ini_path], shell=True)

        # Optional: refresh Explorer
        time.sleep(.5)
        subprocess.run(['ie4uinit.exe', '-ClearIconCache'], shell=True)
        
    except PermissionError as e:
        # print_error("Something fucked in setting the Altar Icon")
        pass



## Could probably make this timer thing into a more extensible wrapper.
def _input_timer():
    print()
    print_error("Time up; I'm killing myself now")
    os._exit(1)
    


def timedinput(timeout, message=' >> '):

    t_thread = threading.Timer(float(timeout), _input_timer)
    t_thread.start()
    result = input(message)
    t_thread.cancel()

    return result


def ensure_altar(desktop: Path) -> Path:
    altar = desktop / ALTAR_FOLDER_NAME
    altar.mkdir(parents=True, exist_ok=True)
    set_folder_icon(altar, ICON_PATH)
    return altar

# endregion

# region Challenges and Classes

# -----------------------------
# Challenge base class
# -----------------------------
class Challenge(ABC):
    name: str = "Unnamed Challenge"
    description: str = "No description."
    win_message = "No win message."

    def on_start(self):
        """Hook run when the challenge begins (optional)."""
        pass

    @abstractmethod
    def is_completed(self, altar_path: Path) -> bool:
        """Return True when the challenge is satisfied."""
        raise NotImplementedError

    def on_complete(self):
        """Hook run when the challenge completes (optional)."""
        pass


# -----------------------------
# OPTIONAL COMPONENT: Intro baby little file feed
# -----------------------------
class ChallengeIntro(Challenge):
    name = "A Trial of Basic Literacy"
    description = "I hunger for a text file named 'munchies.txt'. Place your offering in the Sacrifical Altar."
    win_message = "Well done."

    def is_completed(self, altar_path: Path) -> bool:
        
        for p in altar_path.iterdir():
            if p.name == "desktop.ini":
                continue
            elif p.name == "munchies.txt" and p.is_file():
                return True
            elif p.is_file():
                print_error(f"Me when I fail kindergarten: {p.name}\nGet that shit outta here")
                os.remove(p)
        return False



# -----------------------------
# OPTIONAL COMPONENT: PDF Page Counting
# -----------------------------
# This block uses PyPDF2 to count pages. If PyPDF2 is not installed we fallback to 'presence of a .pdf'.
# To enable: pip install PyPDF2
# To remove: delete this class or replace is_completed body.

class ChallengeFeedPDF(Challenge):
    name = "A Trial of PDFsmanship."
    description = "I hunger for a PDF."
    win_message = "yummy chimken"
    MIN_PAGES = 50

    def is_completed(self, altar_path: Path) -> bool:
        for p in altar_path.iterdir():
            if p.suffix.lower() == ".pdf" and p.is_file():
                if HAS_PYPDF2:
                    try:
                        reader = PdfReader(str(p))
                        pages = len(reader.pages)
                        print_info(f"Found PDF '{p.name}' with {pages} pages.")
                        if pages > self.MIN_PAGES:
                            page_2_text = reader.pages[7].extract_text().lower()
                            if "chicken" in page_2_text:
                                return True
                            else:
                                print_error("Satisfactory in volume, but page 8 could use more chicken.")
                                os.remove(p)
                        else:
                            print_error("Offering too meager. I hunger for more pages.")
                            os.remove(p)
                    except Exception as e:
                        print_error(f"Failed to read PDF {p.name}: {e}")
                else:
                    # fallback: accept any PDF but log notice
                    print_error("You've failed to install PyPDF2. Shame")
                    return False
        
        return False


# -----------------------------
# OPTIONAL COMPONENT: Image "Reindeer" Recognition
# -----------------------------
# We offload to AI.
#
# To remove advanced capability entirely: delete HAS_IMAGEHASH checks and the reference loading.
# endregion
class ChallengeFeedReindeerImage(Challenge):
    name = "A Sacrifice of Flesh"
    description = "I hunger for the meat of the festive beast adorned with horns and bound to servitude at the helm of the fat man's carriage. Or an image of one."
    win_message = "yep that's a reindeer"

    def __init__(self):
        self.gemini_prompt = """You are part of a scripted workflow, and are responsible for image understanding.
        You will be given an image. Your task is to identify if there is a reindeer present in the image.
        You must reply with exactly one word; if there is a reindeer in the image, respond 'yes'.
        If there is not a reindeer in the image, respond 'no'.
        """
        self.model='gemini-2.5-flash'
        self.queries = 0
        self.VALID_EXTS = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp"
        }


    def check_image(self, candidate: Path) -> bool:
        try:
            with open(candidate, 'rb') as img:
                image_bytes = img.read()

            print_info("Consulting with my stooge, who has eyes")


            if self.queries > 4:
                print_error("You've been asking a lot of my stooge. Please take a minute to reflect on your actions.")
                time.sleep(10)
                print_info("50...")
                time.sleep(10)
                print_info("40...")
                time.sleep(10)
                print_info("30...")
                time.sleep(10)
                print_info("20...")
                time.sleep(10)
                print_info("10...")
                time.sleep(10)
                self.queries = 0
                return False

            
            client = genai.Client(api_key=GOOGLE_API_KEY)
            response = client.models.generate_content(
                model = self.model,
                contents = [
                    types.Part.from_bytes(data=image_bytes, mime_type=self.VALID_EXTS[candidate.suffix.lower()]),
                    self.gemini_prompt
                ]
            )
            self.queries += 1

            if response.text == "yes":
                return True
            elif response.text != "no":
                print_info(f"My AI laborer is being unruly. They said {response.text} despite my clear instructions. Lemme try again.")

        except errors.APIError as e:
            if e.code == 429:
                print_error("You've exhausted my stooge. I take this as a personal affront and will be committing suicide as a result. Good day.")
                exit()
        

        except Exception as e:
            print_error(f"Image compare error for {candidate.name}: {e}")
        return False

    def is_completed(self, altar_path: Path) -> bool:
        for p in altar_path.iterdir():
            if not p.is_file() or p.name == "desktop.ini":
                continue
            if p.suffix.lower() in self.VALID_EXTS:

                image_check = gemini_eyeballs(self.gemini_prompt, p)

                # Gemini check
                if image_check and image_check[0] in "yY":
                    return True
                else:
                    print_error("Nay, this beast or whatever displeases me. Please replace it posthaste.")
                    time.sleep(2)
                    return False
                
                
            else:
                print_error("PTOOEY nasty file type. Bad.")
                os.remove(p)
                return False

        return False



# -----------------------------
# Speed Typing Challenge
# -----------------------------
class ChallengeSpeedTyping(Challenge):
    # Times meant to be almost doable but not, with the intended solution being a copy-paste
    name = "A Trial of Humility"
    description = "Type the following self-affirmation. I'm really needy so please hurry and don't mess it up."
    win_message = "pffffffft lmao"

    def __init__(self):

        self.phrases = [
            ["I will never be able to fly by flapping my arms really hard. I walk the ground, downtrodden that my skinny meat sticks don't provide the lift required to get my terrestrial ass off the floor. For this, I weep.", 38],
            ["I am a slow typist. This saddens me. Is it typist? Typer? I don't know. This saddens me even more. I weep, for I am not enough.", 30],
            ["Gods how I wish I was Brennan Lee Mulligan. With his luscious hair, luscious face, luscious voice. Gee golly that man does things to me and I'm not him. Sadge.", 30],
            ["Let any fish who meets my gaze learn the true meaning of fear; for I am the harbinger of death. The bane of creatures sub-aqueous, my rod is true and unwavering as I cast into the aquatic abyss. A man, scorned by this uncaring Earth, finds solace in the sea. My only friend, the worm upon my hook. Wriggling, writhing, struggling to surmount the mortal pointlessness that permeates this barren world. I am alone. I am empty. And yet, I fish.", 81],
            ["Women fear me. Fish fear me. Men turn their eyes away from me. As I walk, no beast dares make a sound in my presence. I am alone on this barren earth.", 28],
            ["I'm a little baby", 6],
            ["My mill grinds rats, and mice. Your mill grinds pepper, and spice. Piss a bed, piss a bed, barley butt. My Bum is so heavy, I can't get up.", 28],
            ["Brother Barnabus, I'm so geeked on purple elixir I hardly even know where I am. It's honestly ruining my life. My crops lay barren, Lady Gwendoline has been abducted by Lord Fergus, Gort the Serf is as unproductive as ever.", 38],
            ["Je ne pourrai jamais voler en battant des bras de toutes mes forces. Je marche a meme le sol, abattu que mes maigres muscles ne me permettent pas de decoller de ce fichu sol. Et pour cela, je pleure.", 43],
            ["aaaaa aaaaaa aaaaaaaaaaa aaaaaaaaaaaaa aa aaaa aaaaaaaaaaa aaaaaaaaaaa aaaaa", 18],
            ["I am a workshy milksop. It's as though me mum's got me back on the mercury and bismuth again. Forlorn am I.", 22],
            ["xdx im so not poggers bestie liek i am NOT giving skibidi ohio rizz. like what the sigma 67", 33],
        ]

        self.selection = r.choice(self.phrases)
        self.passed = False

    def on_start(self):
        
        selected_phrase = self.selection[0]
        
        print_error(f"You have {self.selection[1]} seconds:")
        print_prompt(f"{selected_phrase}")

        completed_input = timedinput(self.selection[1])
        
        words_typed = [word for word in re.split(r"\W+", completed_input.lower()) if word != '']
        split_phrase =  [word for word in re.split(r"\W+", selected_phrase.lower()) if word != '']
        if words_typed == split_phrase:
            self.passed = True
        else:
            diff = set(split_phrase) - set(words_typed)
            if len(diff) > 0:
                print_error(str(diff))
            print_error("Typed it wrong, I'm going to kill myself now.")
            time.sleep(3)
            exit()
            self.passed = False
    
    def is_completed(self, altar_path: Path) -> bool:
        return self.passed



# -----------------------------
# Math / Text Answer Challenge
# -----------------------------
class ChallengeMathAnswer(Challenge):
    name = "A Trial of Knowledge"
    win_message = "Correct, I'm feeling high on mathamphetamines."
    

    def __init__(self, a=r.randint(0,3000), b=r.randint(0,1000), c=r.randint(0,1000)):
        self.a = a
        self.b = b
        self.c = c
        self.correct_answer = str(self.a * self.b // self.c)
        self.description = f"Sacrifice a .txt file that contains the exact numeric answer to {self.a} * {self.b} / {self.c} (rounded down to the nearest whole number)."

    def is_completed(self, altar_path: Path) -> bool:
        for p in altar_path.iterdir():
            if p.suffix.lower() == ".txt" and p.is_file():
                try:
                    txt = p.read_text(errors="ignore").strip()
                except Exception:
                    continue
                # Accept if the numeric answer appears anywhere in the text
                if self.correct_answer in txt:
                    return True
        return False


# -----------------------------
# Password Game Challenge
# -----------------------------
class ChallengePasswordGame(Challenge):
    name = "A Trial of Compliance"
    description = "Offer a sacrifice of a text file containing any password."

    def __init__(self):
        self.requirements = {
            # e.g. vixenmarch0!9673
            "Password must be at least 8 characters long.": [False, True], # Rule, [passed, shown as part of the loop]
            "Password must contain a number.": [False, False],
            "Password must include a special character.": [False, False],
            "Digits in your password must add up to 25.": [False, False],
            "Password must include a month of the year.": [False, False],
            "Password must be at most 18 characters.": [False, False],
            "Password must contain the Roman Numeral for 9.": [False, False],
            "Password must start with a reindeer.": [False, False], # Any of the named ones: Dasher, Dancer, Prancer, Vixen, Comet, Cupid, Donner, Blitzen, Rudolph
            "Password file must match the password, so I can remember it.": [False, False],
            "Keeping your password in a file named after the password is insecure, please reverse it in the file name to make it secret.": [False, False],
            "Password must start with a Roman Numeral.": [False, False],
            "Password must not contain any repeat characters.": [False, False],
        }
        self.successful_password = "yuasehf oijasepnfo9ua09upaoiwejhfalkn"


    def is_completed(self, altar_path: Path, skip_await=False):

        # Try iterating through files in altar, if they're a text file then run through our rule evaluations
        for p in altar_path.iterdir():
            if p.is_file() and p.name != "desktop.ini":
                # Block for change in file, catch file not found errors and run is_completed again to find the new filename.
                try:
                    if skip_await:
                        print_info(f"Oop, looks like the filename changed to {p.name}, using that now")
                    else:
                        print_info(f"that {p.name} file looks mighty interesting, I'm gonna sit and stare at that until it changes")
                        await_file_change(p)
                except FileNotFoundError as e:
                    return self.is_completed(altar_path, True)
                
                print_prompt(f"Your password is {p.read_text()}")
                
                try:
                    matches = self.evaluate_rules(p) # Runs check for a rule, then sets bools appropriately
                except:
                    continue

                success = True
                for i, (rule, bools) in enumerate(self.requirements.items()):
                    time.sleep(.5)
                    if not bools[0]: # Rule is not met
                        success = False
                        if bools[1]: # Rule not met but it is shown
                            print_error(f"{i+1}) {rule}\n{matches[i]}") 
                        else: # Rule is not met and not shown
                            break # Fully jumps out of this block

                    else: # Rule is met
                        if bools[1]: # Rule is met and shown
                            print_good(f"{i+1}) {rule}\n{matches[i]}")
                        else: # Rule is met but not shown
                            continue
                    

                    # "Do I unlock a new rule" block
                    try:
                        show_next = True
                        for j in range(i+1): # Iterates through all requirements up until this point, including the current one
                            if not list(self.requirements.values())[j][0]: # If any of these requirements are not met,
                                show_next = False # don't show next, and work is done
                                break

                        if show_next: # If all rules are met
                            rule_key = list(self.requirements)[i+1] # Grab rule string for the next requirement down the dictionary/list
                            self.requirements[rule_key][1] = True # Set bools[1] (i.e. Shown or not) to True, then return to the start of the 
                    except IndexError: # Next rule is out of bounds, i.e. we've iterated through all rules
                        break

                if success:
                    self.win_message = f"Good password m8e"
                    self.successful_password = p.read_text().rstrip()
                
                return success


    def on_complete(self):
        return self.successful_password


    def evaluate_rules(self, path: Path):

        # Grab content from the given path to work with
        # Grab filename for use as well
        content = path.read_text().rstrip()
        lower_content = content.lower()
        title = path.stem

        matches = []

        for bools in list(self.requirements.values()):
            bools[0] = False


        # if list
        mat = len(content)
        if mat >= 8:
            self.requirements["Password must be at least 8 characters long."][0] = True
        matches.append(f"Password length: {mat}")
        
        mat = re.search("[0-9]", content)
        if re.search("[0-9]", content):
            self.requirements["Password must contain a number."][0] = True
        matches.append(f"Number identified: {mat[0] if mat else mat}")

        mat = re.search("[^a-zA-Z0-9\\s]", content) # Find anything that's not a 
        if mat:
            self.requirements["Password must include a special character."][0] = True
        matches.append(f"Special character identified: {mat[0] if mat else mat}")


        
        sum = 0
        for char in content:
            if char in "123456789":
                sum += int(char)
        if sum == 25:
            self.requirements["Digits in your password must add up to 25."][0] = True
        matches.append(f"Current sum: {sum}")
        
        mat = re.search("(january|february|march|april|may|june|july|august|september|november|december)", lower_content)
        if mat:
            self.requirements["Password must include a month of the year."][0] = True
        matches.append(f"Month identified: {mat[0] if mat else mat}")

        
        mat = len(content)
        if mat <= 18:
            self.requirements["Password must be at most 18 characters."][0] = True
        matches.append(f"Password length: {mat}")

        mat = ("IX" in content)
        if mat:
            self.requirements["Password must contain the Roman Numeral for 9."][0] = True
        matches.append(mat)

        mat = re.match("(dasher|dancer|prancer|vixen|comet|cupid|donner|blitzen|rudolph)", lower_content)
        if mat:
            self.requirements["Password must start with a reindeer."][0] = True
        matches.append(f"Reindeer identified at beginning of password: {mat[0] if mat else mat}")

        if title == content or title == content[::-1]:
            self.requirements["Password file must match the password, so I can remember it."][0] = True
        matches.append(f"Current title: {title}")

        if title == content[::-1]:
            self.requirements["Keeping your password in a file named after the password is insecure, please reverse it in the file name to make it secret."][0] = True
        matches.append(f"Current title: {title}")

        mat = re.match("(I|V|X|L|M|C|D)", content)
        if mat:
            self.requirements["Password must start with a Roman Numeral."][0] = True
        matches.append(f"Roman numeral identified at beginning of password: {mat[0] if mat else mat}")
        
        char_list = []
        repeat_list = []
        no_repeats = True
        for char in lower_content:
            if char not in char_list:
                char_list.append(char)
            else:
                no_repeats = False
                if char not in repeat_list:
                    repeat_list.append(char)
        self.requirements["Password must not contain any repeat characters."][0] = no_repeats
        matches.append(f"Repeat offenders: {repeat_list}")

        # Return a list of the matches/lens/etc that we can map to the rules
        return matches





# -----------------------------
# Challenge Runner
# -----------------------------
class ChallengeReflexes(Challenge):
    name = "A Trial of Reflex."
    description = "Demonstrate deftness of mind and hand by pressing any button within 250 milliseconds."

    def __init__(self):
        self.passed = False
        self.reflex_time = 100000000000   


    def is_completed(self, altar_path: Path):
        time.sleep(5)
        print_info("Ready...")
        time.sleep(2)
        print_info("Set...")
        time.sleep(r.randint(2500,5600)/1000)
        print_prompt("GO")
        start = time.perf_counter()
        getch() # MS C++ Runtime API Input read instead of input() coz input() is fuggin slow
        end = time.perf_counter()

        self.reflex_time = (end-start)*1000
        if self.reflex_time < 1:
            print_error(f"too early eh? it's okay it happens to a lot of guys I've heard")
        elif self.reflex_time < 250:
            self.win_message = f"Wow u did it and in only {self.reflex_time:2f}MS waaoooooowwww *bitcrushed XQC applause*"
            self.passed = True
        else:
            print_error(f"slow assss {self.reflex_time:2f}MS lmaooooo")
        return self.passed




# -----------------------------
# Challenge Runner
# -----------------------------
class ChallengeRunner:
    def __init__(self, altar_path: Path, challenges: list[Challenge]):
        self.altar_path = altar_path
        self.challenges = challenges
        self._show_intro()

    def _show_intro(self):
        header = "A New Hand Touches the Beacon"
        if HAS_RICH:
            console.rule(header)
            console.print("Present your offering.", style="bold")
            console.print(f"My watchful eye turns its gaze towards: [bold cyan]{self.altar_path}[/]\n")
        else:
            print("=" * 60)
            print(header)
            print(f"Altar path: {self.altar_path}")
            print("=" * 60)

    def run(self):

        password = "wsedrfvbhoiasdf hoiuashfbokhunhh"

        for idx, ch in enumerate(self.challenges, 1):
            if HAS_RICH:
                console.print(Panel(f"[bold]{ch.name}[/]\n\n{ch.description}", title=f"Challenge {idx}/{len(self.challenges)}"))
            else:
                print(f"\n--- {ch.name} ---")
                print(ch.description)
            ch.on_start()
            while True:
                try:
                    if ch.is_completed(self.altar_path):
                        result = ch.on_complete()
                        if result:
                            password = result
                        print_good(ch.win_message)
                        print_good(f"Tribulation conquered: {ch.name}\n")
                        # Optionally clear altar between challenges if you like:
                        # self._clear_altar_contents()
                        break
                    time.sleep(POLL_INTERVAL)
                except KeyboardInterrupt:
                    print_error("Interrupted by user. Exiting.")
                    sys.exit(0)

        final = "🎁 YOU'VE DONE WELL ENOUGH. ENTER YOUR PASSWORD TO CONTINUE. 🎁"
        if HAS_RICH:
            console.rule(final)
        else:
            print("\n" + "=" * 60)
            print(final)
            print("=" * 60)
        
        entered_pass = ""
        attempts_remaining = 3
        while attempts_remaining >= 0:
            try:
                entered_pass = input(" >> ")
                if entered_pass == password:
                    webbrowser.open(WINNER_WEBPAGE)
                    return
                else:
                    print_error(f"Incorrect. {attempts_remaining} attempts remaining.")
                    attempts_remaining -= 1
            except KeyboardInterrupt:
                print_error("tsk tsk no ctrl+c on the command line")
                continue

        print_error("Ooh tough luck. Give it another go.")


    def _clear_altar_contents(self):
        """Optional utility to empty the altar between challenges. Use with caution."""
        for p in self.altar_path.iterdir():
            try:
                if p.is_file():
                    if p.name != "desktop.ini":
                        p.unlink()
                elif p.is_dir():
                    # careful: removes directories recursively
                    import shutil
                    shutil.rmtree(p)
            except Exception as e:
                print_error(f"Failed to remove {p}: {e}")

# endregion

# region Main

# -----------------------------
# CLI / Main
# -----------------------------
def main():
    desktop = get_desktop_path()
    altar = ensure_altar(desktop)
    play_sound_async(".\\assets\\startup.wav")
    # print_info(f"My watchful eye turns its gaze upon {altar}")

    # Build challenge list here. Order matters.
    challenges: list[Challenge] = [
        
        # Intro Challenge
        # ChallengeIntro(),
        
        # Math answer (core)
        # ChallengeMathAnswer(),

        # Reindeer image recognition (OPTIONAL COMPONENT)
        ChallengeFeedReindeerImage(),
        
        # Speed Typing
        # ChallengeSpeedTyping(),

        # Password Challenge
        # ChallengePasswordGame(),

        # PDF page requirement (OPTIONAL COMPONENT)
        # ChallengeFeedPDF(),

        # Reflex Challenge
        # ChallengeReflexes(),

    ]

    runner = ChallengeRunner(altar_path=altar, challenges=challenges)
    runner.run()



if __name__ == "__main__":
    main()

    # TODO: More trials?
    # TODO: XQC Clap Sound Effect on Tribulation complete
    # TODO: Powershell wrapper
    # TODO: ????

# endregion