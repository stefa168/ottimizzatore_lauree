package dev.stefa.degreetime;

import lombok.AllArgsConstructor;
import org.jspecify.annotations.NonNull;
import org.jspecify.annotations.NullMarked;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@NullMarked
@AllArgsConstructor
@Component
public class OptimizzationRunner implements CommandLineRunner {
  private final OptimizationService optimizationService;

  @Override
  public void run(String... args) {
    System.out.println("====== STARTING GUROBI TEST ======");

    // Call your method
    String result = optimizationService.testGurobiOptimization();

    System.out.println(result);
    System.out.println("==================================");
  }
}
