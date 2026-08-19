using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class UnityTcpEchoClient : MonoBehaviour
{
    public int portCount = 60;
    private List<TcpListener> listeners = new List<TcpListener>();
    private List<Thread> listenerThreads = new List<Thread>();

    void Start()
    {
        for (int i = 0; i < portCount; i++)
        {
            int port = 32101 + i;
            Thread listenerThread = new Thread(() => ListenOnPort(port));
            listenerThread.IsBackground = true;
            listenerThread.Start();
            listenerThreads.Add(listenerThread);
            Debug.Log($"Started listener on port {port}");
        }
    }

    void ListenOnPort(int port)
    {
        try
        {
            TcpListener server = new TcpListener(IPAddress.Any, port);
            lock (listeners) { listeners.Add(server); }
            server.Start();

            while (true)
            {
                TcpClient client = server.AcceptTcpClient();
                Thread clientThread = new Thread(() => HandleClient(client, port));
                clientThread.IsBackground = true;
                clientThread.Start();
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"Listener error on port {port}: {ex.Message}");
        }
    }

    void HandleClient(TcpClient client, int port)
    {
        try
        {
            NetworkStream stream = client.GetStream();
            byte[] buffer = new byte[1024];
            int bytesRead;

            while ((bytesRead = stream.Read(buffer, 0, buffer.Length)) != 0)
            {
                string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                Debug.Log($"[PORT {port}] IN: {message}");

                byte[] response = Encoding.UTF8.GetBytes(message);
                stream.Write(response, 0, response.Length);
                Debug.Log($"[PORT {port}] OUT: {message}");
            }
        }
        catch (Exception ex)
        {
            Debug.LogWarning($"Client handler error on port {port}: {ex.Message}");
        }
        finally
        {
            client.Close();
        }
    }

    void OnApplicationQuit()
    {
        foreach (TcpListener server in listeners)
        {
            server.Stop();
        }
        foreach (Thread t in listenerThreads)
        {
            if (t.IsAlive)
                t.Abort();
        }
    }
}
