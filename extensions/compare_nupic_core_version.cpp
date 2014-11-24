#include <string.h>
#include <iostream>
#include <nta/Version.hpp>

int main(int argc, char *argv[])
{
  if (strcmp(argv[1], NUPIC_CORE_VERSION) != 0) {
    std::cout << "Unexpected version of nupic.core! Expected \""
              << argv[1]
              << "\", but detected \""
              << NUPIC_CORE_VERSION << "\""
              << std::endl;
    return 1;
  }

  return 0;
}
