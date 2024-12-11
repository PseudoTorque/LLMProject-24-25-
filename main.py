import logging
import os
from openai import OpenAI
from pypdf import PdfReader
from gensim.models import Word2Vec
import gensim
from nltk.tokenize import sent_tokenize, word_tokenize
import warnings
from nltk import download
import pickle as pkl
from pydantic import BaseModel
from icrawler.builtin import GoogleImageCrawler
import random
import datetime
from genericpath import isfile
import random
from textwrap import wrap
import requests
import utils
import json
import os.path
import logging
import multimedia
import pickle
from random import sample
from bs4 import BeautifulSoup
import subtitles 

client = OpenAI(
    api_key=
)

class Scene(BaseModel):
    start_time: float
    end_time: float
    visuals: list[str]
    narration: str
class Video(BaseModel):
    scenes: list[Scene]

warnings.filterwarnings(action='ignore')

def get_word(data, frmt="train"):
    d = []
    test = []
    # iterate through each sentence in the file
    for i in sent_tokenize("".join(data)):
        temp = []
    
        # tokenize the sentence into words
        for j in word_tokenize(i):
            temp.append(j.lower())
    
        d.append(temp)
    if frmt=="t":
        return d
    else:
        for i in d:
            for j in i:
                test.append(j)
        return test

def get_model(data):
    
    
    data = get_word(data)
    # Create CBOW model
    model1 = gensim.models.Word2Vec(data, min_count=1,
                                    vector_size=500, window=100)
    return model1

def extract_text_from_file(filepath):
    if ".pdf" in filepath:
        reader = PdfReader(filepath)

        total = []
        for page in reader.pages:
            text = page.extract_text()
            total.extend(text.split("\n"))
        return "<SENTENCE END>".join(total)

def extract_text_from_directory(dirpath):
    total = []
    for i in os.listdir(dirpath):
        filepath = "%s/%s"%(dirpath, i)
        content = extract_text_from_file(filepath)
        total.append(content)
    return " ".join([i.replace("<SENTENCE END>", "") for i in total])

def split_into_chunks(text, max_chunk_size=500):

    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def save_load_corpus(storepath, mode="r", data=None):
    if mode=="r":
        data = pkl.load(open(storepath, "rb"))
        return data
    if mode=="w":
        store = []
        with open(storepath, "wb+") as file:
            store.extend(data)
            pkl.dump(store, file)
        return store
#print(extract_text_from_file(r"test/fess1ps.pdf"))






def getScript(context, state, data=[]):
    if os.path.isfile("history/scripts/%s.txt" % context):
        logging.warning("(Script Error) Script already generated for %s! fetching..." % context)
        with open("history/scripts/%s.txt" % context, "r") as file:
            return file.read()
    else:
        script = utils.getHistorySpeech(context, state, data)
        script = parseScript(script)
        with open("history/scripts/%s.txt" % context, "w+") as file:
            file.write(script)
        return script
def parseScript(script):
    result=""
    for i in script.split("."):
        if i.count("#") <= 1:
            result = ".".join([result, i])
    script = result
    banned_words = ["-", "_", "=", ":", ";"]
    possible_fillers = ["Hey history buffs! ", "Hey, history buffs!", "Ladies and gentlemen,", "Thank you."]
    possible_fillers.extend([i.lower() for i in possible_fillers])
    for i in possible_fillers:
        script = script.replace(i, "")
    for i in banned_words:
        script = script.replace(i, " ")
    if script[-1] != ".":
        script += "."
    script = " ".join([i for i in script.split(" ") if i!=""])
    return script.lstrip(".")
def getVideoTitleAndDescription(context):
    maxRetries = 3
    while maxRetries > 0:
        response = utils.getTitleAndDescription(getScript(context))
        try:
            output = {}
            result = [i for i in response.split("\n") if i != ""]
            for i in result:
                if "title" in i.lower():
                    output["title"] = "%s %s" % (i.split("Title:")[1].lstrip().lstrip('"').rstrip('"'), "#history")
                elif "description" in i.lower():
                    output["description"] = i.split("Description:")[1].lstrip().lstrip('"').rstrip('"')
            if output["description"] == "" or output["title"] == "":
                pass
            else:
                return output
        except Exception as e:
            logging.info("(Pipeline Error) Response from API for video title and description were not as expected, Error: %s." % e)
            maxRetries -= 1
    return None
