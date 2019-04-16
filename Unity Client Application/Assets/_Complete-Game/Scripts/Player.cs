using UnityEngine;
using System.Collections.Generic;
using UnityEngine.UI;	//Allows us to use UI.
using UnityEngine.SceneManagement;
using UnityEngine.Networking;

namespace Completed
{
    //Player inherits from MovingObject, our base class for objects that can move, Enemy also inherits from this.
    public class Player : MovingObject
    {
        public float restartLevelDelay = 1f;        //Delay time in seconds to restart level.
        public int pointsPerFood = 10;              //Number of points to add to player food points when picking up a food object.
        public int pointsPerSoda = 20;              //Number of points to add to player food points when picking up a soda object.
        public int wallDamage = 1;                  //How much damage a player does to a wall when chopping it.
        public Text foodText;                       //UI Text to display current player food total.
        public AudioClip moveSound1;                //1 of 2 Audio clips to play when player moves.
        public AudioClip moveSound2;                //2 of 2 Audio clips to play when player moves.
        public AudioClip eatSound1;                 //1 of 2 Audio clips to play when player collects a food object.
        public AudioClip eatSound2;                 //2 of 2 Audio clips to play when player collects a food object.
        public AudioClip drinkSound1;               //1 of 2 Audio clips to play when player collects a soda object.
        public AudioClip drinkSound2;               //2 of 2 Audio clips to play when player collects a soda object.
        public AudioClip gameOverSound;             //Audio clip to play when player dies.
        public Text playerText;
        public string playerString;
        public int horizontal_actual = 0;
        public int vertical_actual = 0;
        public string text_id;
        public int client_id;
       

        private Animator animator;                  //Used to store a reference to the Player's animator component.
        public int food = 100;                           //Used to store player food points total during level.
#if UNITY_IOS || UNITY_ANDROID || UNITY_WP8 || UNITY_IPHONE
        private Vector2 touchOrigin = -Vector2.one;	//Used to store location of screen touch origin for mobile controls.
#endif


        //Start overrides the Start function of MovingObject
        protected override void Start()
        {

            GameManager.instance.AddPlayerToList(this);
            //  playerText = GameObject.Find(playerString).GetComponent<Text>();
            //Get a component reference to the Player's animator component
            animator = GetComponent<Animator>();
            //Get the current food point total stored in GameManager.instance between levels.
            food = GameManager.instance.playerFoodPoints;

            //Set the foodText to reflect the current player food total.
            //foodText.text = "Food: " + food;
            SoundManager.instance.musicSource.Stop();
            foodText = GameObject.Find(text_id).GetComponent<Text>();

            //Call the Start function of the MovingObject base class.
            base.Start();
            Debug.Log(this.transform.position.x);

        }


        //This function is called when the behaviour becomes disabled or inactive.
        private void OnDisable()
        {
            //When Player object is disabled, store the current local food total in the GameManager so it can be re-loaded in next level.
            //GameManager.instance.playerFoodPoints = food;
        }


        private void Update()
        {
            //If it's not the player's turn, exit the function.
            //if (!GameManager.instance.playersTurn) return;

            int horizontal = horizontal_actual;
            int vertical = vertical_actual;
            //Debug.Log(this.gameObject.tag);
            //Get input from the input manager, round it to an integer and store in horizontal to set x axis move direction

            horizontal = (int)(Input.GetAxisRaw("Horizontal"));
            //Debug.Log(horizontal);

            //Get input from the input manager, round it to an integer and store in vertical to set y axis move direction
            vertical = (int)(Input.GetAxisRaw("Vertical"));


            //Check if moving horizontally, if so set vertical to zero.
            if (horizontal != 0)
            {
                vertical = 0;
            }


            if (horizontal != 0 || vertical != 0)
            {
                horizontal_actual = horizontal;
                vertical_actual = vertical;
            }

            foodText.text = "Player " +client_id.ToString() + ": " + food.ToString();
        }
		

        public void UpdatePlayerState(List<GameManager.PlayerGameState> player_list)
        {
            //Debug.Log("nicenicenice");
            //Check if we have a non-zero value for horizontal or vertical
            bool found = false;
            foreach(var player in player_list)
            {
                if(client_id == player.id)
                {
                    found = true;
                    food = player.power;
                    AttemptMove<Wall>(player.current_location.x, player.current_location.y);

                    if (player.dead == "true")
                    {
                        Destroy(gameObject);
                    }
                }
            }
            if (found == false)
            {
                Destroy(gameObject);
            }
            //if (horizontal_actual != 0 || vertical_actual != 0)
            //{
                    //Call AttemptMove passing in the generic parameter Wall, since that is what Player may interact with if they encounter one (by attacking it)
                    //Pass in horizontal and vertical as parameters to specify the direction to move Player in.
            //        AttemptMove<Wall>(horizontal_actual, vertical_actual);
            //}
        }


