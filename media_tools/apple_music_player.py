import pyautogui as pag
import random
import time

start_time = time.time()
width, height = pag.size()
pag.PAUSE = 60
while True:
    if time.time() - start_time > 3 * 60 * 60:  # 2 hours
        break
    # gen random number in 0 and width
    x = random.randint(int(width / 100 + 100), int(width - 100))
    y = random.randint(int(width / 100 + 100), int(height - 100))
    # print(x,y)
    # gen random number in 0.1 and 2.0
    pag.moveTo(x, y, duration=random.uniform(0.1, 0.4))

    # random in "a" and "Z"
    key = chr(random.randint(97, 122))
#    pag.typewrite(key, interval=random.uniform(0.1, 0.2))
