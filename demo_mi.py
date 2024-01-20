"""
Experimenting with mutual information / interaction measures
"""

import time
import warnings

import pandas as pd

import numpy as np
from scipy import stats

# A hacked up version to be fast using dataframe tricks (groupby)

def compute_pairwise_dependencies(df):
    avg_unique = {}
    cols = df.columns

    # Compute a hacked up mutual information
    for c in df.columns:
        this_avg_unique = df.groupby(c).nunique().mean()
        this_avg_unique[c] = 1
        avg_unique[c] = np.log(this_avg_unique)

    avg_unique = pd.DataFrame(avg_unique)
    avg_unique = avg_unique[cols]
    avg_unique = avg_unique.loc[cols]
    avg_unique = .5 * (avg_unique + avg_unique.T)
    avg_unique /= np.log(df.shape[0])

    # Compute a pearson correlation for floats
    float_df = df.select_dtypes(float)
    # Remove the floats that are actually discrete values in disguise
    card_floats = float_df.nunique()
    float_cols = card_floats[card_floats > .1 * float_df.shape[0]].index
    float_df = float_df[float_cols]
    for i, col_i in enumerate(float_cols):
        for j, col_j in enumerate(float_cols):
            if i > j:
                continue
            this_value = -np.log(stats.spearmanr(float_df[col_i], float_df[col_j], axis=0).statistic)
            avg_unique.loc[col_i, col_j] = this_value
            avg_unique.loc[col_j, col_i] = this_value

    return avg_unique


# Use adjusted rand index, which makes more sense
from sklearn.metrics import adjusted_rand_score

def compute_pairwise_ari(df):
    avg_unique = pd.DataFrame()
    cols = df.columns

    # Compute a pearson correlation for floats
    float_df = df.select_dtypes(float)
    # Remove the floats that are actually discrete values in disguise
    card_floats = float_df.nunique()
    float_cols = card_floats[card_floats > .1 * float_df.shape[0]].index
    float_df = float_df[float_cols]
    for i, col_i in enumerate(float_cols):
        for j, col_j in enumerate(float_cols):
            if i > j:
                continue
            this_value = stats.spearmanr(float_df[col_i], float_df[col_j], axis=0).statistic
            avg_unique.loc[col_i, col_j] = this_value
            avg_unique.loc[col_j, col_i] = this_value

    # Compute an adjusted rand index for all the rest
    for i, col_i in enumerate(df.columns):
        for j, col_j in enumerate(df.columns):
            if i >= j:
                continue
            if (col_i in float_cols) and (col_j in float_cols):
                continue
            df_i = df[col_i]
            df_j = df[col_j]
            if df_i.isna().any():
                if df_i.dtype.kind == 'O':
                    replacement = 'skrub NaN'
                elif df_i.dtype.kind == 'i':
                    replacement = -999
                elif df_i.dtype.kind == 'f':
                    replacement = -9999
                df_i = df_i.fillna(value=replacement)
            if df_j.isna().any():
                if df_j.dtype.kind == 'O':
                    replacement = 'skrub NaN'
                elif df_j.dtype.kind == 'i':
                    replacement = -999
                elif df_j.dtype.kind == 'f':
                    replacement = -9999
                df_j = df_j.fillna(value=replacement)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                this_value = adjusted_rand_score(df_i, df_j)
            avg_unique.loc[col_i, col_j] = this_value
            avg_unique.loc[col_j, col_i] = this_value

    avg_unique = avg_unique[cols]
    avg_unique = avg_unique.loc[cols]
    return avg_unique


# Apply it to datasets
from skrub import datasets

from matplotlib import pyplot as plt
import seaborn as sns
for fetcher in [datasets.fetch_medical_charge,
                datasets.fetch_open_payments,
                #datasets.fetch_road_safety, # Dtype problems
                #datasets.fetch_traffic_violations, # Too big for now
                datasets.fetch_drug_directory,
                datasets.fetch_employee_salaries]:
    data = fetcher()
    df = data.X

    t0 = time.time()
    pairwise_mi = compute_pairwise_dependencies(df)
    dt = int(time.time() - t0)
    print(f"compute_pairwise_dependencies for {fetcher.__name__}: {dt}s")

    # A quick visualization
    plt.figure()
    sns.heatmap(pairwise_mi, cmap='gist_earth')

    plt.subplots_adjust(left=.4, bottom=.4, top=.99, right=.99)

    plt.figure()
    t0 = time.time()
    pairwise_ari = compute_pairwise_ari(df)
    dt = int(time.time() - t0)
    print(f"compute_pairwise_ari for {fetcher.__name__}: {dt}s")
    sns.heatmap(pairwise_ari, cmap='gist_earth_r')


    plt.subplots_adjust(left=.4, bottom=.4, top=.99, right=.99)
