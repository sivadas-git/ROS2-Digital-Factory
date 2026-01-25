using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class CounterReceiver : MonoBehaviour
{
    public int counterValue = 0;

    private TcpListener listener;
    private Thread listenerThread;
    private bool running = true;

    void Start()
    {
        listenerThread = new Thread(StartServer);
        listenerThread.IsBackground = true;
        listenerThread.Start();
    }

    void StartServer()
    {
        listener = new TcpListener(IPAddress.Any, 25050);
        listener.Start();
        Debug.Log("CounterReceiver listening on port 25050");

        while (running)
        {
            try
            {
                using (TcpClient client = listener.AcceptTcpClient())
                using (NetworkStream stream = client.GetStream())
                {
                    byte[] buffer = new byte[64];
                    int length = stream.Read(buffer, 0, buffer.Length);

                    if (length > 0)
                    {
                        string data = Encoding.UTF8.GetString(buffer, 0, length).Trim();
                        if (int.TryParse(data, out int value))
                        {
                            counterValue = value;
                        }
                    }
                }
            }
            catch { }
        }
    }

    void OnApplicationQuit()
    {
        running = false;
        listener?.Stop();
        listenerThread?.Abort();
    }
}
