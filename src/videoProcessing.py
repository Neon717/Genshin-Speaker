import os

import numpy as np
import cv2
from mss import mss
import pytesseract
import time
import logging
import nameAndGenderChecker
import textRefactor
import re
from PyQt5.QtCore import QObject, pyqtSignal
import pyautogui
import random
from PIL import ImageFont, ImageDraw, Image
import sounddevice as sd
import textToSpeach

DEFAULT_SIZE = 1080

class GenshinVoicer(QObject):
    finished = pyqtSignal()
    ready = pyqtSignal()
    progress = pyqtSignal(int)
    allObjectsCreated = pyqtSignal()
    cudaAvailable = pyqtSignal(bool)
    canRun = True
    proc = None
    monitor = 1
    canSpeak = True
    switchDial = False
    playerName = ""
    voicePlayerName = ""
    detectPlayerName = False
    playerNameForDialHeaderImg = None
    playerNameForDialHeaderImgSmall = None
    global textToSpeach

    _showCVWindows = False

    def __init__(self):
        super().__init__()
        self.allObjectsCreated.emit()
        self.cudaAvailable.emit(textToSpeach.isCudaAvailable())

    def run(self):
        self.runVideoDetect()
        self.finished.emit()

    def runVideoDetect(self):


        self.progress.emit(10)
        textToSpeach.init(self.proc)
        self.progress.emit(20)

        logging.basicConfig(level=logging.INFO, filename=os.path.dirname(__file__) + "/../log.log",filemode="w",
                            format="%(asctime)s %(levelname)s %(message)s", encoding='utf-8')

        beginSpeachTime = 0
        speachTime = 0
        isNowSpeaking = False

        sct = mss()
        mon = sct.monitors[self.monitor]

        speaker = 'baya'
        msgImg = self.replace_zero_alpha_with_noise(
            cv2.resize(
                cv2.imread(os.path.dirname(__file__) + '/../data/Logos/msg.png', cv2.IMREAD_UNCHANGED),
                (0, 0),
                fx= mon["height"]/DEFAULT_SIZE,
                fy= mon["height"]/DEFAULT_SIZE
            ))
        dialHistImg = self.replace_zero_alpha_with_noise(
            cv2.resize(
                cv2.imread(os.path.dirname(__file__) + '/../data/Logos/dialHistory.png', cv2.IMREAD_UNCHANGED),
                (0, 0),
                fx=mon["height"] / DEFAULT_SIZE,
                fy=mon["height"] / DEFAULT_SIZE
            ))
        selectUtterImg = self.replace_zero_alpha_with_noise(
            cv2.resize(
                cv2.imread(os.path.dirname(__file__) + '/../data/Logos/selectUtterMsg.png', cv2.IMREAD_UNCHANGED),
                (0, 0),
                fx=mon["height"] / DEFAULT_SIZE,
                fy=mon["height"] / DEFAULT_SIZE
            ))
        threeDotsImg = self.replace_zero_alpha_with_noise(
            cv2.resize(
                cv2.imread(os.path.dirname(__file__) + '/../data/Logos/3dots.png', cv2.IMREAD_UNCHANGED),
                (0, 0),
                fx=mon["height"] / DEFAULT_SIZE,
                fy=mon["height"] / DEFAULT_SIZE
            ))

        pytesseract.pytesseract.tesseract_cmd = os.path.dirname(__file__) + '/../external/Tesseract-OCR/tesseract.exe'

        top_txt = 0.748148148148148
        down_txt = 0.9537037037037037
        left_txt = 0.16666666666666666
        right_txt = 0.8333333333333334

        top_name = 0.6857407407407407
        down_name = 0.8333333333333334
        left_name = 0.3125
        right_name = 0.6770833333333334

        top_msg = 0.9
        down_msg = 0.99
        left_msg = 0.0
        right_msg = 0.0625

        top_dialHist = 0
        down_dialHist = 0.1111111111111111
        left_dialHist = 0
        right_dialHist = 0.15625

        top_selectUtter = 0.5925925925925926
        down_selectUtter = 0.8796296296296297
        left_selectUtter = 0.6270833333333333
        right_selectUtter = 0.8854166666666666

        top_threeDots = 929
        down_threeDots = top_threeDots + 51
        left_threeDots = 930
        right_threeDots = left_threeDots + 60
        top_threeDots = top_threeDots/1080
        down_threeDots = down_threeDots/1080
        left_threeDots = left_threeDots/1920
        right_threeDots = right_threeDots/1920


        fontSize = mon["height"] / 1080.0 * 31.0
        font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "../data/genshinFont.ttf"), fontSize)
        self._tripleQuestionMarkImg = self.generateTextImage("???", font)


        if self.detectPlayerName and len(self.playerName) > 0:
            self.updatePlayerNickImg()


        print("Начата прогонка Силеро после запуска")
        testText = "Подавляющее большинство критиков оценило умелую стилизацию под язык викторианской эпохи, выполненную американскими писателями; в то же время низкие оценки получила банальность фабулы и оборванные сюжетные линии. Несмотря на многочисленные номинации, роман не получил ни одной литературной премии. Тем не менее критики XXI века подчёркивают, что У. Гибсон и Б. Стерлинг своим романом определили границы стимпанковского субжанра и наметили основные векторы его развития."
        testTextBlocks = re.split("[.,!?]", testText)
        for i in range(len(testTextBlocks)-1):
            if not self.canRun:
                break
            textToSpeach.soundText(testTextBlocks[i], 'random', non_play=True)
            print("прогонка: " + str(i) + "/" + str(len(testTextBlocks)))
            self.progress.emit(40 + int(i/(len(testTextBlocks) - 2) * 60))
            time.sleep(2)
        print("Прогонка Силеро завершена")

        print("Готов к работе")
        self.ready.emit()

        lastTimeSwitchDial = time.time()
        lastDetectedSelectorUtterTime = time.time()

        name_bounding_box = {'top': mon["top"] + int(mon["height"] * top_name), 'left': mon["left"] + int(mon["width"] * left_name),
                             'width': int(mon["width"] * (right_name - left_name)), 'height': int(mon["height"] * (down_name - top_name)),
                             'mon': self.monitor}
        text_bounding_box = {'top': mon["top"] + int(mon["height"] * top_txt), 'left': mon["left"] + int(mon["width"] * left_txt),
                             'width': int(mon["width"] * (right_txt - left_txt)), 'height': int(mon["height"] * (down_txt - top_txt)),
                             'mon': self.monitor}
        threeDots_bounding_box = {'top': mon["top"] + int(mon["height"] * top_threeDots),
                                  'left': mon["left"] + int(mon["width"] * left_threeDots),
                                  'width': int(mon["width"] * (right_threeDots - left_threeDots)),
                                  'height': int(mon["height"] * (down_threeDots - top_threeDots)),
                                  'mon': self.monitor}
        msg_bounding_box = {'top': mon["top"] + int(mon["height"] * top_msg), 'left': mon["left"] + int(mon["width"] * left_msg),
                            'width': int(mon["width"] * (right_msg - left_msg)), 'height': int(mon["height"] * (down_msg - top_msg)),
                            'mon': self.monitor}
        dialHist_bounding_box = {'top': mon["top"] + int(mon["height"] * top_dialHist), 'left': mon["left"] + int(mon["width"] * left_dialHist),
                                 'width': int(mon["width"] * (right_dialHist - left_dialHist)),
                                 'height': int(mon["height"] * (down_dialHist - top_dialHist)),
                                 'mon': self.monitor}
        selectUtter_bounding_box = {'top': mon["top"] + int(mon["height"] * top_selectUtter),
                                    'left': mon["left"] + int(mon["width"] * left_selectUtter),
                                    'width': int(mon["width"] * (right_selectUtter - left_selectUtter)),
                                    'height': int(mon["height"] * (down_selectUtter - top_selectUtter)),
                                    'mon': self.monitor}

        while self.canRun:
            if not self.canSpeak:
                time.sleep(1)
                continue
            mon = sct.monitors[self.monitor]

            textImg = cv2.cvtColor(np.array(sct.grab(text_bounding_box)), cv2.COLOR_BGRA2BGR)
            nameImg = cv2.cvtColor(np.array(sct.grab(name_bounding_box)), cv2.COLOR_BGRA2BGR)

            rawMsgImg = cv2.cvtColor(np.array(sct.grab(msg_bounding_box)), cv2.COLOR_BGRA2BGR)
            resMsg = cv2.matchTemplate(rawMsgImg.astype(np.uint8), msgImg.astype(np.uint8), cv2.TM_CCOEFF_NORMED)
            locMsg = np.where(resMsg >= 0.8)

            if len(locMsg[0]) > 0:
                res, speaker, topName = self._detectName(nameImg, self.playerNameForDialHeaderImgSmall, ((0, 185, 244), (2, 190, 250)))
            else:
                res, speaker, topName = self._detectName(nameImg, self.playerNameForDialHeaderImg, ((0, 195, 255), (0, 195, 255)))

            if res:
                logging.info("start detect text")
                # get text
                subTopText = int(name_bounding_box["top"] + topName - text_bounding_box["top"])
                if subTopText > 0:
                    textImg = textImg[subTopText:,:]

                #gray = cv2.cvtColor(textImg, cv2.COLOR_BGR2GRAY)
                hsv = cv2.cvtColor(textImg, cv2.COLOR_BGR2HSV)
                if mon["height"] < 1000:
                    h_min = np.array((0, 0, 180), np.uint8)
                else:
                    h_min = np.array((12, 7, 232), np.uint8)
                h_max = np.array((17, 9, 247), np.uint8)
                threshWhite = cv2.inRange(hsv, h_min, h_max)

                h_min = np.array((87, 208, 205), np.uint8)
                h_max = np.array((97, 255, 255), np.uint8)
                threshBlue = cv2.inRange(hsv, h_min, h_max)

                thresh = threshWhite | threshBlue

                #Заполнение текста выбора диалога, чтобы не попапло в основной текст
                rawSelectUtter = cv2.cvtColor(np.array(sct.grab(selectUtter_bounding_box)), cv2.COLOR_BGRA2BGR)
                resSelectUtter = cv2.matchTemplate(rawSelectUtter.astype(np.uint8), selectUtterImg.astype(np.uint8), cv2.TM_CCOEFF_NORMED)
                locSelectUtter = np.where(resSelectUtter >= 0.7)
                dtop = int(mon["height"] * (top_selectUtter - top_txt))
                dleft = int(mon["width"] * (left_selectUtter - left_txt))
                for pt in zip(*locSelectUtter[::-1]):
                    dtop1 = dtop + pt[1] - 5
                    dtop2 = dtop + pt[1] + selectUtterImg.shape[1] + 5
                    dleft1 = dleft + pt[0] - 2
                    if dtop1 < 0: dtop1 = 0
                    if dtop2 > 0:
                        thresh[dtop1:dtop2, dleft1:] = 0


                d = pytesseract.image_to_data(thresh, lang='rus', output_type=pytesseract.Output.DICT, config='--psm 6')

                # Проверка наличия имени
                if self.detectPlayerName and len(self.playerName) > 0 and len(self.voicePlayerName):
                    if len(locMsg[0]) > 0:
                        d, textImg, _ = self.replaceSubImageToText(textImg, thresh, self.targetNameImgSmall, self.voicePlayerName, d, font)
                    else:
                        d, textImg, _ = self.replaceSubImageToText(textImg, thresh, self.targetNameImg, self.voicePlayerName, d, font)

                text = ' '.join(d['text'])

                if self._showCVWindows:
                    for i in range(len(d["level"])):
                        if d["level"][i] == 5:
                            cv2.rectangle(textImg, (d["left"][i], d["top"][i]), (d["left"][i] + d["width"][i], d["top"][i] + d["height"][i]), (255, 255, 0), 1)

                    cv2.imshow("text subImage", textImg)
                    cv2.imshow("text thresh", thresh)

                res, text, nexDialog = textRefactor.refactorText(text)

                if not res:
                    # Поиск диалога = "..."
                    rawThreeDotsImg = cv2.cvtColor(np.array(sct.grab(threeDots_bounding_box)), cv2.COLOR_BGRA2BGR)
                    resThreeDots = cv2.matchTemplate(rawThreeDotsImg.astype(np.uint8), threeDotsImg.astype(np.uint8), cv2.TM_CCOEFF_NORMED)
                    locThreeDots = np.where(resThreeDots >= 0.4)
                    if len(locThreeDots[0]) > 0:
                        isNowSpeaking = True
                        nexDialog = True

                #переход к следующему диалогу
                if self.switchDial and nexDialog and isNowSpeaking and time.time() - lastTimeSwitchDial > 1 and (beginSpeachTime + speachTime + 0.5) - time.time() < 0:
                    rawMsgImg = cv2.cvtColor(np.array(sct.grab(msg_bounding_box)), cv2.COLOR_BGRA2BGR)
                    rawDialHistImg = cv2.cvtColor(np.array(sct.grab(dialHist_bounding_box)), cv2.COLOR_BGRA2BGR)

                    resMsg = cv2.matchTemplate(rawMsgImg.astype(np.uint8), msgImg.astype(np.uint8), cv2.TM_CCOEFF_NORMED)
                    resDialHist = cv2.matchTemplate(rawDialHistImg.astype(np.uint8), dialHistImg.astype(np.uint8), cv2.TM_CCOEFF_NORMED)
                    resSelectUtter = cv2.matchTemplate(rawSelectUtter.astype(np.uint8), selectUtterImg.astype(np.uint8), cv2.TM_CCOEFF_NORMED)
                    locMsg = np.where(resMsg >= 0.8)
                    locDialHist = np.where(resDialHist >= 0.6)
                    locSelectUtter = np.where(resSelectUtter >= 0.7)

                    if len(locSelectUtter[0]) > 0:
                        lastDetectedSelectorUtterTime = time.time()

                    if len(locMsg[0]) == 0 and len(locDialHist[0]) > 0 and len(locSelectUtter[0]) == 0 and time.time() - lastDetectedSelectorUtterTime > 3:
                        logging.info("switch to next dialog")
                        #isNowSpeaking = False
                        with pyautogui.hold('space'):
                            time.sleep(0.002 * random.randint(50, 130))
                        lastTimeSwitchDial = time.time() + random.random() * 2
                        print("---------- switch dial ------------")
                        logging.info("switch dial")

                if res:
                    audio, sample_rate = textToSpeach.soundText(text, speaker)

                    #wait until end last speach
                    sleepTime = (beginSpeachTime + speachTime) - time.time()
                    if sleepTime > 0:
                        print("Ожидание конца проигрывания последней реплики")
                        time.sleep(sleepTime)
                    isNowSpeaking = False

                    #play new speach
                    print("Начало проигрывания новой реплики")
                    speachTime = len(audio) / sample_rate
                    sd.play(audio, sample_rate)
                    isNowSpeaking = True
                    beginSpeachTime = time.time()
            k = cv2.waitKey(30)
            if (k & 0xFF) == ord('q'):
                cv2.destroyAllWindows()
                break
        print(8)

    def _detectName(self, nameImg, targetNameImg, threshColorBGRRange) -> [bool, str, int]:
        """
        Обнаруживает имя персонажа на изображении

        Parameters:
        nameImg: Исходное изображение, на котором надо найти имя.

        Returns:
        [успех поиска (bool), найденное имя (str), вертикальная координата имени (int)]
        """
        hsv = cv2.cvtColor(nameImg, cv2.COLOR_BGR2HSV)
        h_min = np.array((21, 250, 234), np.uint8)
        h_max = np.array((28, 255, 255), np.uint8)
        thresh = cv2.inRange(hsv, h_min, h_max)
        if self._showCVWindows:
            cv2.imshow("name", nameImg)
            cv2.imshow("name_threshold", thresh)
            cv2.waitKey(1)

        match = cv2.matchTemplate(thresh, self._tripleQuestionMarkImg, cv2.TM_CCOEFF_NORMED)
        loc = np.where(match >= 0.7)

        tresh2 = cv2.inRange(nameImg, threshColorBGRRange[0], threshColorBGRRange[1])

        if len(loc[0]) > 0:
            name = "???"
        elif len(self.playerName) > 0 and targetNameImg is not None and len((np.where((cv2.matchTemplate(tresh2, targetNameImg, cv2.TM_CCOEFF_NORMED)) >= 0.7))[0]) > 0:
            name = "Main character"
        else:
            name: str = pytesseract.image_to_string(thresh, lang='rus')
        res, speaker = nameAndGenderChecker.RefactorNameAndGetSpeaker(name)
        yName = None
        if res:
            yName = np.median(np.nonzero(thresh)[0])
        return [res, speaker, yName]

    def updatePlayerNickImg(self):
        sct = mss()
        mon = sct.monitors[self.monitor]
        if len(self.playerName) > 0:
            fontSize = mon["height"] / 1080.0 * 31.0
            font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "../data/genshinFont.ttf"), fontSize)
            self.targetNameImg = self.generateTextImage(self.playerName,
                                                        font,
                                                        colorRGB=(246, 242, 238),
                                                        treshRange=((238, 242, 246), (238, 242, 246))
                                                        )

            fontSize = mon["height"] / 1080.0 * 28.0
            font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "../data/genshinFont.ttf"), fontSize)
            self.targetNameImgSmall = self.generateTextImage(self.playerName,
                                                        font,
                                                        colorRGB=(246, 242, 238),
                                                        treshRange=((238, 242, 246), (238, 242, 246))
                                                        )

            fontSize = mon["height"] / 1080.0 * 33.0
            font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "../data/genshinFont.ttf"), fontSize)
            self.playerNameForDialHeaderImg = self.generateTextImage(self.playerName,
                                                                     font,
                                                                     colorRGB=(255, 195, 0),
                                                                     treshRange=((0, 195, 255), (0, 195, 255)),
                                                                     setTreshAsHSV=False
                                                                     )
            fontSize = mon["height"] / 1080.0 * 31.0
            font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "../data/genshinFont.ttf"), fontSize)
            self.playerNameForDialHeaderImgSmall = self.generateTextImage(self.playerName,
                                                                     font,
                                                                     colorRGB=(255, 195, 0),
                                                                     treshRange=((0, 195, 255), (0, 195, 255)),
                                                                     setTreshAsHSV=False
                                                                     )

    def setTravelerGender(self, isMale: bool):
        nameAndGenderChecker.setTravelerGender(isMale)

    def isCudaAvailable(self):
        return textToSpeach.isCudaAvailable()

    def setSpeechSpeed(self, speed):
        textToSpeach.speechSpeed = speed

    def setVolume(self, vol):
        textToSpeach.volume = vol

    def showCVWindows(self):
        self._showCVWindows = True

    def hideCVWindows(self):
        self._showCVWindows = False

    def generateTextImage(self, text, font, colorRGB=None, treshRange=None, setTreshAsHSV=False):
        """
        :param text: Текст, который нужно преобразовать в картинку
        :param font: объект шрифта созданный через ImageFont
        :param colorRGB: цвет текста
        :param treshRange: [minColor, maxColor], color: (B, G, R) или (H, S, V)
        :param setTreshAsHSV: bool switcher
        :return: 2-bit image
        """

        blank_image = np.zeros((font.getbbox(text)[3], font.getbbox(text)[2], 4), np.uint8)
        image = cv2.cvtColor(blank_image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), text, font=font, fill=colorRGB)
        targetImg = np.array(image)[:, :, ::-1].copy()
        if setTreshAsHSV:
            targetImg = cv2.cvtColor(targetImg, cv2.COLOR_BGR2HSV)

        if treshRange is None:
            targetImg = cv2.inRange(targetImg, (127, 127, 127), (255, 255, 255))
        else:
            targetImg = cv2.inRange(targetImg, np.array(treshRange[0], np.uint8), np.array(treshRange[1], np.uint8))
        return targetImg

    def group_near_points(self, points, threshold):
        """Группирует точки, если они близки друг к другу.

        Args:
            points (list of tuples): Список точек (x, y).
            threshold (float): Порог расстояния для группировки.

        Returns:
            list of lists: Список подмассивов сгруппированных точек.
        """
        groups = []
        visited = set()

        for i in range(len(points)):
            if i in visited:
                continue

            current_group = [points[i]]
            visited.add(i)

            for j in range(i + 1, len(points)):
                if j in visited:
                    continue

                distance = np.linalg.norm(np.array(points[i]) - np.array(points[j]))
                if distance < threshold:
                    current_group.append(points[j])
                    visited.add(j)

            groups.append(current_group)

        return groups

    def replaceSubImageToText(self, srcImgColor, srcImgGray, subImageGray, replacementWord, wordDict, font):

        srcImgGray = cv2.inRange(cv2.cvtColor(srcImgColor, cv2.COLOR_BGRA2BGR), (238, 242, 246), (238, 242, 246))


        res = cv2.matchTemplate(srcImgGray, subImageGray, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where(res >= threshold)
        h, w = subImageGray.shape
        candidades = []
        nameCandidates = {"left": [], "top": []}
        for pt in zip(*loc[::-1]):
            if self._showCVWindows:
                cv2.rectangle(srcImgColor, pt, (pt[0] + w, pt[1] + h), (125, 255, 125), 2)
            nameCandidates["left"].append(pt[0])
            nameCandidates["top"].append(pt[1])
            candidades.append([pt[0], pt[1]])
            logging.info("founded nickname candidates on text image")

        listOfNameCandidates = self.group_near_points(candidades, 20)
        for nameCandidates in listOfNameCandidates:

            nameCandidates = {"left": [elem[0] for elem in nameCandidates], "top": [elem[1] for elem in nameCandidates]}
            if len(nameCandidates["top"]) > 1:
                foundedName = {"left": int(np.median(np.asarray(nameCandidates["left"]))), "height": h, "width": w,
                               "top": int(np.median(np.asarray(nameCandidates["top"])))}

                for i in range(len(wordDict["level"])):
                    # Поиск места невероно определённого имени

                    if wordDict["level"][i] == 5 \
                            and abs((wordDict["top"][i] + wordDict["height"][i]) - (foundedName["top"] + foundedName["height"])) < 0.3 * foundedName["height"] \
                            and abs(wordDict["left"][i] - foundedName["left"]) < font.getbbox(" ")[2]:
                        endMark = ""
                        if wordDict["text"][i][-1] in [".", ",", "!", "?"]:
                            endMark = wordDict["text"][i][-1]
                        wordDict["text"][i] = replacementWord + endMark
                        logging.info("replaced nickname to voice version")
                        if self._showCVWindows:
                            cv2.rectangle(srcImgGray, (foundedName["left"], foundedName["top"]),
                                  (foundedName["left"] + foundedName["width"], foundedName["top"] + foundedName["height"]), (255, 255, 255),
                                  1)
                            cv2.rectangle(srcImgColor, (foundedName["left"], foundedName["top"]),
                                  (foundedName["left"] + foundedName["width"], foundedName["top"] + foundedName["height"]), (255, 0, 255), 2)
        return [wordDict, srcImgColor, srcImgGray]

    def replace_zero_alpha_with_noise(self, imageRGBA):
        if imageRGBA.shape[2] == 4:
            alpha_channel = imageRGBA[:, :, 3]
            mask = alpha_channel == 0
            height, width = imageRGBA.shape[:2]
            noise = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
            image = cv2.cvtColor(imageRGBA, cv2.COLOR_RGBA2RGB)
            image[mask] = noise[mask]
            return image
        return imageRGBA

    def setMuteStateForCertainCharacters(self, state:bool):
        nameAndGenderChecker.muteСertainCharacters = state

if __name__ == '__main__':
    genshinVoicer = GenshinVoicer()
    genshinVoicer.run()