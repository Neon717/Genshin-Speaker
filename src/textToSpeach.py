import os
import torch
import sounddevice as sd
import logging
import time_stretch as ts
import numpy as np
import soundfile as sf

model = None
speechSpeed = 1
volume = 1

def isCudaAvailable():
    return torch.cuda.is_available()

def init(proc):
    global model
    print("start init silero")
    device = torch.device(proc)
    torch.set_num_threads(4)
    local_file = os.path.join(os.path.dirname(__file__), '../external/SileroModels/model.pt')
    if not os.path.isfile(local_file):
        torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt',
                                       local_file)

    model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    model.to(device)

    print("finish init silero")

def soundText(sample_text, speaker, non_play = False):
    sample_rate = 48000
    voice_path = None

    if ".pt" in speaker:
        tempPath = os.path.join(os.path.dirname(__file__), ".." + speaker)
        if os.path.isfile(tempPath):
            voice_path = tempPath
            speaker = 'random'
        else:
            print("неверный путь до голоса: " + tempPath)
            logging.info("неверный путь до голоса: " + tempPath)
            speaker = "baya"

    put_accent=True
    put_yo=True
    print("start generate TTS")
    logging.info("start generate TTS")
    cutTexts = split_long_string(sample_text)
    audio = np.array([])
    for text in cutTexts:
        audioPart = model.apply_tts(text=text,
                                    speaker=speaker,
                                    sample_rate=sample_rate,
                                    put_accent=put_accent,
                                    put_yo=put_yo,
                                    voice_path=voice_path)
        audio = np.hstack([audio, audioPart])
    print("finish generate TTS")
    logging.info("finish generate TTS")
    if not non_play:
        if speechSpeed != 1.0:
            audio = ts.stretch(np.asarray(audio), speechSpeed, nfft=1024)
        audio = np.asarray(audio) * volume * (1 + abs(1 - speechSpeed))
    return [audio, sample_rate]

def saveAudioFromText(sample_text, speaker, path):

    sample_rate = 48000
    voice_path = None
    if ".pt" in speaker:
        voice_path = speaker
        speaker = 'random'

    put_accent = True
    put_yo = True
    print("start generate TTS")

    cutTexts = split_long_string(sample_text)
    audio = None
    for text in cutTexts:
        audioPart = model.apply_tts(text=text,
                                    speaker=speaker,
                                    sample_rate=sample_rate,
                                    put_accent=put_accent,
                                    put_yo=put_yo,
                                    voice_path=voice_path)
        if audio is not None:
            audio = np.hstack([audio, (audioPart * 32767).numpy().astype('int16')])
        else:
            audio = (audioPart * 32767).numpy().astype('int16')
    print("finish generate TTS")
    audio_data = audio
    print("_1")

    if audio_data.nbytes * 256 < 2147483647: # У ogg ограничение на размер записи
        sf.write(path, audio_data, sample_rate, format='ogg', subtype='vorbis')
    else:
        sf.write(path, audio_data, sample_rate, format='mp3')
    print("_2")

def split_long_string(input_string):
    # Устанавливаем максимальную длину строки
    max_length = 800
    substrings = []
    # Если длина строки меньше или равна максимальной, возвращаем ее в виде одного элемента списка
    if len(input_string) <= max_length:
        return [input_string]
    start = 0
    while start < len(input_string):
        # Если оставшаяся часть строки меньше или равна 999 символам
        if len(input_string) - start <= max_length:
            substrings.append(input_string[start:])
            break
        # Находим индекс последнего знака в пределах 999 символов
        end = start + max_length
        last_punct_index = -1
        for i in range(end, start, -1):
            if input_string[i-1] in ",.!?;":
                last_punct_index = i
                break
        # Если знак не найден, то просто берем 999 символов
        if last_punct_index == -1:
            last_punct_index = end
        substrings.append(input_string[start:last_punct_index])
        start = last_punct_index
    return substrings

