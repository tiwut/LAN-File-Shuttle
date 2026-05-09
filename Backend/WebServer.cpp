#include "WebServer.h"
#include <QTcpSocket>
#include <QNetworkInterface>
#include <QFile>
#include <QFileInfo>
#include <QUrl>

WebServer::WebServer(QObject *parent) : QObject(parent) {
    connect(&m_server, &QTcpServer::newConnection, this, &WebServer::handleNewConnection);
}

void WebServer::startSharing(const QStringList& files) {
    m_sharedFiles.clear();
    for (const QString& f : files) {
        m_sharedFiles.append(QUrl(f).toLocalFile());
    }

    if (!m_server.isListening()) {
        m_server.listen(QHostAddress::Any, 8080);
    }
    
    m_serverUrl = QString("http://%1:8080").arg(getLocalIp());
    emit serverUrlChanged();
    generateQrCode(m_serverUrl);
}

void WebServer::stopSharing() {
    m_sharedFiles.clear();
    m_server.close();
    m_serverUrl = "";
    emit serverUrlChanged();
}

void WebServer::handleNewConnection() {
    QTcpSocket *client = m_server.nextPendingConnection();
    connect(client, &QTcpSocket::readyRead, this, [this, client]() {
        QByteArray request = client->readAll();
        QString reqStr = QString::fromUtf8(request);
        
        if (reqStr.startsWith("GET / ")) {
            QString html = "<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>"
                           "<style>body{font-family:sans-serif; background:#f4f5f7; padding:20px; text-align:center;} "
                           "a{display:block; padding:15px; background:#0078D4; color:white; text-decoration:none; border-radius:10px; margin:10px 0;}</style></head>"
                           "<body><h2>🚀 LAN Shuttle Share</h2>";
            
            for (const auto& file : m_sharedFiles) {
                QString name = QFileInfo(file).fileName();
                html += "<a href='/download/" + name + "'>Download " + name + "</a>";
            }
            html += "</body></html>";
            
            QString response = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\nConnection: close\r\n\r\n" + html;
            client->write(response.toUtf8());
            client->disconnectFromHost();
            
        } else if (reqStr.startsWith("GET /download/")) {
            int endIdx = reqStr.indexOf(" HTTP");
            QString requestedFile = reqStr.mid(14, endIdx - 14);
            requestedFile = QUrl::fromPercentEncoding(requestedFile.toUtf8());

            QString filePath = "";
            for (const auto& f : m_sharedFiles) {
                if (QFileInfo(f).fileName() == requestedFile) {
                    filePath = f;
                    break;
                }
            }

            QFile file(filePath);
            if (file.open(QIODevice::ReadOnly)) {
                QString header = QString("HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Disposition: attachment; filename=\"%1\"\r\nContent-Length: %2\r\nConnection: close\r\n\r\n")
                                 .arg(QFileInfo(filePath).fileName()).arg(file.size());
                client->write(header.toUtf8());
                client->write(file.readAll());
                file.close();
            } else {
                QString response = "HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\nFile Not Found.";
                client->write(response.toUtf8());
            }
            client->disconnectFromHost();
        }
    });
    
    connect(client, &QTcpSocket::disconnected, client, &QTcpSocket::deleteLater);
}

QString WebServer::getLocalIp() {
    for (const auto& address : QNetworkInterface::allAddresses()) {
        if (address.protocol() == QAbstractSocket::IPv4Protocol && address != QHostAddress::LocalHost)
            return address.toString();
    }
    return "127.0.0.1";
}

void WebServer::generateQrCode(const QString& url) {
    m_qrCodeSvg = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=";
    emit qrCodeImageChanged();
}

QString WebServer::serverUrl() const {
    return m_serverUrl;
}

QString WebServer::qrCodeImage() const {
    return m_qrCodeSvg;
}