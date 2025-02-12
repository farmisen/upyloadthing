import base64
import math

from sqids.constants import DEFAULT_ALPHABET
from sqids.sqids import Sqids


def djb2(s: str) -> int:
    """
    Compute a hash of the input string using the djb2 algorithm.

    This implementation processes the characters in reverse order and
    applies the djb2 algorithm with a twist for 32-bit overflow handling.
    It then adjusts the result to a signed 32-bit integer.

    Args:
        s (str): The input string to be hashed.

    Returns:
        int: A signed 32-bit hash of the input string.
    """
    h = 5381
    for char in reversed(s):
        h = (h * 33) ^ ord(char)
        # 32-bit integer overflow
        h &= 0xFFFFFFFF
    h = (h & 0xBFFFFFFF) | ((h >> 1) & 0x40000000)

    # Convert to signed 32-bit integer
    if h >= 0x80000000:
        h -= 0x100000000

    return h


def shuffle(string: str, seed: str) -> str:
    """
    Shuffle the characters of the given string using a seed.

    The shuffling process is based on a numeric seed derived from the
    djb2 hash of the provided seed string, ensuring that the same seed
    produces the same shuffled result for a given string.

    Args:
        string (str): The string to be shuffled.
        seed (str): The seed string used to influence the shuffling.

    Returns:
        str: The shuffled string.
    """
    chars = list(string)
    seed_num = djb2(seed)

    for i in range(len(chars)):
        j = int(math.fmod(math.fmod(seed_num, i + 1) + i, len(chars)))
        chars[i], chars[j] = chars[j], chars[i]

    return "".join(chars)


def generate_key(file_seed: str, app_id: str) -> str:
    """
    Generate a unique key using a file seed and an application identifier.

    This function generates a unique key by first shuffling the default
    alphabet using the application id as a seed. It then encodes the absolute
    value of the djb2 hash of the application id using the Sqids algorithm and
    a minimum length of 12. Finally, it encodes the file seed with Base64
    in a URL-safe manner and concatenates the two encoded strings.

    Args:
        file_seed (str): A seed string to represent or identify the file.
        app_id (str): The application identifier used to influence the key
                      generation and alphabet shuffling.

    Returns:
        str: The generated unique key.
    """
    alphabet = shuffle(DEFAULT_ALPHABET, app_id)

    encoded_app_id = Sqids(alphabet, min_length=12).encode([abs(djb2(app_id))])
    encoded_file_seed = base64.urlsafe_b64encode(file_seed.encode()).decode()
    return encoded_app_id + encoded_file_seed
