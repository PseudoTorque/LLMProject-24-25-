from PIL import Image
import os
import logging
from moviepy import *
from random import choice, random, randint
from easing_functions import *
from moviepy.video.tools.subtitles import SubtitlesClip
from textwrap import wrap

def resizeandsave(name, size=(1080, 1920)):
    im = Image.open("%s" % name)
    if im.mode != "RGB":
        im = im.convert("RGB")
    width, height = im.size
    while width < size[0] or height < size[1]:
        if width < size[0]:
            scale = size[0]/width
        if height < size[1]:
            scale = size[1]/height
        im =im.resize((int(width*scale), int(height*scale)), Image.Resampling.LANCZOS)
        width, height = im.size
    bounds = (width/2-size[0]/2, height/2-size[1]/2, width/2+size[0]/2, height/2+size[1]/2)
    im = im.crop(bounds)
    tokens = name.split(" ")
    tokens.insert(len(tokens)-1, "edited")
    name = " ".join(tokens)
    if ".png" in name:
        name = "".join(name.split(".png")[0]) + ".jpg"
    im.save(name, "JPEG")

def screenimages(context, directory):
    for i in os.listdir(directory):
        if "edited" not in i and context in i:
            resizeandsave("%s/%s" % (directory, i))
def generatevideo(context, available, directoryimage, directoryvideo, directoryaudio, directorysentiment, sentiment, directorysubtitles):
    fps = 60
    def string(context=context, directory=directoryvideo, directorysentiment=directorysentiment, sentiment=sentiment):
                output = "produced/%s final.mp4" % context
                clips = []
                for i in os.listdir(directory):
                    if "edited" in i and context in i:
                        clips.append(VideoFileClip("%s/%s" % (directory, i)))
                
                
                duration = sum([i.duration for i in clips]) - (2*len(clips))
                
                if "upbeat" in sentiment.lower():
                    sentiment = "upbeat"
                elif "intriguing" in sentiment.lower():
                    sentiment = "intriguing"
                elif "somber" in sentiment.lower():
                    sentiment = "somber"
                
                possible = [i for i in os.listdir("%s/%s" % (directorysentiment, sentiment))]
                choose = choice(possible)

                
                background = AudioFileClip("%s/%s/%s" % (directorysentiment, sentiment, choose))
                total = background.duration
                start = random()*(total-duration)

                background = background.subclipped(start, start+duration)
                background = background.with_volume_scaled(0.2)

                audioclip = AudioFileClip("%s/%s.mp3" % (directoryaudio, context))
                audio = CompositeAudioClip([background, audioclip])

                
                final = [clip if i == 0 else clip.with_effects([vfx.CrossFadeIn(2)]) for i, clip in enumerate(clips)]
                final= concatenate_videoclips(final, padding=-2, method="compose")
                vignette = ImageClip("effects/vignette.png").with_duration(final.duration+2).with_position(("center", "center"))

                print(final, vignette)
                result = CompositeVideoClip([final, vignette], use_bgclip=True)
                result.audio = audio
                if result.duration >= 60:
                    result = result.subclipped(0, 59.85)
                result.write_videofile(output, codec='libx264', fps=fps, threads=4096)
    for i in os.listdir(directoryvideo):
        if "final" in i and context in i:
            logging.warning("(Video Generator Error) Prompt final video has already been generated! fetching...")
            break
    else:
        for i in os.listdir(directoryvideo):
            if "edited" in i and context in i:
                logging.warning("(Video Generator Error) Prompt videos have already been generated! fetching...")
                break
        else:
            for i in os.listdir(directoryimage):
                if "edited" in i and context in i:
                    logging.warning("(Image Screener Error) Images already screened! fetching...")
                    break
            else:
                screenimages(context, directoryimage)



            duration = AudioFileClip("%s/%s.mp3" % (directoryaudio, context)).duration
            left = duration
            size = duration//len(available)
            current = 0
            promptmapping = []
            for i in available:
                if size < left:
                    promptmapping.append({i:(current, current+size)})
                    current += size
                    left -= size
                else:
                    promptmapping.append({i:(current, current+left)})
            newmapping = {}
            for j, i in enumerate(promptmapping):
                newmapping["%s edited %d.jpg" % (context, j)] = list(i.values())[0]
            for j, i in enumerate(newmapping):
                if j==len(newmapping)-1:
                    if length < duration:
                        length = duration
                else:
                    length = newmapping[i][1] - newmapping[i][0] + 2
                rand = randint(8,12)
                def resize_func(t):
                    a = QuadEaseInOut(start=0, end = 0.25, duration = rand)
                    return 1+abs(a(t)/2.5)
                imgclip = ImageClip("%s/%s" % (directoryimage, i))
                imgclip = imgclip.with_position("center", "center")
                imgclip = imgclip.resized(resize_func)
                imgclip = imgclip.with_duration(length)
                CompositeVideoClip([imgclip],size=(1080, 1920)).write_videofile("%s/%s.mp4" % (directoryvideo, i.split(".")[0]),
                                        codec='libx264', audio_codec = "pcm_s32le",
                                        fps=fps, threads=4096)
                duration -=(length-2)
        string()
