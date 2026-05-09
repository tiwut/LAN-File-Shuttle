#pragma once
#include <QObject>
#include <QTcpServer>
#include <QTcpSocket>
#include <QFile>

class ReceiveEngine : public QObject {
    Q_OBJECT
    Q_PROPERTY(int receiveProgress READ receiveProgress NOTIFY receiveProgressChanged)
    Q_PROPERTY(QString currentFileName READ currentFileName NOTIFY currentFileNameChanged)

public:
    explicit ReceiveEngine(QObject *parent = nullptr);
    int receiveProgress() const;
    QString currentFileName() const;

signals:
    void receiveProgressChanged();
    void currentFileNameChanged();
    void transferFinished(QString message);

private slots:
    void onNewConnection();
    void onReadyRead();
    void onClientDisconnected();

private:
    QTcpServer m_server;
    QTcpSocket* m_client = nullptr;
    QFile* m_file = nullptr;
    
    bool m_readingMetadata = true;
    qint64 m_expectedFileSize = 0;
    qint64 m_bytesReceived = 0;
    
    int m_progress = 0;
    QString m_fileName = "";
};
