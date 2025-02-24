#!/usr/bin/env python
#
# Visualises a persistence diagram (or a set thereof) generated from
# DIPHA, the 'Distributed Persistent Homology Algorithm'. The script
# creates a time-varying visualisation of all diagrams. It assumes a
# set of diagrams comes from the same subject.


import argparse
import sys

import numpy as np
import matplotlib.pyplot as plt

from topology import load_persistence_diagram_dipha
from topology import load_persistence_diagram_json
from topology import PersistenceDiagram

from tqdm import tqdm


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('FILE', nargs='+', type=str)
    parser.add_argument('--title', type=str)

    parser.add_argument(
        '-d', '--dimension',
        default=2,
        type=int,
        help='Dimension to use for visualisation'
    )

    args = parser.parse_args()

    # Required to prepare figures of the same dimensions; this prevents
    # points from jumping around.
    min_creation = sys.float_info.max
    max_creation = -min_creation

    persistence_diagrams = []

    for filename in tqdm(args.FILE, desc='File'):

        if filename.endswith('.bin'):
            dimensions, creation, destruction = load_persistence_diagram_dipha(
                filename
            )
        elif filename.endswith('.json'):
            dimensions, creation, destruction = load_persistence_diagram_json(
                filename
            )

        selected_dimension = args.dimension

        creation = creation[dimensions == selected_dimension]
        destruction = destruction[dimensions == selected_dimension]

        assert len(creation) == len(destruction)

        min_creation = min(min_creation, np.min(creation), np.min(destruction))
        max_creation = max(max_creation, np.max(creation), np.max(destruction))

        persistence_diagrams.append((creation, destruction))

    # This ensures that no division by zero error occurs; this is
    # achieved with the trade-off of changing the colour map.
    n = max(len(persistence_diagrams), 2)

    plt.xlim((min_creation * 1.25, max_creation * 1.25))
    plt.ylim((min_creation * 1.25, max_creation * 1.25))

    plt.gca().set_aspect('equal')

    for index, (creation, destruction) in enumerate(persistence_diagrams):

        colours = len(creation) * [index]
        plt.scatter(
            x=creation,
            y=destruction,
            c=colours,
            vmin=0,
            vmax=n - 1,
            cmap='Spectral',
            alpha=1.0 - index / (n - 1) + 0.01,
        )

    if args.title:
        plt.title(args.title)

        # TODO: make configurable
        output = '/tmp/' + args.title.replace(' ', '_') + '.png'
        plt.savefig(output, bbox_inches = 'tight')
    else:
        plt.show()
