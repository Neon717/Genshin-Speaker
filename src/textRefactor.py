import re
import logging
import difflib
import transliterate

letterRegex = "[a-zA-Zа-яА-ЯёЁ]+"
regex = "^[a-zA-Zа-яА-ЯёЁ., ?!\-\(\)\\n«»<>0-9]+[,.?!:]"
regexAdd = "[a-zA-Zа-яА-ЯёЁ0-9]+[a-zA-Zа-яА-ЯёЁ., ?!:\-\(\)\\n«»<>0-9]+$"
enRegex = "[A-Za-z]+"

letterPattern = re.compile(letterRegex)
pattern = re.compile(regex)
patternAdd = re.compile(regexAdd)
enPattern = re.compile(enRegex)


replacedStrings = {"\r": " ",
                   "\n": " ",
                   "..": ".",
                   "|": "",
                   "'": "",
                   "ʹ": "",
                   "ʻ": "",
                   "`": "",
                   "\"": "",
                   "”": "",
                   ":": ".",
                   "«": "",
                   "»": "",
                   "<": "",
                   ">": "",
                   "  ": " "
                   }

lastSpeachText = ""

def refactorText(text: str) -> [bool, str, bool]:
    global lastSpeachText

    nextDialoge = False

    if len(text) > 0 and text[-1] == "\n":
        text = text[0:-1]
    if len(text) > 0:
        print(4.1)
        logging.info("init text <<" + text + ">>")
        for searchedStr in replacedStrings:
            while searchedStr in text:
                text = text.replace(searchedStr, replacedStrings[searchedStr])
        logging.info("1-st filtered text <<" + text + ">>")
        s = pattern.search(text)
        if s is not None:
            print(4.2)
            text = s.group(0)
            logging.info("2-st filtered text <<" + text + ">>")
            s = patternAdd.search(text)
            if s is not None:
                text = s.group(0)
                logging.info("3-st filtered text <<" + text + ">>")

                if len(lastSpeachText) > 0:
                    textBlocks = re.split("([.,!?])", text)
                    lastSpeachTextBlocks = re.split("[.,!?]", lastSpeachText)
                    lastSpeachTextBlocks = [elem for elem in lastSpeachTextBlocks if elem != ""]
                    text = ""
                    logging.info(f"text blocks: {str(textBlocks)}")
                    logging.info(f"last text blocks: {str(lastSpeachTextBlocks)}")
                    for textBlock in reversed(textBlocks):
                        if len(textBlock) > 0:
                            k = difflib.SequenceMatcher(None, lastSpeachTextBlocks[-1], textBlock).ratio()
                            if k < 0.8:
                                text = textBlock + text
                                logging.info(f"added text block: <<{textBlock}>> k={k} < 0.8")
                            else:
                                logging.info(f"break on text block: <<{textBlock}>> k={k} > 0.8")
                                break
                    s = patternAdd.search(text)
                    if s is not None:
                        text = s.group(0)
                    else:
                        text = ""
                        nextDialoge = True
                print("Text <<" + text + ">>\r\n")

                """
                s = enPattern.search(text)
                while s:
                    enWord = s.group(0)
                    ruWord = transliterate.translit(enWord, 'ru')
                    text = text.replace(enWord, ruWord)
                    text = text.replace("W", "В")
                    text = text.replace("w", "в")
                    s = enPattern.search(text)
                logging.info("trenslited eng text <<" + str(text) + ">>")
                """

                if len(text) > 0:
                    print(5)
                    s = letterPattern.search(text)
                    if s is not None:
                        print(6)
                        logging.info("final text <<" + str(text) + ">>")
                        lastSpeachText = text
                        return [True, text, nextDialoge]
    return [False, None, nextDialoge]

def refactorTextSimple(text: str) -> [bool, str]:

    if len(text) > 0 and text[-1] == "\n":
        text = text[0:-1]
    if len(text) > 0:
        print(4.1)
        logging.info("init text <<" + text + ">>")
        for searchedStr in replacedStrings:
            while searchedStr in text:
                text = text.replace(searchedStr, replacedStrings[searchedStr])

        logging.info("1-st filtered text <<" + text + ">>")

        s = pattern.search(text)
        if s is not None:
            print(4.2)
            text = s.group(0)
            logging.info("2-st filtered text <<" + text + ">>")
            s = patternAdd.search(text)
            if s is not None:
                text = s.group(0)
                logging.info("3-st filtered text <<" + text + ">>")


                print("Text <<" + text + ">>\r\n")

                s = enPattern.search(text)
                while s:
                    enWord = s.group(0)
                    ruWord = transliterate.translit(enWord, 'ru')
                    if ruWord == "q": ruWord = "к"
                    text = text.replace(enWord, ruWord)
                    text = text.replace("W", "В")
                    text = text.replace("w", "в")
                    text = text.replace("X Y Z", "")
                    s = enPattern.search(text)
                logging.info("trenslited eng text <<" + str(text) + ">>")

                if len(text) > 0:
                    s = letterPattern.search(text)
                    if s is not None:
                        print(5)
                        logging.info("final text <<" + str(text) + ">>")
                        return [True, text]
    return [False, None]
