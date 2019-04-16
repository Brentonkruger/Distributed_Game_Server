using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

namespace Testing
{
    public class PostData : MonoBehaviour
    {
        // Start is called before the first frame update
        void Start()
        {
            // First parameter is the server, second parameter is the json file
            // Both need to be replaced
            StartCoroutine(Upload("server-name", "json-file"));
        }

        IEnumerator Upload(string url, string json)
        {
            var uwr = new UnityWebRequest(url, "POST");
            byte[] jsonToSend = new System.Text.UTF8Encoding().GetBytes(json);
            uwr.uploadHandler = (UploadHandler)new UploadHandlerRaw(jsonToSend);
            uwr.downloadHandler = (DownloadHandler)new DownloadHandlerBuffer();

            // Change parameters
            uwr.SetRequestHeader("Content-Type", "application/json");

            yield return uwr.SendWebRequest();

            if (uwr.isNetworkError)
            {
                Debug.Log("Error while sending: " + uwr.error);
            }
            else
            {
                Debug.Log("Received: " + uwr.downloadHandler.text);
            }
        }
    }
}

