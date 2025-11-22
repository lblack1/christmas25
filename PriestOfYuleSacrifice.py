#!/usr/bin/env python3
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

try:
    from PIL import Image         # image handling (optional advanced)
    import imagehash             # perceptual hashing (optional advanced)
    HAS_IMAGEHASH = True
except Exception:
    HAS_IMAGEHASH = False


from rich.console import Console
from rich.panel import Panel
HAS_RICH = True
console = Console()

client = genai.Client()

# -----------------------------
# Configuration / Constants
# -----------------------------
POLL_INTERVAL = 1.0  # seconds between checks
ALTAR_FOLDER_NAME = "Sacrificial Altar"
WINNER_WEBPAGE = "https://christmas25.lloyd.black"
ICON_NAME = ".\\assets\\Sacrificial_Altar.ico"

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]



# -----------------------------
# Helper utilities
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


def print_prompt(text: str):
    if HAS_RICH:
        console.print(Panel(text, style="blue"))
    else:
        print("[PROMPT] " + text)



def play_sound_async(path):
    """Play a WAV file asynchronously on Windows using winsound."""
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(f"No such file: {p}")

    def _play():
        winsound.PlaySound(str(p), winsound.SND_FILENAME | winsound.SND_ASYNC)

    threading.Thread(target=_play, daemon=True).start()



def get_desktop_path() -> Path:
    """Locate the current user's Desktop (Windows-friendly)."""
    home = Path.home()
    desktop = home / "Desktop"

    if desktop.exists():
        pass
    elif os.path.exists("C:\\Users\\mrllo\\OneDrive\\Desktop"):
        desktop = Path("C:\\Users\\mrllo\\OneDrive\\Desktop")
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
        subprocess.run(['ie4uinit.exe', '-ClearIconCache'], shell=True)
    except PermissionError as e:
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
    set_folder_icon(altar, ICON_NAME)
    return altar




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
            if p.name == "munchies.txt" and p.is_file():
                return True
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
                            page_2_text = reader.pages[1].extract_text()
                            if "chicken" in page_2_text:
                                return True
                            else:
                                print_error("Satisfactory in volume, but page 2 could use more chicken.")
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

class ChallengeFeedReindeerImage(Challenge):
    name = "A Sacrifice of Flesh"
    description = (
        "I hunger for the meat of the festive beast adorned with horns and bound to servitude at the helm of the fat man's carriage. Or an image of one."
    )
    VALID_EXTS = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }
    win_message = "yep that's a reindeer"



    def __init__(self):
        self.gemini_prompt = """You are part of a scripted workflow, and are responsible for image understanding.
        You will be given an image. Your task is to identify if there is a reindeer present in the image.
        You must reply with exactly one word; if there is a reindeer in the image, respond 'yes'.
        If there is not a reindeer in the image, respond 'no'.
        """
        self.model='gemini-2.5-flash'
        self.queries = 0


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

                # Gemini check
                if self.check_image(p):
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
    name = "A Trial of Humility"
    description = "Type the following self-affirmation. I'm really needy so please hurry and don't mess it up."

    def __init__(self):

        self.phrases = [
            ["I will never be able to fly by flapping my arms really hard. I walk the ground, downtrodden that my skinny meat sticks don't provide the lift required to get my terrestrial ass off the floor. For this, I weep.", 35],
            ["I am a slow typist. This saddens me. Is it typist? Typer? I don't know. This saddens me even more. I weep, for I am not enough.", 27],
            ["Gods how I wish I was Brennan Lee Mulligan. With his luscious hair, luscious face, luscious voice. Gee golly that man does things to me and I'm not him. Sadge.", 27],
            ["Let any fish who meets my gaze learn the true meaning of fear; for I am the harbinger of death. The bane of creatures sub-aqueous, my rod is true and unwavering as I cast into the aquatic abyss. A man, scorned by this uncaring Earth, finds solace in the sea. My only friend, the worm upon my hook. Wriggling, writhing, struggling to surmount the mortal pointlessness that permeates this barren world. I am alone. I am empty. And yet, I fish.", 78],
            ["Women fear me. Fish fear me. Men turn their eyes away from me. As I walk, no beast dares make a sound in my presence. I am alone on this barren earth.", 25],
            ["I'm a little baby", 3],
            ["My mill grinds rats, and mice. Your mill grinds pepper, and spice. Piss a bed, piss a bed, barley butt. My Bum is so heavy, I can't get up.", 25],
            ["Brother Barnabus, I'm so geeked on purple elixir I hardly even know where I am. It's honestly ruining my life. My crops lay barren, Lady Gwendoline has been abducted by Lord Fergus, Gort the Serf is as unproductive as ever.", 35],
            ["Je ne pourrai jamais voler en battant des bras de toutes mes forces. Je marche a meme le sol, abattu que mes maigres muscles ne me permettent pas de decoller de ce fichu sol. Et pour cela, je pleure.", 40],
            ["", ],
            # ["", ],
            # ["", ],
        ]

        self.selection = r.choice(self.phrases)
        self.passed = False

    def on_start(self):
        
        selected_phrase = self.selection[0]
        
        print_error(f"You will have {self.selection[1]} seconds.")
        time.sleep(3)
        print_error("Starting...")
        time.sleep(2)
        print_error("Now")
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
            "Password must be at least 8 characters long": [False, True], # Rule, [passed, shown as part of the loop]
            "Password must contain a number": [False, False],
            "Password must include a special character.": [False, False],
            "Digits in your password must add up to 25.": [False, False],
            "Password must include a month of the year.": [False, False],
            "Password must contain the Roman Numeral for 9.": [False, False],
            "Password must contain a reindeer.": [False, False], # Any of the named ones: Dasher, Dancer, Prancer, Vixen, Comet, Cupid, Donner, Blitzen
            "Password file must match the password, so I can remember it.": [False, False],
            "Keeping your password in a file named after the password is insecure, please reverse it in the file name to make it secret.": [False, False],
        }




    def is_completed(self, altar_path: Path):

        for p in altar_path.iterdir():
            if p.suffix.lower() == ".txt" and p.is_file():
                try:
                    self.evaluate_rules(p)
                except:
                    return False


        


        for rule, passed in enumerate(self.requirements):
            if passed == False:
                return False
            else:
                continue

        return True


    def evaluate_rules(self, path: Path):
        return False

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
                        ch.on_complete()
                        print_good(ch.win_message)
                        print_good(f"Tribulation conquered: {ch.name}\n")
                        # Optionally clear altar between challenges if you like:
                        self._clear_altar_contents()
                        break
                    time.sleep(POLL_INTERVAL)
                except KeyboardInterrupt:
                    print_error("Interrupted by user. Exiting.")
                    sys.exit(0)

        final = "🎁 YOU'VE DONE WELL ENOUGH. CLAIM THY PRIZE. 🎁"
        if HAS_RICH:
            console.rule(final)
        else:
            print("\n" + "=" * 60)
            print(final)
            print("=" * 60)
        
        # time.sleep(5)
        # webbrowser.open(WINNER_WEBPAGE)

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
        ChallengeIntro(),
        
        # Math answer (core)
        # ChallengeMathAnswer(),
        
        # PDF page requirement (OPTIONAL COMPONENT)
        # ChallengeFeedPDF(),

        # Reindeer image recognition (OPTIONAL COMPONENT)
        # ChallengeFeedReindeerImage(),

        # Speed Typing
        # ChallengeSpeedTyping(),



    ]

    runner = ChallengeRunner(altar_path=altar, challenges=challenges)
    runner.run()



if __name__ == "__main__":
    main()

    # TODO: Test Page Length in PyPDF2

