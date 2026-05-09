#include "ReceiveEngine.h"
#include <QStandardPaths>
#include <QDir>
#include <QJsonDocument>
#include <QJsonObject>
#include <QDataStream>

ReceiveEngine::ReceiveEngine(QObject *parent) : QObject(parent) {
    // Listen on Port 65432 for incoming files
    if (m_server.listen(QHostAddress::AnyIPv4, 65432)) {
        connect(&m_server, &QTcpServer::newConnection, this, &ReceiveEngine::onNewConnection);
    }
}

void ReceiveEngine::onNewConnection() {
    if (m_client) return; // Only handle one transfer at a time for now
    
    m_client = m_server.nextPendingConnection();
    m_readingMetadata = true;
    m_bytesReceived = 0;
    m_progress = 0;
    
    connect(m_client, &QTcpSocket::readyRead, this, &ReceiveEngine::onReadyRead);
    connect(m_client, &QTcpSocket::disconnected, this, &ReceiveEngine::onClientDisconnected);
}

void ReceiveEngine::onReadyRead() {
    if (m_readingMetadata) {
        if (m_client->bytesAvailable() < 4) return; // Wait for size integer
        
        quint32 metaSize;
        m_client->read(reinterpret_cast<char*>(&metaSize), sizeof(metaSize));
        
        while (m_client->bytesAvailable() < metaSize) {
            m_client->waitForReadyRead(100);
        }
        
        QByteArray metaData = m_client->read(metaSize);
        QJsonObject meta = QJsonDocument::fromJson(metaData).object();
        
        m_fileName = meta["filename"].toString();
        m_expectedFileSize = meta["filesize"].toVariant().toLongLong();
        emit currentFileNameChanged();
        
        // Save to system Downloads folder
        QString downloadsPath = QStandardPaths::writableLocation(QStandardPaths::DownloadLocation);
        m_file = new QFile(QDir(downloadsPath).filePath(m_fileName), this);
        m_file->open(QIODevice::WriteOnly);
        
        m_readingMetadata = false;
    }
    
    // Read actual file data
    if (!m_readingMetadata) {
        QByteArray chunk = m_client->readAll();
        m_file->write(chunk);
        m_bytesReceived += chunk.size();
        
        m_progress = (m_bytesReceived * 100) / m_expectedFileSize;
        emit receiveProgressChanged();
        
        if (m_bytesReceived >= m_expectedFileSize) {
            m_file->close();
            m_file->deleteLater();
            m_file = nullptr;
            emit transferFinished("Received: " + m_fileName);
            m_client->disconnectFromHost();
        }
    }
}

void ReceiveEngine::onClientDisconnected() {
    if (m_client) {
        m_client->deleteLater();
        m_client = nullptr;
    }
}

int ReceiveEngine::receiveProgress() const { return m_progress; }
QString ReceiveEngine::currentFileName() const { return m_fileName; }