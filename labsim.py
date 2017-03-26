#Script Author: Stephen Thomas

from __future__ import division
from random import expovariate, uniform, seed
import simpy

seed(10)

#Simulation Model Variables
NUM_MACHINES = 80 #number of computers in the lab; resource
THINKRATE = 120 #thinking rate of student; exponential dist.
COMPRATE = 20 #computing rate/hour; exponential dist.
ARR_RATE = 10 #student arrival rate/hour; exponential dist.
MIN_ITER = 1 #minimum iterations (think-compute tasks) per student
MAX_ITER = 5 #maximum iterations (thikn-compute tasks) per student
HOURS = 1000 #simulate for 1000 hours


#Global Simulation Analysis Variables
stu_id = 0 #number to identify student
stu_sat = 0 #students who manage to sit at a computer
stu_renege = 0 #students who turn back because no machine is available
lab_in = [] #list that tracks time students sit
lab_out = [] #list that tracks time students leave
timespent = [] #list for time analysis after simulation ends
compute_que = 0
compute_rec = []


class Complab(object):
    global compute_rec
    #the lab contains a limited number of machines to serve in parallel
    #students request a machine upon arrival, then do their think-compute tasks

    def __init__(self, env, num_machines):
        self.env = env
        self.machine = simpy.Resource(env, num_machines)
        
    def think(self, student): #the thinking rate
        yield self.env.timeout(expovariate(THINKRATE))

    def compute(self, student): #the computation rate
        yield self.env.timeout(expovariate(COMPRATE))
        compute_rec.append(compute_que)


def student(env, name, lab):    #Student arrival process
    global stu_sat, stu_renege, lab_in, lab_out, compute_que, compute_rec

    print "ARR: %s arrives at the lab at %.2f." % (name, env.now)

    if (NUM_MACHINES - lab.machine.count) > 0: #if a terminal is open
        print "RES: Terminal is available!"
        with lab.machine.request() as request:

            yield request #this line is is unrequired, but allows easy modification of waiting ques for students
                          #who are unable to sit at a computer

            print "SAT: %s sits at computer at %.2f and starts thinking." % (name, env.now)
            stu_sat += 1
            lab_in.append(env.now)

            for tasks in range(int(uniform(MIN_ITER, MAX_ITER))):
                yield env.process(lab.think(name))
                print "THK: %s sent request %s to computer at %.2f." % (name, tasks, env.now)
                compute_que += 1

                yield env.process(lab.compute(name))
                print "CPU: %s receives computation %s from mainframe at %.2f." % (name, tasks, env.now)
                compute_que -= 1

            print "EXT: %s leaves the lab at %.2f." % (name, env.now)
            lab_out.append(env.now)

    else: #no terminal is open, student leaves
        stu_renege += 1
        print "RES: Terminal UNAVAILABLE!"
        print "EXT: %s leaves the lab at %.2f." % (name, env.now)


def setup(env, num_machines): #creates the lab and generates student while sim runs
    global stu_id
    complab = Complab(env, num_machines)
    env.process(student(env, 'Student %d' % stu_id, complab))

    while True: #create students while the simulation runs:
        yield env.timeout(expovariate(ARR_RATE))
        stu_id += 1
        env.process(student(env, 'Student %d' % stu_id, complab))

def crunch(): #computes time spent in lab per student, BUT only students who left
    global lab_in, lab_out, timespent
    timespent = []
    for n in range(len(lab_out)):
        stutime = lab_out[n] - lab_in[n]
        timespent.append(stutime)

    avg_time = sum(timespent)/len(timespent)
    avg_comp_que = sum(compute_rec)/len(compute_rec)
    print "Student Arrivals: %d" % (stu_sat + stu_renege)
    print "Students Sat: %d" % stu_sat
    print "Students Reneged: %d" % stu_renege
    print "\n"
    print "Fraction of Reneged Students: %.3f students" % (stu_renege / (stu_sat + stu_renege))
    print "Average Time in lab: %.3f minutes" % (avg_time * 60)
    print "Average Compute Tasks in que: %.3f tasks" % (avg_comp_que)



#Build Simulation Model
print "Computer Lab Simulation"

env = simpy.Environment()
env.process(setup(env, NUM_MACHINES))

print "Running Simulation..."
#Execute the model
env.run(until=HOURS)
print "Simulation Time Reached.  Simulation stopped.\n"

#Analyze the results
crunch()
