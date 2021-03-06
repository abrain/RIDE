#  Copyright 2008-2011 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from math import ceil
import os
import random
import shutil
import time
import sys


ROOT = os.path.dirname(__file__)
lib = os.path.join(ROOT, '..', 'lib')
src = os.path.join(ROOT, '..', 'src')

sys.path.insert(0, lib)
sys.path.insert(0, src)

from model import RIDE
from test_runner import Runner


def do_test(seed, path):
    try:
        ride_runner = init_ride_runner(seed, path)
        for i in range(10000):
            ride_runner.step()
        return 'PASS', seed, i, path
    except Exception, err:
        print err
        print 'i = ', i
        print 'seed was', str(seed)
        print 'path was', path
        return 'FAIL', seed, i, path

def init_ride_runner(seed, path):
    shutil.rmtree(path, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, 'testdir'), os.path.join(path, 'testdir'))
    random.seed(seed)
    ride = RIDE(random, path)
    ride_runner = Runner(ride, random)
    if random.random() > 0.5:
        ride.open_test_dir()
    else:
        ride.open_suite_file()
    return ride_runner


def split(start, end):
    return int(ceil(float(end - start) / 2)) + start


def skip_steps(runner, number_of_steps):
    for i in range(number_of_steps):
        runner.skip_step()

def debug(seed, path, last_index, trace, start, end):
    if last_index == start:
        return trace + [last_index]
    if end <= start:
        return debug(seed, path, last_index, trace + [end], end+1, last_index)
    runner = init_ride_runner(seed, path)
    if trace != []:
        run_trace(runner, trace)
    midpoint = split(start, end)
    runner.skip_steps(midpoint)
    try:
        for j in range(midpoint, last_index):
            runner.step()
        return debug(seed, path, last_index, trace, start, midpoint-1)
    except Exception, err:
        if runner.count == last_index:
            return debug(seed, path, last_index, trace, midpoint, end)
        else:
            print 'New exception during debugging!'
            return debug(seed, path, runner.count, trace, midpoint, runner.count)

def run_trace(runner, trace):
    i = 0
    while i < trace[-1]:
        if i in trace:
            runner.step()
        else:
            runner.skip_step()
        i += 1

def generate_seed():
    seed = long(time.time() * 256)
    if len(sys.argv) == 3:
        seed = long(sys.argv[2])
    return seed

if __name__ == '__main__':
    result, seed, i, path = do_test(generate_seed(), sys.argv[1])
    if result == 'FAIL':
        print '='*80
        trace = debug(seed, path, i, [], 0, i)
        print '#'*80
        print trace
        print '%'*80
        print 'seed = ', seed
        run_trace(init_ride_runner(seed, path), trace)
        print 'error occurred!'

