import collections

class FeatureSpace(object):
    def __init__(self, sentences, min_count=None, append_unknown=True):
        counts = collections.Counter(self.extract(sentences))
        self.space = [f for f in counts if min_count is None or counts[f] >= min_count]

        default_index = len(self.space) if append_unknown else -1
        self.ispace = collections.defaultdict(lambda:default_index, {f:i for i,f in enumerate(self.space)})
        if append_unknown:
            self.space.append(None)

    def index(self, f):
        return self.ispace[f]

    def feature(self, i):
        return self.space[i]

    def size(self):
        return len(self.space)

    def extract(self, sentence):
        raise NotImplementedError("Subclasses must implement this!")

class SupertagSpace(FeatureSpace):
    def __init__(self, sentences, min_count=None, append_unknown=True):
        super(SupertagSpace, self).__init__(sentences, min_count, append_unknown)

    def extract(self, sentences):
        for tokens, supertags in sentences:
            for s in supertags:
                yield s

class EmbeddingSpace(FeatureSpace):
    def __init__(self, sentences, min_count=None, append_unknown=True):
        super(EmbeddingSpace, self).__init__(sentences, min_count, append_unknown)

        # To be set by the configuration.
        self.embedding_size = None

    def extract(self, sentences):
        for tokens, supertags in sentences:
            for t in tokens:
                yield self.extract_from_token(t)

    def extract_from_token(self, token):
        raise NotImplementedError("Subclasses must implement this!")

class PretrainedEmbeddingSpace(EmbeddingSpace):
    def __init__(self, embeddings_file, debug=False):
        already_added = set()
        self.embedding_size = None
        self.space = []
        self.embeddings = []
        with open(embeddings_file) as f:
            for i,line in enumerate(f.readlines()):
                if debug and i > 10:
                    break

                splits = line.split()
                word = splits[0].lower()

                if i == 0 and word != "*unknown*":
                    raise ValueError("First embedding in the file should represent the unknown word.")
                if word not in already_added:
                    embedding = [float(s) for s in splits[1:]]

                    if self.embedding_size is None:
                        self.embedding_size = len(embedding)
                    elif self.embedding_size != len(embedding):
                        raise ValueError("Dimensions mismatch. Expected {} but was {}.".format(self.embedding_size, len(embedding)))

                    already_added.add(word)
                    self.space.append(word)
                    self.embeddings.append(embedding)

        self.space = list(self.space)
        self.ispace = collections.defaultdict(lambda:0, {f:i for i,f in enumerate(self.space)})

class WordSpace(PretrainedEmbeddingSpace):
    def __init__(self, embeddings_file, debug=False):
        super(WordSpace, self).__init__(embeddings_file, debug)

    def extract_from_token(self, token):
        return token.lower()

class PrefixSpace(EmbeddingSpace):
    def __init__(self, sentences, n, min_count=None, append_unknown=True):
        self.n = n
        super(PrefixSpace, self).__init__(sentences, min_count, append_unknown)

    def extract_from_token(self, token):
        return token[:self.n]

class SuffixSpace(EmbeddingSpace):
    def __init__(self, sentences, n, min_count=None, append_unknown=True):
        self.n = n
        super(SuffixSpace, self).__init__(sentences, min_count, append_unknown)

    def extract_from_token(self, token):
        return token[-self.n:]
