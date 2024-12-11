
from moviepy import *
from moviepy.video.tools.drawing import color_gradient
import numpy as np
from PIL import Image
import inflect

p = inflect.engine()


def screen_subtitles(subtitles):
    def replace(string):
        banned_characters = [",", "/", "-", "\"", "'"]
        for i in banned_characters:
            string = string.replace(i, "")
        return string
    local = subtitles
    for j, i in enumerate(local):
        if j != len(local) -1 and j!= 0:
            if i[1] == i[2]:
                curr_word, prev_word, next_word = i[0], local[j-1][0], local[j+1][0]
                try:
                    test = int(prev_word.restrip().lstrip())
                    prev_word = len(p.number_to_words(test))
                except:
                    prev_word = len(prev_word)
                try:
                    test = int(next_word.restrip().lstrip())
                    next_word = len(p.number_to_words(test))
                except:
                    next_word = len(next_word)

                try:
                    test = int(curr_word.restrip().lstrip())
                    curr_word = len(p.number_to_words(test))
                except:
                    curr_word = len(curr_word)

                if curr_word - next_word < curr_word - prev_word:
                    total = curr_word + prev_word
                    timetotal = i[2]-local[j-1][1]
                    curr_share, prev_share = round(timetotal*(curr_word/total), 3), round(timetotal*(prev_word/total), 3)
                    local[j-1] = (local[j-1][0], local[j-1][1], local[j-1][1]+prev_share)
                    local[j] = (i[0], local[j-1][2], i[2])
                    
                else:
                    total = curr_word + next_word
                    timetotal = local[j+1][2] - i[1]
                    curr_share, next_share = round(timetotal*(curr_word/total), 3), round(timetotal*(prev_word/total), 3)
                    local[j] = (i[0], i[1], i[2]+curr_share)
                    local[j+1] = (local[j+1][0], i[2]+curr_share, local[j+1][2])
    for j, i in enumerate(local):
        if j != len(local) -1 and j!= 0:
            if i[1] != local[j-1][2]:
                local[j] = (i[0], local[j-1][2], i[2])
            if i[2] != local[j+1][1]:
                local[j] = (i[0], i[1], local[j+1][1])
        else:
            if j==0:
                if i[2] != local[j+1][1]:
                    local[j] = (i[0], i[1], local[j+1][1]) 
            else:
                if i[1] != local[j-1][2]:
                    local[j] = (i[0], local[j-1][2], i[2])
    return [(i, round(j, 3), round(k, 3)) for i, j, k in local] 


def interpolate_color(color1, color2, t):
    """ Linearly interpolate between two RGB colors. """
    return tuple(np.round((1 - t) * np.array(color1) + t * np.array(color2)).astype(int))

def swell(t, swell_duration=0.1, max_size=1):
    return max_size*(t/swell_duration + 0.02) if t <= swell_duration else max_size
def hookswell(t):
    return swell(t, max_size=3)

