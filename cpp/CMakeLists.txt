cmake_minimum_required(VERSION 3.16)

project(AdventureGameCpp VERSION 1.0.0 LANGUAGES CXX)

add_executable(adventure-game adventure_game.cpp)
target_compile_features(adventure-game PRIVATE cxx_std_17)

if(MSVC)
  target_compile_options(adventure-game PRIVATE /W4)
else()
  target_compile_options(adventure-game PRIVATE -Wall -Wextra -pedantic)
endif()
