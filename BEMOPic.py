# import tkinter module
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
import cv2
import time
from PIL import ImageTk, Image
import threading
CAMERA_INDEX=0

status = ""
killThread=False


def getCameras():
    #get list of cameras
    cameras = []
    for i in range(0, 10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cameras.append(i)
            cap.release()
    return cameras

def getCameraPreview(idx):
    cam = cv2.VideoCapture(idx)
    ret, frame = cam.read()
    if ret:
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    return None

def countdown(t, label, progress):
    while t:
        if killThread:
            return
        mins, secs = divmod(t, 60)
        #take first two digits of seconds
        secs = int(secs)
        mins = int(mins)

        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        label.config(text = "Time until next picture: " + timeformat)
        label.update()

        time.sleep(1)
        if killThread:
            return
        t -= 1
        progress["value"] += 1
        progress.update()

    label.config(text = "Sequence Complete")
    label.update()

def on_closing(dialog, tasks):
    global killThread
    killThread = True

    for task in tasks:
        task.cancel()
    dialog.destroy()
    master.destroy()
    
def takePics():
    #remove all files in directory
    outDir = outText.cget("text")
    import os
    for file in os.listdir(outDir):
        os.remove(outDir + "/" + file)


    #dialog 
    dialog = Toplevel()
    dialog.title("Taking Pictures")
    dialog.resizable(False, False)

    #image box
    #generate white image
    img = Image.new("RGB", (640,480), "white")
    img = ImageTk.PhotoImage(img)
    panel = Label(dialog, image = img)
    panel.image = img
    
    takePicture(0, dialog, panel)

    #grid
    panel.grid(row = 0, column = 0, columnspan = 2)

    labelUpdate = Label(dialog, text = "00:00")
    labelUpdate.grid(row = 1, column = 2)


    #open timing file
    timingConfigFile = configText.cget("text")
    try: 
        timingIntervals = []
        with open (timingConfigFile, "r") as f:
            #read lines
            sum = float(0)
            lines = f.readlines()
            #split into array
            for line in lines:
                timingIntervals.append(float(line))
                sum += float(line)
    
        
        #proress bar
        progress = Progressbar(dialog, orient = HORIZONTAL, length =300, mode = 'determinate')
        progress["maximum"] = (sum * 60)
       # print(sum)
        progress["value"] = 0

        progress.grid(row = 0, column = 1)

        #show dialog
        dialog.deiconify()
        dialog.update()
        
        prev = 0
        
        tasks = []


        for interval in timingIntervals:
            #wait interval minutes
            #print("Waiting for ", interval, " minutes")
            #set timer
            a = threading.Timer((prev + interval) * 60, lambda:[takePicture(interval, dialog, panel)])
            b = threading.Timer((prev) * 60, lambda:countdown(interval * 60, labelUpdate, progress))
            tasks.append(a)
            tasks.append(b)
            a.start()
            b.start()

            prev += interval

        #
    
        #cancel button
        b = Button(dialog, text = "Cancel", command=lambda: [on_closing(dialog,tasks)])
        b.grid(row =1, column = 1)

       # dialog.protocol("WM_DELETE_WINDOW", on_closing(dialog, tasks))


    except:
        pass

def takePicture(interval, dialog, panel):
    if killThread:
        return None
    
    print("Taking picture in ", interval, " minutes")
    #set camera to 1920 x 1080

    cam = cv2.VideoCapture(CAMERA_INDEX)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)


    ret, frame = cam.read()
    
    if ret:
        #save to file
        
        #get time right now
        timefmt = time.strftime("%Y%m%d-%H%M%S")

        outDir = outText.cget("text")
        if killThread:
            return None
        cv2.imwrite(outDir + "/" + str(timefmt) + ".jpg", frame)
        if killThread:
            return None
        if panel != None:
            ig = Image.open(outDir + "/" + str(timefmt) + ".jpg")
            ig = ig.resize((640,480))
            img = ImageTk.PhotoImage(ig)
            #crop image to fit (640,480)
            #img = img.crop((0,0,640,480))

            panel.config(image = img)
            panel.image = img

        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cam.release()



