# wordcount.py

import sys 
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, split
import functions as udfStr

APP_NAME = 'wordcount'

def sparkSession():
     return (SparkSession.builder \
             .appName(APP_NAME) \
             .master('local[1]') \
             .getOrCreate())


def main(sc, argv): 
    filename = argv[1]
    # threshold = int(argv[2])

    dfTextFile = sc.read.text(filename)
    wordCount = dfTextFile \
                 .select(explode(split(dfTextFile.value, ' ')).alias('word')) \
                 .transform(udfStr.remove_punctuation('word')) \
                 .groupBy('word') \
                 .count() \
                 .collect()
    print('-' * 50)
    # wordCount.select('word').show()

    for w in sorted(wordCount, key=lambda x: x[1]):
        print(w)

    print('-' * 50)


if __name__ == '__main__':
    print ('{}={}'.format(sys.argv, len(sys.argv)))
    if len(sys.argv) != 2:
        print ("Usage: wordcount <file>")
        exit(-1)

    main(sparkSession(), sys.argv)

    # Create spark context
    # appName = 'wordcount'
    # conf = SparkConf().setAppName(appName)
    # conf = SparkConf().setMaster('local[1]')
    # sc = SparkContext(conf=conf)

    # threshold = int(sys.argv[2])
    # filename = sys.argv[1]

    # lines = sc.textFile(filename).flatMap(lambda line: line.split(' '))
    # counts = lines.map(lambda x: (x,1)) \
    #               .reduceByKey(lambda x,y: x+y) \
    #               .filter(lambda pair: pair[1] > threshold)
    # output = counts.collect()
    # for (word,count) in sorted(output,key=lambda x:x[1]):
    #     print('%s: %i' %(word, count))


