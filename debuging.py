from graph.base import Graph, Edge, Vertex


g = Graph()
t1 = g.create_vertex(1)
t2 = g.create_vertex(2)
t3 = g.create_vertex(3)
t4 = g.create_vertex(4)
# Vertex(value=1)
# t1 > t2
# t2 < t3
# print("#"  * 100    )

class burp:
    pass

r1 = t3 > t1
r2 = t3 - t1
r3 = t3 < t1
r3 = t3 < t2
r4 = (t3 < t3)(burp())

print(t1.graph.edges)	

g2 = Graph()
t12 = g2.create_vertex(12)
t22 = g2.create_vertex(22)

t12 > t22
t12 - t22
t22 > t12
print(g2.edges)
# print(g.edges)

g3 = Graph()
t13 = g3.create_vertex(13)
t23 = g3.create_vertex(23)
t33 = g3.create_vertex(33)

((t13 > t23)("one") - t33)("two")
print(g3.edges)

