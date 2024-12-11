from moviepy.editor import *
from random import choice, random, randint
from easing_functions import *
from PIL import ImageEnhance
from PIL import Image
import numpy as np

def generateImageClip(visual_path, visual, special=False):
    theme, start, end = visual["theme"], visual["start_time"], visual["end_time"]
    duration = end - start
    if special:
        duration += 1
        end += 1
    im = Image.open(visual_path)
    if theme=="moody":
        im = ImageEnhance.Brightness(im).enhance(0.6)
        im = ImageEnhance.Color(im).enhance(0.1)
    elif theme=="neutral":
        im = ImageEnhance.Brightness(im).enhance(0.4)
        im = ImageEnhance.Color(im).enhance(0.1)
    else:
        im = ImageEnhance.Brightness(im).enhance(0.5)
        im = ImageEnhance.Color(im).enhance(0.1)

    rand = randint(6,12)
    easer = QuadEaseInOut(start=0, end = 0.25, duration = rand)
    def resize_func(t):
        a = easer(t)
        return 1+abs(a/2.5)
    def set_position_func(t):
        scale = resize_func(t)
        new_x, new_y = int(1080*scale), int(1920*scale)
        return (540-new_x//2, 960-new_y//2)

    clip = (ImageClip(np.asarray(im))
            .resize((1080, 1920))
            .set_start(start)
            .set_end(end)
            .set_duration(duration+1)
            )
    clip = clip.resize(resize_func)
    clip = clip.set_position(("center", "center"))
    return clip
    #implement panning, zooming, etc

def composeFinalVideo(baseVideoPath, subtitles, audiopath, volume=1):
    basevideo = VideoFileClip(baseVideoPath)
    baseaudio = basevideo.audio.subclip(0, basevideo.duration-1)
    basevideo = basevideo.without_audio()
    subtitles = [clip.set_start(clip.start+basevideo.duration).set_end(clip.end+basevideo.duration) for clip in subtitles]

    screen = ColorClip(size=(1080, 1920), color=(20, 20, 20)).set_duration(subtitles[-1].end + 2).set_position(("center", "center")).crossfadein(1)
    final = concatenate_videoclips([basevideo, screen], method="compose", padding=-1, bg_color=None)

    im = Image.open(r"data/background.png")
    im = im.convert("RGBA")
    logo_clip = ImageClip(np.asarray(im), duration=screen.duration-2).set_position(("center", "center")).set_opacity(0.8).set_start(0)
    print(logo_clip.duration, "logo_clip")
    ending_audio = AudioFileClip(audiopath)
    ending_audio = ending_audio.set_start(basevideo.duration).volumex(volume)

    possible = [i for i in os.listdir("data/background_music")]
    chosen = choice(possible)
    background_music = AudioFileClip("data/background_music/%s" % chosen)



    to_composite = [final]
    to_composite.extend(subtitles)
    to_composite.append(logo_clip)
    final = CompositeVideoClip(to_composite, size=(1080, 1920), use_bgclip=True)
    print(final.duration)
    random_start = random()*(background_music.duration-final.duration)
    background_music = background_music.subclip(random_start, random_start+final.duration).set_start(0).volumex(0.3)

    composite_audio = CompositeAudioClip([baseaudio, background_music, ending_audio])

    final = final.set_audio(composite_audio)
    if final.duration >= 60:
        final = final.subclip(0, 59.9)
    return final

def composeVideo(clips, subtitles, audiopath):
    clips = [clip if i==0 else clip.crossfadein(1) for i, clip in enumerate(clips)]

    final = concatenate_videoclips(clips, method="compose", padding=-1)
    vignette = ImageClip("effects/vignette.png").set_duration(final.duration).set_pos(("center", "center"))
    audio = AudioFileClip(audiopath)
    to_composite = [final]
    to_composite.extend(subtitles)
    to_composite.append(vignette)
    final = CompositeVideoClip(to_composite, size=(1080, 1920), use_bgclip=True)
    final = final.set_audio(audio)
    return final

def writeVideo(video_path, videoclip, fps=60):
    videoclip.write_videofile(video_path, codec='libx264', fps=fps, threads=8192)