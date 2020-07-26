import datetime
import math
import time
import timeit
import os

from pynput.keyboard import Key, Listener

# dont ask why theres 3 different time modules im not sure either
# this is so bad

# main class
class keyTracker():
    def __init__(self):
        self.allKeyPresses = [] # tracks every single key press and release
        self.keyInfoDic = {} # backbone of the program, tracks all relevant info on each key (that has been pressed at least once)
        self.combos = [] # tracks all combanations of keys pressed (in a single frame)
        self.keyHistory = [] # i mean allKeyPresses kinda does the same thing but im lazy
        self.justPressed = False
        self.totalTimePressed = 0
        self.tick = 0
        self.stop = False

        self.listener = Listener(on_press = self.on_press, on_release = self.on_release)
        self.listener.start()
    
    def on_press(self, key):
        if (self.canInitNewKey(key) == True):
            self.keyInfoDic.get(key).press()
        self.getCombo() # dont think this will cause any problems srsly

    def on_release(self, key):
        self.allKeyPresses.append(f"(R){key}")
        self.keyHistory.append(True)
        self.justPressed = True
        if (self.canInitNewKey(key) == True):
            self.keyInfoDic.get(key).release()

    def canInitNewKey(self, key, tryToCreate = True):
        if (key in self.keyInfoDic):
            return True
        if (tryToCreate):
            self.keyInfoDic[key] = keyInfo(key, self)
        try:
            self.keyInfoDic.get(key).amountPressed
            return True
        except:
            return False
        return False

    def update(self):
                
        holder = self.getAllKeysCurrentlyPressed()
        if (len(holder) == 3 and Key.cmd in holder and Key.shift in holder and Key.esc in holder):
            self.end()
            return
        
        self.tick += 1
        if (self.tick == 60):
            self.tick = 0
        
        self.getCombo()

        if (self.justPressed == False):
            self.keyHistory.append(False)
        else:
            self.justPressed = False

        for key in self.keyInfoDic.values():
            key.update()
    
    def getAllKeysCurrentlyPressed(self):
        holder = []
        for key in self.keyInfoDic.values():
            if (key.isCurrentlyPressed):
                holder.append(key.name)
        return holder

    def getCombo(self): # combo is capped is some places where it makes no sense bc i og named it patterns but i actually need that name somewhere else so i just replaced all of them
        # check if theres a new Combo

        # get all keys current pressed that frame
        newCombo = self.getAllKeysCurrentlyPressed()
        
        if (len(newCombo) < 2):
            return

        # check if the Combo already exists
        isUnique = True
        for Combo in self.combos:
            if (self.areListSame(Combo[0], newCombo) == False):
                continue
            else:
                Combo[1] += 1
                isUnique = False
                break
        if (isUnique):
            # add the Combo if it doesnt
            self.combos.append([newCombo, 1])

        # check if the current.combos contains any.combos of other key
        for Combo in self.combos: # yes im repeating it here but it just looks better ok and there are so many more optimzations u can make y focus on this
            if (self.isListSubset(Combo, newCombo)):
                Combo[1] += 1

    def isListSubset(self, smallerList, biggerList):
        if (len(smallerList) >= len(biggerList)):
            return False
        for content in smallerList:
            if (content not in biggerList):
                return False
        return True

    def areListSame(self, list1, list2):
        if (len(list1) == len(list2)):
            for content in list1:
                if (content not in list2):
                    return False
            return True
        return False

    def end(self):
        self.listener.stop()
        self.stop = True

        username = os.getlogin()
        filePath = os.path.join(f"/Users/{username}/Desktop", "keyInfo.txt")
        f = open(filePath, "w")

        longestKeyHeld = ["null", 0]
        mostAmountOfReleases = ["null", 0]
        mostCommonCombo = [["null"], 0]

        f.write("Key Info\n")
        # print info about how long keys were pressed
        for key in self.keyInfoDic.keys():
            i = self.keyInfoDic[key]

            # get percentage of time a key was pressed, and how long in total
            f.write(f"\n{key}: {round(((i.allTimePressed * 100) / self.totalTimePressed), 2)}% | {round(i.maxTimePressed/60, 2)}s")

            # get longest time a key was held
            if (i.maxTimePressed/60 > longestKeyHeld[1]):
                longestKeyHeld[0] = i.name
                longestKeyHeld[1] = round(i.maxTimePressed/60, 2)
            
            # get most amount of key presses for a single key
            if (i.amountReleased > mostAmountOfReleases[1]):
                mostAmountOfReleases[0] = i.name
                mostAmountOfReleases[1] = i.amountReleased
        
        # get info about combos
        for combo in self.combos:
            if (combo[1] > mostCommonCombo[1]):
                mostCommonCombo = combo

        # get info on presses per min
        enoughInfoForPPM = True
        if (len(self.keyHistory) < 120):
            # only display infomation about ppm if the user has been running the program for more then 2 mins
            # hmm yeah this doesnt seem to work but i cant be bothered lol
            enoughInfoForPPM = False
        else:
            distToEnd = len(self.keyHistory)
            # very good naming scheme
            maxAmountInPeriod = 0
            minAmountInPeriod = 100
            holderInPeriod = 0
            indexInPeriod = 0
            while (distToEnd >= 60):
                presses = self.keyHistory[indexInPeriod: indexInPeriod + 60]
                amountOfValidPresses = 0
                for i in presses:
                    if (i):
                        amountOfValidPresses += 1
                holderInPeriod += amountOfValidPresses
                if (minAmountInPeriod > amountOfValidPresses):
                    minAmountInPeriod = amountOfValidPresses
                elif (maxAmountInPeriod < amountOfValidPresses):
                    maxAmountInPeriod = amountOfValidPresses

                distToEnd -= 1
                indexInPeriod += 1


        f.write("\n\n------\nGeneral Info\n")
        f.write(f"\nLongest key held: {longestKeyHeld[0]} for {longestKeyHeld[1]}s")
        f.write(f"\nMost key presses: {mostAmountOfReleases[0]} x{mostAmountOfReleases[1]}")
        f.write(f"\nMost common combination of keys: {combo[0]}, held for {round(combo[1]/60, 2)}s")
        if (enoughInfoForPPM):
            f.write(f"\nMost key presses per minute: {maxAmountInPeriod}")
            f.write(f"\nMinimum key presses per minute: {minAmountInPeriod}")
            f.write(f"\nAverage key presses per minute: {round(holderInPeriod/indexInPeriod, 2)}")
        else:
            f.write("\nRun the program for more then 2 minutes to recieve data on key presses per minute")
        f.close()
        print(f)

