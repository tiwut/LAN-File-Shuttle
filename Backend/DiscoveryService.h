#pragma once
#include <QObject>
#include <QUdpSocket>
#include <QTimer>
#include <QVariantList>
#include <QVariantMap>
#include <QMap>

class DiscoveryService : public QObject {
    Q_OBJECT
    Q_PROPERTY(QVariantList activeDevices READ activeDevices NOTIFY devicesChanged)

public:
    explicit DiscoveryService(QObject *parent = nullptr);
    QVariantList activeDevices() const;

    Q_INVOKABLE void start();

signals:
    void devicesChanged();

private slots:
    void processDatagrams();
    void broadcastPresence();
    void checkTimeouts();

private:
    QUdpSocket *m_udpSocket;
    QTimer *m_broadcastTimer;
    QTimer *m_timeoutTimer;
    QMap<QString, QVariantMap> m_devices; 
    
    QString m_localIp;
    QString getLocalIp();
};
