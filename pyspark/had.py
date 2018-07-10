#!/usr/bin/env python -tt
# cdc.py
from __future__ import print_function
from os import path
from pyspark.sql import SparkSession
from functions import updir, sel_cols
from transformations import hash_md5, lrtrim, add_default, find_new_recs, find_unchanged_recs, find_changed_recs, \
    merge_recs
from chain import compose

# Constant
APP_NAME = 'cdc'


def sparkSession():
    return (SparkSession.builder \
            .appName(APP_NAME) \
            .master('local[1]') \
            .config("spark.dynamicAllocation.enabled", "true") \
            .config("spark.dynamicAllocation.minExecutors", 1) \
            .config("spark.dynamicAllocation.maxExecutors", 20) \
            .config("spark.dynamicAllocation.executorIdleTimeout", "2m") \
            .config("spark.shuffle.service.enabled", "true") \
            .config("spark.default.parallelism", "12") \
            .config("spark.sql.shuffle.partitions", "200") \
            .getOrCreate())


def main(sc):
    cwd = path.dirname(path.abspath(__file__))
    basedir = updir(cwd, 1)
    files = {
        'c': 'thads2013n.txt',
        'i': 'incoming.csv'
    }
    currentfile = 'file:///' + path.join(basedir, 'data', files['c'])
    incomingfile = 'file:///' + path.join(basedir, 'data', files['i'])

    # if not path.exists(currentfile):
    #     print('Error: File not found: %s' %(currentfile))
    #     exit(-1)
    # if not path.exists(incomingfile):
    #     print('Error: File not found: %s' %(incomingfile))
    #     exit(-1)

    print('%s = %s' % ('current', currentfile))
    print('%s = %s' % ('incoming', incomingfile))

    df_in_old = sc.read.csv(currentfile, header='true')
    df_in_new = sc.read.csv(incomingfile, header='true')

    # Default 
    default_dt = '9999-12-31'
    col_hash_key = 'hash_key'
    col_hash_val = 'hash_value'

    # CDC columns
    col_start_dt = 'effstdt'
    col_end_dt = 'effenddt'

    # Primary keys
    primary_key = ['ccid']

    # Non Primary keys
    xld_cols = primary_key + [col_start_dt, col_end_dt]
    non_primary_key = sel_cols(df_in_new, xld_cols)

    # Display columns
    disp_cols = sel_cols(df_in_old, [col_hash_key, col_hash_val])

    # -----------------------
    # Build Pipeline
    # -----------------------
    #
    # Transformations
    #
    pipeline_xfr_newkv = compose(
        hash_md5(col_hash_val, non_primary_key),
        hash_md5(col_hash_key, primary_key),
        add_default(col_end_dt, default_dt),
        lrtrim([])
    )

    pipeline_xfr_oldkv = compose(
        hash_md5(col_hash_val, non_primary_key),
        hash_md5(col_hash_key, primary_key),
        lrtrim([])
    )
    #
    # NEW records (INSERT)
    #
    pipeline_newrecs = compose(find_new_recs(col_start_dt, col_end_dt, disp_cols))
    #
    # CHANGED records (UPDATES)
    #
    pipeline_upd_newrecs = compose(find_changed_recs(col_start_dt, col_end_dt, disp_cols, 'new'))
    pipeline_upd_oldrecs = compose(find_changed_recs(col_start_dt, col_end_dt, disp_cols, 'old'))
    #
    # UNCHANGED records 
    #
    pipeline_unchangedrecs = compose(find_unchanged_recs(disp_cols))
    #
    # Merge
    #
    sort_keys = primary_key + [col_end_dt]
    sort_order = [1 for i in range(len(primary_key))] + [0]
    pipeline_cdcrecs = compose(merge_recs(sort_keys, sort_order))

    # -----------------------
    # Execute Pipeline
    # -----------------------
    #
    # Basic Transformation
    #
    #df_xfr_newkv = pipeline_xfr_newkv(df_in_new)
    #df_xfr_oldkv = pipeline_xfr_oldkv(df_in_old)
    ##
    ## Cache Dataframe
    ##
    #df_xfr_newkv.persist()
    #df_xfr_oldkv.persist()
    ##
    ## CDC
    ##
    #df_newrecs = pipeline_newrecs(df_xfr_newkv, df_xfr_oldkv)
    #df_upd_newrecs = pipeline_upd_newrecs(df_xfr_newkv, df_xfr_oldkv)
    #df_upd_oldrecs = pipeline_upd_oldrecs(df_xfr_newkv, df_xfr_oldkv)
    #df_unchangedrecs = pipeline_unchangedrecs(df_xfr_newkv, df_xfr_oldkv)
    #df_cdcrecs = pipeline_cdcrecs(df_newrecs, df_upd_newrecs, df_upd_oldrecs, df_unchangedrecs)
    ##
    ## Clear Cache
    ##
    #df_xfr_newkv.unpersist()
    #df_xfr_oldkv.unpersist()
    ##
    ## Display Actions
    ##
    df_in_old.select('CONTROL','AGE1','METRO3','REGION') \
             .orderBy('CONTROL') \
             .show(truncate=False)  # Display
    # df_upd_newrecs.show(truncate=False)          # Display


if __name__ == '__main__':
    main(sparkSession())
