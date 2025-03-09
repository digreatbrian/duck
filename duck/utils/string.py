"""
String utilities module providing a variety of functions for common string manipulation tasks.
"""
import re

from typing import Dict, List


def smart_truncate(text: str, cap: int, grammar: list = None, suffix: str = '...') -> str:
    """
    Truncates the given text if it exceeds the specified character cap,
    ensuring that the truncation occurs at the last complete word or grammar boundary
    defined by the provided list of grammar elements.
    
    Args:
        text (str): The string to be truncated. Can be a regular text or a file path.
        cap (int): The maximum allowed length of the string.
        grammar (list): A list of grammar elements such as words, punctuation, etc. 
                        These will be used to define truncation boundaries.
        suffix (str): The suffix to append if truncation occurs. Default is '...'.
    
    Returns:
        str: The truncated string with the specified suffix appended if truncation occurs, 
             or the original string if no truncation is needed.
    
    Example:
        smart_truncate("This is a long sentence that might need truncation.", 30, grammar=[' ', '.'])
        # Returns: "This is a long..."
    """
    if grammar is None:
        grammar = [' ', '.', ',', ';', ':', '/', '\\']  # default grammar elements

    # Check if truncation is needed
    if len(text) > cap:
        # Calculate the available length for truncation, leaving space for the suffix
        truncated = text[:cap - len(suffix)]
        
        # Iterate over the grammar elements to find the right boundary
        last_boundary = -1
        for elem in grammar:
            last_boundary = truncated.rfind(elem)
            if last_boundary != -1:
                break
        
        # If no grammar boundary was found, truncate at the last character
        if last_boundary == -1:
            truncated = truncated[:cap - len(suffix)]
        else:
            truncated = truncated[:last_boundary]

        # If truncation is still needed, add the suffix
        return truncated + suffix
    
    return text


def capitalize_words(text: str) -> str:
    """
    Capitalizes the first letter of each word in the string.
    """
    return ' '.join(word.capitalize() for word in text.split())


def clean_string(text: str, remove_chars: str = '') -> str:
    """
    Removes unwanted characters (e.g., spaces or specific symbols) from the string.
    """
    cleaned_text = text.strip()  # Trim leading/trailing spaces
    for char in remove_chars:
        cleaned_text = cleaned_text.replace(char, '')
    return cleaned_text


def replace_multiple(text: str, replacements: dict) -> str:
    """
    Replaces multiple substrings with the provided replacements.
    Example: {"old1": "new1", "old2": "new2"}
    """
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def count_words(text: str) -> int:
    """
    Returns the number of words in a string.
    """
    return len(text.split())


def is_palindrome(text: str) -> bool:
    """
    Returns True if the string is a palindrome, otherwise False.
    """
    cleaned_text = ''.join(e for e in text.lower() if e.isalnum())
    return cleaned_text == cleaned_text[::-1]


def find_occurrences(text: str, substring: str) -> list:
    """
    Returns the indices of all occurrences of a substring in the string.
    """
    return [i for i in range(len(text)) if text.startswith(substring, i)]


def wrap_text(text: str, width: int, align: str = "left") -> str:
    """
    Wraps the text to the specified width. Can align the text to left, center, or right.
    
    Args:
        text (str): The text to wrap.
        width (int): The width at which to wrap the text.
        align (str): The alignment type ("left", "center", "right"). Default is "left".
    
    Returns:
        str: The wrapped text, aligned as requested.
    """
    wrapped_lines = []
    
    if align == "left":
        wrapped_lines = [text[i:i+width] for i in range(0, len(text), width)]
    elif align == "center":
        for i in range(0, len(text), width):
            line = text[i:i+width]
            wrapped_lines.append(line.center(width))
    elif align == "right":
        for i in range(0, len(text), width):
            line = text[i:i+width]
            wrapped_lines.append(line.rjust(width))
    
    return '\n'.join(wrapped_lines)


def snake_to_camel_case(text: str) -> str:
    """
    Converts a string from snake_case to camelCase.
    """
    components = text.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])
    

def camel_to_snake_case(text: str) -> str:
    """
    Converts a string from camelCase to snake_case.
    """
    return re.sub('([a-z])([A-Z])', r'\1_\2', text).lower()


def remove_non_alphanumeric(text: str) -> str:
    """
    Removes all characters except alphanumeric (letters and digits).
    """
    return ''.join(e for e in text if e.isalnum())


def to_kebab_case(text: str) -> str:
    """Convert a string to kebab-case."""
    return re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', text).lower()


def to_camel_case(text: str) -> str:
    """Convert a string to camelCase."""
    words = text.split('_')
    return words[0] + ''.join(word.title() for word in words[1:])


def find_and_replace(text: str, target: str, replacement: str) -> str:
    """Replace all occurrences of a target substring with a replacement string."""
    return text.replace(target, replacement)


