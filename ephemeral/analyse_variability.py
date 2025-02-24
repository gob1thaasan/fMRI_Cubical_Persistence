#!/usr/bin/env python3
#
# Analyses the variability of representations (either summary statistic
# curves or persistence images) for the data set.

import argparse
import json

import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np
import pandas as pd

from tqdm import tqdm


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('INPUT', type=str, help='Input file')

    parser.add_argument(
        '-s', '--statistic',
        help='Summary statistic to use. If not set, defaults to assuming a '
             'persistence image data structure.',
        type=str,
        default='',
    )

    parser.add_argument(
        '-r', '--rolling',
        help='If set, uses a rolling window to smooth data.',
        type=int,
        default=0
    )

    # TODO: this should be made configurable
    parser.add_argument(
        '-d', '--drop',
        action='store_true',
        help='If set, drops measurements unrelated to the movie'
    )

    parser.add_argument(
        '-g', '--group',
        help='If set, groups according to cohort.',
        action='store_true'
    )

    args = parser.parse_args()

    with open(args.INPUT) as f:
        data = json.load(f)

    X = []

    for subject in tqdm(sorted(data.keys()), desc='Subject'):

        # Check whether we are dealing with a proper subject, or an
        # information key in the data.
        try:
            _ = int(subject)
        except ValueError:
            continue

        # Deal with a persistence image structure, direct extraction is
        # possible.
        if not args.statistic:

            # Remove data from the relevant statistic if so desired by
            # the client. This makes sense if not all time steps are
            # relevant for the experiment.
            #
            # TODO: make extent of drop configurable
            if args.drop:
                x = data[subject][7:]
            else:
                x = data[subject]

            if args.rolling == 0:
                X.append(x)
            else:
                df = pd.DataFrame(x)
                df = df.rolling(args.rolling, axis=0, min_periods=1).mean()

                X.append(df.to_numpy())

        # Deals with a summary statistic, requires a proper selection
        # first.
        else:

            # Remove data from the relevant statistic if so desired by
            # the client. This makes sense if not all time steps are
            # relevant for the experiment.
            #
            # TODO: make extent of drop configurable
            if args.drop:
                x = data[subject][args.statistic][7:]
            else:
                x = data[subject][args.statistic]

            if args.rolling == 0:
                X.append(x)
            else:
                df = pd.Series(x)
                df = df.rolling(args.rolling, axis=0, min_periods=1).mean()

                X.append(df.to_numpy())

    X = np.array(X)

    # First dimension of `X` represents the subject, which is the axis
    # we to calculate the mean over in all cases.
    mu = np.mean(X, axis=0)

    D = []

    # Report distance to the mean for each subject
    for index, row in enumerate(X):
        if not args.statistic:
            distances = np.sqrt(np.sum(np.abs(row - mu)**2, axis=-1))
        else:
            distances = np.abs(row - mu)

        D.append(distances)

    D = np.array(D)

    # To make the overall summary comparable, every time step needs to
    # be normalised such that the values are distributed in [0, 1], as
    # this will make it possible to compare *different* time steps. In
    # the 'raw' case, an increase in topological scale would also show
    # up as an increase in variability, even though this is *not* part
    # of the data.
    if not args.group:
        D = (D - np.min(D, axis=0)) / (np.max(D, axis=0) - np.min(D, axis=0))

    df = pd.DataFrame(D)

    df_groups = pd.read_csv('../data/participant_groups.csv')

    if args.group:
        df['cohort'] = df_groups['cluster']
        df['cohort'] = df['cohort'].transform(lambda x: 'g' + str(x))

        def _normalise_cohort(df):
            df = df.select_dtypes(np.number)
            df = (df - df.min()) / (df.max() - df.min())
            return df

        # Make the cohort curves configurable; since we are only showing
        # relative variabilities, this is justified.
        df.loc[:, df.columns.drop('cohort')] = df.groupby('cohort').apply(
            _normalise_cohort
        )

        df = df.groupby('cohort').agg(np.std)                  \
            .apply(lambda x: (x - x.mean()) / x.std(), axis=1) \
            .reset_index().melt(
                'cohort',
                var_name='time',
                value_name='std'
        )

        if args.drop:
            df['time'] += 7

        g = sns.FacetGrid(df, col='cohort', height=2, aspect=3)
        g.map(sns.lineplot, 'time', 'std')

    else:
        df = df.std()

        if args.drop:
            df.index += 7

        df.plot()

        print(df.to_csv(
            index_label='time',
            header=['variability'])
        )

    plt.tight_layout()
    plt.show()
