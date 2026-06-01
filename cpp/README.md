# Adventure Game C++ Port

This is a console C++17 port of the current Adventure Game story, combat,
shops, potion flow, and web-style Game Over menu.

Cloud saves are not included in the C++ port because the current Python and web
cloud clients depend on HTTP and JSON behavior that would require extra C++
dependencies. The C++ port uses local saves in `saves/cpp_autosave.cppsave`.

## Linux

```sh
cmake -S cpp -B build/cpp-linux
cmake --build build/cpp-linux
./build/cpp-linux/adventure-game
```

## Windows From Linux With MinGW

Install a MinGW cross-compiler that provides `x86_64-w64-mingw32-g++`, then run:

```sh
cmake -S cpp -B build/cpp-windows \
  -DCMAKE_SYSTEM_NAME=Windows \
  -DCMAKE_CXX_COMPILER=x86_64-w64-mingw32-g++
cmake --build build/cpp-windows
```

The Windows executable will be `build/cpp-windows/adventure-game.exe`.

## Windows Native

With CMake and a C++17 compiler installed:

```bat
cmake -S cpp -B build\cpp-windows
cmake --build build\cpp-windows --config Release
build\cpp-windows\Release\adventure-game.exe
```
