using UnityEngine;
using UnityEngine.SceneManagement;
using System.Collections;
using UnityEngine.Networking;

namespace Completed
{
	using System.Collections.Generic;		//Allows us to use Lists. 
	using UnityEngine.UI;					//Allows us to use UI.
	
	public class GameManager : MonoBehaviour
	{
		public float levelStartDelay = 2f;						//Time to wait before starting level, in seconds.
		public float turnDelay = 0.1f;                          //Delay between each Player turn.
        public int boardSize = 8;
        public int playerFoodPoints = 100;						//Starting value for Player food points.
		public static GameManager instance = null;				//Static instance of GameManager which allows it to be accessed by any other script.
		[HideInInspector] public bool playersTurn = true;       //Boolean to check if it's players turn, hidden in inspector but public.

        public Button connectButton;
        public Button readyButton;
        public InputField inputField;

        private Text levelText;									//Text to display current level number.
        public Text foodText;
        public Text reconnectingText;
		private GameObject levelImage;							//Image to block out level as levels are being set up, background for levelText.
        private GameObject reconnectingImage;
        private GameObject foodObject;
		private BoardManager boardScript;						//Store a reference to our BoardManager which will set up the level.
        private Camera camera;
        private UnityHttpListener listenerScript;
		private int level = 1;									//Current level number, expressed in game as "Day 1".
		private List<Enemy> enemies;                            //List of all Enemy units, used to issue them move commands.
        private List<Player> players;                            //List of all Player units, used to issue them move commands.
        private bool enemiesMoving;								//Boolean to check if enemies are moving.
		private bool doingSetup = true;                         //Boolean to check if we're setting up board, prevent Player from moving during setup.
        public float timeLeft = 5f;
        private int storedTurn = 0;
        public string ip_to_connect;
        public int client_id = 0; // 0 by default, will change
        public int request_num = 0;
        public int num_players;
        public int is_first_initialize = 0;
        public string game_state_json_from_listener;
        private bool waiting_on_gamestate = false;
        private bool reconnecting = false;


        [System.Serializable]
        public class Coord
        {
            public int x;
            public int y;

            public static Coord CreateFromJSON(string jsonString)
            {
                return JsonUtility.FromJson<Coord>(jsonString);
            }

            // Given JSON input:
            // {"name":"Dr Charles","lives":3,"health":0.8}
            // this example will return a PlayerInfo object with
            // name == "Dr Charles", lives == 3, and health == 0.8f.
        }

        [System.Serializable]
        public class PlayerGameState
        {
            public int id;
            public Coord current_location;
            public int power;
            public string dead;
            public List<string> intended_move;

            public static PlayerGameState CreateFromJSON(string jsonString)
            {
                return JsonUtility.FromJson<PlayerGameState>(jsonString);
            }

            // Given JSON input:
            // {"name":"Dr Charles","lives":3,"health":0.8}
            // this example will return a PlayerInfo object with
            // name == "Dr Charles", lives == 3, and health == 0.8f.
        }

        [System.Serializable]
        public class GameState
        {
            public List<Coord> powerup_locations;
            public List<Coord> cracked_locations;
            public List<Coord> stable_locations;
            public List<Coord> hole_locations;
            public List<PlayerGameState> player_list;
            public int board_size;

            public static GameState CreateFromJSON(string jsonString)
            {
                return JsonUtility.FromJson<GameState>(jsonString);
            }

            // Given JSON input:
            // {"name":"Dr Charles","lives":3,"health":0.8}
            // this example will return a PlayerInfo object with
            // name == "Dr Charles", lives == 3, and health == 0.8f.
        }

        [System.Serializable]
        public class GameUpdate
        {
            public GameState GameState;
            public string Type;

            public static GameUpdate CreateFromJSON(string jsonString)
            {
                return JsonUtility.FromJson<GameUpdate>(jsonString);
            }

        }

