#!/usr/bin/env python
# -*- coding: utf-8 -*-
# task coded by P.B. and J.S.

import numpy as np
from psychopy import visual, core, event, gui, data
import random
import pandas as pd
import os
from PIL import Image
from pathlib import Path
from psychopy.hardware import keyboard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

exp_clock = core.Clock()
log_rows = []

info = {'participant': '', 'session': 'heartBEAT practice'}
dlg = gui.DlgFromDict(dictionary=info, title='heartBEAT Practice')
if not dlg.OK:
    core.quit()

LOGFILE = os.path.join(DATA_DIR, f"sub{info['participant']}_heartBeat_practice_log.csv")
first_write = True

#==============  GLOBAL PARAMETERS ==============#
SCREEN_RES       = (1280, 800)  # window res
FULLSCR          = False         # run fullscreen
DEMO_MODE        = True         # True = use mouse instead of joystick for practice
TEXT_SIZE        = 0.05        # height for instruction text
VIEW_DIST_CM     = 57.0         # approx. viewing distance
SCREEN_W_CM      = 30.0         #physical screen width in cm
ALLOW_ESCAPE_QUIT = True        # ESC quits immediately
background_color = (-0.5, -0.5, -0.5)
text_color = "white"

#============== BASIC HELPER FUNCTIONS ===============#
def deg_to_height_units(deg, dist_cm=VIEW_DIST_CM, screen_px=SCREEN_RES, screen_w_cm=SCREEN_W_CM):
    """Convert degrees of visual angle to PsychoPy 'height' coordinates."""
    pix_per_cm = screen_px[0] / screen_w_cm  # approximate
    pix_per_deg = (np.tan(np.radians(1)) * dist_cm) * pix_per_cm
    height_units_per_deg = pix_per_deg / screen_px[1]
    return deg * height_units_per_deg

def open_window():
    win = visual.Window(size=SCREEN_RES, fullscr=FULLSCR, screen=0, winType='pyglet', allowGUI=True, allowStencil=False,
        monitor='testMonitor', color=[-0.7, -0.7, -0.7], colorSpace='rgb', blendMode='avg', useFBO=True, units='height')
    # In demo mode, use mouse for control
    win.mouseVisible = DEMO_MODE
    if DEMO_MODE:
        win.mouse = event.Mouse(win=win)
    return win

# =========================
# parallel port 
# =========================
use_parallel_port = False   # set True in scanner/lab computer
parallel_address = "0x2FE8"

class DummyPort:
    """No-op port for local testing."""
    def setData(self, value: int) -> None:
        print(f"[DummyPort] setData({value})")

def init_port(use_parallel_port: bool, address: str):
    if not use_parallel_port:
        return DummyPort()
    try:
        from psychopy import parallel
        port = parallel.ParallelPort(address=address)
        port.setData(0)
        print(f"Connected to parallel port at {address}")
        return port
    except Exception as exc:
        print(f"Could not initialize parallel port ({exc}). Falling back to DummyPort.")
        return DummyPort()

#===================================== SAVING DATA=====================================#
def log_event(*, trial, segment, onset, offset, planned_dur, image_path=None, question_text=None, 
    response=None, rt=None):
    global first_write
    row = {
        "trial": trial,
        "segment": segment,
        "onset_s": onset,
        "offset_s": offset,
        "planned_dur_s": planned_dur,
        "actual_dur_s": offset - onset,
        "image_path": image_path or "",
        "question_text": question_text or "",
        "response": response or "",
        "rt": rt or ""
    }
    df = pd.DataFrame([row])
    df.to_csv(LOGFILE, mode="a", header=first_write, index=False)
    first_write = False

#======== define & load variables ===============#
win = open_window()
win.mouseVisible = False 

# Timing
imgISI_duration = 5.0
fixation_duration = 1.0
image_duration = 0.5
gap_duration = 0.20
trigger_pulse_s = 0.005