class keyInfo():
    def __init__(self, name, parent):
        # needed vars
        self.name = name
        self.parent = parent
        self.isCurrentlyPressed = False

        # track vars related to amount x
        self.amountPressed = 0
        self.amountReleased = 0
        
        # tracks vars related to length
        self.maxTimePressed = 0
        self.currentTimePressed = 0
        self.allTimePressed = 0

    def press(self):
        # since sometimes a key is held for less then a frame, just manually add 1 to the relevant vars (so it doesnt get skipped)
        self.isCurrentlyPressed = True
        self.amountPressed += 1
        self.allTimePressed += 1
        self.parent.totalTimePressed += 1
        self.currentTimePressed += 1
    
    def release(self):
        self.isCurrentlyPressed = False
        self.amountReleased += 1
    
    # called every frame (1/60 of a second)
    def update(self):
        if (self.isCurrentlyPressed):
            # tracks the total time a key was held down for
            self.allTimePressed += 1
            self.parent.totalTimePressed += 1

            # tracks longest time a key was a held for
            self.currentTimePressed += 1
        else:
            if (self.currentTimePressed > self.maxTimePressed):
                # what is more costly, check another if or assigning a value?
                self.maxTimePressed = self.currentTimePressed
                self.currentTimePressed = 0

k = keyTracker()
lastTicked, currentTick = 0, 0
lastTime = datetime.datetime.now().microsecond
passedOnce = False

while (True): # wait for the sec to finish, sub the remaning time from 1 mil, then sleep for that amount
    # check for the next 1/60 of a second
    if (lastTime - datetime.datetime.now().microsecond > 16400 and lastTime - datetime.datetime.now().microsecond < 17000):
        currentTick += 1
        if (currentTick >= 60):
            currentTick = 0
            time.sleep((1_000_000 - datetime.datetime.now().microsecond)/1_000_000)
        lastTicked = currentTick * 16666

        # actual code
        k.update()

        if (k.stop):
            break