        [System.Serializable]
        public class ClientJoin
        {
            public int Client_ID;
            public int N_Request;
            public string Reconnecting;
            public string Type;

            public static GameState CreateFromJSON(string jsonString)
            {
                return JsonUtility.FromJson<GameState>(jsonString);
            }

        }

        //Awake is always called before any Start functions

        void Awake()
		{
            //Check if instance already exists
            if (instance == null)

                //if not, set instance to this
                instance = this;

            //If instance already exists and it's not this:
            else if (instance != this)

                //Then destroy this. This enforces our singleton pattern, meaning there can only ever be one instance of a GameManager.
                Destroy(gameObject);	
			
			//Sets this to not be destroyed when reloading scene
			DontDestroyOnLoad(gameObject);
			
			//Assign enemies to a new List of Enemy objects.
			enemies = new List<Enemy>();

            //Assign players to a new List of Player objects.
            players = new List<Player>();

            //Get a component reference to the attached BoardManager script
            boardScript = GetComponent<BoardManager>();
            listenerScript = GetComponent <UnityHttpListener>();

			//Call the InitGame function to initialize the first level 
			InitGame();

        }

        void onSubmitIp(string arg0)
        {
            //Output this to console when Button1 or Button3 is clicked
            ip_to_connect = arg0 + ":5000";


        }

        IEnumerator Upload(string url, string json, string type)
        {
            var uwr = new UnityWebRequest(url, "POST");
            byte[] jsonToSend = new System.Text.UTF8Encoding().GetBytes(json);
            uwr.uploadHandler = (UploadHandler)new UploadHandlerRaw(jsonToSend);
            uwr.downloadHandler = (DownloadHandler)new DownloadHandlerBuffer();
            Debug.Log("message " + json);
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
                if (type.Equals("client_join"))
                {
                    ClientJoin client_join_message = JsonUtility.FromJson<ClientJoin>(uwr.downloadHandler.text);
                    client_id = client_join_message.Client_ID;
                    if (client_join_message.Reconnecting != null)
                    {
                        reconnecting = true;
                    }
                }



            }
        }

        public void sendMovements(int x, int y, int client_id)
        {
            string move = "S"; //dont move
            if (x == 1)
            {
                 move = "R";
            }
            else if (x == -1)
            {
                move = "L";
            }
            else if (y == 1)
            {
                move = "U";
            }
            else if (y == -1)
            {
                move = "D";
            }


            string connect_message = " {\"Type\": \"PlayerMovement\", \"Operation\": [\"" + move + "\"]," + " \"Client_ID\": " + client_id + ",\"N_Request\": " + request_num + "} ";

            Debug.Log(connect_message);
            StartCoroutine(Upload("http://" + ip_to_connect + "/PlayerMovement", (string)connect_message, "movement") );
            request_num += 1;
        }

        void ConnectClick()
        {
            //Output this to console when Button1 or Button3 is clicked
            Debug.Log("You have clicked the connect button!");
            connectButton.gameObject.SetActive(false);
            levelText.text = "Please ready up";
            Debug.Log(ip_to_connect);
            string connect_message = " {\"Type\": \"ClientJoin\", \"N_Request\": " + request_num + "} ";
            Debug.Log(ip_to_connect + "/ClientJoin");
            StartCoroutine(Upload("http://" + ip_to_connect + "/ClientJoin", connect_message, "client_join"));

            inputField.gameObject.SetActive(false);
            readyButton.gameObject.SetActive(true);
            listenerScript.StartServer();
            request_num += 1;

        }

        void ReadyClick()
        {
            //Output this to console when Button1 or Button3 is clicked

            string ready_message = " {\"Type\": \"Ready\", \"Client_ID\": " + client_id + ",\"N_Request\": " + request_num + "} ";
            Debug.Log(ready_message);
            StartCoroutine(Upload("http://" + ip_to_connect + "/Ready", ready_message, "ready"));

            levelText.text = "Waiting for other players..";
            Debug.Log("You have clicked the ready button!");
            request_num += 1;

        }

