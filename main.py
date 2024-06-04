from dataclasses import dataclass, field
from typing import Annotated
from timefold.solver.domain import (planning_entity, planning_solution,
                                    PlanningListVariable, PlanningScore,
                                    PlanningEntityCollectionProperty,
                                    ValueRangeProvider)
from timefold.solver.score import (constraint_provider, SimpleScore,
                                   ConstraintFactory, Constraint)
from timefold.solver.config import (SolverConfig, ScoreDirectorFactoryConfig,
                                    TerminationConfig, Duration)
from timefold.solver import SolverFactory
from random import Random
import turtle

@dataclass
class Location:
   id: int
   latitude: float
   longitude: float
   distance_dict: dict[int, int]
   
   def distance_to(self, other: 'Location') -> int:
       return round(((self.latitude - other.latitude)**2 + (self.longitude - other.longitude)**2)**0.5 * 100)

@planning_entity
@dataclass
class Vehicle:
    start_location: Location
    visits: Annotated[list[Location], PlanningListVariable] = field(default_factory=list)
    
    def total_distance(self) -> int:
        previous = self.start_location
        total = 0
        for visit in self.visits:
            total += previous.distance_dict[visit.id]
            previous = visit
        total += previous.distance_dict[self.start_location.id]
        return total


@planning_solution
@dataclass    
class RoutingPlan:
    vehicles: Annotated[list[Vehicle], PlanningEntityCollectionProperty]
    visits: Annotated[list[Location], ValueRangeProvider]
    score: Annotated[SimpleScore, PlanningScore] = field(default=None)

@constraint_provider
def vrp_constraints(cf: ConstraintFactory) -> list[Constraint]:
    return [
        cf.for_each(Vehicle)
          .penalize(SimpleScore.ONE, lambda vehicle: vehicle.total_distance())
          .as_constraint('Minimize distance')
    ]


def generate_problem():
    random = Random(0)
    location_count = 100
    vehicle_count = 4

    locations = [
        Location(i, random.randint(0, 100), random.randint(0, 100), {})
        for i in range(location_count)
    ]
    for location in locations:
        for i in range(location_count):
            other = locations[i]
            location.distance_dict[i] = location.distance_to(other)
    
    vehicles = [
        Vehicle(random.choice(locations))
        for i in range(vehicle_count)
    ]

    return RoutingPlan(vehicles, locations)


solver_config = SolverConfig(
    solution_class=RoutingPlan,
    entity_class_list=[Vehicle],
    score_director_factory_config=ScoreDirectorFactoryConfig(
        constraint_provider_function=vrp_constraints
    ),
    termination_config=TerminationConfig(
        spent_limit=Duration(seconds=30)
    )
)

solver_factory = SolverFactory.create(solver_config)
solver = solver_factory.build_solver()
solution = solver.solve(generate_problem())


# Draw the solution
random = Random(0)

scale = 5
turtle.colormode(255)
turtle.setup(100 * scale, 100 * scale)
turtle.title(f'Routing plan - Score {solution.score.score}')
offset = 50 * scale
for vehicle in solution.vehicles:
    color = (random.randint(0, 256), random.randint(0, 256), random.randint(0, 256))
    turtle.teleport(vehicle.start_location.latitude * scale - offset, vehicle.start_location.longitude * scale - offset)
    turtle.color(color)
    turtle.dot(3 * scale)
    turtle.pendown()
    for visit in vehicle.visits:
        turtle.goto(visit.latitude * scale - offset, visit.longitude * scale - offset)
        turtle.dot(scale)
    turtle.goto(vehicle.start_location.latitude * scale - offset, vehicle.start_location.longitude * scale - offset)
    turtle.penup()

turtle.done()
