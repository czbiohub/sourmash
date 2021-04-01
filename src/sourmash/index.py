"An Abstract Base Class for collections of signatures."

from abc import abstractmethod, ABC
from collections import namedtuple


class Index(ABC):
    @abstractmethod
    def signatures(self):
        "Return an iterator over all signatures in the Index object."

    @abstractmethod
    def insert(self, signature):
        """ """

    @abstractmethod
    def save(self, path, storage=None, sparseness=0.0, structure_only=False):
        """ """

    @classmethod
    @abstractmethod
    def load(cls, location, leaf_loader=None, storage=None, print_version_warning=True):
        """ """

    def find(self, search_fn, *args, **kwargs):
        """Use search_fn to find matching signatures in the index.

        search_fn(other_sig, *args) should return a boolean that indicates
        whether other_sig is a match.

        Returns a list.
        """

        matches = []

        for node in self.signatures():
            if search_fn(node, *args):
                matches.append(node)
        return matches

    def search(self, query, threshold=None,
               do_containment=False, do_max_containment=False,
               ignore_abundance=False, **kwargs):
        """Return set of matches with similarity above 'threshold'.

        Results will be sorted by similarity, highest to lowest.

        Optional arguments accepted by all Index subclasses:
          * do_containment: default False. If True, use Jaccard containment.
          * best_only: default False. If True, allow optimizations that
            may. May discard matches better than threshold, but first match
            is guaranteed to be best.
          * ignore_abundance: default False. If True, and query signature
            and database support k-mer abundances, ignore those abundances.

        Note, the "best only" hint is ignored by LinearIndex.
        """

        # check arguments
        if threshold is None:
            raise TypeError("'search' requires 'threshold'")
        threshold = float(threshold)

        if do_containment and do_max_containment:
            raise TypeError("'do_containment' and 'do_max_containment' cannot both be True")

        # configure search - containment? ignore abundance?
        if do_containment:
            query_match = lambda x: query.contained_by(x, downsample=True)
        elif do_max_containment:
            query_match = lambda x: query.max_containment(x, downsample=True)
        else:
            query_match = lambda x: query.similarity(
                x, downsample=True, ignore_abundance=ignore_abundance)

        # do the actual search:
        matches = []

        for ss in self.signatures():
            score = query_match(ss)
            if score >= threshold:
                matches.append((score, ss, self.filename))

        # sort!
        matches.sort(key=lambda x: -x[0])
        return matches

    def gather(self, query, *args, **kwargs):
        "Return the match with the best Jaccard containment in the Index."
        if not query.minhash:             # empty query? quit.
            return []

        scaled = query.minhash.scaled
        if not scaled:
            raise ValueError('gather requires scaled signatures')

        threshold_bp = kwargs.get('threshold_bp', 0.0)
        threshold = 0.0

        # are we setting a threshold?
        if threshold_bp:
            # if we have a threshold_bp of N, then that amounts to N/scaled
            # hashes:
            n_threshold_hashes = float(threshold_bp) / scaled

            # that then requires the following containment:
            threshold = n_threshold_hashes / len(query.minhash)

            # is it too high to ever match? if so, exit.
            if threshold > 1.0:
                return []

        # actually do search!
        results = []
        for ss in self.signatures():
            cont = query.minhash.contained_by(ss.minhash, True)
            if cont and cont >= threshold:
                results.append((cont, ss, self.filename))

        results.sort(reverse=True, key=lambda x: (x[0], x[1].md5sum()))

        return results

    @abstractmethod
    def select(self, ksize=None, moltype=None):
        ""

class LinearIndex(Index):
    "An Index for a collection of signatures. Can load from a .sig file."
    def __init__(self, _signatures=None, filename=None):
        self._signatures = []
        if _signatures:
            self._signatures = list(_signatures)
        self.filename = filename

    def signatures(self):
        return iter(self._signatures)

    def __len__(self):
        return len(self._signatures)

    def insert(self, node):
        self._signatures.append(node)

    def save(self, path):
        from .signature import save_signatures
        with open(path, 'wt') as fp:
            save_signatures(self.signatures(), fp)

    @classmethod
    def load(cls, location):
        from .signature import load_signatures
        si = load_signatures(location, do_raise=True)

        lidx = LinearIndex(si, filename=location)
        return lidx

    def select(self, ksize=None, moltype=None):
        def select_sigs(ss, ksize=ksize, moltype=moltype):
            if (ksize is None or ss.minhash.ksize == ksize) and \
               (moltype is None or ss.minhash.moltype == moltype):
               return True

        return self.filter(select_sigs)

    def filter(self, filter_fn):
        siglist = []
        for ss in self._signatures:
            if filter_fn(ss):
                siglist.append(ss)

        return LinearIndex(siglist, self.filename)


class MultiIndex(Index):
    """An Index class that wraps other Index classes.

    The MultiIndex constructor takes two arguments: a list of Index
    objects, and a matching list of sources (filenames, etc.)  If the
    source is not None, then it will be used to override the 'filename'
    in the triple that is returned by search and gather.

    One specific use for this is when loading signatures from a directory;
    MultiIndex will properly record which files provided which signatures.
    """
    def __init__(self, index_list, source_list):
        self.index_list = list(index_list)
        self.source_list = list(source_list)
        assert len(index_list) == len(source_list)

    def signatures(self):
        for idx in self.index_list:
            for ss in idx.signatures():
                yield ss

    def __len__(self):
        return sum([ len(idx) for idx in self.index_list ])

    def insert(self, *args):
        raise NotImplementedError

    @classmethod
    def load(self, *args):
        raise NotImplementedError

    def save(self, *args):
        raise NotImplementedError

    def select(self, ksize=None, moltype=None):
        new_idx_list = []
        new_src_list = []
        for idx, src in zip(self.index_list, self.source_list):
            idx = idx.select(ksize=ksize, moltype=moltype)
            new_idx_list.append(idx)
            new_src_list.append(src)

        return MultiIndex(new_idx_list, new_src_list)

    def filter(self, filter_fn):
        new_idx_list = []
        new_src_list = []
        for idx, src in zip(self.index_list, self.source_list):
            idx = idx.filter(filter_fn)
            new_idx_list.append(idx)
            new_src_list.append(src)

        return MultiIndex(new_idx_list, new_src_list)

    def search(self, query, *args, **kwargs):
        # do the actual search:
        matches = []
        for idx, src in zip(self.index_list, self.source_list):
            for (score, ss, filename) in idx.search(query, *args, **kwargs):
                best_src = src or filename # override if src provided
                matches.append((score, ss, best_src))
                
        # sort!
        matches.sort(key=lambda x: -x[0])
        return matches

    def gather(self, query, *args, **kwargs):
        "Return the match with the best Jaccard containment in the Index."
        # actually do search!
        results = []
        for idx, src in zip(self.index_list, self.source_list):
            for (score, ss, filename) in idx.gather(query, *args, **kwargs):
                best_src = src or filename # override if src provided
                results.append((score, ss, best_src))
            
        results.sort(reverse=True, key=lambda x: (x[0], x[1].md5sum()))

        return results