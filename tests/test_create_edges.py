from graph.base import Graph

def test_create_edge():
    g = Graph()
    t1 = g.create_vertex(1)
    t2 = g.create_vertex(2)
    t3 = g.create_vertex(3)
    t4 = g.create_vertex(4)
    # t1 > t2
    # t2 < t3
    # print("#"  * 100    )

    class burp:
        pass

    r1 = t3 > t1
    r2 = t3 - t1
    r3 = t3 < t1
    r3 = t3 < t2
    r3 = (t3 < t3)(burp())