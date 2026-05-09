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

    Q_INVOKABLE void acceptTransfer(const QString& savePath);
    Q_INVOKABLE void rejectTransfer();

signals:
    void receiveProgressChanged();
    void currentFileNameChanged();
    void transferFinished(QString message);
    void incomingTransfer(QString fileName, qint64 fileSize);

private slots:
    void onNewConnection();
    void onReadyRead();
    void onClientDisconnected();

private:
    QTcpServer m_server;
    QTcpSocket* m_client = nullptr;
    QFile* m_file = nullptr;
    
    enum State { Idle, ReadingMetadata, WaitingForUser, ReceivingData };
    State m_state = Idle;

    qint64 m_expectedFileSize = 0;
    qint64 m_bytesReceived = 0;
    
    int m_progress = 0;
    QString m_fileName = "";
};
