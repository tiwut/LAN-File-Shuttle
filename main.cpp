#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include "Backend/TransferEngine.h"
#include "Backend/WebServer.h"
#include "Backend/DiscoveryService.h"

using namespace Qt::StringLiterals;

int main(int argc, char *argv[]) {
    QGuiApplication app(argc, argv);
    app.setOrganizationName("Tiwut");
    app.setApplicationName("LAN Shuttle Pro V3");

    TransferEngine transferEngine;
    WebServer webServer;
    DiscoveryService discoveryService;

    discoveryService.start();

    QQmlApplicationEngine engine;
    
    engine.rootContext()->setContextProperty("transferEngine", &transferEngine);
    engine.rootContext()->setContextProperty("webServer", &webServer);
    engine.rootContext()->setContextProperty("discoveryService", &discoveryService);

    const QUrl url(u"qrc:/qt/qml/ShuttleUI/Main.qml"_s);
    QObject::connect(&engine, &QQmlApplicationEngine::objectCreated,
                     &app, [url](QObject *obj, const QUrl &objUrl) {
        if (!obj && url == objUrl) QCoreApplication::exit(-1);
    }, Qt::QueuedConnection);
    engine.load(url);

    return app.exec();
}