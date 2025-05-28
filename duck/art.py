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
    
    bold_start = "\033[1m"
    bold_end = "\033[0m"
    
    # Display large art only if the screen is sufficiently wide and tall
    if columns >= 80 and lines >= 24:  # Common size for tablets and PCs
        print(bold_start + duck_art_large + bold_end)
    else:
        print(bold_start + duck_art_small + bold_end)


if __name__ == "__main__":
    display_duck_art()
