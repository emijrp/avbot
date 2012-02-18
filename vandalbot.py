# -*- coding: utf-8 -*-

# Copyright (C) 2012 emijrp <emijrp@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import nltk
import glob
import os
import random
import re
import sys
import time

wordlemmatizer = nltk.WordNetLemmatizer()
commonwords = []

revs = {}
#training using vandalism corpus 2010
globs = [glob.glob(os.path.join('part%d/' % i, '*.txt')) for i in range(1,int(sys.argv[1]))]
c = 0
for glob_ in globs:
    for infile in glob_:
        c += 1
        if c % 10000 == 0:
            print c, 'files'
        text_file = open(infile, 'r')
        revid = infile.split('/')[1].split('.')[0]
        revs[revid] = unicode(text_file.read(), 'utf-8')
        text_file.close()
print c, 'files'

id2revid = {}
f = open('edits.csv', 'r')
for l in f.readlines():
    l = l[:-1].split(',')
    if revs.has_key(l[2]) and revs.has_key(l[3]):
        id2revid[l[0]] = [l[2], l[3]]
f.close()

gold = {}
f = open('gold-annotations.csv', 'r')
for l in f.readlines():
    l = l[:-1].split(',')
    if id2revid.has_key(l[0]):
        gold[l[0]] = l[1]
f.close()

regulartexts =  []
vandaltexts = []
for k, v in gold.items():
    if v == '"vandalism"':
        vandaltexts.append([revs[id2revid[k][0]], revs[id2revid[k][1]], k])
        #print 'http://en.wikipedia.org/w/index.php?diff=next&oldid=%s' % id2revid[k][0]
    elif v == '"regular"':
        regulartexts.append([revs[id2revid[k][0]], revs[id2revid[k][1]], k])

mixededits = [(edit, 'vandalism') for edit in vandaltexts]
mixededits += [(edit, 'regular') for edit in regulartexts]
random.shuffle(mixededits)
print len(vandaltexts), 'vandalism', len(regulartexts), 'regular', len(mixededits), 'total'

regexps = {}
for r in open('vandalbot.regexps', 'r').readlines():
    r = r[:-1]
    if r and r[0] != '#':
        regexps[r] = re.compile(r)

def edit_features(edit):
    #classifier using manual regexps 
    features = {}
    
    #regexps
    for rname, regexp in regexps.items():
        if len(re.findall(regexp, edit[1])) > len(re.findall(regexp, edit[0])):
            features[rname] = True
    
    #blanking detector
    if len(edit[0]):
        features['size-change-%d' % ((((len(edit[1])-len(edit[0]))/(len(edit[0]))/100))/10*10)] = True # -5%, +5%, -10%, +10%, ...
    
    return features

featuresets = [(edit_features(n), g) for (n, g) in mixededits]

range_ = [i/10.0 for i in range(1,10)]
best = [0, 0, 0, 0, [], [], [], []]
for threshold in range_:
    size = int(len(featuresets)*threshold)
    train_set, test_set = featuresets[:size], featuresets[size:]
    classifier = nltk.NaiveBayesClassifier.train(train_set)
    accuracy = nltk.classify.accuracy(classifier, test_set)
    revertedfine = []
    falsenegatives = []
    falsepositives = []
    c = 0
    for example in test_set:
        result = classifier.classify(example[0])
        #print result
        if result == 'regular' and example[1] == 'vandalism':
            falsenegatives.append(mixededits[size+c][0][2])
        elif result == 'vandalism' and example[1] == 'regular':
            falsepositives.append(mixededits[size+c][0][2])
        if result == 'vandalism' and example[1] == 'vandalism':
            revertedfine.append(mixededits[size+c][0][2])
        c += 1
    
    if accuracy > best[3]:
        best = [size, len(featuresets)-size, threshold, accuracy, revertedfine, falsenegatives, falsepositives, classifier.most_informative_features(50)]
    #classifier.show_most_informative_features(20)

print 'Best run: train set size [%d], test set size [%d], threshold [%.2f], accuracy [%f], revertedfine [%d], errors[%d]' % (best[0], best[1], best[2], best[3], len(best[4]), len(best[5])+len(best[6]))
print 'False negatives [%d]:' % (len(best[5])), ', '.join(['http://en.wikipedia.org/w/index.php?diff=next&oldid=%s' % (id2revid[i][0]) for i in best[5]])
print 'False positives [%d]:' % (len(best[6])), ', '.join(['http://en.wikipedia.org/w/index.php?diff=next&oldid=%s' % (id2revid[i][0]) for i in best[6]])
#print best[6]
