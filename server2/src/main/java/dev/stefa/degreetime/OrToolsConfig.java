package dev.stefa.degreetime;

import com.google.ortools.Loader;
import jakarta.annotation.PostConstruct;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OrToolsConfig {

  @PostConstruct
  public void init() {
    // This ensures the C++ native libraries are loaded into the JVM
    // right when Spring Boot initializes this bean.
    Loader.loadNativeLibraries();
    System.out.println("OR-Tools Native Libraries Loaded Successfully!");
  }
}
