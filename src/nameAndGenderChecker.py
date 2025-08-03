import re
import transliterate
import logging
import speakersOfCharacters
import difflib
import os

regexName = "^[a-zA-Zа-яА-ЯёЁ«»? \-]+$"
patternName = re.compile(regexName)
speaker = 'baya'
speakersOfCharacters.readCharactersDataBase()

muteСertainCharacters = False
mutedCharacters = []
with open(os.path.join(os.path.dirname(__file__), "../data/Characters/mutedCharacters.json"), 'r', encoding='utf-8') as openfile:
    import json
    mutedCharacters: list = json.load(openfile)

def RefactorNameAndGetSpeaker(name:str) -> [bool, str]:
    global speaker

    name = name.replace("\r", '')
    name = name.replace("\n", '')
    if patternName.search(name) is not None:
        print("name: " + name)
        logging.info("1 name: " + name)
        k = -1
        nameOfSelectedCharacter = None
        for nameDB, attrsDB in speakersOfCharacters.charactersDataBase.items():
            ratio = difflib.SequenceMatcher(None, name, nameDB).ratio()
            if ratio > k:
                speaker = attrsDB.get("speaker")
                k = ratio
                nameOfSelectedCharacter = nameDB
        logging.info("selected characker: " + str(nameOfSelectedCharacter))
        print("selected Character: " + str(nameOfSelectedCharacter))

        if muteСertainCharacters and nameOfSelectedCharacter in mutedCharacters:
            logging.info("selected characker in mute list")
            print("selected characker in mute list")
            return [False, None]

        return [True, speaker]
    return [False, None]

def setTravelerGender(isMale:bool):
    db = speakersOfCharacters.readCharactersDataBase()
    if db.get("Main character"):
        if isMale:
            db["Main character"]["speaker"] = "eugene"
        else:
            db["Main character"]["speaker"] = "baya"
    speakersOfCharacters.writeCharactersDataBase(db)
