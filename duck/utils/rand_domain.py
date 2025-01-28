import random
import string


def generate_random_label(length: int) -> str:
    """
    Generates a random label for a domain name.

    Args:
        length (int): The length of the label.

    Returns:
        str: A random label.
    """
    return "".join(
        random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_domain(max_labels: int = 3,
                           max_label_length: int = 32) -> str:
    """
    Generates a random domain name valid according to RFC 1034/1035.

    Args:
        max_labels (int): Maximum number of labels in the domain. Default is 3.
        max_label_length (int): Maximum length of each label. Default is 63.

    Returns:
        str: A random domain name.
    """
    labels = [
        generate_random_label(random.randint(1, max_label_length))
        for _ in range(max_labels)
    ]
    return ".".join(labels) + ".com"
