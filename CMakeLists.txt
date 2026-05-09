cmake_minimum_required(VERSION 3.16)
project(LANShuttlePro VERSION 3.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick Network)

if(COMMAND qt_policy)
    qt_policy(SET QTP0001 NEW)
endif()

qt_add_executable(appLANShuttlePro
    main.cpp
    Backend/TransferEngine.cpp Backend/TransferEngine.h
    Backend/WebServer.cpp Backend/WebServer.h
    Backend/DiscoveryService.cpp Backend/DiscoveryService.h
)

qt_add_qml_module(appLANShuttlePro
    URI ShuttleUI
    VERSION 1.0
    QML_FILES Main.qml
)

target_link_libraries(appLANShuttlePro PRIVATE
    Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick Qt6::Network
)