# Files
script_dir = Path("/Volumes/labshare/Joanne/heartBEAT/dataframes")
data_dir = Path("/Volumes/labshare/Joanne/heartBEAT/data")
practice_file = script_dir / "practice.csv"

#visual vars
img_stim = visual.ImageStim(win, image=None, size=(0.76, 0.74),pos=(0, 0), ori=0)  
fix_stim = visual.TextStim(win, text="+", height=0.06)
iti_cross = visual.TextStim(win, "+", height=0.06, pos=(0, 0))
fixation = visual.TextStim(win, "o", height=0.065,  pos=(0, 0))
blank = visual.TextStim(win, "", height=0.05, pos=(0, 0))

# questions vars
q2 = visual.TextStim(win, "How confident are you in your image choice?", height=0.06, pos=(0, 0.17), wrapWidth=1.4)
q1 = visual.TextStim(win, "Which image produced a greater change in your heart response?", height=0.06, pos=(0, 0.17))
choice1 = visual.TextStim(win=win, text='1',pos=(-0.35, -0.1), height=0.07, color='white');
choice2 = visual.TextStim(win=win, text='2', pos=(0.35, -0.1), height=0.07, color='white');
polygon1 = visual.Rect(win=win, width=(0.22, 0.27)[0], height=(0.22, 0.27)[1], pos=(-0.32, -0.1), lineWidth=6.0, lineColor='white', fillColor=None)
polygon2 = visual.Rect(win=win,width=(0.22, 0.27)[0], height=(0.22, 0.27)[1], pos=(0.32, -0.1),lineWidth=6.0, lineColor='white', fillColor=None)
key_resp = keyboard.Keyboard()

horLine = visual.Line(win=win, start=(-0.39, -0.05),end=(0.39, -0.05),
    ori=0, pos=(0, -0.165), lineWidth=9,  colorSpace='rgb',  lineColor='white', fillColor='white',interpolate=True)
tick_len = 0.08
tick_y = -0.06
tick1 = visual.Line(win=win, start=(-0.39, tick_y - tick_len/2), end=(-0.39, tick_y + tick_len/2), lineWidth=5, lineColor='white')
tick2 = visual.Line(win=win, start=(-0.13, tick_y - tick_len/2), end=(-0.13, tick_y + tick_len/2), lineWidth=5, lineColor='white')
tick3 = visual.Line(win=win, start=( 0.13, tick_y - tick_len/2), end=( 0.13, tick_y + tick_len/2), lineWidth=5, lineColor='white')
tick4 = visual.Line(win=win, start=( 0.39, tick_y - tick_len/2), end=( 0.39, tick_y + tick_len/2), lineWidth=5, lineColor='white')
QuestionScale = visual.RatingScale(win=win, scale=None, showValue=False, showAccept=False, textColor="darkGrey", skipKeys=None, stretch=2.0, tickHeight=-1.0)
num1 = visual.TextStim(win=win, text='1',pos=(-0.39, -0.13), height=0.06, wrapWidth=1.8, color='white');
num2 = visual.TextStim(win=win, text='2',pos=(-0.13, -0.13), height=0.06, wrapWidth=1.8, color='white');
num3 = visual.TextStim(win=win, text='3',pos=(0.13, -0.13), height=0.06, wrapWidth=1.8, color='white');
num4 = visual.TextStim(win=win, text='4',pos=(0.39, -0.13), height=0.06, wrapWidth=1.8, color='white');
qText = visual.TextStim(win=win, text='',pos=(0, 0.2), height=0.058, wrapWidth=1.2, color='white');
LeftAnchor = visual.TextStim(win=win, text='Not at all confident',pos=(-0.41, -0.24), height=0.045, wrapWidth=0.3, color='white');
RightAnchor = visual.TextStim(win=win, text='Very confident',pos=(0.41, -0.24), height=0.045, wrapWidth=0.3, color='white');

