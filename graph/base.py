import enum
import json
import warnings
from typing import Any, Union
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

def restrict_member_class_init(cls):
    cls._gate_keeper = None
    
    class MemberClass(Hashable):
        def __init__(self, **data) -> None:
            if cls._gate_keeper is None:
                raise GraphError(f"An object of type '{type(self).__name__}' \
can obly be created through an instance of '{cls.__name__}'.")
            super().__init__(**data)

    setattr(cls, "MemberClass", MemberClass) 
    return cls

@restrict_member_class_init
class Graph(BaseModel):
    vertices: set["Vertex"] = set()
    edges: set["Edge"] = set()

    def create_vertex(self, data) -> "Vertex":
        Graph._gate_keeper = self
        vertex = Vertex(value=data, graph=self)
        Graph._gate_keeper = None
        self.vertices.add(vertex)
        return vertex


@restrict_member_class_init
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

    def _create_edge(self, vertex: "Vertex", weight: Any = None) -> "Edge":
        Vertex._gate_keeper = self
        edge = Edge(weight=weight, vertex1=self, vertex2=vertex, _graph=self.graph)
        Vertex._gate_keeper = None
        return edge

    @save_relationship
    def edge(self, vertex: "Vertex", weight: Any = None) -> "Edge":
        return self._create_edge(vertex, weight)

    @save_relationship
    def ledge(self, vertex: "Vertex", weight: Any = None) -> "Edge":
        edge = self._create_edge(vertex, weight)
        edge.direction = Direction.LEFT
        return edge

    @save_relationship
    def redge(self, vertex: "Vertex", weight: Any = None) -> "Edge":
        edge = self._create_edge(vertex, weight)
        edge.direction = Direction.RIGHT
        return edge

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


class Edge(Vertex.MemberClass):
    vertex1: Vertex = None
    vertex2: Vertex = None
    direction: Direction = Direction.NONE
    weight: Any = None

    def _get_unique_id(self) -> str:
        return f"{hash(self.vertex1)}{hash(self.vertex2)}{self.direction}{self.weight}"

    def __hash__(self) -> int:
        return hash(self._get_unique_id())

    def __call__(self, weight: Any) -> "Edge":
        self.weight = weight
        return self

    def edge(self, other: Union[Vertex, "Edge"], weight: Any = None) -> "Edge":
        if isinstance(other, Vertex):
            return self.vertex2.edge(other, weight)
        return self.vertex2.edge(other.vertex1, weight)

    def ledge(self, other: Union[Vertex, "Edge"], weight: Any = None) -> "Edge":
        if isinstance(other, Vertex):
            return self.vertex2.ledge(other, weight)
        return self.vertex2.ledge(other.vertex1, weight)

    def redge(self, other: Union[Vertex, "Edge"], weight: Any = None) -> "Edge":
        if isinstance(other, Vertex):
            return self.vertex2.rledge(other, weight)
        return self.vertex2.redge(other.vertex1, weight)
    
    def __lt__(self, other: Union[Vertex, "Edge"]) -> "Edge":
        return self.ledge(other)

    def __gt__(self, other: Union[Vertex, "Edge"]) -> "Edge":
        return self.redge(other)

    def __sub__(self, other: Union[Vertex, "Edge"]) -> "Edge":
        return self.edge(other)

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
