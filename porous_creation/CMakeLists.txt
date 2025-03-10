find_package(
  Python
  COMPONENTS Interpreter Development.Module NumPy
  REQUIRED)
find_package(OpenMP REQUIRED)

set(cython_modules_cpp floodfill_voronoi)

foreach(cython_module ${cython_modules_cpp})
  add_custom_command(
    OUTPUT ${cython_module}.cxx
    COMMENT "Generating ${cython_module}.cxx from ${cython_module}.pyx"
    COMMAND
      Python::Interpreter -m cython --cplus
      "${CMAKE_CURRENT_SOURCE_DIR}/${cython_module}.pyx" --output-file
      ${cython_module}.cxx
    VERBATIM)
  python_add_library(${cython_module} MODULE ${cython_module}.cxx WITH_SOABI)
  target_include_directories(${cython_module}
                             PRIVATE "." ${Python_NumPy_INCLUDE_DIRS})
  target_link_libraries(${cython_module} PRIVATE OpenMP::OpenMP_CXX)
  install(TARGETS ${cython_module} DESTINATION plugins/porous_creation/)
endforeach()