# text for the instructions screens
instr1="In this part of the study, you will be viewing images and judging your physiological responses to them.\n\nPress SPACE to continue."
instr2="Before we start, we will collect a 60-second recording of your heart activity while you are at rest.\n\nPlease try your best to keep your left arm still and relaxed."
instr3="In this task, you will see two images presented in sequence.\n\n After each sequence, you will be prompted to choose which image provoked a bigger change in your heart response.\n\nPress 1 if the first image provoked a bigger change.\n Press 2 if the second image provoked a bigger change.\n\nThen, you will be prompted to report how confident you are in your choice of image, from 1 (not at all confident) to 4 (very confident).\n\nPress SPACE to continue."
instr4="We will first do a few practice trials.\n\nPress SPACE to begin!"

#======================================  MORE FUNCTIONS =============================================#
#==============  Instr screens ==============#
start_pos=(0, 0.0)
kb = keyboard.Keyboard()
def show_instr_screen(win, message, keyPress):
    instr = visual.TextStim(win=win, text=message, color='white', height=0.05, wrapWidth=1.4, pos=(0, 0.0))
    kb.clearEvents()
    while True:
        instr.draw()
        win.flip()
        keys = kb.getKeys(keyList=[keyPress, "escape"], waitRelease=False)
        if keys:
            if keys[0].name == "escape":
                win.close()
                core.quit()
            elif keys[0].name == keyPress:
                break

# ============================ show images =================================#
def show_img(draw_stim, duration, code, *, trial, segment, image_path=None):
    onset = exp_clock.getTime()
    clock = core.Clock()
    port.setData(0)
    while clock.getTime() < duration:
        if "escape" in event.getKeys():
            win.close()
            core.quit()
        draw_stim.draw()
        win.flip()
    offset = exp_clock.getTime()
    log_event(trial=trial, segment=segment, onset=onset, offset=offset,
              planned_dur=duration, image_path=image_path)

# ================================ fixations ======================================#
def show_iti(duration, *, trial, segment="iti"):
    onset = exp_clock.getTime()
    clock = core.Clock()
    while clock.getTime() < duration:
        if "escape" in event.getKeys():
            win.close()
            port.setData(0)
            core.quit()
        iti_cross.draw()
        win.flip()
    offset = exp_clock.getTime()
    log_event(trial=trial, segment=segment, onset=onset, offset=offset,
              planned_dur=duration)

def show_Fix(duration, *, trial, segment="o_fix"):
    onset = exp_clock.getTime()
    clock = core.Clock()
    while clock.getTime() < duration:
        if "escape" in event.getKeys():
            win.close()
            port.setData(0)
            core.quit()
        fixation.draw()
        win.flip()
    offset = exp_clock.getTime()
    log_event(trial=trial, segment=segment, onset=onset, offset=offset,
              planned_dur=duration)

#====================================== self report Qs =========================================#
def question1(*, trial, segment, feedback_dur=0.40):
    onset = exp_clock.getTime()
    clock = core.Clock()
    nums = [choice1, choice2]
    for num in nums:
        num.setColor("white")
    response = None
    rt = None
    feedback_onset = None
    event.clearEvents(eventType='keyboard')
    while True:
        keys = event.getKeys(keyList=["1", "2", "escape"], timeStamped=clock)
        for key, key_rt in keys:
            if key == "escape":
                win.close()
                port.setData(0)
                core.quit()
            if response is None and key in ["1", "2"]:
                response = key
                rt = key_rt
                for num in nums:
                    num.setColor("white")
                nums[int(response) - 1].setColor("blue")
                feedback_onset = clock.getTime()
        choice1.draw()
        choice2.draw()
        polygon1.draw()
        polygon2.draw()
        q1.draw()
        win.flip()
        if response is not None and (clock.getTime() - feedback_onset) >= feedback_dur:
            break
    offset = exp_clock.getTime()
    port.setData(0)
    log_event(trial=trial, segment=segment, onset=onset, offset=offset, planned_dur=feedback_dur if response is not None else "", question_text="ImageChoice", response=response, rt=rt)

