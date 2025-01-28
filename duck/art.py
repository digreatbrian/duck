"""
This provides accessibility to Duck Ansi/Ascii Art.
"""

import shutil

duck_art_large = """
██████╗  ██╗   ██╗ ██████╗██╗  ██╗
██╔══██╗ ██║   ██║██╔════╝██║ ██╔╝
██║  ██║ ██║   ██║██║     █████╔╝ 
██║  ██║ ██║   ██║██║     ██╔═██╗ 
██████╔╝╚██████╔╝╚██████╗ ██║  ██╗
╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝
"""

duck_art_small = """
   __
<(o )___
 (  ._> /
  `----'
"""


def display_duck_art():
    # Get terminal size
    columns, lines = shutil.get_terminal_size(fallback=(80, 24))

    # Display large art only if the screen is sufficiently wide and tall
    if columns >= 80 and lines >= 24:  # Common size for tablets and PCs
        print(duck_art_large)
    else:
        print(duck_art_small)


if __name__ == "__main__":
    display_duck_art()
