#pragma once
#include <QObject>
#include <QTcpServer>
#include <QStringList>

class WebServer : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString serverUrl READ serverUrl NOTIFY serverUrlChanged)
    Q_PROPERTY(QString qrCodeImage READ qrCodeImage NOTIFY qrCodeImageChanged)

public:
    explicit WebServer(QObject *parent = nullptr);
    Q_INVOKABLE void startSharing(const QStringList& files);
    Q_INVOKABLE void stopSharing();

    QString serverUrl() const;
    QString qrCodeImage() const;

signals:
    void serverUrlChanged();
    void qrCodeImageChanged();

private slots:
    void handleNewConnection();

private:
    QTcpServer m_server;
    QStringList m_sharedFiles;
    QString m_serverUrl;
    QString m_qrCodeSvg;
    
    void generateQrCode(const QString& url);
    QString getLocalIp();
};
