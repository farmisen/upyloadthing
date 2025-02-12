from typing import Any

from inflection import underscore


def snakify(data: Any) -> Any:
    """Recursively converts all dictionary keys from camelCase to snake_case.

    This function handles nested data structures, converting all dictionary
    keys from camelCase to snake_case format while preserving the original
    values.

    Args:
        data (Any): The data to convert. Can be a dictionary, list, or
        any other type.
            - If dict: converts all keys and recursively processes values
            - If list: recursively processes all items
            - Other types: returned as-is

    Returns:
        Any: The processed data with all dictionary keys converted to
        snake_case
    """
    if isinstance(data, dict):
        return {underscore(key): snakify(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [snakify(item) for item in data]
    return data