def create_styled_subtitle_clip(words_with_times, videopath, chunksize=3, font='Segoe-UI-Bold', fontsize=70, box_color=[30, 30, 30],
                                gradient_colors=((217, 217, 217), (255, 255, 255)),
                                active_gradient_colors=((143, 62, 1), (242, 108, 7)),
                                hook_colors=((88, 0, 156), (222, 0, 41)),
                                box_padding=(30, 10), position=("center", 0.75)):
    """
    Creates a styled subtitle clip where the text has a vertical gradient color and is bound by a black box with rounded corners.

    Parameters:
    - words_with_times: List of tuples, where each tuple is (word, start_time, end_time).
    - font: The font of the subtitle text.
    - fontsize: The size of the font.
    - box_color: The color of the background box.
    - gradient_color_start: The starting color of the vertical gradient on the text.
    - gradient_color_end: The ending color of the vertical gradient on the text.
    - box_padding: Padding around the text inside the box, given as (x_padding, y_padding).
    - box_opacity: Opacity of the background box (0.0 is fully transparent, 1.0 is fully opaque).
    - position: The position of the subtitle text on the screen.

    Returns:
    - CompositeVideoClip with the styled subtitles added.
    """
    first = words_with_times[0]
    words_with_times = words_with_times[1:]

    # Create a list to hold all the text clips
    text_clips = []
    box_clips = []
    counter = 0

    hook = (TextClip(first[0], font=font, fontsize=fontsize, color="white")
                        .with_position(position, relative=True)
                        .with_start(first[1])
                        .with_end(first[2])
                        .with_duration(first[2]-first[1])).to_mask()
    txt_size = hook.size
    gradient = color_gradient(txt_size, p1=(txt_size[0]//2, 0), p2=(txt_size[0]//2, txt_size[1]), 
                                  col1=hook_colors[1], col2=hook_colors[0]).astype('uint8')
    
    gradient_clip = (ImageClip(np.asarray(Image.fromarray(gradient)))
                        .with_position(position, relative=True)
                        .with_start(first[1])
                        .with_end(first[2])
                        .with_duration(first[2]-first[1]))
    hook = gradient_clip.with_mask(hook)
    box_size = (txt_size[0] + 10*2, txt_size[1])
    color_clip = ColorClip(size=(box_size[0], box_size[1]), color=box_color)
    color_clip = color_clip.with_position((position[0], position[1]+(box_padding[1]/1920)), relative=True)
    color_clip = color_clip.with_duration(first[2]-first[1])
    color_clip = color_clip.with_start(first[1])
    color_clip = color_clip.with_end(first[2])


    text_clips.append(hook.resized(hookswell))
    box_clips.append(color_clip.resized(hookswell))
    
    

    for i in range(0, len(words_with_times), chunksize):
        # Get the chunk of words
        chunk = words_with_times[i:i + chunksize]
        words = " ".join([word for word, _, _ in chunk])
        start_time = chunk[0][1]
        end_time = chunk[-1][2]
    




        # Create the basic text clip (white color, as it will be masked)
        txt_clip = (TextClip(words, font=font, fontsize=fontsize,  color="white")
                    .with_position(position, relative=True)
                    .with_start(start_time)
                    .with_end(end_time)
                    .with_duration(end_time - start_time)).to_mask()

        # Generate a vertical gradient image to overlay on the text

        txt_size = txt_clip.size
        box_size = (txt_size[0] + box_padding[0]*2, txt_size[1] + box_padding[1]*2)
        color_clip = ColorClip(size=(box_size[0], box_size[1]), color=box_color)
        color_clip = color_clip.with_position((position[0], position[1]-(box_padding[1]/1920)*0.3), relative=True)
        color_clip = color_clip.with_duration(end_time-start_time)
        color_clip = color_clip.with_start(start_time)
        color_clip = color_clip.with_end(end_time)
        
        gradient = color_gradient(txt_size, p1=(txt_size[0]//2, 0), p2=(txt_size[0]//2, txt_size[1]), 
                                  col1=gradient_colors[1], col2=gradient_colors[0]).astype('uint8')
        concat = []
        temp, text = "", []
        for i in words.split(" "):
            temp = " ".join([temp, i])
            text.append(temp.lstrip())
        text = [TextClip(i, font=font, fontsize=fontsize, color="white").size for i in text]
        for j, i in enumerate(text):
            starttime, endtime = words_with_times[j+counter][1], words_with_times[j+counter][2]
            duration = round(endtime-starttime, 3)
            txt_clip = (TextClip(words, font=font, fontsize=fontsize, color="white")
                        .with_position(position, relative=True)
                        .with_start(starttime)
                        .with_end(endtime)
                        .with_duration(duration)).to_mask()
            
            gradient_active = color_gradient(i, p1=(i[0]//2, 0), p2=(i[0]//2, i[1]), 
                                            col1=active_gradient_colors[1], col2=active_gradient_colors[0]).astype('uint8')
            im = Image.fromarray(gradient)
            if j==0:
                if duration > 0.2:
                    gradient_clip = (ImageClip(np.asarray(im))
                        .with_position(position, relative=True)
                        .with_start(starttime)
                        .with_end(starttime+round(duration/2, 3))
                        .with_duration(round(duration/2, 3)))
                    masked_txt_clip = gradient_clip.with_mask(txt_clip)
                    concat.append(masked_txt_clip.resized(swell))

                    im.paste(Image.fromarray(gradient_active))
                    gradient_clip = (ImageClip(np.asarray(im))
                        .with_position(position, relative=True)
                        .with_start(starttime+round(duration/2, 3))
                        .with_end(endtime)
                        .with_duration(round(duration/2, 3)))
                    masked_txt_clip = gradient_clip.with_mask(txt_clip)
                    concat.append(masked_txt_clip)
                else:
                    im.paste(Image.fromarray(gradient_active))
                    gradient_clip = (ImageClip(np.asarray(im))
                                .with_position(position, relative=True)
                                .with_start(starttime)
                                .with_end(endtime)
                                .with_duration(duration))
                    masked_txt_clip = gradient_clip.with_mask(txt_clip)
                    concat.append(masked_txt_clip.resized(swell))
            else:
                im.paste(Image.fromarray(gradient_active))
                gradient_clip = (ImageClip(np.asarray(im))
                                .with_position(position, relative=True)
                                .with_start(starttime)
                                .with_end(endtime)
                                .with_duration(duration))
                masked_txt_clip = gradient_clip.with_mask(txt_clip)
                concat.append(masked_txt_clip)

        


        #textline = concatenate(concat, method="compose", bg_color=None).set_start(start_time).set_end(end_time).set_position(position, relative=True).resizedd(swell)
        
        counter += chunksize
        box_clips.append(color_clip.resized(swell))
        text_clips.extend(concat)
        # Apply the gradient to the text by masking
        
        
        # Create the black box with rounded corners and add padding
        


        # Append the styled TextClip to the list

    # Combine all the TextClips into a single CompositeVideoClip

    #return (box_clips, text_clips)

    main_video_clip = VideoFileClip(videopath)

# Step 2: Generate the subtitle clip
    words_with_times = screen_subtitles(words_with_times)

    clips = [main_video_clip]
    clips.extend(box_clips)
    clips.extend(text_clips)
    # Step 3: Overlay the subtitle clip on the main video
    final_clip = CompositeVideoClip(clips, size=(1080, 1920), use_bgclip=True)
    final_clip.audio = main_video_clip.audio
    # Step 4: Write the result to a file
    final_clip.write_videofile("final_video_with_subtitles.mp4", codec="libx264", fps=30, threads= 4096)