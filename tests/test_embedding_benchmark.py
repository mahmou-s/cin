from benchmarks.embedding_benchmark import FakeModel, benchmark
def test_fake_embedding_benchmark():
    result=benchmark(FakeModel(4),['a','bb','ccc'])
    assert result['items']==3
    assert result['dimension']==4
    assert result['items_per_second']>0
