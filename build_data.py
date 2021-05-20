#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Luc Gerrits
"""

import os
import sys
import pandas as pd
import numpy as np
import glob
import pylab as pl
from matplotlib import cm
from scipy.ndimage.filters import gaussian_filter1d
from datetime import datetime

#%%
#global variables:
export_data_path = "./datas_csv/"
export_data_filename=sys.argv[1] if len(sys.argv)>1 else "no_name"
data_path = "./datas/"
image_directory="./images/"
final_df = None
conf_figsize=(15,8)
#detect_benchmarks_on="commits"
detect_benchmarks_on="commits_tot"

#jump of N detect_benchmarks_on (= change of test)
detect_benchmark_threshold=5000

#~300 blocks for init in our case:
detect_benchmark_start=True
initialization_threshold=1100

#benchmark ended if consecutive elements are equal.
detect_benchmark_stop=True
#Delete all data between start of detected consecutive element and jump of detect_benchmark_threshold
#Using 2, stop detected when 2 consecutive elements are strictly equal
#Note: minimum=2, recommended=4
detect_benchmark_stop_elements=10 #use something low (<5)
detect_benchmark_stop_elements_std=0.01 #use something low (<0.5)
detect_benchmark_stop_previous_elements=1

if not os.path.exists(image_directory):
    os.makedirs(image_directory)
    
if not os.path.exists(export_data_path):
    os.makedirs(export_data_path)
#%%
#
# Get all CSV files and put it inside dataframes
#
all_files = glob.glob(data_path + "/*.csv")
tmp_df = {}
for filename in all_files:
    df = pd.read_csv(filename, index_col=None, header=0, usecols=["time", "mean"],)
    field_name = os.path.basename(filename)[:-4]#remove extension
#    try:#test if field exists
#        test=fields[field_name]
#    except:
#        print("Missing CSV file for field: {}".format(field_name))
#        exit(1)

    tmp_df[field_name] = df
    #rename columns
    tmp_df[field_name].columns = ["time", field_name]
#%%
#
# Merge data into one table
#
final_df = tmp_df[detect_benchmarks_on] #init with commits
for field_key in tmp_df.keys():
    #skip first because already in final_df
    if field_key == detect_benchmarks_on:
        continue
    #merge tables
    #help, see https://pandas.pydata.org/docs/user_guide/merging.html#brief-primer-on-merge-methods-relational-algebra
    final_df = final_df.merge(tmp_df[field_key], on="time", how="left")

#fill NaN with previous value
final_df = final_df.fillna(method='ffill').fillna(0)
#%%
#
# Print available columns
#
print("Columns available are:")
final_df_cols=[] #contains the columns in the same order then final_df columns
for col in final_df.columns:
    print("{}, ".format(col), end='') #print the columns to know whats available
    final_df_cols.append(col)
print("")

#%%
#
# Benchmark detection: use to distinguish multiple test in the dataframe
#
final_df["test#"]=1
#detect_benchmark_threshold if commits jump N tx = change of test (VERIFY ALLWAYS IF TESTS MATCH ACTUAL TESTS)
previous=0 #previous value to compare to
number_of_benchmarks=1 #this is will be the nb of tests at the end of the for loop
col_detect_index=final_df_cols.index(detect_benchmarks_on)
for index, row in final_df.iterrows():
    if index == 0:
        previous=row[col_detect_index]
        continue #init first value
    if abs(row[col_detect_index] - (previous)) > detect_benchmark_threshold:
        number_of_benchmarks = number_of_benchmarks + col_detect_index
    previous=row[col_detect_index]
    final_df.loc[index, "test#"] = number_of_benchmarks
print("Benchmark detected = {}".format(number_of_benchmarks))
#end benchmark detection

#%%
#
# Filter out initialization of the test: only keep data where commits>1000
#

#detect benchmark start
#thanks to https://stackoverflow.com/a/27360130/13187605
if detect_benchmark_start:
    final_df = final_df.drop(final_df[(final_df[detect_benchmarks_on] >= 0) & (final_df[detect_benchmarks_on] < initialization_threshold)].index)
    final_df = final_df.reset_index(drop=True)

#detect_benchmark_stop=False
#detect benchmark stop
if detect_benchmark_stop:
    
    col_detect_index=final_df_cols.index(detect_benchmarks_on)
    #def remove_consecutive_elements(mydf):
    start_delete=False
    previous_elements=[] #previous value to compare to, act like a fifo
    previous=0 #previous value to compare to
    
    cur_benchmark=1
    for index, row in final_df.iterrows():
        if len(previous_elements) > detect_benchmark_stop_elements:
            previous_elements.pop(0) #do fifo stype array 
        previous_elements.append(round(row[col_detect_index], 3))
    
        if index > detect_benchmark_stop_elements:
            #print("{} {} => {}".format(index,previous_elements,np.array(previous_elements).std()))
            
            #detecte le debut de la fin du test
            if np.array(previous_elements).std() < detect_benchmark_stop_elements_std and start_delete == False:
#                print("{} {} => {}".format(index,previous_elements,np.array(previous_elements).std()))
                #found same consecutive elements !
                for i in range(0, detect_benchmark_stop_elements+detect_benchmark_stop_previous_elements):
                    final_df = final_df.drop(index-i)
                start_delete=True
                continue
            if start_delete == True:
                final_df = final_df.drop(index)
            
            if cur_benchmark != row["test#"]:
#                print("Change in test, stop end detection. Detect benchmark stop from {} to {}".format(start_at_index,index))
                start_delete = False #can start deleting delete again
                cur_benchmark=row["test#"]   
                                  
final_df = final_df.reset_index(drop=True)

#%%
#
# Plot function
# (auto color and auto benchmark detection based on "test#" column)
#
#color map here:
cm_subsection = np.linspace(0.0, 1.0, number_of_benchmarks+1)
colors = [ cm.jet(x) for x in cm_subsection ]
#self inc on each myplot() call:
total_plots=0
#general plot fct to make it simple:
def myplot(plot_type, X_colomn_name, Y_colomn_name, display=False, smooth = False):
    global total_plots
    #help on legend placement here: https://stackoverflow.com/a/4701285/13187605
#    pl.figure(total_plots)
    fig, ax = pl.subplots(1,1,figsize=conf_figsize)
    for i in range(1, number_of_benchmarks+1):
        #print lines for each test, using diff colors
        if X_colomn_name == "index":
            X_values=final_df.loc[final_df['test#'] == i].index
        else:
            X_values=final_df.loc[final_df['test#'] == i].values[:,final_df_cols.index(X_colomn_name)]
        Y_values=final_df.loc[final_df['test#'] == i].values[:,final_df_cols.index(Y_colomn_name)]
        if smooth:
            Y_values= gaussian_filter1d(Y_values, sigma=1) # make more smooth: BE CARFUL
        if plot_type == "line":
            ax.plot(X_values,Y_values, color=colors[i], label="Test#{}".format(i))
        elif plot_type == "scatter":
            ax.scatter(X_values,Y_values, color=colors[i], label="Test#{}".format(i))
        elif plot_type == "bar":
            if len(X_values) == 0: #fix an value error create by "bar" if empty data
                X_values= [0]
                Y_values= [0]
            ax.bar(X_values, Y_values, color=colors[i], alpha=0.5, label="Test#{}".format(i))
            # pl.hist(Y_values, color=colors[i], label="Test#{} ({})".format(i, Y_colomn_name))
        else:
            print("ERROR: Unknown plot type: {}".format(plot_type))
            exit(1)
    ax.set_title("f({})={}".format(X_colomn_name, Y_colomn_name))
    ax.set_xlabel(X_colomn_name)
    ax.set_ylabel(Y_colomn_name)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    pl.savefig(image_directory + "X=" + X_colomn_name + "|Y=" + Y_colomn_name + '.png', bbox_inches='tight', dpi=200)
    total_plots+=1
    if not display:
        pl.close(fig)

def getVariance(data):
    # info on axis selection: https://stackoverflow.com/a/46223968/13187605
    #Axis 1 will act on all the COLUMNS in each ROW
    #Axis 0 will act on all the ROW in each COLUMNS
    return data.mean(axis=0).var(axis=0,ddof=1)
def getStd(data):
    # info on axis selection: https://stackoverflow.com/a/46223968/13187605
    #Axis 1 will act on all the COLUMNS in each ROW
    #Axis 0 will act on all the ROW in each COLUMNS
    return data.mean(axis=0).std(axis=0,ddof=1)

def myplot_merged(X_colomn_name, Y_colomn_name, display=False):
    global total_plots

    #Note: X_colomn_name should be time !!

    #Some results of:
    #Variance: describes how much a random variable differs from its expected value.
    #Standard deviation is the measure of dispersion of a set of data from its mean.
    
    Y_colomn_merged_array = merge_tests_data_from(Y_colomn_name).values
    Y_colomn_merged_array_mean = Y_colomn_merged_array.mean(axis=1)

    X_colomn_merged_array = merge_tests_data_from(X_colomn_name).values.mean(axis=1) #avg times
    # utcfromtimestamp need 10 digit timestamp
    start=datetime.utcfromtimestamp(X_colomn_merged_array[0]) #/1e9
    end=datetime.utcfromtimestamp(X_colomn_merged_array[-1]) #/1e9
    avg_time_sec=(end-start).total_seconds()
    avg_time_min=avg_time_sec/60
    
    #show some data
#    pl.figure(total_plots)
    total_plots+=1
    fig, axs = pl.subplots(2,1,figsize=conf_figsize)
    i=1
    for col_arr in Y_colomn_merged_array.T:
        axs[0].plot(col_arr, label="Test {}".format(i))
        i+=1
    axs[0].plot(Y_colomn_merged_array_mean, label="Mean of all tests")
    
    axs[0].plot([], [], ' ', label="Mean={:.2f}".format(Y_colomn_merged_array.mean()))
    axs[0].plot([], [], ' ', label="Variance={:.2f} (?)".format(getVariance(Y_colomn_merged_array)))
    axs[0].plot([], [], ' ', label="Std={:.2f}".format(getStd(Y_colomn_merged_array)))
    axs[0].plot([], [], ' ', label="Time={:.1f}min".format(avg_time_min))
    axs[0].set_title("Tests with mean ({})".format(Y_colomn_name))
    axs[0].legend()
    

#    ax.plot(merged_array.mean(axis=1)-merged_array.var(axis=1,ddof=1), label="variance of all tests")
    axs[1].plot(Y_colomn_merged_array.var(axis=1,ddof=1), label="f({})=Var({})".format(X_colomn_name, Y_colomn_name))
    axs[1].plot(Y_colomn_merged_array.std(axis=1,ddof=1), label="f({})=Std({})".format(X_colomn_name, Y_colomn_name))
    axs[1].legend()
    pl.savefig(image_directory + "merged|X=" + X_colomn_name + "|Y=" + Y_colomn_name + '.png', bbox_inches='tight', dpi=200)
    if not display:
        pl.close(fig)
#%%
#
# Merge function of multiple signals
#

def merge_tests_data_from(colomn_name):
    tmp={}
    for i in range(1, number_of_benchmarks+1):
        values=final_df.loc[final_df['test#'] == i].values[:,final_df_cols.index(colomn_name)]
        tmp2= {}
        tmp2[i]=values
        tmp[i]=pd.DataFrame(tmp2)
    #for help, see https://pandas.pydata.org/docs/user_guide/merging.html
    temp_elements = pd.concat(tmp, axis=1, join="outer")
    temp_elements = temp_elements.fillna(method='ffill')
    return temp_elements

def merge_and_mean_tests_data_from(colomn_name):
    d=merge_tests_data_from(colomn_name).values.mean(axis=1) #mean all rows
    return d

#%%
#
# Some fix on time values
# And export to csv

if len(sys.argv)>1:
    #print(final_df)
    print("Data shape: {}".format(final_df.shape))
    filename=export_data_path +export_data_filename+".csv"
    final_df[['time']] = (df[['time']]/1e9).astype(int)
    final_df.to_csv(filename, index=False)
    print("Data exported to '{}'".format(filename))

    #merge and export all merged data:
    final_merged_df = {
            "time": merge_and_mean_tests_data_from("time").astype(int) #init with time
            }
    for col in final_df_cols:
            if col != "time":
                final_merged_df[col] = merge_and_mean_tests_data_from(col)
    final_merged_df = pd.DataFrame(final_merged_df) #to dataframe
    final_merged_df["test_name"]=export_data_filename #set test name in cas we need it
    print("Merged shape: {}".format(final_merged_df.values.shape))
    filename=export_data_path +"merged_"+export_data_filename+".csv"
    final_merged_df.to_csv(filename, index=False)
    print("Merged data exported to '{}'".format(filename))
# exit() #for debug

#%%
#
# Start plotting from here
#

#myplot("line", "time", "commits_rate", True, True)
#myplot("line", "time", "tx_exec_rate", True, True)
#myplot("scatter", "index", "commits", True, True)
#myplot("scatter", "time", "commits", True, True)
#myplot("scatter", "commits_rate", "rest_api_batch_rate", True, False)

#myplot_merged("time", "commits_rate", True)
#myplot_merged("time", "tx_exec_rate", True)

#%%
#
# Generate all image data posible
# (CARFUL: creates ~100 images)
#
#for col in final_df_cols:
#    for col2 in final_df_cols:
#        if col != col2 and col2 != "time":
#            print("Generating f({})={}".format(col, col2))
#            myplot("line",col, col2)

#for col in final_df_cols:
#        if col != "time":
#            print("Generating f({})={}".format("time", col))
#            myplot_merged("time", col)

#pl.show()