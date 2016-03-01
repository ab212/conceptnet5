from scipy import sparse
import pandas as pd
from ordered_set import OrderedSet
from collections import defaultdict
from ..vectors import replace_numbers


class SparseMatrixBuilder:
    """
    SparseMatrixBuilder is a utility class that helps build a matrix of
    unknown shape.
    """
    def __init__(self):
        self.row_index = []
        self.col_index = []
        self.values = []

    def __setitem__(self, key, val):
        row, col = key
        self.row_index.append(row)
        self.col_index.append(col)
        self.values.append(val)

    def tocsr(self, shape, dtype=float):
        return sparse.coo_matrix((self.values, (self.row_index, self.col_index)),
                                 shape=shape, dtype=dtype).tocsr()


def build_from_conceptnet_table(filename, orig_index=()):
    """
    Read a file of tab-separated association data from ConceptNet, such as
    `data/assoc/reduced.csv`. Return a SciPy sparse matrix of the associations,
    and a pandas Index of labels.

    If you specify `orig_index`, then the index of labels will be pre-populated
    with existing labels, and any new labels will get index numbers that are
    higher than the index numbers the existing labels use. This is important
    for producing a sparse matrix that can be used for retrofitting onto an
    existing dense labeled matrix (see retrofit.py).
    """
    mat = SparseMatrixBuilder()

    # TODO: rebalance by dataset? Or maybe do that when building the
    # associations in the first place.

    labels = OrderedSet(orig_index)

    totals = defaultdict(float)
    with open(str(filename), encoding='utf-8') as infile:
        for line in infile:
            concept1, concept2, value_str, dataset, relation = line.strip().split('\t')

            index1 = labels.add(replace_numbers(concept1))
            index2 = labels.add(replace_numbers(concept2))
            value = float(value_str)
            mat[index1, index2] = value
            mat[index2, index1] = value
            totals[index1] += value
            totals[index2] += value

    # add self-loops on the diagonal with equal weight to the rest of the row
    for key, value in totals.items():
        mat[key, key] = value

    shape = (len(labels), len(labels))
    index = pd.Index(labels)
    return mat.tocsr(shape), index