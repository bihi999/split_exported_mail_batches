
def split_string(input_string: str, regex: str) -> List[str]:
    """
    Teilt einen String anhand eines Regex und gibt eine Liste von Teilstrings zurück.
    
    :param input_string: Der zu teilende String
    :param regex: Der Regex, der als Trenner angewandt wird
    :return: Liste von Teilstrings
    """
    return re.split(regex, input_string)