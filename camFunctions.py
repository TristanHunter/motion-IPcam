import cv2
import subprocess as sp
import numpy as np
import datetime
import sys

# USAGE: ./camFunctions.py Cam1 480 640 20 22:00:00

def main(argv=[__name__]):

    cam_name = str(sys.argv[1])
    height = int(sys.argv[2])
    width = int(sys.argv[3])
    fps = int(sys.argv[4])
    backup_time = str(sys.argv[5])

    print(recMotion(cam_name, height, width, fps, backup_time))
    return 0


def vidReader(camName):

    pipeName = 'fifo' + camName
    
    command = [ 'ffmpeg',
        '-i', pipeName, 
        '-pix_fmt', 'bgr24',      # opencv requires bgr24 pixel format.
        '-vcodec', 'rawvideo',
        '-an','-sn',              # we want to disable audio processing (there is no audio)
        '-f', 'image2pipe',
        '-', '-v', '8', '-hide_banner']

    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**8)    
    return pipe

def vidWriter(vidName, WIDTH, HEIGHT, FPS):

    # vidName must include file extension

    dim = str(WIDTH) + 'x' + str(HEIGHT)

    command = ['ffmpeg',
        '-y',                   # overwrite if existing
        '-v', '8',              # only output fatal errors
        '-f', 'rawvideo',       # raw video streams from pi
        '-vcodec','rawvideo',
        '-s', dim,
        '-pix_fmt', 'bgr24',    # opencv uses bgr format
        '-r', str(FPS),
        '-i', '-',              # read input from stdin
        '-an',                  # no audio
        '-vcodec', 'libx264',
        '-crf', '23',           # Const rate factor to compress vid
         vidName ]

    pipe = sp.Popen(command, stdin=sp.PIPE)
    
    return pipe
    


def recMotion(name, HEIGHT, WIDTH, FPS, backupTime):

    saveDir = './saved/'
    frameCt = 0
    startDT = datetime.datetime.now()

    # initialize video reader pipe
    pipeIn = vidReader(name)

    # initialize video writer pipe
    vidName = str(startDT.strftime('%Y-%m-%d_%H-%M-%S_')) + name + '.mp4'
    pipeOut = vidWriter(vidName, WIDTH, HEIGHT, FPS)
    
    # init parms for motion detection
    grey_image = np.zeros((HEIGHT,WIDTH,3), np.float32)         # temporary grayscale img for editing
    moving_average = np.zeros((HEIGHT,WIDTH,3), np.float32)     # dynamic background image
    difference = None                                           # img sized 2d array to store frame diffs
    ceil = 20                                                   # max contour vector size to trigger motion

    # start recording
    firstRun = True
    while True:
    
        # Capture a single frame
        raw_image = pipeIn.stdout.read(WIDTH*HEIGHT*3)          # 3rd dimension is for bgr frames

        # transform the frame read into a numpy array
        frame =  np.fromstring(raw_image, dtype='uint8')
        frame = frame.reshape((HEIGHT,WIDTH,3))          
    
        frame = cv2.flip(frame, 0)
        
        if firstRun:                                ###  Move outside while looop
            moving_avg = np.float32(frame)
            difference = np.float32(frame)
            firstRun = False

        # look for motion in new frame
        moving_avg = cv2.accumulateWeighted(frame, moving_avg, 0.020)   # Compute the background average
        temp = np.float32(frame)                                        # Copy to temp to operate on
        difference = cv2.absdiff(temp, moving_avg)
        4*difference                                                    # Amplify difference
        grey_image = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)       # Convert the image for thresholding
        ret, grey_image = cv2.threshold(grey_image, 32, 255, 0)
        grey_image = np.uint8(grey_image)                               # Narrowing to 8bit int for contour function
        grey_image, contours, hierarchy = cv2.findContours(grey_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # print a timestamp on the video frame
        timestamp = str(datetime.datetime.now().replace(microsecond=0))
        frame = cv2.putText(frame, timestamp, (10,30), cv2.FONT_HERSHEY_SIMPLEX, .75, (255,255,255))

        # Write video if motion - before drawing contours!
        if len(contours) > 20:                          
            pipeOut.stdin.write(frame.tostring())
            frameCt = frameCt + 1

        cv2.drawContours(frame, contours, -1, (0,255,0))                # Draw contours                  
        cv2.imshow(name, frame)                                        # Display video frame

        k = chr(cv2.waitKey(1) & 0xFF)      # Must use key wait for imshow
        if k == 'q':                        # Press q to quit
            break
        elif k == 's':                      # Press s to save
            if frameCt > FPS:               # Only save if longer than 1 sec
                pipeOut.stdin.flush()
                pipeOut.stdin.close()
                sp.call(["mv", '-f', vidName, (saveDir + vidName)])
                startDT = datetime.datetime.now()
                vidName = str(startDT.strftime('%Y-%m-%d_%H-%M-%S_')) + name + '.mp4'
                pipeOut = vidWriter(vidName, WIDTH, HEIGHT, FPS)
                frameCt = 0

        # Check if it is backup time
        now = datetime.datetime.now().strftime('%H:%M:%S')
        if now == backupTime and frameCt > FPS:    # only write if at least 1 sec recorded
            #save video and start a new one
            print('saving video backup')
            pipeOut.stdin.flush()
            pipeOut.stdin.close()
            sp.call(["mv", '-f', vidName, (saveDir + vidName)])
            startDT = datetime.datetime.now()
            vidName = str(startDT.strftime('%Y-%m-%d_%H-%M-%S_')) + name + '.mp4'
            pipeOut = vidWriter(vidName, WIDTH, HEIGHT, FPS)
            frameCt = 0
            
        pipeIn.stdout.flush()

    stopDT = datetime.datetime.now()
    deltaDT = stopDT - startDT
    print (str(deltaDT))
    print (("Frame Count: %d") % frameCt)
    
    cv2.destroyAllWindows()

    # Cleanup pipes
    pipeIn.stdout.flush() 
    pipeOut.stdin.flush()
    pipeIn.stdout.close()
    pipeOut.stdin.close()

    # Save current vid or delete if empty
    if frameCt > 0:
        savePath = saveDir + vidName
        sp.call(["mv", '-f', vidName, savePath])
    else:
        sp.call(["rm", '-f', vidName])

    pipeOut.wait()
    pipeIn.wait()



main()
