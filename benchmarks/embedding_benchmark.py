"""Small deterministic embedding benchmark harness; real model results are intentionally not run here."""
from time import perf_counter

def benchmark(model, texts):
    start=perf_counter(); vectors=[model.encode(t) for t in texts]; elapsed=perf_counter()-start
    return {'items':len(texts),'seconds':elapsed,'items_per_second':len(texts)/elapsed if elapsed else 0,'dimension':len(vectors[0]) if vectors else 0}

class FakeModel:
    def __init__(self, dimension=8): self.dimension=dimension
    def encode(self, text): return [float((len(text)+i)%17) for i in range(self.dimension)]

if __name__=='__main__': print(benchmark(FakeModel(),['CIN benchmark']*100))
