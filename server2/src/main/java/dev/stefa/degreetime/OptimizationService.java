package dev.stefa.degreetime;

import com.google.ortools.linearsolver.MPConstraint;
import com.google.ortools.linearsolver.MPObjective;
import com.google.ortools.linearsolver.MPSolver;
import com.google.ortools.linearsolver.MPVariable;
import org.springframework.stereotype.Service;

@Service
public class OptimizationService {

  public String testGurobiOptimization() {
    // Instantiate the Gurobi solver
    MPSolver solver = MPSolver.createSolver("GUROBI");

    if (solver == null) {
      return "Error: Could not create solver GUROBI. Check your server environment variables.";
    }

    double infinity = Double.POSITIVE_INFINITY;

    // Variables
    MPVariable x = solver.makeIntVar(0.0, infinity, "x");
    MPVariable y = solver.makeIntVar(0.0, infinity, "y");

    // Constraints
    MPConstraint c0 = solver.makeConstraint(-infinity, 14.0, "c0");
    c0.setCoefficient(x, 1);
    c0.setCoefficient(y, 2);

    MPConstraint c1 = solver.makeConstraint(0.0, infinity, "c1");
    c1.setCoefficient(x, 3);
    c1.setCoefficient(y, -1);

    MPConstraint c2 = solver.makeConstraint(-infinity, 2.0, "c2");
    c2.setCoefficient(x, 1);
    c2.setCoefficient(y, -1);

    // Objective
    MPObjective objective = solver.objective();
    objective.setCoefficient(x, 3);
    objective.setCoefficient(y, 4);
    objective.setMaximization();

    // Solve
    MPSolver.ResultStatus resultStatus = solver.solve();

    if (resultStatus == MPSolver.ResultStatus.OPTIMAL) {
      return String.format("Solved via Gurobi! Max Profit: $%.2f | X: %d, Y: %d",
          objective.value(), (int) x.solutionValue(), (int) y.solutionValue());
    } else {
      return "No optimal solution found.";
    }
  }
}