using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

namespace Testing
{
    public class GetData : MonoBehaviour
    {
        // Start is called before the first frame update
        void Start()
        {
            StartCoroutine(Receive());
        }

        IEnumerator Receive()
        {
            UnityWebRequest www = UnityWebRequest.Get("server-name");
            yield return www.SendWebRequest();

            if (www.isNetworkError || www.isHttpError)
            {
                Debug.Log(www.error);
            }
            else
            {
                Debug.Log(www.downloadHandler.text);
            }

            byte[] results = www.downloadHandler.data;
        }
    }   
}