def question2(*, trial, segment, feedback_dur=0.40):
    onset = exp_clock.getTime()
    clock = core.Clock()
    ticks = [tick1, tick2, tick3, tick4]
    nums = [num1, num2, num3, num4]
    for num in nums:
        num.setColor("white")
    response = None
    rt = None
    feedback_onset = None
    event.clearEvents(eventType='keyboard')
    while True:
        keys = event.getKeys(keyList=["1", "2", "3", "4", "escape"], timeStamped=clock)
        for key, key_rt in keys:
            if key == "escape":
                win.close()
                port.setData(0)
                core.quit()
            if response is None and key in ["1", "2", "3", "4"]:
                response = key
                rt = key_rt
                for num in nums:
                    num.setColor("white")
                nums[int(response) - 1].setColor("blue")
                feedback_onset = clock.getTime()
        horLine.draw()
        for tick in ticks:
            tick.draw()
        for num in nums:
            num.draw()
        LeftAnchor.draw()
        RightAnchor.draw()
        q2.draw()
        win.flip()
        if response is not None and (clock.getTime() - feedback_onset) >= feedback_dur:
            break
    offset = exp_clock.getTime()
    port.setData(0)
    log_event(trial=trial, segment=segment, onset=onset, offset=offset, planned_dur=feedback_dur if response is not None else "", question_text="ImageConfidence", response=response, rt=rt)

# ======================= trials and blocks =================== #
image_base_dir = Path('/Volumes/labshare/Joanne/heartBEAT/dataframes')
image_duration = 0.500
def run_PRACTICEtrials(row, *, trial_label, iti_dur):
    # random ITI
    show_iti(iti_dur, trial=trial_label, segment="iti")
    # fixation
    show_Fix(fixation_duration, trial=trial_label, segment="fixation")
    # image 1
    img1_path = str(image_base_dir / row["Img1Dir"])
    img_stim.image = img1_path
    show_img(img_stim, image_duration, code=0, trial=trial_label, segment="image1", image_path=img1_path)
    # 6 s ISI
    show_iti(imgISI_duration, trial=trial_label, segment="isi_after_image1")
    
    # image 2
    img2_path = str(image_base_dir / row["Img2Dir"])
    img_stim.image = img2_path
    show_img(img_stim, image_duration, code=0, trial=trial_label, segment="image2", image_path=img2_path)
    # 6 s ISI
    show_iti(imgISI_duration, trial=trial_label, segment="isi_after_image2")
    # questions
    question1(trial=trial_label, segment="question1")
    show_iti(0.20, trial=trial_label, segment="isi_betweenQs")
    question2(trial=trial_label, segment="question2")

# =========================
# =========================
# RUN Pracice!!!!!!!!!!!!!!!!
# =========================
#========== instruction screens =========#
show_instr_screen(win, instr1, 'space')
show_instr_screen(win, instr2, 's')
show_instr_screen(win, '+', 's')
show_instr_screen(win, instr3, 'space')
show_instr_screen(win, instr4, 'space')
show_iti(5, trial="begin run") # change to 20 for scan task

#========== run practice  =========#
kb = keyboard.Keyboard()
port = init_port(use_parallel_port, parallel_address)
port.setData(0)

# ========================= load csvs! ===================
practice_file = script_dir / "practice.csv"
practice_df = pd.read_csv(practice_file)
practice_df["Img1Dir"] = practice_df["Img1Dir"].astype(str)
practice_df["Img2Dir"] = practice_df["Img2Dir"].astype(str)

for trial_num, (_, row) in enumerate(practice_df.iterrows(), start=1):
    trial_label = f"practice_trial{trial_num}"
    run_PRACTICEtrials(row, trial_label=trial_label, iti_dur=5.0)
show_instr_screen(win, "Great job with the practice!\n\nThe experimenter will be with you shortly.","s")

win.close()
core.quit()
