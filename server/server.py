#The place where all the replicas logic will be saved.
from VR_replica import replica
import asyncio

#TODO: Add function to check where a player will endup given the gamestate and intended movemnts of all players
#TODO: Add function for logic in player movement


def main():
    rep = replica.replica()
    


if __name__ == '__main__':
    asyncio.run(main())
