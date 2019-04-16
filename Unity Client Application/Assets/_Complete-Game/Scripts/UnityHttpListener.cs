using UnityEngine;
using UnityEngine.Networking;
using System;
using System.IO;
using System.Net;
using System.Threading;
using System.Net.Sockets;

namespace Completed
{
    public class UnityHttpListener : MonoBehaviour
    {

        private HttpListener listener;
        private Thread listenerThread;
        public int turn = 1;
        public string body;
        public string game_state;
        public static int GetRandomUnusedPort()
        {
            var listener = new TcpListener(IPAddress.Any, 0);
            listener.Start();
            var port = ((IPEndPoint)listener.LocalEndpoint).Port;
            listener.Stop();
            return port;
        }

        public void StartServer()
        {
            int port = GetRandomUnusedPort();
            Debug.Log(port);
            listener = new HttpListener();
            listener.Prefixes.Add("http://localhost:4444/");
            listener.Prefixes.Add("http://127.0.0.1:8050/");
            listener.Prefixes.Add("http://0.0.0.0:" + port + "/");
            listener.Prefixes.Add("http://*:8080/");

            listener.AuthenticationSchemes = AuthenticationSchemes.Anonymous;
            listener.Start();

            listenerThread = new Thread(startListener);
            listenerThread.Start();
            Debug.Log("Server Started");
            //https:///gist.github.com/amimaro/10e879ccb54b2cacae4b81abea455b10

        }

        private void startListener()
        {
            while (true)
            {
                var result = listener.BeginGetContext(ListenerCallback, listener);
                result.AsyncWaitHandle.WaitOne();
            }
        }

        private void ListenerCallback(IAsyncResult result)
        {
            var context = listener.EndGetContext(result);

            Debug.Log("Method: " + context.Request.HttpMethod);
            Debug.Log("LocalUrl: " + context.Request.Url.LocalPath);

            if (context.Request.QueryString.AllKeys.Length > 0)
                foreach (var key in context.Request.QueryString.AllKeys)
                {
                    Debug.Log("Key: " + key + ", Value: " + context.Request.QueryString.GetValues(key)[0]);
                }

            if (context.Request.HttpMethod == "POST")
            {
                Thread.Sleep(1000);
                var data_text = new StreamReader(context.Request.InputStream,
                                    context.Request.ContentEncoding).ReadToEnd();
              
                game_state = data_text.Replace("'", "\"");
                Debug.Log(data_text);


            }

            context.Response.Close();
            turn += 1;
        }

    }
}