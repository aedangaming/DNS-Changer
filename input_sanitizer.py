_FA_TO_ENG = {
    "آ": "H",
    "ا": "h",
    "ب": "f",
    "پ": "\\",
    "ت": "j",
    "ث": "e",
    "ج": "[",
    "چ": "]",
    "ح": "p",
    "خ": "o",
    "د": "n",
    "ذ": "b",
    "ر": "v",
    "ز": "c",
    "ژ": "C",
    "س": "s",
    "ش": "a",
    "ص": "w",
    "ض": "q",
    "ط": "x",
    "ظ": "z",
    "ع": "u",
    "غ": "y",
    "ف": "t",
    "ق": "r",
    "ک": ";",
    "گ": "'",
    "ل": "g",
    "م": "l",
    "ن": "k",
    "و": ",",
    "ه": "i",
    "ی": "d",
}


def convert_keystrokes_fa_to_en(input: str) -> str:
    result = ""
    for char in input:
        if _FA_TO_ENG.get(char):
            result = result + _FA_TO_ENG[char]
        else:
            result = result + char

    return result