        //this is called only once, and the paramter tell it to be called only after the scene was loaded
        //(otherwise, our Scene Load callback would be called the very first load, and we don't want that)
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static public void CallbackInitialization()
        {
            //register the callback to be called everytime the scene is loaded
            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        //This is called each time a scene is loaded.
        static private void OnSceneLoaded(Scene arg0, LoadSceneMode arg1)
        {
            instance.level++;
            instance.InitGame();
        }

		
		//Initializes the game for each level.
		void InitGame()
		{
			//While doingSetup is true the player can't move, prevent player from moving while title card is up.
			doingSetup = true;
			
			//Get a reference to our image LevelImage by finding it by name.
			levelImage = GameObject.Find("LevelImage");
            reconnectingImage = GameObject.Find("ReconnectingImage");


            foodText = GameObject.Find("TimeText").GetComponent<Text>();
            foodText.text = "Time Left -> " + (int)timeLeft;

            //Get a reference to our text LevelText's text component by finding it by name and calling GetComponent.
            levelText = GameObject.Find("LevelText").GetComponent<Text>();
            reconnectingText = GameObject.Find("ReconnectingText").GetComponent<Text>();


            //Set the text of levelText to the string "Day" and append the current level number.
            levelText.text = "Welcome";
            reconnectingText.text = "Reconnecting...";
			
			//Set levelImage to active blocking player's view of the game board during setup.
			levelImage.SetActive(true);

            connectButton = GameObject.Find("Connect_Button").GetComponent<Button>();
            readyButton = GameObject.Find("Ready_Button").GetComponent<Button>();
            inputField = GameObject.Find("Input_Field").GetComponent<InputField>();
            camera = GameObject.Find("Main Camera").GetComponent<Camera>();
            inputField.onEndEdit.AddListener(onSubmitIp);  // This also works
            connectButton.onClick.AddListener(ConnectClick);
            readyButton.onClick.AddListener(ReadyClick);

            readyButton.gameObject.SetActive(false);

            //Call the HideLevelImage function with a delay in seconds of levelStartDelay.
            //Invoke("HideLevelImage", levelStartDelay);

            //Clear any Enemy objects in our List to prepare for next level.
            enemies.Clear();
            //Call the SetupScene function of the BoardManager script, pass it current level number.
            //UpdateGameState();

        }


        //Hides black image used between levels
        void HideLevelImage()
		{
			//Disable the levelImage gameObject.
			levelImage.SetActive(false);
            inputField.gameObject.SetActive(false);
            readyButton.gameObject.SetActive(false);
            connectButton.gameObject.SetActive(false);
            //Set doingSetup to false allowing player to move again.
			doingSetup = false;
		}

        //Hides black image used between levels
        void HideReconnectingImage()
        {
            //Disable the levelImage gameObject.
            reconnectingImage.SetActive(false);
        }

        //Update is called every frame.
        void Update()
        {
            //Check that playersTurn or enemiesMoving or doingSetup are not currently true.
            //if(playersTurn || enemiesMoving || doingSetup)

            //If any of these are true, return and do not start MoveEnemies.
            //return;

            //Start moving enemies.
            //StartCoroutine(MoveEnemies());

            if (reconnecting == true)
            {
                reconnectingImage.SetActive(true);
            }
            else
            {
                reconnectingImage.SetActive(false);
            }

            if (is_first_initialize == 1)
            {
                if (listenerScript.turn == storedTurn)
                {
                    if (waiting_on_gamestate)
                    {
                        timeLeft = 0;
                    }
                    else
                    {
                        timeLeft -= Time.deltaTime;
                    }
                        //Debug.Log(timeLeft);

                        if (timeLeft < 0)
                        {
                            //Start moving players.
                            if (waiting_on_gamestate == false)
                            {
                                StartCoroutine(SendMovePlayers());
                                waiting_on_gamestate = true;
                                timeLeft = 5f;
                            }

                        }

                        foodText.text = ("Time Left -> " + (int)timeLeft);

                }
                else
                {
                    reconnecting = false;
                    waiting_on_gamestate = false;
                    game_state_json_from_listener = listenerScript.game_state;
                    UpdateGameState(game_state_json_from_listener);
                    storedTurn += 1;
                    timeLeft = 5f;

                }
            }
            else
            {
                if (listenerScript.turn != storedTurn)
                {
                    reconnecting = false;
                    game_state_json_from_listener = listenerScript.game_state;
                    Debug.Log(game_state_json_from_listener + "-> THIS IS THE FIRST TURN" );
                    UpdateGameState(game_state_json_from_listener);
                    Invoke("HideLevelImage", levelStartDelay);
                    storedTurn += 1;
                    timeLeft = 5f;

                }
            }
        }

        IEnumerator waiter()
        {
            //Wait for 2 seconds
            yield return new WaitForSeconds(1);
        }


        //Call this to add the passed in Enemy to the List of Enemy objects.
        public void AddEnemyToList(Enemy script)
		{
			//Add Enemy to List enemies.
			enemies.Add(script);
		}


        //Call this to add the passed in Player to the List of Player objects.
        public void AddPlayerToList(Player script)
        {
            //Add Enemy to List enemies.
            players.Add(script);
            Debug.Log(script.gameObject.tag);
        }


        //GameOver is called when the player reaches 0 food points
        public void GameOver(string tag)
		{
			//Set levelText to display number of levels passed and game over message
			levelText.text = "#1 idiot " +  tag + " lost.";
			
			//Enable black background image gameObject.
			levelImage.SetActive(true);
			
			//Disable this GameManager.
			enabled = false;
		}
		
		//Coroutine to move enemies in sequence.
		IEnumerator MoveEnemies()
		{
			//While enemiesMoving is true player is unable to move.
			enemiesMoving = true;
			
			//Wait for turnDelay seconds, defaults to .1 (100 ms).
			yield return new WaitForSeconds(turnDelay);
			
			//If there are no enemies spawned (IE in first level):
			if (enemies.Count == 0) 
			{
				//Wait for turnDelay seconds between moves, replaces delay caused by enemies moving when there are none.
				yield return new WaitForSeconds(turnDelay);
			}
			
			//Loop through List of Enemy objects.
			for (int i = 0; i < enemies.Count; i++)
			{
				//Call the MoveEnemy function of Enemy at index i in the enemies List.
				enemies[i].MoveEnemy ();
				
				//Wait for Enemy's moveTime before moving next Enemy, 
				yield return new WaitForSeconds(enemies[i].moveTime);
			}
			//Once Enemies are done moving, set playersTurn to true so player can move.
			playersTurn = true;
			
			//Enemies are done moving, set enemiesMoving to false.
			enemiesMoving = false;
		}

        //Coroutine to move players in sequence.
        IEnumerator SendMovePlayers()
        {

            //Wait for turnDelay seconds, defaults to .1 (100 ms).
            yield return new WaitForSeconds(0.1f);

            //If there are no enemies spawned (IE in first level):
            if (players.Count == 0)
            {
                //Wait for turnDelay seconds between moves, replaces delay caused by enemies moving when there are none.
                yield return new WaitForSeconds(turnDelay);
            }

            //Loop through List of Player objects.
            for (int i = 0; i < players.Count; i++)
            {
                //Debug.Log("moiving");
                //Call the MoveEnemy function of Enemy at index i in the enemies List.
                players[i].SendMove();

                //Wait for Enemy's moveTime before moving next Enemy, 
                yield return new WaitForSeconds(players[i].moveTime);
            }

        }

        GameState parseGameStateJson(string data)
        {
            //string data = "{ \"powerup_locations\": [{\"x\": 0, \"y\":3}], \"cracked_locations\": [{\"x\": 0, \"y\":1}, {\"x\": 2, \"y\":2}], \"stable_locations\": [{\"x\": 0, \"y\":0}, {\"x\": 2, \"y\":1}, {\"x\": 2, \"y\":0}, {\"x\": 1, \"y\":1}, {\"x\": 1, \"y\":0}, {\"x\": 0, \"y\":2}], \"hole_locations\": [{\"x\": 1, \"y\":2}], \"player_list\": [{\"id\": 0, \"current_location\": {\"x\": 1, \"y\":1}, \"power\": 1}, {\"id\": 1, \"current_location\": {\"x\": 1, \"y\":2}, \"power\": 0, \"dead\":true}, {\"id\": 2, \"current_location\": {\"x\": 5, \"y\":5}, \"power\": 0, \"dead\":true}, {\"id\": 3, \"current_location\": {\"x\": 6, \"y\":6}, \"power\": 0, \"dead\":true} ]}";
            GameState loadedData = JsonUtility.FromJson<GameUpdate>(data).GameState;
            return loadedData;
        }

        void UpdateGameState(string data)
        {
            GameState gamestate = parseGameStateJson(data);
            Debug.Log(gamestate.board_size);
            Debug.Log(gamestate.board_size.ToString() + "-> this is teh board size");
            List<Vector3> powerupList = new List<Vector3>();
            List<Vector3> crackedList = new List<Vector3>();
            List<Vector3> stableList = new List<Vector3>();
            List<Vector3> holeList = new List<Vector3>();

            foreach (var powerup in gamestate.powerup_locations)
            {
                float x = (float)powerup.x;
                float y = (float)powerup.y;
                Vector3 powerupVector = new Vector3(x, y, 0f);
                powerupList.Add(powerupVector);

            }

            foreach (var cracked in gamestate.cracked_locations)
            {
                float x = (float)cracked.x;
                float y = (float)cracked.y;
                Vector3 powerupVector = new Vector3(x, y, 0f);
                crackedList.Add(powerupVector);

            }

            foreach (var stable in gamestate.hole_locations)
            {
                float x = (float)stable.x;
                float y = (float)stable.y;
                Vector3 holeVector = new Vector3(x, y, 0f);
                holeList.Add(holeVector);

            }

            if (is_first_initialize == 0)
            {
                is_first_initialize = 1;
                Debug.Log(gamestate.board_size);
                CreateBoard((int)gamestate.board_size);
                InitialiseObjects(gamestate.player_list, crackedList, powerupList, holeList);
                
            }
            else
            {
                boardScript.InstantiateWalls(crackedList);
                boardScript.InstantiatePowerups(powerupList);
                boardScript.InstantiateHoles(holeList);

                // move and do gamestate stuff 
                foreach (var player in players)
                {
                    player.UpdatePlayerState(gamestate.player_list);

                }
            }
        }

        void CreateBoard(int boardsize)
        {
            Debug.Log("Creating Board with " + boardsize.ToString());
            boardScript.rows = boardsize;
            boardScript.columns = boardsize;
            boardScript.SetupScene(level);
            updateCamera(boardsize);

        }

        void InitialiseObjects(List<PlayerGameState> players, List<Vector3> walls, List<Vector3> powerups, List<Vector3> holes)
        {
            boardScript.InstantiatePlayers(players);
            boardScript.InstantiateWalls(walls);
            boardScript.InstantiatePowerups(powerups);
            boardScript.InstantiateHoles(holes);

            }

            void updateCamera(int boardSize)
        {
            Debug.Log("Board Size equals " + boardSize);
            float xy = (float)((boardSize) / 2f) - 0.5f;
            Debug.Log(xy);
            camera.transform.position = new Vector3(xy, xy, -10f);
            Debug.Log(camera.transform.position);
            camera.orthographicSize = (float)(boardSize/2f) + 1f;
            Debug.Log(camera.orthographicSize);

        }







    }
}

