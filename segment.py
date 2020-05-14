import pandas
import numpy

class segment:
    def __init__(self, start=(0, 0), end=(0, 0), length=0, avgspeed=0, cars=[]):
        self.start = start
        self.end = end
        self.length = length
        self.avgspeed = avgspeed
        # self.cars = cars
        self.midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        self.speedhist = pandas.DataFrame({"speed": []})
        self.exclusion = 1
