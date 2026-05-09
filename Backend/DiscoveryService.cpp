#include "DiscoveryService.h"
#include <QNetworkInterface>
#include <QJsonDocument>
#include <QJsonObject>
#include <QHostInfo>
#include <QDateTime>

const quint16 DISCOVERY_PORT = 50000;

DiscoveryService::DiscoveryService(QObject *parent) : QObject(parent) {
    m_localIp = getLocalIp();
    
    m_udpSocket = new QUdpSocket(this);
    m_broadcastTimer = new QTimer(this);
    m_timeoutTimer = new QTimer(this);

    connect(m_udpSocket, &QUdpSocket::readyRead, this, &DiscoveryService::processDatagrams);
    connect(m_broadcastTimer, &QTimer::timeout, this, &DiscoveryService::broadcastPresence);
    connect(m_timeoutTimer, &QTimer::timeout, this, &DiscoveryService::checkTimeouts);
}

void DiscoveryService::start() {
    m_udpSocket->bind(QHostAddress::AnyIPv4, DISCOVERY_PORT, QUdpSocket::ShareAddress | QUdpSocket::ReuseAddressHint);
    
    m_broadcastTimer->start(2000);
    m_timeoutTimer->start(5000);
    
    broadcastPresence();
}

void DiscoveryService::broadcastPresence() {
    QJsonObject me;
    me["hostname"] = QHostInfo::localHostName();
    me["ip"] = m_localIp;
    me["os"] = "Linux";

    QByteArray datagram = QJsonDocument(me).toJson(QJsonDocument::Compact);
    m_udpSocket->writeDatagram(datagram, QHostAddress::Broadcast, DISCOVERY_PORT);
}

void DiscoveryService::processDatagrams() {
    while (m_udpSocket->hasPendingDatagrams()) {
        QByteArray datagram;
        datagram.resize(m_udpSocket->pendingDatagramSize());
        QHostAddress sender;
        
        m_udpSocket->readDatagram(datagram.data(), datagram.size(), &sender);
        
        if (sender.toString() == m_localIp) continue;

        QJsonDocument doc = QJsonDocument::fromJson(datagram);
        if (doc.isObject()) {
            QJsonObject obj = doc.object();
            QString ip = obj["ip"].toString();
            
            QVariantMap deviceData;
            deviceData["hostname"] = obj["hostname"].toString();
            deviceData["ip"] = ip;
            deviceData["last_seen"] = QDateTime::currentMSecsSinceEpoch();
            
            m_devices.insert(ip, deviceData);
            emit devicesChanged();
        }
    }
}

void DiscoveryService::checkTimeouts() {
    qint64 now = QDateTime::currentMSecsSinceEpoch();
    bool changed = false;

    for (auto it = m_devices.begin(); it != m_devices.end(); ) {
        if (now - it.value()["last_seen"].toLongLong() > 10000) {
            it = m_devices.erase(it);
            changed = true;
        } else {
            ++it;
        }
    }

    if (changed) emit devicesChanged();
}

QVariantList DiscoveryService::activeDevices() const {
    QVariantList list;
    for (const auto& dev : m_devices) {
        list.append(dev);
    }
    return list;
}

QString DiscoveryService::getLocalIp() {
    for (const auto& address : QNetworkInterface::allAddresses()) {
        if (address.protocol() == QAbstractSocket::IPv4Protocol && address != QHostAddress::LocalHost)
            return address.toString();
    }
    return "127.0.0.1";
}