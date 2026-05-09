#include "TransferEngine.h"
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>

TransferEngine::TransferEngine(QObject *parent) : QObject(parent) {
    m_socket = new QTcpSocket(this);
    
    // Once connected, start sending
    connect(m_socket, &QTcpSocket::connected, this, &TransferEngine::onEncrypted);
    connect(m_socket, &QTcpSocket::bytesWritten, this, &TransferEngine::writeNextChunk);
}

void TransferEngine::sendFileSecurely(const QString& ip, int port, const QString& filePath) {
    m_currentFile = new QFile(filePath, this);
    if (!m_currentFile->open(QIODevice::ReadOnly)) {
        emit transferComplete(false, "Cannot open file.");
        return;
    }
    m_totalBytes = m_currentFile->size();
    m_bytesSent = 0;
    
    m_socket->connectToHost(ip, port); // Connect to the ReceiveEngine!
}

void TransferEngine::onEncrypted() {
    QJsonObject meta;
    meta["filename"] = QFileInfo(m_currentFile->fileName()).fileName();
    meta["filesize"] = m_totalBytes;
    
    QByteArray metaData = QJsonDocument(meta).toJson();
    quint32 size = metaData.size();
    
    m_socket->write(reinterpret_cast<const char*>(&size), sizeof(size));
    m_socket->write(metaData);
}

void TransferEngine::writeNextChunk() {
    if (!m_currentFile) return;
    
    QByteArray chunk = m_currentFile->read(65536); 
    if (chunk.isEmpty()) {
        m_currentFile->close();
        m_currentFile->deleteLater();
        m_currentFile = nullptr;
        m_socket->disconnectFromHost();
        emit transferComplete(true, "Transfer finished successfully!");
        return;
    }
    
    m_socket->write(chunk);
    m_bytesSent += chunk.size();
    m_progress = (m_bytesSent * 100) / m_totalBytes;
    emit progressChanged();
}

int TransferEngine::progress() const { return m_progress; }
QString TransferEngine::speed() const { return m_speed; }