def getKeywordsFromSummary( summary):
    def checkNumberedListElement(text):
        try:
            test = int(text.split(".")[0])
            return True
        except:
            return False
    response, result = utils.getKeywordsFromSummary(summary).split("\n"), []
    for i in response:
        if "." in i and checkNumberedListElement(i):
            result.append(i.split(".")[1].lstrip())
    return result
def directscript(context, state, data):
    speech = getScript(context, state, data)
    
    if os.path.isfile("history/audio/%s.mp3" % context):
        logging.warning("(TTS Error) Speech already generated for %s! fetching..." % context)
    else:
        utils.generateVoiceOver(speech, "history/audio/%s.mp3" % context, "en_male_wizard")

    def getFullForms(speech):
        result = []
        def isNumber(word):
            for i in word:
                try:
                    test = int(i)
                    return True
                except:
                    pass
            return False
        def isAllCaps(word):
            for i in word:
                if i.upper() != i:
                    return False
            if not isNumber(word):
                return True
        for i in speech.split(" "):
            if isAllCaps(i):
                result.append(i)
        return result
    # check transcription output format and modify 
    if os.path.isfile("history/transcriptions/%s.pkl" % context):
            logging.warning("(Transcription Error) Transcription already generated for %s! fetching..." % context)
            with open("history/transcriptions/%s.pkl" % context, "rb") as file:
                transcription = pkl.load(file)
    else:
        maxRetries = 3
        transcription = utils.getTranscript("history/audio/%s.mp3"%context)
        while maxRetries > 0:
            if abs(len(speech.split(" ")) - len(transcription.words)) > 5:
                logging.warning("(Transcription Error) Transcription for %s is invalid! Retrying... (Iteration %d)" % (context, (3-maxRetries)+1))
                transcription = utils.getTranscript("history/audio/%s.mp3"%context)
                maxRetries -= 1
            else:
                break
        else:
            return False
        with open("history/transcriptions/%s.pkl" % context, "wb+") as file:
            pkl.dump(transcription, file)



    

    def formatsubs(text):
        currentSection = 0
        output = []
        def makeSubRipStr(rawText, initialTimeStamp, finalTimeStamp, currentSection, width=17): 

            rawText = rawText.strip()
            rawText = "\n".join(wrap(rawText, width))

            def convertTimeStampToTc(seconds):
                millisecond = int((seconds-int(seconds))*1000)
                second = int(seconds)%60
                minutes=int(seconds)//60
                hours=minutes//24
                return f"{hours:02d}:{minutes:02d}:{second:02d},{millisecond:03d}"
            
            formattedText= f'{currentSection}\n{convertTimeStampToTc(initialTimeStamp)} --> {convertTimeStampToTc(finalTimeStamp)}\n{rawText}\n\n'
            return formattedText
        for sourceTuple in text:
                currentSection += 1
                text, initialTimeStamp, finalTimeStamp = sourceTuple
                result = makeSubRipStr(text, initialTimeStamp, finalTimeStamp, currentSection)
                output.append(result)
        return "".join(output)    
    def extractsubtitles(chunksize, transcription=transcription):
        words = transcription.words
        result,output = [],[]
        temp = [i for i in speech.split(" ") if i != ""]
        for i, j in enumerate(words):
            if i < len(temp):
                print(j)
                output.append((temp[i], round(j.start, 3), round(j.end, 3)))
        for i, j in enumerate(output):
            if i!=0:
                if j[1] == j[2]:
                    result.append((j[0], output[i-1][2], j[2]))
                else:
                    result.append((j[0], j[1], j[2]))
            else:
                if j[1] == j[2]:
                    result.append((j[0], 0, j[2]))
                else:
                    result.append((j[0], j[1], j[2]))
        print(result)
        return result
        for i in words:  
            word = i['word']
            for j, k in enumerate(temp):
                if word.lower() in k.lower():
                    result.append({'word':k.lstrip("."), 'start':round(i['start'], 3), 'end':round(i['end'], 3)})
                    if j != len(temp)-1:
                        temp = temp[j+1:]
                    break
        temp = result
        while len(temp)>0:
            if chunksize < len(temp):
                for i in range(chunksize):
                    screen = temp[:i+1]
                    text = " ".join([i["word"] for i in screen])
                    start = screen[-1]["start"]
                    end = screen[-1]["end"]
                    output.append((text, start, end))
                temp = temp[chunksize:]
            else:
                for i in range(len(temp)):
                    screen = temp
                    text = " ".join([i["word"] for i in screen])
                    start = screen[-1]["start"]
                    end = screen[-1]["end"]
                    output.append((text, start, end))
                temp = []
        return output
        
    def getsubtitles(context=context):
        if os.path.isfile("history/subtitles/%s.srt" % context):
            logging.warning("(Subtitle Error) Subtitle file already exists! fetching...")
            with open("history/subtitles/%s.srt" % context, "r") as file:
                subtitles = file.read()
        else:
            temp = 3
            while temp < 5:
                try:
                    response = formatsubs(extractsubtitles(chunksize=temp))
                    break
                except:
                    temp += 1
            else:
                response = formatsubs(extractsubtitles(chunksize=5))
            with open("history/subtitles/%s.srt" % context, "w+") as file:
                file.write(response)
            subtitles = response
        return subtitles

    getsubtitles()   
    
    imaged = False
    for name in os.listdir("history/images"):
        if context in name:
            imaged = True
            logging.warning("(Image Generation Error) Images already generated for %s! fetching..." % context)
            break
    keywords = [i for i in os.listdir("history/images") if context in i and "edited" in i]
    if not imaged: 
        keywords = getKeywordsFromSummary(speech)
        for i in keywords:
            utils.generateimages(context, "history/images", i)

    def getmusicsentiment(text=speech, context=context):
        if os.path.isfile("history/sentiment/%s.txt" % context):
            logging.warning("(Sentiment Error) Sentiment file already exists! fetching...")
            with open("history/sentiment/%s.txt" % context, "r") as file:
                sentiment = file.read()
        else:
            response = utils.getsentiment(text)
            with open("history/sentiment/%s.txt" % context, "w+") as file:
                file.write(response.rstrip(".").lstrip(",").split("\n")[0].lower())
            sentiment = response
        return sentiment
    multimedia.generatevideo(context, keywords, "history/images", "history/videos", "history/audio", "history/sentiment", getmusicsentiment(), "history/subtitles")
    temp = 3
    while temp < 5:
        try:
            response = formatsubs(extractsubtitles(chunksize=temp))
            break
        except:
            temp += 1
    else:
        response = formatsubs(extractsubtitles(chunksize=5))
    subtitles.create_styled_subtitle_clip(extractsubtitles(chunksize=temp),"produced/%s final.mp4" % context)
    return True
    
test = save_load_corpus(r"data/corpus.pkl", "r")
model = get_model(test)

response = [
        {"role": "system", "content": "You are a history enthusiast and an educator and you will follow the instructions to respond to users query."}
    ]
while True:
    command = input("Enter your query or 'make summary' if you want the video summary.-> ")
    if "make summary" in command:
        break
    try:
        similarity = [(i, model.wv.similarity(command, i)) for i in get_word("".join(test))]
        not_present_in_corpus = False
        command = command + " Do not make up any information; the following is a similarity score between the query and corpus, use the data accordingly to formulate the query" + str(similarity)
        #directscript(context, not_present_in_corpus, similarity)
    except KeyError as e:
        not_present_in_corpus = True
    response = utils.chat(response, message=command)
    print(response[-1]["content"].replace("\n", " "))
        

if response != []:  
    query = utils.chat(response)[-1]["content"]
    context = "".join([i for i in query.replace(" ", "") if i.isalnum()])
    print(context)
    #directscript(context, False, [])




