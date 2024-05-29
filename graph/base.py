import enum
import json
import warnings
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Direction(enum.Enum):
    LEFT = enum.auto()
    RIGHT = enum.auto()
    NONE = enum.auto()


class GraphError(Exception):
    pass


class GraphWarning(Warning):
    pass


class Hashable(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    def __hash__(self) -> int:
        return hash(self.id)


class Graph(BaseModel):
    vertices: set["Vertex"] = set()
    edges: set["Edge"] = set()

    _keeper = None

    def create_vertex(self, data) -> "Vertex":
        Graph._keeper = self
        vertex = Vertex(value=data, graph=self)
        self.vertices.add(vertex)
        Graph._keeper = None
        return vertex

    class MemberClass(Hashable):
        def __init__(self, **data) -> None:
            if Graph._keeper is None:
                raise GraphError(
                    "You must create a vertex through a graph using the 'create_vertex' \
method."
                )
            super().__init__(**data)


class Vertex(Graph.MemberClass):
    value: Any = None
    graph: Graph = None

    def save_relationship(func) -> None:
        def wrapper(self, vertex: "Vertex", *args, **kwargs):
            edge = func(self, vertex, *args, **kwargs)
            # for some reason the hash is not working...
            if hash(edge) in [hash(e) for e in self.graph.edges]:
                warnings.warn(f"Edge '{edge}' already exists", GraphWarning)
            else:
                self.graph.edges.add(edge)
            return edge

        return wrapper

    def _create_edge(self, vertex: "Vertex", value: Any = None) -> "Edge":
        return Edge(weight=value, vertex1=self, vertex2=vertex, _graph=self.graph)
    
    @save_relationship
    def edge(self, vertex: "Vertex", value: Any = None) -> "Edge":
        return self._create_edge(vertex, value)

    @save_relationship
    def ledge(self, vertex: "Vertex", value: Any = None) -> "Edge":
        e = self._create_edge(vertex, value)
        e.direction = Direction.LEFT
        return e

    @save_relationship
    def redge(self, vertex: "Vertex", value: Any = None) -> "Edge":
        e = self._create_edge(vertex, value)
        e.direction = Direction.RIGHT
        return e

    def __lt__(self, other: "Vertex") -> "Edge":
        return self.ledge(other)

    def __gt__(self, other: "Vertex") -> "Edge":
        return self.redge(other)

    def __sub__(self, other: "Vertex") -> "Edge":
        return self.edge(other)

    def __str__(self) -> str:
        try:
            val = json.dumps(self.value)
        except TypeError:
            val = str(self.value)
        return f"(value: {val})"

    __repr__ = __str__


class Edge(Hashable):
    vertex1: Vertex = None
    vertex2: Vertex = None
    direction: Direction = Direction.NONE
    weight: Any = None
        
    def __init__(self, **data) -> None:
        _graph = data.pop("_graph")
        if _graph is None:
            raise GraphError(
                "To create an edge you must go through a vertex using the 'edge', 'ledge', \
'redge' methods (or '-', '<', '>' operators) or pass _graph."
            )
        vertex1 = data["vertex1"]
        vertex2 = data["vertex2"]
        if vertex1 is None or vertex2 is None:
            raise GraphError("You must pass vertex1 and vertex2.")
        if vertex1.graph != vertex2.graph:
            raise GraphError("Vertices must belong to the same graph.")
        if vertex1.graph != _graph:
            vertex1_str = f'{data["vertex1"]}'
            vertex2_str = f'{data["vertex2"]}'
            warnings.warn(f"Vertices '{vertex1_str}' and '{vertex2_str}' are not \
members of ther target graph: they will be cloned.", GraphWarning)
            data["vertex1"] = _graph.create_vertex(vertex1.dict())
            data["vertex2"] = _graph.create_vertex(vertex2.dict())
        super().__init__(**data)
        

    def _get_unique_id(self) -> str:
        return f"{hash(self.vertex1)}{hash(self.vertex2)}{self.direction}{self.weight}"

    def __hash__(self) -> int:
        return hash(self._get_unique_id())

    def __call__(self, weight: Any) -> "Edge":
        self.weight = weight
        return self

    def __str__(self) -> str:
        if self.weight is None:
            rel_weight = ""
        else:
            try:
                weight_str = json.dumps(self.weight)
            except TypeError:
                weight_str = str(self.weight)
            rel_weight = f"weight: {weight_str}"
        rel_str = f"--[{rel_weight}]--"
        if self.direction == Direction.LEFT:
            rel_str = "<" + rel_str
        elif self.direction == Direction.RIGHT:
            rel_str = rel_str + ">"
        return f"{self.vertex1} {rel_str} {self.vertex2}"

    __repr__ = __str__
