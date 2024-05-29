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

    @save_relationship
    def edge(self, vertex: "Vertex", value: Any = None) -> "Edge":
        return Edge(value=value, vertex1=self, vertex2=vertex)

    @save_relationship
    def ledge(self, vertex: "Vertex", value: Any = None) -> "Edge":
        e = Edge(value=value, vertex1=self, vertex2=vertex)
        e.direction = Direction.LEFT
        return e

    @save_relationship
    def redge(self, vertex: "Vertex", value: Any = None) -> "Edge":
        e = Edge(value=value, vertex1=self, vertex2=vertex)
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
    vertex1: Vertex
    vertex2: Vertex = None
    direction: Direction = Direction.NONE
    value: Any = None

    def _get_unique_id(self) -> str:
        return f"{hash(self.vertex1)}{hash(self.vertex2)}{self.direction}{self.value}"

    def __hash__(self) -> int:
        return hash(self._get_unique_id())

    def __call__(self, value: Any) -> "Edge":
        self.value = value
        return self

    def __str__(self) -> str:
        if self.value is None:
            rel_value = ""
        else:
            try:
                val = json.dumps(self.value)
            except TypeError:
                val = str(self.value)
            rel_value = f"value: {val}"
        rel = f"--[{rel_value}]--"
        if self.direction == Direction.LEFT:
            rel = "<" + rel
        elif self.direction == Direction.RIGHT:
            rel = rel + ">"
        return f"{self.vertex1} {rel} {self.vertex2}"

    __repr__ = __str__

