import json
import re
import os
import requests

jsonFileName = os.path.join(os.path.dirname(__file__), '../data/Characters/characters.json')
charactersDataBase = dict()

def readCharactersDataBase():
    print("get characters DB")
    global charactersDataBase
    if len(charactersDataBase.items()) == 0:
        checkCharactersDataUpdate()

        print("read characters DB")
        with open(jsonFileName, 'r', encoding='utf-8') as openfile:
            charactersDataBase = json.load(openfile)
            return charactersDataBase
    else:
        return charactersDataBase


def writeCharactersDataBase(data):
    print("write characters DB")
    with open(jsonFileName, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
        global charactersDataBase
        charactersDataBase = data

def checkCharactersDataUpdate():
    response = requests.get('https://raw.githubusercontent.com/Neon717/Genshin-Speaker/refs/heads/main/README.md')
    if response.status_code == 200:
        srcStr = "#version:"
        if srcStr in str(response.content):
            startPos = str(response.content).find(srcStr) + len(srcStr)
            endPos = str(response.content).find("-->", startPos)
            webVersion = str(response.content)[startPos:endPos]
            regex = r'\d+\.\d+-\d+'
            patternF = re.compile(regex)
            s = patternF.search(webVersion)
            if s:
                webVersion = s.group(0)
                settingsFile = os.path.join(os.path.dirname(__file__), '../data/settings.json')
                with open(settingsFile, 'r', encoding='utf-8') as openfile:
                    settings = json.load(openfile)
                if settings.get("versionCharactersDB") != webVersion:
                    response = requests.get('https://raw.githubusercontent.com/Neon717/Genshin-Speaker/refs/heads/main/data/Characters/characters.json')
                    if response.status_code == 200:
                        with open(jsonFileName + "d", 'wb') as file:
                            file.write(response.content)

                        settings["versionCharactersDB"] = webVersion
                        with open(settingsFile, 'w', encoding='utf-8') as f:
                            json.dump(settings, f, ensure_ascii=False)
                        print("База персонажей обновлена")