        public void SendMove()
        {
            if (client_id == GameManager.instance.client_id)
            {
                GameManager.instance.sendMovements(horizontal_actual, vertical_actual, client_id);
            }
        }

        //AttemptMove overrides the AttemptMove function in the base class MovingObject
        //AttemptMove takes a generic parameter T which for Player will be of the type Wall, it also takes integers for x and y direction to move in.
        protected override void AttemptMove <T> (int xDir, int yDir)
		{
            //Every time player moves, subtract from food points total.
            //food--;

            //Update food text display to reflect current score.
            //foodText.text = "Food: " + food;
            if (this.gameObject.tag == "Player")
            {
                Debug.Log(xDir);
            }
            //Call the AttemptMove method of the base class, passing in the component T (in this case Wall) and x and y direction to move.
            base.AttemptMove <T> (xDir, yDir);
			
			//Hit allows us to reference the result of the Linecast done in Move.
			RaycastHit2D hit;
			
			//If Move returns true, meaning Player was able to move into an empty space.
			if (Move (xDir, yDir, out hit)) 
			{
				//Call RandomizeSfx of SoundManager to play the move sound, passing in two audio clips to choose from.
				SoundManager.instance.RandomizeSfx (moveSound1, moveSound2);
			}
			
			//Since the player has moved and lost food points, check if the game has ended.
			//CheckIfGameOver ();
			
			//Set the playersTurn boolean of GameManager to false now that players turn is over.
			GameManager.instance.playersTurn = false;
		}
		
		
		//OnCantMove overrides the abstract function OnCantMove in MovingObject.
		//It takes a generic parameter T which in the case of Player is a Wall which the player can attack and destroy.
		protected override void OnCantMove <T> (T component)
		{

		}
		
		
		//OnTriggerEnter2D is sent when another object enters a trigger collider attached to this object (2D physics only).
		private void OnTriggerEnter2D (Collider2D other)
		{
            //Check if the tag of the trigger collided with is Exit.
            // if (other.tag == "Exit")
            //{
            //    //Invoke the Restart function to start the next level with a delay of restartLevelDelay (default 1 second).
            //    Invoke("Restart", restartLevelDelay);

            //Disable the player object since level is over.
            //     enabled = false;
            // }

            //Check if the tag of the trigger collided with is Food.
            //else 
            if (other.tag == "Food")
			{
				//Add pointsPerFood to the players current food total.
				//#food += pointsPerFood;
				
				//Update foodText to represent current total and notify player that they gained points
				//foodText.text = "+" + pointsPerFood + " Food: " + food;
				
				//Call the RandomizeSfx function of SoundManager and pass in two eating sounds to choose between to play the eating sound effect.
				SoundManager.instance.RandomizeSfx (eatSound1, eatSound2);
				
				//Disable the food object the player collided with.
				other.gameObject.SetActive (false);
			}
			
			//Check if the tag of the trigger collided with is Soda.
			else if(other.tag == "Soda")
			{
				//Add pointsPerSoda to players food points total
				//food += pointsPerSoda;
				
				//Update foodText to represent current total and notify player that they gained points
				//foodText.text = "+" + pointsPerSoda + " Food: " + food;
				
				//Call the RandomizeSfx function of SoundManager and pass in two drinking sounds to choose between to play the drinking sound effect.
				SoundManager.instance.RandomizeSfx (drinkSound1, drinkSound2);
				
				//Disable the soda object the player collided with.
				other.gameObject.SetActive (false);
			}
		}
		
		
		//Restart reloads the scene when called.
		private void Restart ()
		{
			//Load the last scene loaded, in this case Main, the only scene in the game. And we load it in "Single" mode so it replace the existing one
            //and not load all the scene object in the current scene.
            SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex, LoadSceneMode.Single);
		}
		
		
		//CheckIfGameOver checks if the player is out of food points and if so, ends the game.
		private void CheckIfGameOver ()
		{
			//Check if food point total is less than or equal to zero.
			if (food <= 0) 
			{
				//Call the PlaySingle function of SoundManager and pass it the gameOverSound as the audio clip to play.
				SoundManager.instance.PlaySingle (gameOverSound);
				
				//Stop the background music.
				SoundManager.instance.musicSource.Stop();
				
				//Call the GameOver function of GameManager.
				GameManager.instance.GameOver (this.gameObject.tag);
			}
		}
	}
}

