# wordcount.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from chain import compose, chain

APP_NAME = 'wordcount'

def sparkSession():
     return (SparkSession.builder \
             .appName(APP_NAME) \
             .master('local[1]') \
             .getOrCreate())


@chain
def with_stuff1(a1, a2, df):
    return df.withColumn('stuff1', lit(a1))


@chain
def with_stuff2(a1, df):
    return df.withColumn('stuff2', lit(a1))


def main(sc): 
    data = [("jose", 1), ("li", 2), ("liz", 3)]
    source_df = sc.createDataFrame(data, ["name", "age"])

    # Transform pipeline
    pipeline = compose(
                    with_stuff1("nice","person"),
                    with_stuff2("yoyo")
                )
    actual_df = pipeline(source_df)
    print(actual_df.show())


if __name__ == '__main__':
    # print ('{}={}'.format(sys.argv, len(sys.argv)))
    # if len(sys.argv) != 2:
    #     print ("Usage: wordcount <file>")
    #     exit(-1)

    main(sparkSession())


