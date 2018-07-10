# wordcount.py

from __future__ import print_function
from sys import argv
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, split
from functions import updir
from transformations import remove_punctuations
from chain import compose
from os import path

APP_NAME = 'wordcount'

def sparkSession():
     return (SparkSession.builder \
             .appName(APP_NAME) \
             .master('local[1]') \
             .getOrCreate())


def main(sc, arg): 
    cwd = path.dirname(path.abspath(__file__))
    basedir = updir(cwd,1)
    filename  = 'file:///' + path.join(basedir, 'data', 'wordcount.txt')
    # filename = arg[1]
    # threshold = int(argv[2])

    dfTextFile = sc.read.text(filename)
    dfIn = dfTextFile.select(explode(split(dfTextFile.value, '\s+')).alias('word'))

    # Transform pipeline
    pipeline = compose(remove_punctuations('word'))
    dfCount = pipeline(dfIn) \
             .groupBy('word') \
             .count() \
             .collect()
    print('-' * 50)
    # wordCount.select('word').show()
    for w in sorted(dfCount, key=lambda x: x[1]):
        print(w)
    print('-' * 50)


if __name__ == '__main__':
    # print ('{}={}'.format(sys.argv, len(sys.argv)))
    # if len(sys.argv) != 2:
    #     print ("Usage: wordcount <file>")
    #     exit(-1)

    main(sparkSession(), argv)


