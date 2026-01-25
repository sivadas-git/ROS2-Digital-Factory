using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.IO;
using UnityEngine;

public class ServerRobot : MonoBehaviour
{
    public int port = 23009;
    private TcpListener listener;
    private Thread listenerThread;

    void Start()
    {
        listener = new TcpListener(IPAddress.Any, port);
        listener.Start();
        Debug.Log($"[VR] Robot TCP Server listening on port {port}");

        listenerThread = new Thread(ListenForClients);
        listenerThread.IsBackground = true;
        listenerThread.Start();
    }

    void ListenForClients()
    {
        try
        {
            while (true)
            {
                TcpClient client = listener.AcceptTcpClient();
                ThreadPool.QueueUserWorkItem(HandleClient, client);
            }
        }
        catch (SocketException)
        {
            // Expected when listener.Stop() is called
        }
        catch (Exception ex)
        {
            Debug.LogError($"[VR] Listener exception: {ex.Message}");
        }
    }

    void HandleClient(object clientObj)
    {
        TcpClient client = (TcpClient)clientObj;

        try
        {
            using (NetworkStream stream = client.GetStream())
            using (StreamReader reader = new StreamReader(stream, Encoding.UTF8))
            using (StreamWriter writer = new StreamWriter(stream, Encoding.UTF8) { AutoFlush = true })
            {
                while (true)
                {
                    // Newline-framed protocol: one message per line
                    string line = reader.ReadLine();
                    if (line == null) break; // client closed

                    // Echo immediately (RTT path)
                    writer.WriteLine(line);

                    // Optional: do parsing/processing AFTER echo if needed
                    // ProcessRobotLine(line);
                }
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"[VR] Client handler exception: {ex.Message}");
        }
        finally
        {
            try { client.Close(); } catch { }
        }
    }

    void OnApplicationQuit()
    {
        try
        {
            listener?.Stop();
        }
        catch { }
    }
}
