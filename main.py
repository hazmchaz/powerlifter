class Powerlifter:
    def __init__(self, squat, deadlift, bench, bw):
        self.squat = squat
        self.deadlift = deadlift
        self.bench = bench
        self.bw = bw
        self.total = sum([squat, deadlift, bench])
        self.wilks = self.total * (500 / (
                -216.0475144 + 16.2606339 * bw - 0.002388645 * (bw ** 2) - 0.00113732 * (bw ** 3) + (
                bw ** 4) * 7.01863 * 10 ** -6 + (bw ** 5) * -1.291 * 10 ** -8))


def makearray(one, two, three, four):
    array = [one, two, three, four]
    return array


newArray = makearray(1, 2, 3, 4)

for val in newArray:
    if val >= 2:
        print(val)

horry = Powerlifter(160, 250, 125, 101)
daniel = Powerlifter(170, 215, 105, 88)

lifters = [horry, daniel]

for lifter in lifters:
    if lifter != lifters[(len(lifters) - 1)]:
        print(lifter.wilks, ", ")
    else:
        print(lifter.wilks)
