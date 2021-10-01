from __future__ import annotations
from typing import List, Dict, Optional
from pathlib import Path

import json

from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware



class ParticipantNotFound(HTTPException):

    def __init__(self):
        super().__init__(
            status_code=404,
            detail="Participant not found."
        )


class IllegalVote(HTTPException):

    def __init__(self):
        super().__init__(
            status_code=400,
            detail="Illegal vote."
        )


class Participant(BaseModel):

    name: str
    avatar: Optional[str] = None
    points: int = 0
    j_75_played: bool = False
    j_100_played: bool = False

    available_votes: List[int] = [
        12, 10,
        8, 7,
        6, 5,
        4, 3,
        2, 1
    ]

    voted_for: Dict[str, int] = Field(
        default_factory=dict
    )

    can_vote: bool = True
    is_checked: bool = False

    def register_vote_for(
            self,
            voted_by: Participant,
            vote
    ):
        self.voted_by[voted_by.name] = vote
        self.points += vote

    def register_vote_by(
            self,
            vote_for: Participant,
            vote: int
    ) -> Participant:
        if vote not in self.available_votes:
            raise IllegalVote()

        self.available_votes.remove(vote)

        self.voted_for[vote_for.name] = vote

        vote_for.register_vote_by(
            self, vote
        )

        self.can_vote = bool(self.available_votes)

        return vote_for


class Vote(BaseModel):

    voted_by: str
    voted_for: str
    vote: int


class Game(BaseModel):

    participants: List[Participant]
    save_file: Optional[str] = None
    audio_name: Optional[str] = None
    player_name: Optional[str] = None
    voter: Optional[Participant] = None
    vote_buff: Optional[dict] = None

    @classmethod
    def load_game(
            cls,
            load_file: str,
    ) -> Game:
        save_file = Path(load_file)
        with open(save_file, "r") as save:
            data = json.load(save)
        return cls(
            participants=[
                Participant(**val)
                for val in data["participants"]
            ],
            save_file=str(save_file)
        )

    def _get_participant(self, name: str) -> Participant:
        result = self.participants.get(name)
        if result is None:
            raise ParticipantNotFound()
        return result

    def save_game(self):
        with open(self.save_file, "w") as save:
            json.dump(self.dict(), save, indent=2)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get(
    "/game",
    response_model=Game
)
def get_game():
    game = Game.load_game("./game.json")
    return game


@app.post(
    "/game",
)
def save_game(game: Game):
    game.save_game()


@app.post(
    "/reset",
)
def reset_game():
    game = Game.load_game("./default.game.json")
    game.save_file = "game.json"
    game.save_game()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