def startPictures():
    #get camera idx
    cameraIdx = dropdown.get()
    global CAMERA_INDEX
    CAMERA_INDEX = int(cameraIdx)
    #hide main window
    master.withdraw()
    #show new dialog 
    dialog = Toplevel()
    dialog.title("WARNING")
    dialog.geometry("300x100")
    dialog.resizable(False, False)
    #put text on screen
    l = Label(dialog, text = "WARNING: All files in directory will be destroyed!!!")
    dirName = Label (dialog, text = "Directory: " + outText.cget("text"))
    l2 = Label(dialog, text = "Are you sure you want to continue?")
    #grid
    l.grid(row = 0, column = 0, columnspan = 2)
    dirName.grid(row = 1, column = 0, columnspan = 2)
    l2.grid(row = 2, column = 0, columnspan = 2)

    #button
    b1 = Button(dialog, text = "Yes", command=lambda: [dialog.destroy(), takePics()])
    b2 = Button(dialog, text = "No", command=
                lambda: [dialog.destroy(), master.deiconify()])
    b1.grid(row = 3, column = 0)    
    b2.grid(row = 3, column = 1)
 


def updateStatus():
    outDir = outText.cget("text")
    timingConfigFile = configText.cget("text")
    cameraIdx = dropdown.get()

    configReady = False
    dirReady = False
    #try to open the timing config file
    try: 
        with open (timingConfigFile, "r") as f:
            configReady = True
    except:
        configReady = False
    #check if directory is valid
    print("outDir: ", outDir)
    if outDir != "":
        dirReady = True
    print("configReady: ", configReady)
    print("dirReady: ", dirReady)
    if configReady and dirReady:    
        print("READY")
        statusText.config(text = "Status: READY")
        b1.config(state=NORMAL)
    elif not configReady and dirReady:
        print("Select a valid config file")
        statusText.config(text = "Status: Select a valid config file")
        b1.config(state=DISABLED)
    elif configReady and not dirReady:
        print("Select a valid output directory")
        statusText.config(text = "Status: Select a valid output directory")
        b1.config(state=DISABLED)
    else:
        print("Select a valid output directory and config file")
        statusText.config(text = "Status: Select a valid output directory and config file")
        b1.config(state=DISABLED)


def setOutDir():
    outDir = filedialog.askdirectory()
    #update label
    outText.config(text = outDir)
    updateStatus()


def setTimingConfigFile():
    timingConfigFile = filedialog.askopenfilename(filetypes=[("FIRE Config Files", ".fire")])
    #update label
    configText.config(text = timingConfigFile)
    updateStatus()



# creating main tkinter window/toplevel
master = Tk()

cameras = getCameras()

# this will create a label widget
l1 = Label(master, text = "Output Directory: ")
l2 = Label(master, text = "Timing Configuration File: ")
dropdown = Combobox(master, values = cameras)
l3 = Label(master, text = "Select Camera: ")
# grid method to arrange labels in respective
# rows and columns as specified
l1.grid(row = 0, column = 0, sticky = W, pady = 2)
l2.grid(row = 1, column = 0, sticky = W, pady = 2)
l3.grid(row = 2, column = 0, sticky = W, pady = 2)
dropdown.grid(row = 2, column = 1, pady = 2)

# entry widgets, used to take entry from user
e1 = Button(master, text = "Browse", command=setOutDir)
e2 = Button(master, text="Browse", command=setTimingConfigFile)

# this will arrange entry widgets
e1.grid(row = 0, column = 1, pady = 2)
e2.grid(row = 1, column = 1, pady = 2)

outText = Label(master, text = "", justify=LEFT)
configText = Label(master, text = "",justify=LEFT)
outText.grid(row = 0, column = 2, columnspan = 4)
configText.grid(row = 1, column = 2, columnspan = 4)

#Status label
statusText = Label(master, text = "Status: IDLE",anchor='w')
statusText.grid(row = 3, column = 0)


# # setting image with the help of label
# Label(master, image = img1).grid(row = 0, column = 2,
# 	columnspan = 2, rowspan = 2, padx = 5, pady = 5)

# button widget
b1 = Button(master, text = "Start", state=DISABLED, command=startPictures)

# arranging button widgets
b1.grid(row = 3, column = 2, sticky = E)
# infinite loop which can be terminated 
# by keyboard or mouse interrupt
mainloop()