def find_all_occurrences(text: str, target: str) -> List[int]:
    """Return all starting indices where the target substring occurs in the text (uses regex)."""
    return [m.start() for m in re.finditer(re.escape(target), text)]


def justify_text(text: str, width: int, direction: str = "left") -> str:
    """
    Justify text to the left, right, or center to fit a specified width.

    Args:
        text (str): The input text.
        width (int): The target width to justify to.
        direction (str): The direction to justify ("left", "right", or "center").

    Returns:
        str: The text formatted to the specified width.
    """
    if direction == "left":
        return text.ljust(width)
    elif direction == "right":
        return text.rjust(width)
    elif direction == "center":
        return text.center(width)
    else:
        raise ValueError("Direction must be 'left', 'right', or 'center'.")


def remove_extra_spaces(text: str) -> str:
    """Remove extra spaces from a string, leaving only one space between words."""
    return re.sub(r'\s+', ' ', text).strip()


def remove_punctuation(text: str) -> str:
    """Remove punctuation from a string."""
    return re.sub(r'[^\w\s]', '', text)


def remove_non_alphanumeric(text: str) -> str:
    """Remove all non-alphanumeric characters (keeps letters and numbers)."""
    return re.sub(r'[^a-zA-Z0-9]', '', text)


def string_similarity(str1: str, str2: str) -> float:
    """Compute the similarity between two strings using Levenshtein distance."""
    import Levenshtein
    return Levenshtein.ratio(str1, str2)


def are_anagrams(str1: str, str2: str) -> bool:
    """Check if two strings are anagrams of each other."""
    return sorted(str1) == sorted(str2)


def to_base64(text: str) -> str:
    """Encode a string in base64."""
    import base64
    return base64.b64encode(text.encode()).decode()


def from_base64(encoded_text: str) -> str:
    """Decode a base64 encoded string."""
    import base64
    return base64.b64decode(encoded_text.encode()).decode()


def wrap_words(text: str, line_length: int) -> str:
    """Wrap words at a specified line length."""
    wrapped_text = ""
    current_line = []
    
    for word in text.split():
        if sum(len(w) for w in current_line) + len(word) + len(current_line) > line_length:
            wrapped_text += " ".join(current_line) + "\n"
            current_line = [word]
        else:
            current_line.append(word)
    
    wrapped_text += " ".join(current_line)
    return wrapped_text


def transform_case_based_on_condition(text: str, condition: bool) -> str:
    """
    Change the case of the string based on a condition.
    
    Args:
        text (str): The input string.
        condition (bool): If True, converts text to uppercase; else lowercase.
        
    Returns:
        str: The transformed string.
    """
    return text.upper() if condition else text.lower()


def reverse_words_in_sentence(text: str) -> str:
    """Reverse the order of words in a string."""
    return ' '.join(text.split()[::-1])


def pad_text(text: str, total_length: int, padding_char: str = " ") -> str:
    """Pad a string to a specific total length."""
    return text.ljust(total_length, padding_char)


def is_camel_case(s: str) -> bool:
    """
    Check if a given string follows CamelCase (UpperCamelCase) or lowerCamelCase.
    
    Args:
        s (str): The input string to check.

    Returns:
        bool: True if the string is in CamelCase or lowerCamelCase, False otherwise.
    """
    # Ensure the string contains only letters and starts correctly
    return bool(re.fullmatch(r"[a-z]+(?:[A-Z][a-z]*)*", s) or re.fullmatch(r"[A-Z][a-z]*(?:[A-Z][a-z]*)*", s))


def is_camel_case(s: str) -> bool:
    """Checks if a string follows camelCase (lowerCamelCase)."""
    return bool(re.fullmatch(r"[a-z]+(?:[A-Z][a-z]*)*", s))


def is_pascal_case(s: str) -> bool:
    """Checks if a string follows PascalCase (UpperCamelCase)."""
    return bool(re.fullmatch(r"[A-Z][a-z]*(?:[A-Z][a-z]*)*", s))


def is_snake_case(s: str) -> bool:
    """Checks if a string follows snake_case."""
    return bool(re.fullmatch(r"[a-z]+(?:_[a-z]+)*", s))


def is_screaming_snake_case(s: str) -> bool:
    """Checks if a string follows SCREAMING_SNAKE_CASE."""
    return bool(re.fullmatch(r"[A-Z]+(?:_[A-Z]+)*", s))


def is_kebab_case(s: str) -> bool:
    """Checks if a string follows kebab-case."""
    return bool(re.fullmatch(r"[a-z]+(?:-[a-z]+)*", s))


def is_train_case(s: str) -> bool:
    """Checks if a string follows Train-Case (Capitalized Kebab Case)."""
    return bool(re.fullmatch(r"[A-Z][a-z]*(?:-[A-Z][a-z]*)*", s))
