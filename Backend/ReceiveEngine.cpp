#include "ReceiveEngine.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QUrl>

ReceiveEngine::ReceiveEngine(QObject *parent) : QObject(parent) {
    if (m_server.listen(QHostAddress::AnyIPv4, 65432)) {
        connect(&m_server, &QTcpServer::newConnection, this, &ReceiveEngine::onNewConnection);
    }
}

void ReceiveEngine::onNewConnection() {
    if (m_client) return; 
    
    m_client = m_server.nextPendingConnection();
    m_state = ReadingMetadata;
    m_bytesReceived = 0;
    m_progress = 0;
    
    connect(m_client, &QTcpSocket::readyRead, this, &ReceiveEngine::onReadyRead);
    connect(m_client, &QTcpSocket::disconnected, this, &ReceiveEngine::onClientDisconnected);
}

void ReceiveEngine::onReadyRead() {
    if (m_state == ReadingMetadata) {
        if (m_client->bytesAvailable() < 4) return;
        
        quint32 metaSize;
        m_client->peek(reinterpret_cast<char*>(&metaSize), sizeof(metaSize));
        
        if (m_client->bytesAvailable() < metaSize + 4) return;
        
        m_client->read(reinterpret_cast<char*>(&metaSize), sizeof(metaSize));
        QByteArray metaData = m_client->read(metaSize);
        QJsonObject meta = QJsonDocument::fromJson(metaData).object();
        
        m_fileName = meta["filename"].toString();
        m_expectedFileSize = meta["filesize"].toVariant().toLongLong();
        emit currentFileNameChanged();
        
        m_state = WaitingForUser;
        emit incomingTransfer(m_fileName, m_expectedFileSize);
        return; 
    }
    
    if (m_state == ReceivingData && m_file) {
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
            m_state = Idle;
        }
    }
}

void ReceiveEngine::acceptTransfer(const QString& savePath) {
    if (m_state != WaitingForUser) return;
    
    QString realPath = QUrl(savePath).toLocalFile(); 
    if (realPath.isEmpty()) realPath = savePath;
    
    m_file = new QFile(realPath, this);
    if (m_file->open(QIODevice::WriteOnly)) {
        m_state = ReceivingData;
        
        if (m_client->bytesAvailable() > 0) {
            onReadyRead();
        }
    } else {
        rejectTransfer();
    }
}

void ReceiveEngine::rejectTransfer() {
    if (m_client) m_client->disconnectFromHost();
    m_state = Idle;
}

void ReceiveEngine::onClientDisconnected() {
    if (m_client) {
        m_client->deleteLater();
        m_client = nullptr;
    }
    if (m_file) {
        m_file->close();
        m_file->deleteLater();
        m_file = nullptr;
    }
    m_state = Idle;
}

int ReceiveEngine::receiveProgress() const { return m_progress; }
QString ReceiveEngine::currentFileName() const { return m_fileName; }